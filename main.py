from configparser import ConfigParser
from typing import List, Optional
from datetime import date, timedelta, datetime

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from pydantic import BaseModel
from pydantic.fields import Field
from sqlalchemy import text
from sqlalchemy import engine_from_config
import sqlalchemy
from jose import JWTError, jwt

from playground.create_tables import create_tables

SECRET_KEY = "6c7161d209dc4182936cfe756ab7ee32c04b6cd4cb8f6925f73a88fe0762f2f1"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 100
MAX_VOTES_PER_USER = 3
ADMIN = "Domroon"
SUPERUSER = "Andreas"


def get_config(filename="database.ini", section="test"):
    parser = ConfigParser()
    parser.read(filename)
    return dict(parser.items(section))


engine = engine_from_config(get_config(), prefix='sqlalchemy.')
app = FastAPI()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class User(BaseModel):
    name: str
    password: str


class UserOut(BaseModel):
    user_id: int
    name: str
    password: str
    accept_invitation: bool = Field(None)
    vote_qty: int = 0


class Song(BaseModel):
    title: str
    interpreter: str
    leadsheet: str
    music: str


class Vote(BaseModel):
    user_id: int
    song_id: int


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    user_id: Optional[str] = None


def get_password_hash(password):
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def authenticate_user(username: str, password: str):
    get_user = text("""
    SELECT user_id, name, password FROM users WHERE name=:name
    """)
    with engine.connect() as connection:
        user = list(connection.execute(get_user, {"name": username}))
    if not user:
        return False
    user = user[0]
    if not verify_password(password, user["password"]):
        return False
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def read_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credential (JWR Error)",
        headers={"WWW-Authenticate": "Bearer"},
    )
    credentials_exception_id = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials (No user_id)",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception_id
        token_data = TokenData(user_id=user_id)
    except JWTError as error:
        raise credentials_exception

    get_user = text("""
    SELECT * FROM users WHERE user_id=:user_id
    """)
    with engine.connect() as connection:
        user_list = list(connection.execute(get_user, {"user_id": token_data.user_id}))
    user = user_list[0]
    return user


def check_user_scope(username: str, usernames: list, ):
    permission_exception = HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Not enough permissions",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if username not in usernames:
        raise permission_exception


@app.post("/users/")
async def create_user_list(user_list: List[User], current_user: User = Depends(read_current_user)):
    check_user_scope(current_user["name"], [ADMIN])
    with engine.connect() as connection:
        connection.execute("DROP TABLE IF EXISTS users")
        create_users = """
        CREATE TABLE users(
            user_id SERIAL PRIMARY KEY,
            name VARCHAR(20) NOT NULL,
            password VARCHAR(255) NOT NULL,
            accept_invitation BOOLEAN,
            vote_qty SMALLINT DEFAULT 0 NOT NULL
        )
        """
        connection.execute(create_users)

        insert_user = text("""
            INSERT INTO users (name, password)
            VALUES (:name, :password)""")
        for user in user_list:
            hashed_password = get_password_hash(user.password)
            user.password = hashed_password
            connection.execute(insert_user, {"name": user.name, "password": user.password})

    return user_list


@app.get(
    "/users/", response_model=List[UserOut], response_model_exclude={"password"}
)
async def get_all_users(current_user: User = Depends(read_current_user)):
    check_user_scope(current_user["name"], [ADMIN, SUPERUSER])
    with engine.connect() as connection:
        sql = "SELECT * FROM users ORDER BY user_id;"
        return list(connection.execute(text(sql)))


@app.patch("/user/status/{user_id}", response_model=List[UserOut], response_model_exclude={"password"})
async def change_invitation_status(user_id: int, answer: bool = None):
    with engine.connect() as connection:
        sql = text("UPDATE users SET accept_invitation=:status WHERE user_id=:id;")
        connection.execute(sql, {"status": answer, "id": user_id})
        sql2 = text("SELECT * FROM users WHERE user_id=:id;")
        user = connection.execute(sql2, {"id": user_id})
        return list(user)


