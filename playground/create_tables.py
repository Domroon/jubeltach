from playground.connect import config

import psycopg2


def create_tables():
    ''' Create tables in the PostgreSQL database '''
    commands = (
        """
        CREATE TABLE users (
            user_id SERIAL PRIMARY KEY,
            name VARCHAR(20) NOT NULL,
            password VARCHAR(255) NOT NULL,
            accept_invitation BOOLEAN,
            vote_qty SMALLINT DEFAULT 0 NOT NULL
        )
        """,
        """
        CREATE TABLE songs (
            song_id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            interpreter VARCHAR(255) NOT NULL,
            leadsheet VARCHAR(255),
            music VARCHAR(255)
        )
        """,
        """
        CREATE TABLE votes (
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
        """
    )

    conn = None
    try:
        params = config()

        conn = psycopg2.connect(**params)
        cur = conn.cursor()

        for command in commands:
            cur.execute(command)
        
        cur.close()
        conn.commit()
        print("Sucessfully created all tables")
    
    except (Exception, psycopg2.DatabaseError) as error:
        raise error
    finally:
        if conn is not None:
            conn.close()
    

def main():
    create_tables()


if __name__ == '__main__':
    main()
