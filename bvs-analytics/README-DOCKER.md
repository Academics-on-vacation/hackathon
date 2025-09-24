# 🐳 Docker для BVS Analytics

## Быстрый старт

### Запуск приложения
```bash
cd bvs-analytics
docker-compose up -d
```

### Остановка приложения
```bash
docker-compose down
```

### Просмотр логов
```bash
docker-compose logs -f
```

### Перезапуск
```bash
docker-compose restart
```

## Доступ к приложению

- **API:** http://localhost:8000
- **Документация:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health

## Полезные команды

```bash
# Пересборка образа
docker-compose build

# Запуск с пересборкой
docker-compose up --build -d

# Статус контейнера
docker-compose ps

# Вход в контейнер
docker-compose exec bvs-analytics bash

# Просмотр логов приложения
docker-compose exec bvs-analytics tail -f bvs_analytics.log

# Остановка и удаление всего
docker-compose down -v
```

## Структура

- **Dockerfile** - образ для приложения
- **docker-compose.yml** - конфигурация сервиса
- **Volumes:**
  - `./backend/uploads` - загруженные файлы
  - `./backend/logs` - логи приложения
  - `./backend/bvs_analytics.db` - база данных SQLite
  - `./backend/.env` - переменные окружения

## Troubleshooting

### Контейнер не запускается
```bash
docker-compose logs
```

### Порт занят
```bash
# Изменить порт в docker-compose.yml
ports:
  - "8001:8000"  # вместо 8000:8000
```

### Проблемы с правами доступа
```bash
sudo chown -R $USER:$USER backend/
```

Готово! Теперь можно просто использовать `docker-compose up -d` и `docker-compose down`.