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
