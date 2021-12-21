from playground.connect import config

import psycopg2


def update_user_invitation(user_id, bool_statement):
    """ update the invitation status based on the user_id """
    sql = """ UPDATE users
                SET accept_invitation = %s
                WHERE user_id = %s"""
    conn = None
    updated_rows = 0
    try:
        params = config()
        conn = psycopg2.connect(**params)
        cur = conn.cursor()
        cur.execute(sql, (bool_statement, user_id))
        updated_rows = cur.rowcount
        conn.commit()
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        raise error
    finally:
        if conn is not None:
            conn.close()
    
    print(f'updates rows: {updated_rows}')


def update_user_vote_qty(user_id, qty_of_votes):
    """ update the vote quantity based on the user_id """
    sql = """ UPDATE users
                SET vote_qty = %s
                WHERE user_id = %s"""
    conn = None
    updated_rows = 0
    try:
        params = config()
        conn = psycopg2.connect(**params)
        cur = conn.cursor()
        cur.execute(sql, (qty_of_votes, user_id))
        updated_rows = cur.rowcount
        conn.commit()
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        raise error
    finally:
        if conn is not None:
            conn.close()
    
    print(f'updated rows: {updated_rows}')


def main():
    update_user_invitation(1, 'false'),
    update_user_invitation(4, 'true'),
    update_user_invitation(3, 'false')
    update_user_vote_qty(1, 42)
    update_user_vote_qty(3, 21)


if __name__ == '__main__':
    main()