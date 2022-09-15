FROM postgres:10.12

COPY init-user-db.sh /docker-entrypoint-initdb.d/init-user-db.sh
