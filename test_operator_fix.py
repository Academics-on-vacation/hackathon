#!/usr/bin/env python3
"""
Тест исправления парсинга оператора
"""

import sys
import os
sys.path.append('bvs-analytics/backend')

from parsers.telegram_parser import TelegramParser
import pandas as pd
import re

def test_operator_fix():
    """Тестируем исправление парсинга оператора"""
    
    # Читаем проблемную строку
    file_path = 'data/2025.xlsx'
    df = pd.read_excel(file_path, sheet_name='Result_1', nrows=5)
    
    # Строка 2 (Ростовский) - проблемная
    row = df.iloc[1]
    shr_msg = str(row.get('SHR', ''))
    
    print("=== Тест исправления парсинга оператора ===\n")
    
    # Создаем парсер
    parser = TelegramParser()
    
    # Очищаем сообщение
    clean_message = shr_msg.replace('¶', ' ').replace('\n', ' ').replace('\r', ' ')
    
    print("Очищенное сообщение:")
    print(repr(clean_message))
    print()
    
    # Тестируем первый паттерн из метода _extract_operator
    pattern1 = r'OPR/([^¶\n\r]+?)(?:\s+REG/|\s+TYP/|\s+RMK/|\s+SID/|¶|$)'
    match1 = re.search(pattern1, clean_message, re.MULTILINE | re.DOTALL)
    
    print(f"Паттерн 1: {pattern1}")
    if match1:
        result1 = match1.group(1).strip()
        print(f"✅ Результат: '{result1}'")
    else:
        print("❌ Не найдено")
    
    # Тестируем основной паттерн из конструктора
    main_pattern = parser.opr_pattern
    match_main = re.search(main_pattern, clean_message)
    
    print(f"\nОсновной паттерн: {main_pattern}")
    if match_main:
        result_main = match_main.group(1).strip()
        print(f"✅ Результат: '{result_main}'")
    else:
        print("❌ Не найдено")
    
    # Тестируем метод парсера
    print(f"\nМетод парсера:")
    operator = parser._extract_operator(shr_msg)
    print(f"Результат: '{operator}'")
    
    # Попробуем более простой паттерн
    simple_pattern = r'OPR/([^¶\n\r]+?)(?=\s+REG/)'
    match_simple = re.search(simple_pattern, clean_message)
    
    print(f"\nПростой паттерн: {simple_pattern}")
    if match_simple:
        result_simple = match_simple.group(1).strip()
        print(f"✅ Результат: '{result_simple}'")
    else:
        print("❌ Не найдено")

if __name__ == "__main__":
    test_operator_fix()