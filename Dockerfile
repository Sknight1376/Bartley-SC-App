FROM postgres

COPY init.d /docker-entrypoint-initdb.d/

COPY handicaps.csv /var/handicaps.csv

