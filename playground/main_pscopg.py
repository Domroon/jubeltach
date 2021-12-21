from configparser import ConfigParser

from fastapi import FastAPI
from fastapi.param_functions import Depends
from pydantic import BaseModel
import psycopg2


class User(BaseModel):
    user_id: int
    name: str
    password: str
    accept_invitation: bool
    vote_qty: int


app = FastAPI()


def config(filename='database.ini', section='postgresql'):
    parser = ConfigParser()
    parser.read(filename)

    db = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            db[param[0]] = param[1]
    else:
        raise Exception(f'Section {section} not found in the {filename} file')

    return db


@app.get("/users/")
async def get_all_users(config: dict = Depends(config)):
    conn = psycopg2.connect(**config)
    cur = conn.cursor()
    cur.execute('SELECT * FROM users ORDER BY user_id;')
    users = cur.fetchall()
    cur.close()
    conn.close()

    return users


@app.get("/user/{user_id}")
async def get_user(user_id: int, config: dict = Depends(config)):
    conn = psycopg2.connect(**config)
    cur = conn.cursor()
    SQL = 'SELECT * FROM users WHERE user_id=(id) VALUES (%s)'
    id = 4
    cur.execute(SQL, id)
    user = cur.fetchone()
    cur.close()
    conn.close()