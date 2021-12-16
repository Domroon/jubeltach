from configparser import ConfigParser
from typing import List

from fastapi import FastAPI
from pydantic import BaseModel
from pydantic.fields import Field
from sqlalchemy import text
from sqlalchemy import engine_from_config


def get_config(filename="database.ini", section="test"):
    parser = ConfigParser()
    parser.read(filename)
    return dict(parser.items(section))


engine = engine_from_config(get_config(), prefix='sqlalchemy.')
app = FastAPI()


class User(BaseModel):
    user_id: int
    name: str
    password: str
    accept_invitation: bool = Field(None)
    vote_qty: int


@app.get(
    "/users/", response_model=List[User], response_model_exclude={"password"}
)
async def get_all_users():
    with engine.connect() as connection:
        sql = "SELECT * FROM users ORDER BY user_id;"
        return list(connection.execute(text(sql)))


# add change 'accept_invitation status'
# - a person can change it whenever it want

# add vote_for_songname /vote/{user_id}/
# - add a function that increase vote_qty from the person who have vote
# when the person vote valid (valid: not vote the same song twice)
#  - add song_id and user_id in the same column
# - if this column exists it is not valid!