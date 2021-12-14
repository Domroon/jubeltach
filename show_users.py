from connect import config

import psycopg2


def get_users():
    """ query data from the users table """
    conn = None
    try:
        params = config()
        conn = psycopg2.connect(**params)
        cur = conn.cursor()
        sql_command = """SELECT * FROM users ORDER BY user_id;"""
        cur.execute(sql_command)
        print(f'The quantity of users: {cur.rowcount}')
        row = cur.fetchone()

        while row is not None:
            print(row)
            row = cur.fetchone()

        cur.close()
    except(Exception, psycopg2.DatabaseError) as error:
        raise error
    finally:
        if conn is not None:
            conn.close()


def main():
    get_users()


if __name__ == '__main__':
    main()