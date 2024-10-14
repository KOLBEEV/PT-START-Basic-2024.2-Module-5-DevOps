В проекте 2 ветки:
1. docker - в ней все необходимые файлы для развёртывания контейнеров.
2. ansible - в ней находится плейбук для настройки 3 машин.

## Инструкция по развёртыванию контейнеров.
## Шаг 1: Настройка реестра Docker на ВМ-1

### Остановка и удаление контейнеров, очистка системы Docker и запуск реестра

Выполните следующую команду на ВМ-1 (машине, где будет находиться реестр):
```bash
docker stop $(docker ps -q) && docker rm $(docker ps -aq) && docker system prune -a && docker ps && docker images && docker run -d -p 5000:5000 --name registry registry:2
```

Если команда завершится неудачей, выполните:
```bash
docker rm $(docker ps -aq) && docker system prune -a && docker ps && docker images && docker run -d -p 5000:5000 --name registry registry:2
```

Если и это не поможет:
```bash
docker system prune -a && docker ps && docker images && docker run -d -p 5000:5000 --name registry registry:2
```

---

## Шаг 2: Сборка и загрузка Docker-образов в локальный реестр

### Образ для бота

Перейдите в папку `bot_image` и выполните:
```bash
docker build -t bot_image .
docker tag bot_image localhost:5000/bot_image
docker push localhost:5000/bot_image
```

### Образ базы данных

Перейдите в папку `db_image` и выполните:
```bash
docker build -t db_image .
docker tag db_image localhost:5000/db_image
docker push localhost:5000/db_image
```

### Образ репликации базы данных

Перейдите в папку `db_repl_image` и выполните:
```bash
docker build -t db_repl_image .
docker tag db_repl_image localhost:5000/db_repl_image
docker push localhost:5000/db_repl_image
```

---

## Шаг 3: Развертывание на ВМ-2

### Остановка и удаление контейнеров, очистка системы Docker

На ВМ-2 в папке с `docker-compose.yml` и `.env` выполните:
```bash
docker stop $(docker ps -q) && docker rm $(docker ps -aq) && docker system prune -a && docker ps && docker images
```

Если команда завершится неудачей:
```bash
docker rm $(docker ps -aq) && docker system prune -a && docker ps && docker images
```

Если и это не поможет:
```bash
docker system prune -a && docker ps && docker images
```

### Обновление и запуск Docker Compose

В файле `docker-compose.yml` измените адрес хоста с реестром на фактический адрес ВМ-1. Затем выполните:
```bash
docker compose up --build
```

---

## Шаг 4: Проверка работы бота

После завершения настройки убедитесь, что бот работает корректно.
```
