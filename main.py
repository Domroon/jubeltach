from configparser import ConfigParser
from typing import List
import json

from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from pydantic.fields import Field
from sqlalchemy import text
from sqlalchemy import engine_from_config

from playground.create_tables import create_tables


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


# add vote_for_songname /vote/{user_id}/
# - add a function that increase vote_qty from the person who have vote
# when the person vote valid (valid: not vote the same song twice)
#  - add song_id and user_id in the same column
# - if this column exists it is not valid!