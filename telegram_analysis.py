import pandas as pd
import re
from datetime import datetime
from typing import Dict, List, Tuple, Optional

def analyze_telegram_patterns():
    """Анализирует паттерны в телеграммах для создания парсера"""
    
    print("=== АНАЛИЗ ПАТТЕРНОВ ТЕЛЕГРАММ ===\n")
    
    # Примеры SHR сообщений из данных
    shr_examples = [
        "(SHR-ZZZZZ\n-ZZZZ0900\n-M0016/M0026 /ZONA R0,7 5509N03737E/\n-ZZZZ0900\n-DEP/5509N03737E DEST/5509N03737E DOF/240101 EET/UUWV0001\nOPR/МЕНЖУЛИН АЛЕКСЕЙ ПЕТРОВИ4 REG/07C4935 TYP/BLA RMK/MР11608,\nОКРУЖНОСТЬ РАДИУСОМ 0.7 КМ, С ЦЕНТРОМ 5509N03737E, ОБЕСПЕ4ЕНИЕ\nСОГЛАСОВАНО BWS GEPRC CINEBOT30 . СВЯЗЬ С ОПЕРАТОРОМ БВС МЕНЖУЛИН\nАЛЕКСЕЙ +79771173700. SID/7771445428)",
        
        "(SHR-ZZZZZ\n-ZZZZ0400\n-M0025/M0027 /ZONA 6837N08005E 6837N08007E 6834N08010E 6836N08022E\n6843N08026E 6845N08032E 6841N08039E 6840N08036E 6842N08031E\n6836N08027E 6830N08014E 6837N08005E/\n-ZZZZ1800\n-DEP/6836N08007E DEST/6836N08007E DOF/240102 EET/UNKU0001 UNKL0001\nOPR/ООО ФИНКО REG/0267J81 02K6779 TYP/2BLA RMK/MR091162 MESSOIAHA GT\nWZL/POS 683605N0800635E R 500 M H ABS 0-270 M MONITORING TRUBOPROVODA\nPOLET W ZONE H 250-270 M AMSL 220-250 AGL SHR RAZRABOTAL PRP\nAWERXKOW TEL 89127614825 WZAIMODEJSTWIE S ORGANAMI OWD OSUQESTWLIAET\nWNESHNIJ PILOT BWS САЛТЫКОВ 89174927358 89128709162 SID/7771444381)"
    ]
    
    # Примеры DEP сообщений
    dep_examples = [
        "(DEP-ZZZZZ-ZZZZ0900-ZZZZ\n-REG/07C4935 DOF/240101 RMK/MR11608 DEP/5509N03737E DEST/5509N03737E)",
        "(DEP-ZZZZZ-ZZZZ0400-ZZZZ1800\n-DEP/6836N08007E DEST/6836N08007E DOF/240102\nREG/0267J81 RMK/MR091162)"
    ]
    
    # Примеры ARR сообщений
    arr_examples = [
        "(ARR-ZZZZZ-ZZZZ0900-ZZZZ1515\n-REG/07C4935 DOF/240101 RMK/MR11608 DEP/5509N03737E\n DEST/5509N03737E)",
        "(ARR-ZZZZZ-ZZZZ0400-ZZZZ1325\n-DEP/6836N08007E DEST/6836N08007E DOF/240102 REG/0267J81\nRMK/MR091162)"
    ]
    
    print("1. ПАТТЕРНЫ КООРДИНАТ:")
    coord_patterns = [
        "5509N03737E",  # DDMMN/DDDMME
        "6836N08007E",
        "683605N0800635E",  # DDMMSSN/DDDMMSSE
        "554529N0382503E"
    ]
    
    for coord in coord_patterns:
        lat, lon = parse_coordinates(coord)
        print(f"   {coord} -> Lat: {lat:.6f}, Lon: {lon:.6f}")
    
    print("\n2. ПАТТЕРНЫ ВРЕМЕНИ:")
    time_patterns = [
        "ZZZZ0900",  # 09:00 UTC
        "ZZZZ1515",  # 15:15 UTC
        "ZZZZ0400"   # 04:00 UTC
    ]
    
    for time_str in time_patterns:
        time_parsed = parse_time(time_str)
        print(f"   {time_str} -> {time_parsed}")
    
    print("\n3. ПАТТЕРНЫ ДАТ:")
    date_patterns = [
        "DOF/240101",  # 2024-01-01
        "DOF/240102",  # 2024-01-02
        "DOF/241231"   # 2024-12-31
    ]
    
    for date_str in date_patterns:
        date_parsed = parse_date(date_str)
        print(f"   {date_str} -> {date_parsed}")
    
    print("\n4. ИЗВЛЕЧЕНИЕ КЛЮЧЕВЫХ ПОЛЕЙ:")
    
    # Анализ первого SHR сообщения
    shr_msg = shr_examples[0]
    fields = extract_shr_fields(shr_msg)
    
    print("   Из SHR сообщения:")
    for key, value in fields.items():
        print(f"     {key}: {value}")

