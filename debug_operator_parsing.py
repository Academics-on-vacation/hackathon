#!/usr/bin/env python3
"""
Отладка парсинга оператора
"""

import sys
import os
sys.path.append('bvs-analytics/backend')

from parsers.telegram_parser import TelegramParser
import pandas as pd
import re

def debug_operator_parsing():
    """Отладка парсинга оператора"""
    
    # Читаем проблемную строку из Excel
    file_path = 'data/2025.xlsx'
    df = pd.read_excel(file_path, sheet_name='Result_1', nrows=5)
    
    # Берем строку 2 (Ростовский) где оператор парсится неполно
    row = df.iloc[1]  # Строка 2 (индекс 1)
    shr_msg = str(row.get('SHR', ''))
    
    print("=== Отладка парсинга оператора ===\n")
    print("Исходное SHR сообщение:")
    print(repr(shr_msg))
    print("\nОчищенное сообщение:")
    clean_message = shr_msg.replace('¶', ' ').replace('\n', ' ').replace('\r', ' ')
    print(repr(clean_message))
    
    # Ищем OPR/ в сообщении
    opr_start = clean_message.find('OPR/')
    if opr_start != -1:
        print(f"\nOPR/ найден на позиции: {opr_start}")
        opr_part = clean_message[opr_start:]
        print(f"Часть с OPR/: {repr(opr_part[:200])}")
    
    # Тестируем разные паттерны
    parser = TelegramParser()
    
    patterns = [
        r'OPR/([^¶\n\r]+?)(?:\s+REG/|\s+TYP/|\s+RMK/|\s+SID/|¶|$)',
        r'OPR/([^/]+?)(?:\s+[A-Z]{3}/)',
        r'OPR/([^\n\r]+?)(?=\n|\r|$)',
        r'OPR/([^¶\n\r]+?)(?=\s+REG/)',
        r'OPR/(.+?)(?=\s+REG/)',
        r'OPR/(.+?)REG/',
    ]
    
    print("\n=== Тестирование паттернов ===")
    for i, pattern in enumerate(patterns, 1):
        print(f"\nПаттерн {i}: {pattern}")
        match = re.search(pattern, clean_message, re.MULTILINE | re.DOTALL)
        if match:
            operator = match.group(1).strip()
            print(f"✅ Найдено: '{operator}'")
        else:
            print("❌ Не найдено")
    
    # Тестируем текущий метод парсера
    print("\n=== Текущий метод парсера ===")
    operator = parser._extract_operator(shr_msg)
    print(f"Результат: '{operator}'")

if __name__ == "__main__":
    debug_operator_parsing()