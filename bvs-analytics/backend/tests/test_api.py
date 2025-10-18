#!/usr/bin/env python3
"""
Тест API без запуска сервера
"""

import sys
from pathlib import Path

# Добавляем корневую директорию в PYTHONPATH
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

def test_imports():
    """Тестирует импорты всех модулей"""
    
    print("=== ТЕСТ ИМПОРТОВ ===\n")
    
    try:
        print("1. Тестируем импорт конфигурации...")
        from app.core.config import settings
        print(f"   ✅ Конфигурация загружена: {settings.PROJECT_NAME}")
        
        print("2. Тестируем импорт моделей...")
        from app.models.flight import Flight, Region
        print("   ✅ Модели импортированы")
        
        print("3. Тестируем импорт схем...")
        from app.schemas.flight import FlightCreate, BasicMetrics
        print("   ✅ Схемы импортированы")
        
        print("4. Тестируем импорт парсера...")
        from parsers.telegram_parser import TelegramParser
        print("   ✅ Парсер импортирован")
        
        print("5. Тестируем импорт сервисов...")
        from app.services.flight_service import FlightService
        print("   ✅ Сервисы импортированы")
        
        print("6. Тестируем импорт API...")
        from app.api.flights import router
        print("   ✅ API роутеры импортированы")
        
        print("7. Тестируем импорт главного приложения...")
        from app.main import app
        print("   ✅ FastAPI приложение импортировано")
        
        print("\n✅ Все импорты успешны!")
        return True
        
    except Exception as e:
        print(f"\n❌ Ошибка импорта: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database_models():
    """Тестирует создание моделей базы данных"""
    
    print("\n=== ТЕСТ МОДЕЛЕЙ БД ===\n")
    
    try:
        from app.core.database import engine, Base
        from app.models.flight import Flight, Region
        
        print("1. Создаем таблицы в памяти...")
        Base.metadata.create_all(bind=engine)
        print("   ✅ Таблицы созданы успешно")
        
        print("2. Проверяем структуру таблиц...")
        tables = Base.metadata.tables.keys()
        print(f"   ✅ Созданы таблицы: {list(tables)}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Ошибка создания БД: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_parser_integration():
    """Тестирует интеграцию парсера с моделями"""
    
    print("\n=== ТЕСТ ИНТЕГРАЦИИ ПАРСЕРА ===\n")
    
    try:
        from parsers.telegram_parser import TelegramParser
        from parsers.data_processor import DataProcessor
        
        parser = TelegramParser()
        processor = DataProcessor()
        
        # Тестовое SHR сообщение
        shr_msg = """(SHR-ZZZZZ
-ZZZZ0900
-M0016/M0026 /ZONA R0,7 5509N03737E/
-ZZZZ0900
-DEP/5509N03737E DEST/5509N03737E DOF/240101 EET/UUWV0001
OPR/МЕНЖУЛИН АЛЕКСЕЙ ПЕТРОВИ4 REG/07C4935 TYP/BLA RMK/MР11608
SID/7771445428)"""
        
        print("1. Парсим тестовое сообщение...")
        flight_data = parser.parse_shr_message(shr_msg)
        print(f"   ✅ Сообщение распарсено: {flight_data.get('registration')}")
        
        print("2. Создаем запись для БД...")
        flight_record = processor.create_flight_record(flight_data)
        print(f"   ✅ Запись создана: {len(flight_record)} полей")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Ошибка интеграции: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_schemas():
    """Тестирует Pydantic схемы"""
    
    print("\n=== ТЕСТ СХЕМ API ===\n")
    
    try:
        from app.schemas.flight import FlightCreate, BasicMetrics, RegionRating
        from datetime import datetime
        
        print("1. Тестируем создание схемы полета...")
        flight_data = FlightCreate(
            flight_id="TEST001",
            registration="07C4935",
            aircraft_type="BLA",
            operator="Test Operator",
            departure_lat=55.15,
            departure_lon=37.617,
            arrival_lat=55.15,
            arrival_lon=37.617
        )
        print(f"   ✅ Схема полета создана: {flight_data.flight_id}")
        
        print("2. Тестируем схему метрик...")
        metrics = BasicMetrics(
            total_flights=100,
            avg_duration_minutes=45.5,
            unique_aircraft=25,
            unique_operators=10,
            date_range={'min': datetime.now(), 'max': datetime.now()}
        )
        print(f"   ✅ Схема метрик создана: {metrics.total_flights} полетов")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Ошибка схем: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Запускает все тесты"""
    
    print("🚀 ЗАПУСК ТЕСТОВ BVS ANALYTICS API\n")
    
    tests = [
        ("Импорты модулей", test_imports),
        ("Модели базы данных", test_database_models),
        ("Интеграция парсера", test_parser_integration),
        ("Схемы API", test_api_schemas),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"ТЕСТ: {test_name}")
        print('='*60)
        
        if test_func():
            passed += 1
            print(f"\n✅ ТЕСТ '{test_name}' ПРОЙДЕН")
        else:
            print(f"\n❌ ТЕСТ '{test_name}' ПРОВАЛЕН")
    
    print(f"\n{'='*60}")
    print(f"РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ")
    print('='*60)
    print(f"Пройдено: {passed}/{total}")
    print(f"Процент успеха: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! API готов к работе.")
        print("\nДля запуска сервера выполните:")
        print("python3 run.py")
        print("\nДокументация API: http://localhost:8000/docs")
    else:
        print(f"\n⚠️  {total-passed} тестов провалено. Требуется исправление.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)