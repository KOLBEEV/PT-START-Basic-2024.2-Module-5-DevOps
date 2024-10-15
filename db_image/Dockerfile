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

# Изменение прав доступа к ключам SSH
RUN chmod 600 /etc/ssh/ssh_host_rsa_key /etc/ssh/ssh_host_ecdsa_key /etc/ssh/ssh_host_ed25519_key

# Открытие порта для SSH
EXPOSE 5432 22

# Копирование SQL скрипта и настройка базы данных

COPY ./init.sql /docker-entrypoint-initdb.d/

