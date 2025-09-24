#!/usr/bin/env python3
"""
Тест парсера телеграмм БВС
"""

import sys
import os
import unittest
from datetime import datetime

# Добавляем путь к корневой директории проекта
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from parsers.telegram_parser import TelegramParser


class TestTelegramParser(unittest.TestCase):
    """Тесты для парсера телеграмм БВС"""
    
    def setUp(self):
        """Настройка тестов"""
        self.parser = TelegramParser()
        
        # Тестовые сообщения
        self.shr_example = """(SHR-ZZZZZ
-ZZZZ0900
-M0016/M0026 /ZONA R0,7 5509N03737E/
-ZZZZ0900
-DEP/5509N03737E DEST/5509N03737E DOF/240101 EET/UUWV0001
OPR/МЕНЖУЛИН АЛЕКСЕЙ ПЕТРОВИ4 REG/07C4935 TYP/BLA RMK/MР11608,
ОКРУЖНОСТЬ РАДИУСОМ 0.7 КМ, С ЦЕНТРОМ 5509N03737E, ОБЕСПЕ4ЕНИЕ
СОГЛАСОВАНО BWS GEPRC CINEBOT30 . СВЯЗЬ С ОПЕРАТОРОМ БВС МЕНЖУЛИН
АЛЕКСЕЙ +79771173700. SID/7771445428)"""
        
        self.dep_example = """(DEP-ZZZZZ-ZZZZ0900-ZZZZ
-REG/07C4935 DOF/240101 RMK/MR11608 DEP/5509N03737E DEST/5509N03737E)"""
        
        self.arr_example = """(ARR-ZZZZZ-ZZZZ0900-ZZZZ1515
-REG/07C4935 DOF/240101 RMK/MR11608 DEP/5509N03737E
 DEST/5509N03737E)"""
    
    def test_parse_shr_message(self):
        """Тест парсинга SHR сообщения"""
        result = self.parser.parse_shr_message(self.shr_example)
        
        self.assertNotIn('error', result)
        self.assertEqual(result['message_type'], 'SHR')
        self.assertEqual(result['registration'], '07C4935')
        self.assertEqual(result['aircraft_type'], 'BLA')
        self.assertIn('МЕНЖУЛИН', result['operator'])
        self.assertEqual(result['sid'], '7771445428')
        self.assertEqual(result['flight_date'], '2024-01-01')
        self.assertEqual(result['departure_time'], '09:00')
        
        # Проверяем координаты
        self.assertIsNotNone(result['departure_coords'])
        self.assertIsNotNone(result['destination_coords'])
        
        # Проверяем унифицированные телефонные номера
        self.assertIn('phone_numbers', result)
        self.assertIn('79771173700', result['phone_numbers'])
    
    def test_parse_dep_message(self):
        """Тест парсинга DEP сообщения"""
        result = self.parser.parse_dep_message(self.dep_example)
        
        self.assertNotIn('error', result)
        self.assertEqual(result['message_type'], 'DEP')
        self.assertEqual(result['registration'], '07C4935')
        self.assertEqual(result['flight_date'], '2024-01-01')
    
    def test_parse_arr_message(self):
        """Тест парсинга ARR сообщения"""
        result = self.parser.parse_arr_message(self.arr_example)
        
        self.assertNotIn('error', result)
        self.assertEqual(result['message_type'], 'ARR')
        self.assertEqual(result['registration'], '07C4935')
        self.assertEqual(result['flight_date'], '2024-01-01')
        self.assertEqual(result['arrival_time'], '1515')
    
    def test_parse_coordinates(self):
        """Тест парсинга различных форматов координат"""
        test_cases = [
            ("5509N03737E", (55.15, 37.617)),
            ("683605N0800635E", (68.601389, 80.109722)),
            ("554529N0382503E", (55.758056, 38.417500)),
        ]
        
        for coord_str, expected in test_cases:
            with self.subTest(coord_str=coord_str):
                lat, lon = self.parser._parse_coordinates(coord_str)
                self.assertAlmostEqual(lat, expected[0], places=5)
                self.assertAlmostEqual(lon, expected[1], places=5)
    
    def test_combined_flight_parsing(self):
        """Тест объединенного парсинга полета"""
        result = self.parser.parse_flight_messages(
            self.shr_example, self.dep_example, self.arr_example
        )
        
        self.assertNotIn('error', result)
        self.assertEqual(result['registration'], '07C4935')
        self.assertIn('departure_datetime', result)
        self.assertIn('arrival_datetime', result)
        self.assertIn('duration_minutes', result)
        
        # Проверяем унифицированные телефонные номера
        self.assertIn('phone_numbers', result)
        self.assertIn('79771173700', result['phone_numbers'])
    
    def test_phone_number_extraction_and_normalization(self):
        """Тест извлечения и унификации телефонных номеров"""
        # Тестовое сообщение с различными форматами номеров
        test_message = """(SHR-ZZZZZ
-ZZZZ0900
OPR/ТЕСТОВЫЙ ОПЕРАТОР +79123456789 8(987)654-32-10 REG/TEST123 TYP/BLA
СВЯЗЬ +7 800 555 35 35 SID/1234567890)"""
        
        result = self.parser.parse_shr_message(test_message)
        
        self.assertNotIn('error', result)
        self.assertIn('phone_numbers', result)
        
        # Проверяем, что все номера унифицированы
        expected_phones = ['79123456789', '79876543210', '78005553535']
        for phone in expected_phones:
            self.assertIn(phone, result['phone_numbers'])
    
    def test_2025_format_parsing(self):
        """Тест парсинга формата 2025.xlsx"""
        shr_2025 = """(SHR-TEST123
-ZZZZ0800
-M0100/M0200
-DEP/5509N03737E DEST/5509N03737E DOF/250101
OPR/ТЕСТОВЫЙ ОПЕРАТОР 2025 REG/TEST2025 TYP/QUAD
RMK/ТЕСТОВЫЙ ПОЛЕТ +79123456789 SID/1234567890)"""
        
        result = self.parser.parse_shr_message_2025(shr_2025)
        
        self.assertNotIn('error', result)
        self.assertEqual(result['flight_id'], 'TEST123')
        self.assertEqual(result['registration'], 'TEST2025')
        self.assertEqual(result['aircraft_type'], 'QUAD')
        self.assertIn('min_altitude', result)
        self.assertIn('max_altitude', result)
        self.assertEqual(result['min_altitude'], 100)
        self.assertEqual(result['max_altitude'], 200)
        
        # Проверяем унифицированные телефонные номера
        self.assertIn('phone_numbers', result)
        self.assertIn('79123456789', result['phone_numbers'])


def run_manual_test():
    """Запуск ручного теста с выводом результатов"""
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
    # Можно запустить либо unittest, либо ручной тест
    import argparse
    
    parser = argparse.ArgumentParser(description='Тест парсера телеграмм БВС')
    parser.add_argument('--manual', action='store_true', help='Запустить ручной тест с подробным выводом')
    args = parser.parse_args()
    
    if args.manual:
        run_manual_test()
    else:
        unittest.main()