#!/usr/bin/env python3
"""
Финальный тест улучшенного парсера
"""

import sys
import os
sys.path.append('bvs-analytics/backend')

from parsers.data_processor import DataProcessor
import pandas as pd

def test_final_improvements():
    """Финальный тест всех улучшений"""
    
    print("=== Финальный тест улучшенного парсера ===\n")
    
    # Создаем процессор данных
    processor = DataProcessor()
    
    # Обрабатываем небольшую часть файла
    file_path = 'data/2025.xlsx'
    
    # Читаем только первые 5 строк для тестирования
    df = pd.read_excel(file_path, sheet_name='Result_1', nrows=5)
    
    print(f"Обрабатываем {len(df)} строк из файла 2025.xlsx\n")
    
    flights = []
    for idx, row in df.iterrows():
        center_name = str(row.get('Центр ЕС ОрВД', '')).strip()
        shr_msg = processor._clean_message(row.get('SHR', ''))
        dep_msg = processor._clean_message(row.get('DEP', ''))
        arr_msg = processor._clean_message(row.get('ARR', ''))
        
        if not shr_msg or not center_name:
            continue
        
        # Парсим сообщения с помощью улучшенного парсера
        flight_data = processor.parser.parse_flight_messages_2025(shr_msg, dep_msg, arr_msg)
        
        if 'error' not in flight_data:
            flight_data['region_name'] = center_name
            flight_data['source_sheet'] = 'Result_1'
            flight_data['center_name'] = center_name
            
            # Обогащаем данными о регионе из geojson
            flight_data = processor._enrich_with_region_data(flight_data)
            
            flights.append(flight_data)
            
            print(f"--- Полет {idx + 1}: {center_name} ---")
            print(f"✅ Flight ID: {flight_data.get('flight_id', 'N/A')}")
            print(f"✅ Регистрация: {flight_data.get('registration', 'N/A')}")
            print(f"✅ Тип ВС: {flight_data.get('aircraft_type', 'N/A')}")
            print(f"✅ Оператор: '{flight_data.get('operator', 'N/A')}'")
            
            # Координаты
            dep_coords = flight_data.get('departure_coords')
            dest_coords = flight_data.get('destination_coords')
            
            if dep_coords:
                print(f"✅ Координаты вылета: {dep_coords[0]:.6f}, {dep_coords[1]:.6f}")
            else:
                print("❌ Координаты вылета не найдены")
                
            if dest_coords:
                print(f"✅ Координаты назначения: {dest_coords[0]:.6f}, {dest_coords[1]:.6f}")
            else:
                print("❌ Координаты назначения не найдены")
            
            # Времена
            if flight_data.get('departure_datetime'):
                print(f"✅ Время вылета: {flight_data['departure_datetime']}")
            if flight_data.get('arrival_datetime'):
                print(f"✅ Время посадки: {flight_data['arrival_datetime']}")
            
            # Высоты
            if flight_data.get('min_altitude') and flight_data.get('max_altitude'):
                print(f"✅ Высоты: {flight_data['min_altitude']}-{flight_data['max_altitude']} м")
            
            # Телефоны
            if flight_data.get('phone_numbers'):
                print(f"✅ Телефоны: {flight_data['phone_numbers']}")
            
            # Регион из geojson
            if flight_data.get('region_name_latin'):
                print(f"✅ Регион (geojson): {flight_data['region_name_latin']}")
            
            print()
    
    print(f"=== Итого обработано: {len(flights)} полетов ===")
    
    # Статистика по координатам
    with_dep_coords = sum(1 for f in flights if f.get('departure_coords'))
    with_dest_coords = sum(1 for f in flights if f.get('destination_coords'))
    with_operator = sum(1 for f in flights if f.get('operator'))
    
    print(f"✅ С координатами вылета: {with_dep_coords}/{len(flights)}")
    print(f"✅ С координатами назначения: {with_dest_coords}/{len(flights)}")
    print(f"✅ С оператором: {with_operator}/{len(flights)}")

if __name__ == "__main__":
    try:
        test_final_improvements()
    except Exception as e:
        print(f"Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()