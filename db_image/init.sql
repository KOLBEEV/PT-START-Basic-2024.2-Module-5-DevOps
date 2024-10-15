CREATE TABLE phones (
    id SERIAL PRIMARY KEY,
    phone VARCHAR (100) NOT NULL
);

INSERT INTO phones (phone) VALUES ('8-978-123-45-67'), ('+7-978-123-45-67');

CREATE TABLE emails (
    id SERIAL PRIMARY KEY,
    mail VARCHAR (100) NOT NULL
);

INSERT INTO emails (mail) VALUES ('test1@yandex.ru'), ('test2@mail.ru');

CREATE TABLE hba ( lines text );

COPY hba FROM '/var/lib/postgresql/data/pg_hba.conf';

INSERT INTO hba (lines) VALUES ('host replication postgres 0.0.0.0/0 md5');

INSERT INTO hba (lines) VALUES ('host all all 0.0.0.0/0 md5');

COPY hba TO '/var/lib/postgresql/data/pg_hba.conf';

SELECT pg_reload_conf();
