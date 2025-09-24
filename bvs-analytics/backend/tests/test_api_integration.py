#!/usr/bin/env python3
"""
Тест API без запуска сервера
"""

import sys
import os
import unittest
from datetime import datetime

# Добавляем путь к корневой директории проекта
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestAPIIntegration(unittest.TestCase):
    """Тесты интеграции API компонентов"""
    
    def test_imports(self):
        """Тестирует импорты всех модулей"""
        try:
            from app.core.config import settings
            self.assertIsNotNone(settings.PROJECT_NAME)
            
            from app.models.flight import Flight, Region
            self.assertTrue(hasattr(Flight, '__tablename__'))
            
            from app.schemas.flight import FlightCreate, BasicMetrics
            self.assertTrue(hasattr(FlightCreate, '__fields__'))
            
            from parsers.telegram_parser import TelegramParser
            parser = TelegramParser()
            self.assertIsNotNone(parser)
            
            from app.services.flight_service import FlightService
            self.assertTrue(hasattr(FlightService, 'get_flights'))
            
            from app.api.flights import router
            self.assertIsNotNone(router)
            
            from app.main import app
            self.assertIsNotNone(app)
            
        except ImportError as e:
            self.fail(f"Import failed: {e}")
    
    def test_database_models(self):
        """Тестирует создание моделей базы данных"""
        try:
            from app.core.database import engine, Base
            from app.models.flight import Flight, Region
            
            # Создаем таблицы в памяти
            Base.metadata.create_all(bind=engine)
            
            # Проверяем структуру таблиц
            tables = Base.metadata.tables.keys()
            self.assertIn('flights', tables)
            self.assertIn('regions', tables)
            
        except Exception as e:
            self.fail(f"Database model test failed: {e}")
    
    def test_parser_integration(self):
        """Тестирует интеграцию парсера с моделями"""
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
            
            # Парсим тестовое сообщение
            flight_data = parser.parse_shr_message(shr_msg)
            self.assertNotIn('error', flight_data)
            self.assertEqual(flight_data.get('registration'), '07C4935')
            
            # Создаем запись для БД
            flight_record = processor.create_flight_record(flight_data)
            self.assertIsInstance(flight_record, dict)
            self.assertGreater(len(flight_record), 0)
            
        except Exception as e:
            self.fail(f"Parser integration test failed: {e}")
    
    def test_api_schemas(self):
        """Тестирует Pydantic схемы"""
        try:
            from app.schemas.flight import FlightCreate, BasicMetrics, RegionRating
            
            # Тестируем создание схемы полета
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
            self.assertEqual(flight_data.flight_id, "TEST001")
            
            # Тестируем схему метрик
            metrics = BasicMetrics(
                total_flights=100,
                avg_duration_minutes=45.5,
                unique_aircraft=25,
                unique_operators=10,
                date_range={'min': datetime.now(), 'max': datetime.now()}
            )
            self.assertEqual(metrics.total_flights, 100)
            
        except Exception as e:
            self.fail(f"API schemas test failed: {e}")
    
    def test_phone_normalizer_integration(self):
        """Тестирует интеграцию нормализатора телефонных номеров"""
        try:
            from app.utils.phone_normalizer import normalize_phone_number, normalize_phone_numbers
            from parsers.telegram_parser import TelegramParser
            
            # Проверяем, что функции доступны
            self.assertIsNotNone(normalize_phone_number)
            self.assertIsNotNone(normalize_phone_numbers)
            
            # Проверяем интеграцию с парсером
            parser = TelegramParser()
            test_message = """(SHR-TEST
OPR/ТЕСТОВЫЙ ОПЕРАТОР +79123456789 REG/TEST TYP/BLA
SID/1234567890)"""
            
            result = parser.parse_shr_message(test_message)
            self.assertNotIn('error', result)
            
            # Проверяем, что телефонные номера унифицированы
            if 'phone_numbers' in result:
                for phone in result['phone_numbers']:
                    self.assertTrue(phone.startswith('7'))
                    self.assertEqual(len(phone), 11)
                    self.assertTrue(phone.isdigit())
            
        except Exception as e:
            self.fail(f"Phone normalizer integration test failed: {e}")


def run_manual_test():
    """Запуск ручного теста с выводом результатов"""
    print("🚀 ЗАПУСК ТЕСТОВ BVS ANALYTICS API\n")
    
    tests = [
        ("Импорты модулей", test_imports_manual),
        ("Модели базы данных", test_database_models_manual),
        ("Интеграция парсера", test_parser_integration_manual),
        ("Схемы API", test_api_schemas_manual),
        ("Интеграция нормализатора телефонов", test_phone_normalizer_integration_manual),
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


def test_imports_manual():
    """Ручной тест импортов"""
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
        
        print("8. Тестируем импорт нормализатора телефонов...")
        from app.utils.phone_normalizer import normalize_phone_number
        print("   ✅ Нормализатор телефонов импортирован")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Ошибка импорта: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_database_models_manual():
    """Ручной тест моделей БД"""
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


def test_parser_integration_manual():
    """Ручной тест интеграции парсера"""
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


def test_api_schemas_manual():
    """Ручной тест схем API"""
    try:
        from app.schemas.flight import FlightCreate, BasicMetrics, RegionRating
        
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


def test_phone_normalizer_integration_manual():
    """Ручной тест интеграции нормализатора телефонов"""
    try:
        from app.utils.phone_normalizer import normalize_phone_number, normalize_phone_numbers
        from parsers.telegram_parser import TelegramParser
        
        print("1. Тестируем функции нормализации...")
        test_phone = "+79123456789"
        normalized = normalize_phone_number(test_phone)
        print(f"   ✅ {test_phone} → {normalized}")
        
        print("2. Тестируем интеграцию с парсером...")
        parser = TelegramParser()
        test_message = """(SHR-TEST
OPR/ТЕСТОВЫЙ ОПЕРАТОР +79123456789 8(987)654-32-10 REG/TEST TYP/BLA
SID/1234567890)"""
        
        result = parser.parse_shr_message(test_message)
        if 'phone_numbers' in result:
            print(f"   ✅ Извлечены и унифицированы номера: {result['phone_numbers']}")
        else:
            print("   ⚠️ Номера не найдены в сообщении")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Ошибка интеграции нормализатора: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Можно запустить либо unittest, либо ручной тест
    import argparse
    
    parser = argparse.ArgumentParser(description='Тест интеграции API')
    parser.add_argument('--manual', action='store_true', help='Запустить ручной тест с подробным выводом')
    args = parser.parse_args()
    
    if args.manual:
        success = run_manual_test()
        sys.exit(0 if success else 1)
    else:
        unittest.main()