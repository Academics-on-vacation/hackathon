#!/usr/bin/env python3
"""
Тестирование улучшенного парсера на реальных данных из 2025.xlsx
"""

import sys
import os
sys.path.append('bvs-analytics/backend')

from parsers.telegram_parser import TelegramParser
import pandas as pd

def test_parser_improvements():
    """Тестируем улучшения парсера"""
    parser = TelegramParser()
    
    # Читаем тестовые данные из Excel
    file_path = 'data/2025.xlsx'
    df = pd.read_excel(file_path, sheet_name='Result_1', nrows=10)
    
    print("=== Тестирование улучшенного парсера ===\n")
    
    for idx, row in df.iterrows():
        if idx >= 5:  # Тестируем только первые 5 строк
            break
            
        center = row.get('Центр ЕС ОрВД', '')
        shr_msg = str(row.get('SHR', ''))
        dep_msg = str(row.get('DEP', ''))
        arr_msg = str(row.get('ARR', ''))
        
        if not shr_msg or shr_msg == 'nan':
            continue
            
        print(f"--- Строка {idx + 1}: {center} ---")
        
        # Парсим с помощью улучшенного парсера
        result = parser.parse_flight_messages_2025(shr_msg, dep_msg, arr_msg)
        
        if 'error' in result:
            print(f"❌ Ошибка парсинга: {result['error']}")
            continue
            
        # Выводим ключевые поля
        print(f"✅ Flight ID: {result.get('flight_id', 'N/A')}")
        print(f"✅ Регистрация: {result.get('registration', 'N/A')}")
        print(f"✅ Тип ВС: {result.get('aircraft_type', 'N/A')}")
        print(f"✅ Оператор: {result.get('operator', 'N/A')}")
        
        # Координаты
        dep_coords = result.get('departure_coords')
        dest_coords = result.get('destination_coords')
        
        if dep_coords:
            print(f"✅ Координаты вылета: {dep_coords[0]:.6f}, {dep_coords[1]:.6f}")
        else:
            print("❌ Координаты вылета не найдены")
            
        if dest_coords:
            print(f"✅ Координаты назначения: {dest_coords[0]:.6f}, {dest_coords[1]:.6f}")
        else:
            print("❌ Координаты назначения не найдены")
            
        # Времена
        if result.get('departure_datetime'):
            print(f"✅ Время вылета: {result['departure_datetime']}")
        if result.get('arrival_datetime'):
            print(f"✅ Время посадки: {result['arrival_datetime']}")
            
        # Высоты
        if result.get('min_altitude') and result.get('max_altitude'):
            print(f"✅ Высоты: {result['min_altitude']}-{result['max_altitude']} м")
            
        # Телефоны
        if result.get('phone_numbers'):
            print(f"✅ Телефоны: {result['phone_numbers']}")
            
        print()

def test_specific_patterns():
    """Тестируем конкретные паттерны извлечения"""
    parser = TelegramParser()
    
    print("=== Тестирование конкретных паттернов ===\n")
    
    # Тест 1: ADEPZ координаты
    dep_msg = """-TITLE IDEP
-SID 7772251137
-ADD 250124
-ATD 0600
-ADEP ZZZZ
-ADEPZ 440846N0430829E
-PAP 0"""
    
    print("Тест 1: ADEPZ координаты")
    coords = parser._extract_adepz_coordinates(dep_msg)
    if coords:
        print(f"✅ ADEPZ: {coords[0]:.6f}, {coords[1]:.6f}")
    else:
        print("❌ ADEPZ не найдены")
    
    # Тест 2: ADARRZ координаты
    arr_msg = """-TITLE IARR
-SID 7772251137
-ADA 250124
-ATA 1250
-ADARR ZZZZ
-ADARRZ 440846N0430829E
-PAP 0"""
    
    print("Тест 2: ADARRZ координаты")
    coords = parser._extract_adarrz_coordinates(arr_msg)
    if coords:
        print(f"✅ ADARRZ: {coords[0]:.6f}, {coords[1]:.6f}")
    else:
        print("❌ ADARRZ не найдены")
    
    # Тест 3: ZONA координаты
    shr_msg = """(SHR-00725
-ZZZZ0600
-M0000/M0005 /ZONA R0,5 4408N04308E/
-ZZZZ0700
-DEP/4408N04308E DEST/4408N04308E DOF/250124 OPR/ГУ МЧС РОССИИ ПО
СТАВРОПОЛЬСКОМУ КРАЮ REG/00724,REG00725 STS/SAR TYP/BLA RMK/WR655"""
    
    print("Тест 3: ZONA координаты")
    coords = parser._extract_zona_coordinates(shr_msg)
    if coords:
        print(f"✅ ZONA: {coords[0]:.6f}, {coords[1]:.6f}")
    else:
        print("❌ ZONA не найдены")
    
    # Тест 4: Улучшенный оператор
    print("Тест 4: Улучшенный парсинг оператора")
    operator = parser._extract_operator(shr_msg)
    if operator:
        print(f"✅ Оператор: '{operator}'")
    else:
        print("❌ Оператор не найден")
    
    print()

if __name__ == "__main__":
    try:
        test_specific_patterns()
        test_parser_improvements()
    except Exception as e:
        print(f"Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()