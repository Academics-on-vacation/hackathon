#!/usr/bin/env python3
"""
Тест функции унификации телефонных номеров
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.utils.phone_normalizer import normalize_phone_number, normalize_phone_numbers

def test_phone_normalization():
    """Тестирует функцию унификации телефонных номеров"""
    
    # Тестовые случаи: (входной номер, ожидаемый результат)
    test_cases = [
        # Стандартные форматы
        ("+79123456789", "79123456789"),
        ("89123456789", "79123456789"),
        ("79123456789", "79123456789"),
        
        # С пробелами и разделителями
        ("+7 912 345 67 89", "79123456789"),
        ("8 (912) 345-67-89", "79123456789"),
        ("8-912-345-67-89", "79123456789"),
        ("+7 (912) 345 67 89", "79123456789"),
        
        # Без кода страны
        ("9123456789", "79123456789"),
        
        # Некорректные номера
        ("123456789", None),  # слишком короткий
        ("891234567890", None),  # слишком длинный
        ("+1234567890", None),  # не российский номер
        ("", None),  # пустая строка
        (None, None),  # None
        
        # Граничные случаи
        ("77123456789", None),  # двойная семерка
        ("+7 800 555 35 35", "78005553535"),  # бесплатный номер
    ]
    
    print("Тестирование функции normalize_phone_number:")
    print("=" * 50)
    
    passed = 0
    failed = 0
    
    for input_phone, expected in test_cases:
        result = normalize_phone_number(input_phone)
        status = "✓" if result == expected else "✗"
        
        print(f"{status} '{input_phone}' -> '{result}' (ожидалось: '{expected}')")
        
        if result == expected:
            passed += 1
        else:
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"Пройдено тестов: {passed}")
    print(f"Провалено тестов: {failed}")
    print(f"Общий результат: {'УСПЕХ' if failed == 0 else 'ПРОВАЛ'}")
    
    # Тест функции normalize_phone_numbers
    print("\nТестирование функции normalize_phone_numbers:")
    print("=" * 50)
    
    test_list = ["+79123456789", "89876543210", "invalid", "+7 800 555 35 35", ""]
    expected_list = ["79123456789", "79876543210", "78005553535"]
    
    result_list = normalize_phone_numbers(test_list)
    
    print(f"Входной список: {test_list}")
    print(f"Результат: {result_list}")
    print(f"Ожидалось: {expected_list}")
    
    list_test_passed = result_list == expected_list
    print(f"Тест списка: {'✓ УСПЕХ' if list_test_passed else '✗ ПРОВАЛ'}")
    
    return failed == 0 and list_test_passed

if __name__ == "__main__":
    success = test_phone_normalization()
    sys.exit(0 if success else 1)