@app.post("/songs/")
async def create_song_list(song_list: List[Song]):
    # song_list_dict = jsonable_encoder(song_list)
    # return song_list_dict
    with engine.connect() as connection:
        connection.execute("DROP TABLE IF EXISTS songs")
        create_songs = """
        CREATE TABLE songs (
            song_id SERIAL PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            interpreter VARCHAR(255) NOT NULL,
            leadsheet VARCHAR(255),
            music VARCHAR(255)
        )
        """
        connection.execute(create_songs)

        insert_song = text("""
            INSERT INTO songs (title, interpreter, leadsheet, music)
            VALUES (:title, :interpreter, :leadsheet, :music)""")
        for song in song_list:
            connection.execute(insert_song, {"title": song.title, "interpreter": song.interpreter, "leadsheet": song.leadsheet, "music": song.music})

    return song_list


@app.get("/songs/")
async def get_all_songs():
    with engine.connect() as connection:
        sql = "SELECT * FROM songs ORDER BY song_id;"
        return list(connection.execute(text(sql)))


@app.post("/votes/")
async def create_votes_table():
    with engine.connect() as connection:
        sql = text("""
        CREATE TABLE IF NOT EXISTS votes(
            user_id INTEGER NOT NULL,
            song_id INTEGER NOT NULL,
            PRIMARY KEY (user_id, song_id),
            FOREIGN KEY (user_id)
                REFERENCES users (user_id)
                ON UPDATE CASCADE ON DELETE CASCADE,
            FOREIGN KEY (song_id)
                REFERENCES songs (song_id)
                ON UPDATE CASCADE ON DELETE CASCADE
        )
        """)
        connection.execute(sql)

        votes = text("SELECT * FROM votes;")

        return votes


@app.post("/vote/{user_id}/{song_id}")
async def vote_for_song_id(user_id: int, song_id: int):
    get_vote_qty = text("""
        SELECT vote_qty FROM users WHERE user_id=:user_id""")

    insert_vote = text("""
        INSERT INTO votes (user_id, song_id)
        VALUES (:user_id, :song_id)""")

    increase_vote_qty = text("""
        UPDATE users SET vote_qty=:vote_qty WHERE user_id=:user_id;
        """)

    with engine.connect() as connection:
        vote_qty_list = connection.execute(get_vote_qty, {"user_id": user_id})
        vote_qty_dict = list(vote_qty_list)[0]
        if vote_qty_dict["vote_qty"] == MAX_VOTES_PER_USER:
            raise HTTPException(status_code=403, detail="The user has reached the maximum number of votes")

        try:
            connection.execute(insert_vote, {"user_id": user_id, "song_id": song_id})
            new_vote_qty = vote_qty_dict["vote_qty"] + 1
            connection.execute(increase_vote_qty, {"vote_qty": new_vote_qty, "user_id": user_id})
        except sqlalchemy.exc.IntegrityError:
            raise HTTPException(status_code=403, detail="The user can only select the same song once")

        show_vote = text("""
        SELECT * FROM votes WHERE user_id=:user_id AND song_id=:song_id;
        """)
        vote = connection.execute(show_vote, {"user_id": user_id, "song_id": song_id})

    return list(vote)[0]

@app.get("/votes")
async def get_all_votes():
    with engine.connect() as connection:
        get_all_votes = """
        SELECT s.song_id, s.title, s.interpreter, COUNT(v.song_id)
        FROM votes as v, songs as s
        WHERE s.song_id=v.song_id
        GROUP BY s.song_id, v.song_id, s.title, s.interpreter
        ORDER BY COUNT(v.song_id) DESC;
        """
    
        votes = connection.execute(get_all_votes)

    return list(votes)


@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user["user_id"])}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/current", response_model=UserOut, response_model_exclude={"password"})
async def get_current_user(current_user: User = Depends(read_current_user)):
    return current_user


# -> add oauth2 security

# - add a link that shows a table with the songs and how much they are voted

# - add song change
# - add songlist delete

# - add userlist delete

# - add user change
# - add user delete

# - add song change
# - add song delete

# - add voteliste delete

