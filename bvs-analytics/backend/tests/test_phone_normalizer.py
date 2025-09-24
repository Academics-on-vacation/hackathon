#!/usr/bin/env python3
"""
Тест функции унификации телефонных номеров
"""

import sys
import os
import unittest

# Добавляем путь к корневой директории проекта
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.utils.phone_normalizer import normalize_phone_number, normalize_phone_numbers


class TestPhoneNormalizer(unittest.TestCase):
    """Тесты для функций нормализации телефонных номеров"""
    
    def test_normalize_phone_number_standard_formats(self):
        """Тест стандартных форматов номеров"""
        test_cases = [
            ("+79123456789", "79123456789"),
            ("89123456789", "79123456789"),
            ("79123456789", "79123456789"),
        ]
        
        for input_phone, expected in test_cases:
            with self.subTest(input_phone=input_phone):
                result = normalize_phone_number(input_phone)
                self.assertEqual(result, expected)
    
    def test_normalize_phone_number_with_separators(self):
        """Тест номеров с разделителями"""
        test_cases = [
            ("+7 912 345 67 89", "79123456789"),
            ("8 (912) 345-67-89", "79123456789"),
            ("8-912-345-67-89", "79123456789"),
            ("+7 (912) 345 67 89", "79123456789"),
        ]
        
        for input_phone, expected in test_cases:
            with self.subTest(input_phone=input_phone):
                result = normalize_phone_number(input_phone)
                self.assertEqual(result, expected)
    
    def test_normalize_phone_number_without_country_code(self):
        """Тест номеров без кода страны"""
        result = normalize_phone_number("9123456789")
        self.assertEqual(result, "79123456789")
    
    def test_normalize_phone_number_invalid_cases(self):
        """Тест некорректных номеров"""
        invalid_cases = [
            "123456789",      # слишком короткий
            "891234567890",   # слишком длинный
            "+1234567890",    # не российский номер
            "",               # пустая строка
            None,             # None
            "77123456789",    # двойная семерка
        ]
        
        for invalid_phone in invalid_cases:
            with self.subTest(invalid_phone=invalid_phone):
                result = normalize_phone_number(invalid_phone)
                self.assertIsNone(result)
    
    def test_normalize_phone_number_toll_free(self):
        """Тест бесплатных номеров"""
        result = normalize_phone_number("+7 800 555 35 35")
        self.assertEqual(result, "78005553535")
    
    def test_normalize_phone_numbers_list(self):
        """Тест функции нормализации списка номеров"""
        input_list = ["+79123456789", "89876543210", "invalid", "+7 800 555 35 35", ""]
        expected_list = ["79123456789", "79876543210", "78005553535"]
        
        result_list = normalize_phone_numbers(input_list)
        self.assertEqual(result_list, expected_list)
    
    def test_normalize_phone_numbers_empty_list(self):
        """Тест пустого списка"""
        result = normalize_phone_numbers([])
        self.assertEqual(result, [])
    
    def test_normalize_phone_numbers_none_input(self):
        """Тест None на входе"""
        result = normalize_phone_numbers(None)
        self.assertEqual(result, [])


def run_manual_test():
    """Запуск ручного теста с выводом результатов"""
    print("Тестирование функции normalize_phone_number:")
    print("=" * 50)
    
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
    # Можно запустить либо unittest, либо ручной тест
    import argparse
    
    parser = argparse.ArgumentParser(description='Тест нормализации телефонных номеров')
    parser.add_argument('--manual', action='store_true', help='Запустить ручной тест с подробным выводом')
    args = parser.parse_args()
    
    if args.manual:
        success = run_manual_test()
        sys.exit(0 if success else 1)
    else:
        unittest.main()