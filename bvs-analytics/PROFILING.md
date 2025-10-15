# Профилирование кода в BVS Analytics

Этот документ описывает, как использовать систему профилирования для анализа производительности приложения.

## Обзор

Система профилирования позволяет:
- Автоматически профилировать HTTP запросы
- Управлять профилированием через API
- Использовать различные типы профайлеров (cProfile, PyInstrument)
- Сохранять результаты в различных форматах (текст, HTML, бинарный)
- Анализировать узкие места в производительности

## Установка зависимостей

Все необходимые зависимости уже добавлены в `requirements.txt`. Установите их:

```bash
cd bvs-analytics/backend
pip install -r requirements.txt
```

## Быстрый старт

### 1. Запуск сервиса

```bash
cd bvs-analytics/backend
python run.py
```

Сервис будет доступен по адресу: `http://localhost:8000`

### 2. Включение профилирования через API

```bash
# Включить профилирование
curl -X POST http://localhost:8000/api/v1/profiling/enable

# Проверить статус
curl http://localhost:8000/api/v1/profiling/status
```

### 3. Выполнение тяжёлых запросов

После включения профилирования все запросы будут автоматически профилироваться. Например:

```bash
# Выполните ваш тяжёлый запрос
curl -X GET "http://localhost:8000/api/v1/flights?limit=1000"
```

### 4. Получение результатов

```bash
# Список всех профилей
curl http://localhost:8000/api/v1/profiling/profiles

# Скачать конкретный профиль
curl -O http://localhost:8000/api/v1/profiling/profiles/GET__api_v1_flights_20250115_123456.txt
```

### 5. Выключение профилирования

```bash
curl -X POST http://localhost:8000/api/v1/profiling/disable
```

## API Endpoints

### POST `/api/v1/profiling/enable`
Включить профилирование всех запросов.

**Ответ:**
```json
{
  "enabled": true,
  "output_directory": "profiling_results",
  "total_profiles": 5
}
```

### POST `/api/v1/profiling/disable`
Выключить профилирование.

### GET `/api/v1/profiling/status`
Получить текущий статус профилирования.

### GET `/api/v1/profiling/profiles`
Получить список всех сохранённых профилей.

**Ответ:**
```json
[
  {
    "name": "GET__api_v1_flights_20250115_123456.txt",
    "size": 15234,
    "created": "2025-01-15T12:34:56"
  }
]
```

### GET `/api/v1/profiling/profiles/{profile_name}`
Скачать файл профиля.

### DELETE `/api/v1/profiling/profiles/{profile_name}`
Удалить конкретный профиль.

### DELETE `/api/v1/profiling/profiles`
Удалить все профили.

## Типы профайлеров

### cProfile (по умолчанию)
- Встроенный в Python
- Низкие накладные расходы
- Детальная статистика по функциям
- Результаты в текстовом и бинарном формате

### PyInstrument
- Более наглядная визуализация
- HTML отчёты с интерактивными графиками
- Лучше для понимания общей картины
- Немного больше накладных расходов

Чтобы использовать PyInstrument, измените в `app/main.py`:

```python
app.add_middleware(
    ProfilingMiddleware,
    profiler_type="pyinstrument",  # вместо "cprofile"
    profile_all=False,
    min_duration=0.0
)
```

## Результаты профилирования

Все результаты сохраняются в директории `profiling_results/` в корне проекта.

### Формат имени файла
```
{HTTP_METHOD}_{путь_с_подчёркиваниями}_{timestamp}.{расширение}
```

Примеры:
- `GET__api_v1_flights_20250115_123456.txt` - текстовый отчёт cProfile
- `GET__api_v1_flights_20250115_123456.prof` - бинарный файл cProfile
- `POST__api_v1_flights_analyze_20250115_123456.html` - HTML отчёт PyInstrument

### Анализ результатов cProfile

Текстовый файл содержит:
```
Profile: GET__api_v1_flights
Elapsed time: 2.3456 seconds
================================================================================

   ncalls  tottime  percall  cumtime  percall filename:lineno(function)
     1000    0.234    0.000    1.567    0.002 flight_service.py:45(get_flights)
     5000    0.456    0.000    0.789    0.000 database.py:123(execute_query)
```

Ключевые метрики:
- **ncalls** - количество вызовов функции
- **tottime** - общее время в функции (без подфункций)
- **cumtime** - общее время включая подфункции
- **percall** - среднее время на вызов

### Анализ бинарных файлов .prof

Используйте встроенные инструменты Python:

```bash
# Интерактивный анализ
python -m pstats profiling_results/GET__api_v1_flights_20250115_123456.prof

# В интерактивном режиме:
# sort cumtime  - сортировать по cumulative time
# stats 20      - показать топ 20 функций
# callers       - показать кто вызывает функцию
```

Или используйте визуализацию:

```bash
# Установите gprof2dot и graphviz
pip install gprof2dot
brew install graphviz  # или apt-get install graphviz

# Создайте граф
gprof2dot -f pstats profiling_results/GET__api_v1_flights_20250115_123456.prof | dot -Tpng -o profile_graph.png
```

