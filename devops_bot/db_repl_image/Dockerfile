FROM postgres:15

ENV POSTGRES_DB=db_emails_phones
ENV POSTGRES_USER=postgres
ENV POSTGRES_PASSWORD=12345678

COPY ./psql_repl_configs/. /var/lib/postgresql/data/