def parse_coordinates(coord_str: str) -> Tuple[float, float]:
    """Парсит координаты из различных форматов"""
    # Удаляем пробелы
    coord_str = coord_str.strip()
    
    # Паттерн для координат: DDMM[SS]N/DDDMM[SS]E
    pattern = r'(\d{4,6})([NS])(\d{5,7})([EW])'
    match = re.match(pattern, coord_str)
    
    if not match:
        raise ValueError(f"Неверный формат координат: {coord_str}")
    
    lat_str, lat_dir, lon_str, lon_dir = match.groups()
    
    # Парсим широту
    if len(lat_str) == 4:  # DDMM
        lat_deg = int(lat_str[:2])
        lat_min = int(lat_str[2:4])
        lat_sec = 0
    elif len(lat_str) == 6:  # DDMMSS
        lat_deg = int(lat_str[:2])
        lat_min = int(lat_str[2:4])
        lat_sec = int(lat_str[4:6])
    else:
        raise ValueError(f"Неверный формат широты: {lat_str}")
    
    lat = lat_deg + lat_min/60 + lat_sec/3600
    if lat_dir == 'S':
        lat = -lat
    
    # Парсим долготу
    if len(lon_str) == 5:  # DDDMM
        lon_deg = int(lon_str[:3])
        lon_min = int(lon_str[3:5])
        lon_sec = 0
    elif len(lon_str) == 7:  # DDDMMSS
        lon_deg = int(lon_str[:3])
        lon_min = int(lon_str[3:5])
        lon_sec = int(lon_str[5:7])
    else:
        raise ValueError(f"Неверный формат долготы: {lon_str}")
    
    lon = lon_deg + lon_min/60 + lon_sec/3600
    if lon_dir == 'W':
        lon = -lon
    
    return lat, lon

def parse_time(time_str: str) -> str:
    """Парсит время из формата ZZZZHHMM"""
    if time_str.startswith('ZZZZ') and len(time_str) == 8:
        hours = time_str[4:6]
        minutes = time_str[6:8]
        return f"{hours}:{minutes}"
    return time_str

def parse_date(date_str: str) -> str:
    """Парсит дату из формата DOF/YYMMDD"""
    if date_str.startswith('DOF/') and len(date_str) == 10:
        year = "20" + date_str[4:6]  # Предполагаем 21 век
        month = date_str[6:8]
        day = date_str[8:10]
        return f"{year}-{month}-{day}"
    return date_str

def extract_shr_fields(shr_message: str) -> Dict[str, str]:
    """Извлекает ключевые поля из SHR сообщения"""
    fields = {}
    
    # Извлекаем регистрационный номер
    reg_match = re.search(r'REG/([A-Z0-9]+)', shr_message)
    if reg_match:
        fields['registration'] = reg_match.group(1)
    
    # Извлекаем тип БВС
    typ_match = re.search(r'TYP/([A-Z0-9]+)', shr_message)
    if typ_match:
        fields['aircraft_type'] = typ_match.group(1)
    
    # Извлекаем оператора
    opr_match = re.search(r'OPR/([^\\n]+)', shr_message)
    if opr_match:
        fields['operator'] = opr_match.group(1).strip()
    
    # Извлекаем координаты вылета
    dep_match = re.search(r'DEP/(\d{4,6}[NS]\d{5,7}[EW])', shr_message)
    if dep_match:
        fields['departure_coords'] = dep_match.group(1)
    
    # Извлекаем координаты назначения
    dest_match = re.search(r'DEST/(\d{4,6}[NS]\d{5,7}[EW])', shr_message)
    if dest_match:
        fields['destination_coords'] = dest_match.group(1)
    
    # Извлекаем дату
    dof_match = re.search(r'DOF/(\d{6})', shr_message)
    if dof_match:
        fields['date'] = dof_match.group(1)
    
    # Извлекаем время вылета
    time_match = re.search(r'-ZZZZ(\d{4})', shr_message)
    if time_match:
        fields['departure_time'] = time_match.group(1)
    
    # Извлекаем SID
    sid_match = re.search(r'SID/(\d+)', shr_message)
    if sid_match:
        fields['sid'] = sid_match.group(1)
    
    return fields

def create_sample_parser():
    """Создает пример парсера для демонстрации"""
    
    print("\n=== ПРИМЕР ПАРСЕРА ===\n")
    
    # Пример SHR сообщения
    shr_example = """(SHR-ZZZZZ
-ZZZZ0900
-M0016/M0026 /ZONA R0,7 5509N03737E/
-ZZZZ0900
-DEP/5509N03737E DEST/5509N03737E DOF/240101 EET/UUWV0001
OPR/МЕНЖУЛИН АЛЕКСЕЙ ПЕТРОВИ4 REG/07C4935 TYP/BLA RMK/MР11608,
ОКРУЖНОСТЬ РАДИУСОМ 0.7 КМ, С ЦЕНТРОМ 5509N03737E, ОБЕСПЕ4ЕНИЕ
СОГЛАСОВАНО BWS GEPRC CINEBOT30 . СВЯЗЬ С ОПЕРАТОРОМ БВС МЕНЖУЛИН
АЛЕКСЕЙ +79771173700. SID/7771445428)"""
    
    print("Исходное SHR сообщение:")
    print(shr_example)
    print("\nРезультат парсинга:")
    
    # Парсим сообщение
    fields = extract_shr_fields(shr_example)
    
    # Преобразуем координаты
    if 'departure_coords' in fields:
        lat, lon = parse_coordinates(fields['departure_coords'])
        print(f"Координаты вылета: {lat:.6f}, {lon:.6f}")
    
    # Преобразуем дату и время
    if 'date' in fields and 'departure_time' in fields:
        date_str = parse_date(f"DOF/{fields['date']}")
        time_str = parse_time(f"ZZZZ{fields['departure_time']}")
        print(f"Дата и время вылета: {date_str} {time_str}")
    
    # Выводим остальные поля
    for key, value in fields.items():
        if key not in ['departure_coords', 'date', 'departure_time']:
            print(f"{key}: {value}")

if __name__ == "__main__":
    analyze_telegram_patterns()
    create_sample_parser()