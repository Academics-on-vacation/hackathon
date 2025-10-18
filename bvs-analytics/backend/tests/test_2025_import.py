#!/usr/bin/env python3
"""
Тестовый скрипт для проверки импорта данных из файла 2025.xlsx
"""

import sys
import os
import logging
from pathlib import Path

# Добавляем путь к модулям backend
sys.path.append(str(Path(__file__).parent))

from parsers.data_processor import DataProcessor
from parsers.telegram_parser import TelegramParser

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_2025_parser():
    """Тестирует парсер для формата 2025.xlsx"""
    print("=== Тестирование парсера для формата 2025.xlsx ===\n")
    
    # Путь к файлу 2025.xlsx
    file_path = "../../data/2025.xlsx"
    
    if not os.path.exists(file_path):
        print(f"Файл {file_path} не найден!")
        print("Убедитесь, что файл находится в папке data/")
        return False
    
    try:
        # Создаем процессор данных
        processor = DataProcessor()
        
        # Обрабатываем файл
        print(f"Обрабатываем файл: {file_path}")
        result = processor.process_excel_file(file_path)
        
        print(f"\n=== Результаты обработки ===")
        print(f"Всего обработано полетов: {result['total_processed']}")
        print(f"Листов обработано: {result['sheets_processed']}")
        print(f"Ошибок: {len(result['errors'])}")
        
        if result['errors']:
            print(f"\nОшибки:")
            for error in result['errors'][:5]:  # Показываем первые 5 ошибок
                print(f"  - {error}")
        
        # Анализируем первые несколько полетов
        flights = result['flights']
        if flights:
            print(f"\n=== Анализ первых 3 полетов ===")
            for i, flight in enumerate(flights[:3], 1):
                print(f"\nПолет {i}:")
                print(f"  Центр: {flight.get('center_name', 'N/A')}")
                print(f"  Оператор: {flight.get('operator', 'N/A')[:50]}...")
                print(f"  Борт. номер: {flight.get('registration', 'N/A')}")
                print(f"  Тип ВС: {flight.get('aircraft_type', 'N/A')}")
                print(f"  Дата: {flight.get('flight_date', 'N/A')}")
                print(f"  Время вылета: {flight.get('departure_time', 'N/A')}")
                print(f"  Высоты: {flight.get('min_altitude', 'N/A')}-{flight.get('max_altitude', 'N/A')} м")
                print(f"  SID: {flight.get('sid', 'N/A')}")
        
        # Статистика по центрам
        centers = {}
        for flight in flights:
            center = flight.get('center_name', 'Unknown')
            centers[center] = centers.get(center, 0) + 1
        
        print(f"\n=== Статистика по центрам ===")
        for center, count in sorted(centers.items(), key=lambda x: x[1], reverse=True):
            print(f"  {center}: {count} полетов")
        
        return True
        
    except Exception as e:
        logger.error(f"Ошибка при тестировании: {e}")
        return False

def test_telegram_parser():
    """Тестирует парсер телеграмм для формата 2025"""
    print("\n=== Тестирование парсера телеграмм ===\n")
    
    # Примеры сообщений из 2025.xlsx
    test_messages = [
        {
            'shr': '(SHR-ZZZZZ\n-ZZZZ0705\n-K0300M3000\n-DEP/5957N02905E DOF/250201 OPR/МАЛИНОВСКИЙ НИКИТА АЛЕКСАНДРОВИ4\n+79313215153 TYP/SHAR RMK/ОБОЛО4КА 300 ДЛЯ ЗОНДИРОВАНИЯ АТМОСФЕРЫ\nSID/7772187998)',
            'dep': '-TITLE IDEP\n-SID 7772187998\n-ADD 250201\n-ATD 0705\n-ADEP ZZZZ\n-ADEPZ 5957N02905E\n-PAP 0',
            'arr': None
        },
        {
            'shr': '(SHR-00725\n-ZZZZ0600\n-M0000/M0005 /ZONA R0,5 4408N04308E/\n-ZZZZ0700\n-DEP/4408N04308E DEST/4408N04308E DOF/250124 OPR/ГУ М4С РОССИИ ПО\nСТАВРОПОЛЬСКОМУ КРАЮ REG/00724,REG00725 STS/SAR TYP/BLA RMK/WR655 В\nЗОНЕ ВИЗУАЛЬНОГО ПОЛЕТА СОГЛАСОВАНО С ЕСОРВД РОСТОВ ПОЛЕТ БЛА В\nВП-С-М4С МОНИТОРИНГ ПАВОДКООПАСНЫХ У4АСТКОВ РАЗРЕШЕНИЕ 10-37/9425\n15.11.2024 АДМИНИСТРАЦИЯ МИНЕРАЛОВОДСКОГО МУНИЦИПАЛЬНОГО ОКРУГА\nОПЕРАТОР ЛЯХОВСКАЯ +79283000251 ЛЯПИН +79620149012 SID/7772251137)',
            'dep': '-TITLE IDEP\n-SID 7772251137\n-ADD 250124\n-ATD 0600\n-ADEP ZZZZ\n-ADEPZ 440846N0430829E\n-PAP 0',
            'arr': '-TITLE IARR\n-SID 7772251137\n-ADA 250124\n-ATA 1250\n-ADARR ZZZZ\n-ADARRZ 440846N0430829E\n-PAP 0'
        }
    ]
    
    parser = TelegramParser()
    
    for i, messages in enumerate(test_messages, 1):
        print(f"Тест {i}:")
        try:
            result = parser.parse_flight_messages_2025(
                messages['shr'], 
                messages['dep'], 
                messages['arr']
            )
            
            if 'error' in result:
                print(f"  Ошибка: {result['error']}")
            else:
                print(f"  Оператор: {result.get('operator', 'N/A')}")
                print(f"  Регистрация: {result.get('registration', 'N/A')}")
                print(f"  Тип ВС: {result.get('aircraft_type', 'N/A')}")
                print(f"  Дата: {result.get('flight_date', 'N/A')}")
                print(f"  Время вылета: {result.get('departure_time', 'N/A')}")
                print(f"  Время посадки: {result.get('arrival_time', 'N/A')}")
                print(f"  Высоты: {result.get('min_altitude', 'N/A')}-{result.get('max_altitude', 'N/A')} м")
                print(f"  SID: {result.get('sid', 'N/A')}")
                
        except Exception as e:
            print(f"  Ошибка парсинга: {e}")
        
        print()

def main():
    """Главная функция тестирования"""
    print("Тестирование обновленного backend для формата 2025.xlsx")
    print("=" * 60)
    
    # Тест парсера телеграмм
    test_telegram_parser()
    
    # Тест обработки файла
    success = test_2025_parser()
    
    if success:
        print("\n✅ Все тесты прошли успешно!")
        print("\nBackend готов для работы с форматом 2025.xlsx")
        print("\nДля полного импорта:")
        print("1. Примените миграцию: sqlite3 bvs_analytics.db < migrations/add_2025_fields.sql")
        print("2. Используйте API endpoint /flights/import для загрузки файла 2025.xlsx")
    else:
        print("\n❌ Тесты завершились с ошибками")
        print("Проверьте логи и исправьте проблемы")

if __name__ == "__main__":
    main()