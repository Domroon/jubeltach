from configparser import ConfigParser
from typing import List
import json

from fastapi import FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder
import psycopg2
from psycopg2.errors import UniqueViolation
from pydantic import BaseModel
from pydantic.fields import Field
from sqlalchemy import text
from sqlalchemy import engine_from_config
import sqlalchemy

from playground.create_tables import create_tables


MAX_VOTES_PER_USER = 3


def get_config(filename="database.ini", section="test"):
    parser = ConfigParser()
    parser.read(filename)
    return dict(parser.items(section))


engine = engine_from_config(get_config(), prefix='sqlalchemy.')
app = FastAPI()


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


@app.post("/users/")
async def create_user_list(user_list: List[User]):
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
            connection.execute(insert_user, {"name": user.name, "password": user.password})

    return user_list


@app.get(
    "/users/", response_model=List[UserOut], response_model_exclude={"password"}
)
async def get_all_users():
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


# add vote_for_songname /vote/{user_id}/{song_id}
# - add a function that increase vote_qty from the person who have vote

# - add a link that shows a table with the songs and how much they are voted

# - add songlist delete

# - add userlist delete

# -add user delete

# - add song delete