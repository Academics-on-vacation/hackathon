#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест для проверки обогащения данных полета 2025 формата информацией о регионе
"""

import sys
import os

# Добавляем путь к модулям приложения
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from parsers.data_processor import DataProcessor
from parsers.telegram_parser import TelegramParser

def test_region_enrichment_2025():
    """Тест обогащения данных полета 2025 формата информацией о регионе"""
    print("Тест обогащения данных полета 2025 формата информацией о регионе")
    print("=" * 60)
    
    # Создаем экземпляры парсера и процессора данных
    parser = TelegramParser()
    processor = DataProcessor()
    
    # Проверяем, что RegionLocator инициализирован
    if processor.region_locator is None:
        print("ОШИБКА: RegionLocator не инициализирован")
        return False
    
    print("RegionLocator успешно инициализирован")
    
    # Тестовое SHR сообщение 2025 формата с координатами в Сочи
    shr_msg = """(SHR-ABC123
-ZZZZ1000
-M0020/M0030 /ZONA R1.0 4336N03944E/
-ZZZZ1000
-DEP/4336N03944E DEST/4336N03944E DOF/240102 EET/ROST0002
OPR/ИВАНОВ ИВАН ИВАНОВИЧ REG/RA1234 TYP/DJI RMK/М12345,
ОКРУЖНОСТЬ РАДИУСОМ 1.0 КМ, С ЦЕНТРОМ 4336N03944E, ОБЕСПЕЧЕНИЕ
СОГЛАСОВАНО BWS GEPRC CINEBOT30 . СВЯЗЬ С ОПЕРАТОРОМ БВС ИВАНОВ
ИВАН +79123456789. SID/78005553535)"""
    
    dep_msg = """(DEP-ABC123
-ZZZZ1000
-REG/RA1234 DOF/240102 RMK/M12345 DEP/4336N03944E DEST/4336N03944E)"""
    
    arr_msg = """(ARR-ABC123
-ZZZZ1000-ZZZZ1230
-REG/RA1234 DOF/240102 RMK/M12345 DEP/4336N03944E
 DEST/4336N03944E)"""
    
    # Парсим сообщения в формате 2025
    print("\nПарсинг сообщений 2025 формата...")
    flight_data = parser.parse_flight_messages_2025(shr_msg, dep_msg, arr_msg)
    
    if 'error' in flight_data:
        print(f"ОШИБКА при парсинге: {flight_data['error']}")
        return False
    
    print("Сообщения успешно распаршены")
    print(f"Координаты вылета: {flight_data.get('departure_coords')}")
    
    # Обогащаем данными о регионе
    print("\nОбогащение данными о регионе...")
    enriched_data = processor._enrich_with_region_data(flight_data)
    
    # Проверяем, что поля cartodb_id и name_latin добавлены
    cartodb_id = enriched_data.get('region_cartodb_id')
    name_latin = enriched_data.get('region_name_latin')
    
    print(f"cartodb_id: {cartodb_id}")
    print(f"name_latin: {name_latin}")
    
    if cartodb_id is not None and name_latin is not None:
        print("\n✓ Тест пройден: Поля cartodb_id и name_latin успешно добавлены")
        print(f"  Значения: cartodb_id={cartodb_id}, name_latin='{name_latin}'")
        return True
    else:
        print("\n✗ Тест не пройден: Поля cartodb_id и/или name_latin отсутствуют")
        return False

if __name__ == "__main__":
    success = test_region_enrichment_2025()
    sys.exit(0 if success else 1)