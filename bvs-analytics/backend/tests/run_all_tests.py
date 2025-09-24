#!/usr/bin/env python3
"""
Запуск всех тестов BVS Analytics
"""

import sys
import os
import unittest
import argparse

# Добавляем путь к корневой директории проекта
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def discover_and_run_tests():
    """Автоматически находит и запускает все тесты"""
    # Находим все тесты в папке tests
    loader = unittest.TestLoader()
    start_dir = os.path.dirname(__file__)
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    # Запускаем тесты
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


def run_manual_tests():
    """Запускает ручные тесты с подробным выводом"""
    print("🚀 ЗАПУСК ВСЕХ ТЕСТОВ BVS ANALYTICS\n")
    
    # Импортируем функции ручных тестов
    from test_phone_normalizer import run_manual_test as phone_test
    from test_telegram_parser import run_manual_test as parser_test
    from test_api_integration import run_manual_test as api_test
    
    tests = [
        ("Нормализация телефонных номеров", phone_test),
        ("Парсер телеграмм БВС", parser_test),
        ("Интеграция API", api_test),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*80}")
        print(f"ТЕСТ: {test_name}")
        print('='*80)
        
        try:
            if test_func():
                passed += 1
                print(f"\n✅ ТЕСТ '{test_name}' ПРОЙДЕН")
            else:
                print(f"\n❌ ТЕСТ '{test_name}' ПРОВАЛЕН")
        except Exception as e:
            print(f"\n❌ ТЕСТ '{test_name}' ПРОВАЛЕН С ОШИБКОЙ: {e}")
    
    print(f"\n{'='*80}")
    print(f"ОБЩИЕ РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ")
    print('='*80)
    print(f"Пройдено: {passed}/{total}")
    print(f"Процент успеха: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
        print("\n📋 Что было протестировано:")
        print("   ✅ Унификация телефонных номеров в формат 7XXXXXXXXXX")
        print("   ✅ Интеграция нормализатора с парсером телеграмм")
        print("   ✅ Парсинг SHR, DEP, ARR сообщений")
        print("   ✅ Извлечение и унификация телефонных номеров из сообщений")
        print("   ✅ Интеграция всех компонентов API")
        print("\n🚀 Система готова к работе!")
    else:
        print(f"\n⚠️  {total-passed} тестов провалено. Требуется исправление.")
    
    return passed == total


def main():
    """Главная функция"""
    parser = argparse.ArgumentParser(description='Запуск тестов BVS Analytics')
    parser.add_argument('--manual', action='store_true', 
                       help='Запустить ручные тесты с подробным выводом')
    parser.add_argument('--unittest', action='store_true', 
                       help='Запустить unittest тесты')
    
    args = parser.parse_args()
    
    if args.manual:
        success = run_manual_tests()
    elif args.unittest:
        success = discover_and_run_tests()
    else:
        # По умолчанию запускаем unittest
        print("Запуск unittest тестов (используйте --manual для подробного вывода)")
        success = discover_and_run_tests()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()