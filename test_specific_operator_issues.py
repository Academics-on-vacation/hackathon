#!/usr/bin/env python3
"""
Тест конкретных проблем с парсингом операторов
"""

import sys
import os
sys.path.append('bvs-analytics/backend')

from parsers.telegram_parser import TelegramParser
import re

def test_specific_issues():
    """Тестируем конкретные проблемы с операторами"""
    
    print("=== Тест конкретных проблем с операторами ===\n")
    
    # Проблемное сообщение 1
    msg1 = """(SHR-ZZZZZ
-ZZZZ0500
-M0009/M0145 /ZONA MR062364/
-ZZZZ1100
-DEP/5425N06437E DEST/5425N06437E DOF/250614 EET/USSS0001 OPR/БУТИН
АЛЕКСАНДР ДМИТРИЕВИ4 REG/0V95647 095V653 TYP/2BLA RMK/ФИЛИАЛ ППК
РОСКАДАСТР УРАЛГЕОИНФОРМ АЭРОФОТОСЬЕМКА ОПЕРАТОР БУТИН АЛЕКСАНДР
ДМИТРИЕВИ4 +7 962 386 58 65 БАС ГЕОСКАН 201М РАЗРЕШЕНИЯ ГШ ВС РФ
НОМЕР 346/7/3494 ОТ 19.12.2024 ГОДА ШТАБА ЦВО НОМЕР 18/97 ОТ
10.02.2025 ФСБ РФ НОМЕР 99/3/1/3487 ОТ 20.03. 2025 МО ЦЕЛИННОГО ОТ
15.04.2025 МО ЗВЕРИНОГОЛОВСКОГО НОМЕР 0247 ОТ 10.04.2025 SID/7772642696)"""

    # Проблемное сообщение 2
    msg2 = """(SHR-ZZZZZ
-ZZZZ0500
-M0050/M0070 /ZONA 6407N04039E 6408N04046E 6335N04045E 6325N04024E
6320N04028E 6320N04012E 6325N04017E 6338N04038E 6407N04039E/
-ZZZZ1200
-DEP/6347N04041E DEST/6347N04041E DOF/250607 EET/ULLL0001 OPR/ООО
ГАУСС REG/0935G90 093G585 TYP/BLA RMK/КО 01073 ТИП БВС SUPERCAM S350
ОПЕРАТОР БВС ТУМИН 89202272125 ПАРШИН 89999700125 ДИСПЕТ4ЕР ТЕРЕЩЕНКО
89282637673 ПОЛЕТЫ ВО ВР7127 РАЗРЕШЕНЫ: КОМАНДИР В/421514 ТРУБИЦЫН
ОД ПЕРЕВАЛОВ РП ТАЛАГИ КАБАКОВ РП ВАСЬКОВО ПОЛОВЦЕВ ОД ПЛЕСЕЦК
НИКИШАЕВ ОД КОСМОДРОМ СВЯДНЕВ SID/7772619481)"""

    parser = TelegramParser()
    
    print("Тест 1: БУТИН АЛЕКСАНДР ДМИТРИЕВИ4")
    print("Исходное сообщение:")
    print(repr(msg1))
    print()
    
    # Очищаем сообщение
    clean_msg1 = msg1.replace('\n', ' ').replace('\r', ' ')
    print("Очищенное сообщение:")
    print(repr(clean_msg1))
    print()
    
    # Ищем OPR/ часть
    opr_start = clean_msg1.find('OPR/')
    if opr_start != -1:
        opr_part = clean_msg1[opr_start:opr_start+100]
        print(f"OPR/ часть: {repr(opr_part)}")
    
    # Тестируем разные паттерны
    patterns = [
        r'OPR/([^¶\n\r]+?)(?=\s+REG/)',
        r'OPR/([^/]+?)(?=\s+REG/)',
        r'OPR/(.+?)(?=\s+REG/)',
        r'OPR/([^\n\r]+?)\s+REG/',
    ]
    
    for i, pattern in enumerate(patterns, 1):
        print(f"\nПаттерн {i}: {pattern}")
        match = re.search(pattern, clean_msg1, re.MULTILINE | re.DOTALL)
        if match:
            result = match.group(1).strip()
            print(f"✅ Найдено: '{result}'")
        else:
            print("❌ Не найдено")
    
    # Тестируем текущий парсер
    print(f"\nТекущий парсер:")
    operator1 = parser._extract_operator(msg1)
    print(f"Результат: '{operator1}'")
    
    print("\n" + "="*50)
    print("Тест 2: ООО ГАУСС")
    print("Исходное сообщение:")
    print(repr(msg2))
    print()
    
    # Очищаем сообщение
    clean_msg2 = msg2.replace('\n', ' ').replace('\r', ' ')
    print("Очищенное сообщение:")
    print(repr(clean_msg2))
    print()
    
    # Ищем OPR/ часть
    opr_start = clean_msg2.find('OPR/')
    if opr_start != -1:
        opr_part = clean_msg2[opr_start:opr_start+100]
        print(f"OPR/ часть: {repr(opr_part)}")
    
    # Тестируем разные паттерны
    for i, pattern in enumerate(patterns, 1):
        print(f"\nПаттерн {i}: {pattern}")
        match = re.search(pattern, clean_msg2, re.MULTILINE | re.DOTALL)
        if match:
            result = match.group(1).strip()
            print(f"✅ Найдено: '{result}'")
        else:
            print("❌ Не найдено")
    
    # Тестируем текущий парсер
    print(f"\nТекущий парсер:")
    operator2 = parser._extract_operator(msg2)
    print(f"Результат: '{operator2}'")

if __name__ == "__main__":
    test_specific_issues()