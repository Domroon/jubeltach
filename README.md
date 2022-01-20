# How to Setup the Project

1. Install PostgresQl: https://wiki.debian.org/PostgreSql
2. Add a database 'jubeltachDB'
   2.1. Run Backend at User postgres: su postgres
3. Change the password of the postgres user:
   https://chartio.com/resources/tutorials/how-to-set-the-default-user-password-in-postgresql/
4. At "create_user_list" comment out:
   "current_user: User = Depends(read_current_user)"
   "check_user_scope(current_user["name"], [ADMIN])"
5. At "/docs" add post user-list, post song-list and post votes
6. Enable https https://kifarunix.com/how-to-create-self-signed-ssl-certificate-with-mkcert-on-ubuntu-18-04/
   and https://dev.to/rajshirolkar/fastapi-over-https-for-development-on-windows-2p7d
7. more secure https: https://letsencrypt.org/de/getting-started/

# Database Commands

\du - Show Database Users
\dt - Show Tables

You can also use all sql commands directly in the PostgreSQL shell
(Don't forget the ';' after each command!)

linux command to go into the postgreSQL shell: sudo -u postgres psql jubeltachDB

# Documentation of the used Librarys

https://www.postgresql.org/docs/13/index.html
https://www.postgresqltutorial.com/postgresql-python/

https://fastapi.tiangolo.com
