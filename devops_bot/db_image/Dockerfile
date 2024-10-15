FROM postgres:15

ENV POSTGRES_DB=db_emails_phones
ENV POSTGRES_USER=postgres
ENV POSTGRES_PASSWORD=12345678

# Установка SSH-сервера
RUN apt-get update && apt-get install -y openssh-server sudo

# Создание директории для SSH
RUN mkdir /var/run/sshd

# Установка пароля для root (выберите более безопасный пароль)
RUN echo 'root:12345678' | chpasswd

# Разрешить root доступ по SSH
RUN sed -i 's/PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config

COPY ./ssh_configs/. /etc/ssh/

# Открытие порта для SSH
EXPOSE 5432 22

# Копирование SQL скрипта и настройка базы данных

COPY ./init.sql /docker-entrypoint-initdb.d/

COPY ./psql_configs/. /var/lib/postgresql/data/

# Запуск PostgreSQL и SSH
CMD service ssh start && docker-entrypoint.sh postgres


#COPY ./pg_hba.conf /var/lib/postgresql/data/

#COPY ./aaa /var/lib/postgresql/data/

#RUN chown -R postgres:postgres /var/lib/postgresql/data/

#RUN mkdir -p /oracle/pg_data/archive

#RUN chown -R postgres:postgres /oracle/pg_data/archive

#RUN sudo service postgresql restart

#/usr/share/postgresql/15/postgresql.conf.sample
#/usr/share/postgresql/15/pg_hba.conf.sample
#/var/lib/postgresql/data/postgresql.auto.conf
# PGPASSWORD="12345678" pg_basebackup -h db -D /var/lib/postgresql/15/main/ -U repl_user -v --write-recovery-conf
#var/lib/postgresql/data