## Программное использование

### Профилирование отдельных функций

```python
from app.utils.profiler import profile

@profile(name="my_heavy_function", profiler_type="cprofile")
def my_heavy_function():
    # ваш код
    pass
```

### Профилирование блока кода

```python
from app.utils.profiler import profile_block

def my_function():
    # обычный код
    
    with profile_block("heavy_computation"):
        # тяжёлые вычисления
        result = complex_calculation()
    
    return result
```

### Ручное управление профилированием

```python
from app.utils.profiler import profiler_manager

# Включить
profiler_manager.enable()

# Выполнить код
do_something()

# Выключить
profiler_manager.disable()

# Получить статистику
stats = profiler_manager.get_stats_summary()
print(f"Создано профилей: {stats['total_profiles']}")
```

## Настройка middleware

В `app/main.py` можно настроить поведение middleware:

```python
app.add_middleware(
    ProfilingMiddleware,
    profiler_type="cprofile",      # Тип профайлера
    profile_all=False,              # True = профилировать всегда, False = только когда enabled
    min_duration=0.1                # Логировать только запросы длиннее 0.1 сек
)
```

## Рекомендации по использованию

### Для разработки
1. Включите профилирование локально
2. Выполните проблемные запросы
3. Проанализируйте результаты
4. Оптимизируйте узкие места
5. Повторите профилирование для проверки

### Для production
1. **НЕ включайте** `profile_all=True` в production
2. Включайте профилирование только для конкретных запросов через API
3. Используйте `min_duration` для фильтрации быстрых запросов
4. Регулярно очищайте старые профили
5. Рассмотрите использование внешних инструментов (py-spy, Datadog, New Relic)

### Для удалённой машины

Если вы запускаете на другой машине:

```bash
# На удалённой машине
ssh user@remote-host

# Запустите сервис
cd /path/to/bvs-analytics/backend
python run.py

# С локальной машины включите профилирование
curl -X POST http://remote-host:8000/api/v1/profiling/enable

# Выполните тяжёлые запросы
curl -X GET "http://remote-host:8000/api/v1/flights?limit=10000"

# Скачайте результаты
curl -O http://remote-host:8000/api/v1/profiling/profiles/GET__api_v1_flights_20250115_123456.txt

# Выключите профилирование
curl -X POST http://remote-host:8000/api/v1/profiling/disable
```

## Альтернативные инструменты

### py-spy (для production)
Профайлер с минимальными накладными расходами, работает без изменения кода:

```bash
# Установка
pip install py-spy

# Профилирование работающего процесса
py-spy record -o profile.svg --pid <PID>

# Или запуск с профилированием
py-spy record -o profile.svg -- python run.py
```

### line_profiler (для детального анализа)
Профилирование построчно:

```bash
pip install line_profiler

# Добавьте @profile к функции
# Запустите
kernprof -l -v your_script.py
```

## Troubleshooting

### Профилирование не работает
1. Проверьте, что профилирование включено: `GET /api/v1/profiling/status`
2. Убедитесь, что запрос не пропускается (не статический файл, не /health)
3. Проверьте логи: `tail -f bvs_analytics.log`

### Файлы профилей не создаются
1. Проверьте права на запись в директорию `profiling_results/`
2. Убедитесь, что запрос выполнился успешно
3. Проверьте, что установлены все зависимости

### Слишком большие файлы профилей
1. Используйте `min_duration` для фильтрации
2. Профилируйте только конкретные эндпоинты
3. Регулярно очищайте старые профили

## Примеры использования

### Пример 1: Профилирование конкретного запроса

```bash
# 1. Включить профилирование
curl -X POST http://localhost:8000/api/v1/profiling/enable

# 2. Выполнить тяжёлый запрос
curl -X GET "http://localhost:8000/api/v1/flights/analytics?start_date=2024-01-01&end_date=2024-12-31"

# 3. Получить список профилей
curl http://localhost:8000/api/v1/profiling/profiles

# 4. Скачать последний профиль
curl -O http://localhost:8000/api/v1/profiling/profiles/GET__api_v1_flights_analytics_20250115_143022.txt

# 5. Выключить профилирование
curl -X POST http://localhost:8000/api/v1/profiling/disable
```

### Пример 2: Сравнение до и после оптимизации

```bash
# Профилирование до оптимизации
curl -X POST http://localhost:8000/api/v1/profiling/enable
curl -X GET "http://localhost:8000/api/v1/flights?limit=5000"
curl http://localhost:8000/api/v1/profiling/profiles > before.json

# Внесите изменения в код

# Профилирование после оптимизации
curl -X GET "http://localhost:8000/api/v1/flights?limit=5000"
curl http://localhost:8000/api/v1/profiling/profiles > after.json

# Сравните результаты
diff before.json after.json
```

## Дополнительные ресурсы

- [Python cProfile документация](https://docs.python.org/3/library/profile.html)
- [PyInstrument GitHub](https://github.com/joerick/pyinstrument)
- [py-spy GitHub](https://github.com/benfred/py-spy)
- [Профилирование Python приложений](https://realpython.com/python-profiling/)