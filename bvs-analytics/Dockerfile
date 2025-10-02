FROM python:3.11-slim

# Устанавливаем системные зависимости для PostgreSQL
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    texlive-latex-base \
    texlive-latex-recommended \
    texlive-fonts-recommended \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы зависимостей
COPY backend/requirements.txt .

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY backend/ .

# Копируем файлы из data
COPY data/ /app/data/

# Создаем необходимые директории
RUN mkdir -p uploads logs data

# Открываем порт
EXPOSE 8000

# Команда запуска
CMD ["python", "run.py"]
