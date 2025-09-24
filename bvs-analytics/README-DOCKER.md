# 🐳 Docker для BVS Analytics с PostgreSQL

## Быстрый старт

### Запуск приложения (с PostgreSQL)
```bash
cd bvs-analytics
docker-compose up -d
```

### Остановка приложения
```bash
docker-compose down
```

### Остановка с удалением данных
```bash
docker-compose down -v
```

### Просмотр логов
```bash
# Все сервисы
docker-compose logs -f

# Только приложение
docker-compose logs -f bvs-analytics

# Только база данных
docker-compose logs -f postgres
```

### Перезапуск
```bash
docker-compose restart
```

## Доступ к приложению

- **API:** http://localhost:8000
- **Документация:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health
- **PostgreSQL:** localhost:5432 (postgres/postgres)

## Сервисы

### 1. PostgreSQL
- **Образ:** postgres:15-alpine
- **База данных:** bvs_analytics
- **Пользователь:** postgres
- **Пароль:** postgres
- **Порт:** 5432

### 2. BVS Analytics API
- **Порт:** 8000
- **База данных:** автоматически подключается к PostgreSQL
- **Volumes:** uploads, logs

## Полезные команды

```bash
# Пересборка образа
docker-compose build

# Запуск с пересборкой
docker-compose up --build -d

# Статус контейнеров
docker-compose ps

# Вход в контейнер приложения
docker-compose exec bvs-analytics bash

# Вход в PostgreSQL
docker-compose exec postgres psql -U postgres -d bvs_analytics

# Просмотр логов приложения
docker-compose exec bvs-analytics tail -f bvs_analytics.log

# Бэкап базы данных
docker-compose exec postgres pg_dump -U postgres bvs_analytics > backup.sql

# Восстановление базы данных
docker-compose exec -T postgres psql -U postgres bvs_analytics < backup.sql
```

## Структура

- **Dockerfile** - образ для приложения (с поддержкой PostgreSQL)
- **docker-compose.yml** - конфигурация с PostgreSQL
- **Volumes:**
  - `./backend/uploads` - загруженные файлы
  - `./backend/logs` - логи приложения
  - `postgres_data` - данные PostgreSQL

## Переменные окружения

Приложение автоматически использует:
```
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/bvs_analytics
```

## Troubleshooting

### Контейнеры не запускаются
```bash
docker-compose logs
```

### PostgreSQL не готов
```bash
# Проверить статус
docker-compose ps postgres

# Проверить логи
docker-compose logs postgres
```

### Порты заняты
```bash
# Изменить порты в docker-compose.yml
ports:
  - "8001:8000"  # для приложения
  - "5433:5432"  # для PostgreSQL
```

### Проблемы с правами доступа
```bash
sudo chown -R $USER:$USER backend/
```

### Очистка всех данных
```bash
docker-compose down -v
docker system prune -f
```

## Makefile команды

Если у вас есть Makefile, используйте:
```bash
make up      # запуск
make down    # остановка
make logs    # логи
make build   # пересборка
```

Готово! Теперь приложение работает с PostgreSQL в Docker.