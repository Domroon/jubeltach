from playground.connect import config

import psycopg2


USER_LIST = [
    ('Andre', 'test123'),
    ('Dominik', 'gutes passwort'),
    ('Abraham', 'abraham123'),
]


def insert_user(name, password):
    """ insert a new user into the users table """
    sql = """ INSERT INTO users(name, password) VALUES(%s, %s) RETURNING user_id;"""
    conn = None
    user_id = None
    try:
        params = config()
        conn = psycopg2.connect(**params)
        cur = conn.cursor()
        cur.execute(sql, (name, password, ))
        user_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        raise error
    finally:
        if conn is not None:
            conn.close()


def insert_user_list(user_list):
    """ inser multiple users into the user table """
    sql = """ INSERT INTO users(name, password) VALUES(%s, %s)"""
    conn = None
    try:
        params = config()
        conn = psycopg2.connect(**params)
        cur = conn.cursor()
        cur.executemany(sql, user_list)
        conn.commit()
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        raise error
    finally:
        if conn is not None:
            conn.close()


def main():
    insert_user('Frodo', 'geheim')
    insert_user_list(USER_LIST)


if __name__ == '__main__':
    main()