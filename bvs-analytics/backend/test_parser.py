#!/usr/bin/env python3
"""
Тест парсера телеграмм БВС
"""

import sys
from pathlib import Path

# Добавляем корневую директорию в PYTHONPATH
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

from parsers.telegram_parser import TelegramParser

def test_parser():
    """Тестирует парсер на примерах из данных"""
    
    parser = TelegramParser()
    
    # Пример SHR сообщения из данных
    shr_example = """(SHR-ZZZZZ
-ZZZZ0900
-M0016/M0026 /ZONA R0,7 5509N03737E/
-ZZZZ0900
-DEP/5509N03737E DEST/5509N03737E DOF/240101 EET/UUWV0001
OPR/МЕНЖУЛИН АЛЕКСЕЙ ПЕТРОВИ4 REG/07C4935 TYP/BLA RMK/MР11608,
ОКРУЖНОСТЬ РАДИУСОМ 0.7 КМ, С ЦЕНТРОМ 5509N03737E, ОБЕСПЕ4ЕНИЕ
СОГЛАСОВАНО BWS GEPRC CINEBOT30 . СВЯЗЬ С ОПЕРАТОРОМ БВС МЕНЖУЛИН
АЛЕКСЕЙ +79771173700. SID/7771445428)"""
    
    # Пример DEP сообщения
    dep_example = """(DEP-ZZZZZ-ZZZZ0900-ZZZZ
-REG/07C4935 DOF/240101 RMK/MR11608 DEP/5509N03737E DEST/5509N03737E)"""
    
    # Пример ARR сообщения
    arr_example = """(ARR-ZZZZZ-ZZZZ0900-ZZZZ1515
-REG/07C4935 DOF/240101 RMK/MR11608 DEP/5509N03737E
 DEST/5509N03737E)"""
    
    print("=== ТЕСТ ПАРСЕРА ТЕЛЕГРАММ БВС ===\n")
    
    # Тест парсинга SHR сообщения
    print("1. Тест SHR сообщения:")
    shr_result = parser.parse_shr_message(shr_example)
    
    if 'error' not in shr_result:
        print("✅ SHR сообщение успешно распарсено:")
        for key, value in shr_result.items():
            if key != 'raw_message':
                print(f"   {key}: {value}")
    else:
        print(f"❌ Ошибка парсинга SHR: {shr_result['error']}")
    
    print("\n" + "="*50 + "\n")
    
    # Тест парсинга DEP сообщения
    print("2. Тест DEP сообщения:")
    dep_result = parser.parse_dep_message(dep_example)
    
    if 'error' not in dep_result:
        print("✅ DEP сообщение успешно распарсено:")
        for key, value in dep_result.items():
            if key != 'raw_message':
                print(f"   {key}: {value}")
    else:
        print(f"❌ Ошибка парсинга DEP: {dep_result['error']}")
    
    print("\n" + "="*50 + "\n")
    
    # Тест парсинга ARR сообщения
    print("3. Тест ARR сообщения:")
    arr_result = parser.parse_arr_message(arr_example)
    
    if 'error' not in arr_result:
        print("✅ ARR сообщение успешно распарсено:")
        for key, value in arr_result.items():
            if key != 'raw_message':
                print(f"   {key}: {value}")
    else:
        print(f"❌ Ошибка парсинга ARR: {arr_result['error']}")
    
    print("\n" + "="*50 + "\n")
    
    # Тест объединенного парсинга
    print("4. Тест объединенного парсинга полета:")
    combined_result = parser.parse_flight_messages(shr_example, dep_example, arr_example)
    
    if 'error' not in combined_result:
        print("✅ Полет успешно распарсен:")
        for key, value in combined_result.items():
            if not key.startswith('raw_'):
                print(f"   {key}: {value}")
    else:
        print(f"❌ Ошибка объединенного парсинга: {combined_result['error']}")
    
    print("\n" + "="*50 + "\n")
    
    # Тест парсинга координат
    print("5. Тест парсинга различных форматов координат:")
    coord_examples = [
        "5509N03737E",      # DDMMN/DDDMME
        "683605N0800635E",  # DDMMSSN/DDDMMSSE
        "554529N0382503E",  # DDMMSSN/DDDMMSSE
    ]
    
    for coord in coord_examples:
        try:
            lat, lon = parser._parse_coordinates(coord)
            print(f"   {coord} → Lat: {lat:.6f}, Lon: {lon:.6f}")
        except Exception as e:
            print(f"   ❌ {coord} → Ошибка: {e}")
    
    print("\n=== ТЕСТ ЗАВЕРШЕН ===")

if __name__ == "__main__":
    test_parser()