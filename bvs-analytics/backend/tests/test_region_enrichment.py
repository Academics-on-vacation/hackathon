#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест для проверки обогащения данных полета информацией о регионе
"""

import sys
import os

# Добавляем путь к модулям приложения
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from parsers.data_processor import DataProcessor
from parsers.telegram_parser import TelegramParser

def test_region_enrichment():
    """Тест обогащения данных полета информацией о регионе"""
    print("Тест обогащения данных полета информацией о регионе")
    print("=" * 50)
    
    # Создаем экземпляры парсера и процессора данных
    parser = TelegramParser()
    processor = DataProcessor()
    
    # Проверяем, что RegionLocator инициализирован
    if processor.region_locator is None:
        print("ОШИБКА: RegionLocator не инициализирован")
        return False
    
    print("RegionLocator успешно инициализирован")
    
    # Тестовое SHR сообщение с координатами в Москве
    shr_msg = """(SHR-ZZZZZ
-ZZZZ0900
-M0016/M0026 /ZONA R0,7 5509N03737E/
-ZZZZ0900
-DEP/5509N03737E DEST/5509N03737E DOF/240101 EET/UUWV0001
OPR/МЕНЖУЛИН АЛЕКСЕЙ ПЕТРОВИ4 REG/07C4935 TYP/BLA RMK/MР11608,
ОКРУЖНОСТЬ РАДИУСОМ 0.7 КМ, С ЦЕНТРОМ 5509N03737E, ОБЕСПЕ4ЕНИЕ
СОГЛАСОВАНО BWS GEPRC CINEBOT30 . СВЯЗЬ С ОПЕРАТОРОМ БВС МЕНЖУЛИН
АЛЕКСЕЙ +79771173700. SID/7771445428)"""
    
    dep_msg = """(DEP-ZZZZZ-ZZZZ0900-ZZZZ
-REG/07C4935 DOF/240101 RMK/MR11608 DEP/5509N03737E DEST/5509N03737E)"""
    
    arr_msg = """(ARR-ZZZZZ-ZZZZ0900-ZZZZ1515
-REG/07C4935 DOF/240101 RMK/MR11608 DEP/5509N03737E
 DEST/5509N03737E)"""
    
    # Парсим сообщения
    print("\nПарсинг сообщений...")
    flight_data = parser.parse_flight_messages(shr_msg, dep_msg, arr_msg)
    
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
    success = test_region_enrichment()
    sys.exit(0 if success else 1)