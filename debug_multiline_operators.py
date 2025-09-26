#!/usr/bin/env python3
"""
Отладка парсинга многострочных операторов
"""

import sys
import os
sys.path.append('bvs-analytics/backend')

from parsers.telegram_parser import TelegramParser
import pandas as pd
import re

def debug_multiline_operators():
    """Отладка парсинга многострочных операторов"""
    
    # Читаем проблемные строки
    file_path = 'data/2025.xlsx'
    df = pd.read_excel(file_path, sheet_name='Result_1', nrows=5)
    
    parser = TelegramParser()
    
    print("=== Отладка многострочных операторов ===\n")
    
    # Тестируем строки 3 и 5 (МВД ПО и ОТДЕЛ)
    test_cases = [
        (2, "МВД ПО РЕСПУБЛИКЕ АЛТАЙ"),  # строка 3 (индекс 2)
        (4, "ОТДЕЛ ПРИМЕНЕНИЯ БАС УЭР ЦУКС ГЛАВНОГО УПРАВЛЕНИЯ МЧС РОССИИ ПО Г МОСКВЕ")  # строка 5 (индекс 4)
    ]
    
    for idx, expected in test_cases:
        row = df.iloc[idx]
        center = row.get('Центр ЕС ОрВД', '')
        shr_msg = str(row.get('SHR', ''))
        
        print(f"--- Тест {idx + 1}: {center} ---")
        print(f"Ожидается: '{expected}'")
        print()
        
        # Показываем исходное сообщение
        print("Исходное SHR:")
        print(repr(shr_msg))
        print()
        
        # Очищенное сообщение
        clean_msg = shr_msg.replace('¶', ' ').replace('\n', ' ').replace('\r', ' ')
        print("Очищенное:")
        print(repr(clean_msg))
        print()
        
        # Ищем OPR/ часть
        opr_start = clean_msg.find('OPR/')
        if opr_start != -1:
            # Ищем REG/ после OPR/
            reg_start = clean_msg.find('REG/', opr_start)
            if reg_start != -1:
                opr_part = clean_msg[opr_start:reg_start]
                print(f"OPR/ до REG/: {repr(opr_part)}")
                
                # Извлекаем только текст после OPR/
                opr_text = opr_part[4:].strip()  # убираем "OPR/"
                print(f"Текст оператора: '{opr_text}'")
            else:
                print("REG/ не найден после OPR/")
        
        # Тестируем новые паттерны
        patterns = [
            r'OPR/(.+?)(?=\s+REG/)',
            r'OPR/(.+?)(?=\s+TYP/)',
            r'OPR/(.+?)(?=\s+RMK/)',
            r'OPR/(.+?)(?=\s+SID/)',
        ]
        
        print("\nТестирование паттернов:")
        for i, pattern in enumerate(patterns, 1):
            match = re.search(pattern, clean_msg, re.MULTILINE | re.DOTALL)
            if match:
                result = match.group(1).strip()
                result = re.sub(r'\s+', ' ', result)  # нормализуем пробелы
                print(f"Паттерн {i}: '{result}'")
                break
        else:
            print("Ни один паттерн не сработал")
        
        # Тестируем текущий парсер
        print(f"\nТекущий парсер: '{parser._extract_operator(shr_msg)}'")
        print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    debug_multiline_operators()