from configparser import ConfigParser
from typing import List

import psycopg2
from pydantic.fields import Field
from sqlalchemy import create_engine
from fastapi import FastAPI
from pydantic import BaseModel


def config(filename='database.ini', section='postgresql'):
    parser = ConfigParser()
    parser.read(filename)

    db = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            db[param[0]] = param[1]
    else:
        raise Exception(f'Not found section "{section}" in the file "{filename}"')

    return db


db_inf = config()
engine = create_engine(f"postgresql+psycopg2://{db_inf['user']}:{db_inf['password']}@{db_inf['host']}/{db_inf['database']}")
conn = engine.connect()
app = FastAPI()


class User(BaseModel):
    user_id: int
    name: str
    password: str
    accept_invitation: bool = Field(None)
    vote_qty: int


@app.get("/users/", response_model=List[User], response_model_exclude={"password"})
def show_all_users():
    sql = 'SELECT * FROM users ORDER BY user_id;'
    users = conn.execute(sql).fetchall()
    return users