import pandas as pd
import re
import os
from typing import List, Dict, Any, Optional
import logging
from .telegram_parser import TelegramParser
import sys

# Добавляем путь к модулям приложения
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from app.utils.RegionLocator import RegionLocator

logger = logging.getLogger(__name__)

class DataProcessor:
    """Обработчик данных из Excel файлов"""
    
    def __init__(self):
        self.parser = TelegramParser()
        
        # Инициализируем RegionLocator с правильным путем к russia.geojson
        current_dir = os.path.dirname(os.path.abspath(__file__))
        geojson_path = os.path.join(current_dir, "..", "..", "data", "russia.geojson")
        try:
            self.region_locator = RegionLocator(geojson_path)
            logger.info(f"RegionLocator initialized with geojson: {geojson_path}")
        except Exception as e:
            logger.error(f"Failed to initialize RegionLocator: {e}")
            self.region_locator = None
        
        # Маппинг регионов из названий листов
        self.region_mapping = {
            'Москва': 'Московская область',
            'Санкт-Петербург': 'Санкт-Петербург',
            'Калининград': 'Калининградская область',
            'Ростов-на-Дону': 'Ростовская область',
            'Самара': 'Самарская область',
            'Екатеринбург': 'Свердловская область',
            'Тюмень': 'Тюменская область',
            'Новосибирск': 'Новосибирская область',
            'Красноярск': 'Красноярский край',
            'Иркутск': 'Иркутская область',
            'Якутск': 'Республика Саха (Якутия)',
            'Магадан': 'Магаданская область',
            'Хабаровск': 'Хабаровский край',
            'Симферополь': 'Республика Крым',
            'Result_1': None  # Агрегированные данные
        }
    
    def process_excel_file(self, file_path: str) -> Dict[str, Any]:
        """Обрабатывает Excel файл с данными полетов"""
        try:
            excel_file = pd.ExcelFile(file_path)
            all_flights = []
            errors = []
            processed_sheets = 0
            
            logger.info(f"Processing Excel file: {file_path}")
            logger.info(f"Found sheets: {excel_file.sheet_names}")
            
            for sheet_name in excel_file.sheet_names:
                if sheet_name in ['Лист1']:  # Пропускаем пустые листы
                    continue
                
                try:
                    df = pd.read_excel(file_path, sheet_name=sheet_name)
                    flights = self._process_sheet(df, sheet_name)
                    all_flights.extend(flights)
                    processed_sheets += 1
                    logger.info(f"Processed sheet '{sheet_name}': {len(flights)} flights")
                    
                except Exception as e:
                    error_msg = f"Error processing sheet '{sheet_name}': {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
            
            return {
                'flights': all_flights,
                'errors': errors,
                'total_processed': len(all_flights),
                'sheets_processed': processed_sheets
            }
            
        except Exception as e:
            logger.error(f"Error processing Excel file: {e}")
            return {
                'flights': [],
                'errors': [f"Failed to process file: {str(e)}"],
                'total_processed': 0,
                'sheets_processed': 0
            }
    
    def _process_sheet(self, df: pd.DataFrame, sheet_name: str) -> List[Dict[str, Any]]:
        """Обрабатывает отдельный лист Excel"""
        flights = []
        region_name = self.region_mapping.get(sheet_name, sheet_name)
        
        logger.info(f"Processing sheet '{sheet_name}' with {len(df)} rows")
        logger.info(f"Columns: {list(df.columns)}")
        
        # Определяем формат листа по колонкам
        if self._is_2025_format(df):
            flights = self._process_2025_format(df, sheet_name)
        elif self._is_shr_dep_arr_format(df):
            flights = self._process_shr_dep_arr_format(df, region_name)
        elif self._is_detailed_format(df):
            flights = self._process_detailed_format(df, region_name)
        elif self._is_aggregated_format(df):
            flights = self._process_aggregated_format(df, region_name)
        else:
            logger.warning(f"Unknown format for sheet '{sheet_name}'")
        
        return flights
    
    def _is_shr_dep_arr_format(self, df: pd.DataFrame) -> bool:
        """Проверяет, является ли лист форматом SHR/DEP/ARR"""
        columns = [col.upper() for col in df.columns]
        return 'SHR' in columns and ('DEP' in columns or 'ARR' in columns)
    
    def _is_detailed_format(self, df: pd.DataFrame) -> bool:
        """Проверяет, является ли лист детальным форматом (как Новосибирск)"""
        columns = [col.lower() for col in df.columns]
        return any('рейс' in col for col in columns) or any('борт' in col for col in columns)
    
    def _is_aggregated_format(self, df: pd.DataFrame) -> bool:
        """Проверяет, является ли лист агрегированным форматом"""
        columns = [col.lower() for col in df.columns]
        return any('центр' in col for col in columns)
    
    def _is_2025_format(self, df: pd.DataFrame) -> bool:
        """Проверяет, является ли лист форматом 2025.xlsx"""
        columns = [col for col in df.columns]
        # Формат 2025: ['Центр ЕС ОрВД', 'SHR', 'DEP', 'ARR']
        return (len(columns) == 4 and
                'Центр ЕС ОрВД' in columns and
                'SHR' in columns and
                'DEP' in columns and
                'ARR' in columns)
    
    def _enrich_with_region_data(self, flight_data: Dict[str, Any]) -> Dict[str, Any]:
        """Обогащает данные полета информацией о регионе из geojson"""
        if not self.region_locator:
            return flight_data
        
        # Пробуем найти регион по координатам вылета
        coords_to_check = []
        if 'departure_coords' in flight_data and flight_data['departure_coords']:
            coords_to_check.append(('departure', flight_data['departure_coords']))
        
        if 'arrival_coords' in flight_data and flight_data['arrival_coords']:
            coords_to_check.append(('arrival', flight_data['arrival_coords']))
        elif 'destination_coords' in flight_data and flight_data['destination_coords']:
            coords_to_check.append(('destination', flight_data['destination_coords']))
        
        # Ищем регион по первым доступным координатам
        for coord_type, coords in coords_to_check:
            try:
                lat, lon = coords
                region_info = self.region_locator.get_region(lat, lon)
                if region_info:
                    # Добавляем информацию о регионе
                    flight_data[f'{coord_type}_region_cartodb_id'] = region_info.get('cartodb_id')
                    flight_data[f'{coord_type}_region_name_latin'] = region_info.get('name_latin')
                    flight_data[f'{coord_type}_region_name'] = region_info.get('name')
                    
                    # Если это первый найденный регион, добавляем общие поля
                    if 'region_cartodb_id' not in flight_data:
                        flight_data['region_cartodb_id'] = region_info.get('cartodb_id')
                        flight_data['region_name_latin'] = region_info.get('name_latin')
                    
                    logger.debug(f"Found region for {coord_type} coords ({lat}, {lon}): {region_info.get('name')} (cartodb_id: {region_info.get('cartodb_id')})")
                    break
            except Exception as e:
                logger.debug(f"Error finding region for {coord_type} coords: {e}")
                continue
        
        return flight_data
    
    def _process_shr_dep_arr_format(self, df: pd.DataFrame, region_name: str) -> List[Dict[str, Any]]:
        """Обрабатывает формат с колонками SHR/DEP/ARR"""
        flights = []
        
        for idx, row in df.iterrows():
            try:
                # Получаем сообщения
                shr_msg = self._clean_message(row.get('SHR', ''))
                dep_msg = self._clean_message(row.get('DEP', ''))
                arr_msg = self._clean_message(row.get('ARR', ''))
                
                # Пропускаем пустые строки
                if not shr_msg:
                    continue
                
                # Парсим сообщения
                flight_data = self.parser.parse_flight_messages(shr_msg, dep_msg, arr_msg)
                
                if 'error' not in flight_data:
                    flight_data['region_name'] = region_name
                    flight_data['source_sheet'] = region_name
                    
                    # Обогащаем данными о регионе из geojson
                    flight_data = self._enrich_with_region_data(flight_data)
                    
                    flights.append(flight_data)
                else:
                    logger.warning(f"Failed to parse flight in row {idx}: {flight_data['error']}")
                    
            except Exception as e:
                logger.error(f"Error processing row {idx}: {e}")
        
        return flights
    
    def _process_detailed_format(self, df: pd.DataFrame, region_name: str) -> List[Dict[str, Any]]:
        """Обрабатывает детальный формат (как в Новосибирске)"""
        flights = []
        
        for idx, row in df.iterrows():
            try:
                flight_data = {
                    'region_name': region_name,
                    'source_sheet': region_name,
                    'flight_id': str(row.get('Рейс', '')),
                    'aircraft_type': str(row.get('Тип/ группа ВС', '')),
                    'registration': str(row.get('Борт. номер ВС.', '')),
                    'operator': str(row.get('Владелец ВС.', '')),
                }
                
                # Обрабатываем времена
                dep_time = row.get('Время вылета.')
                arr_time = row.get('Время посадки.')
                
                if pd.notna(dep_time):
                    flight_data['departure_datetime'] = pd.to_datetime(dep_time)
                if pd.notna(arr_time):
                    flight_data['arrival_datetime'] = pd.to_datetime(arr_time)
                
                # Вычисляем длительность
                if 'departure_datetime' in flight_data and 'arrival_datetime' in flight_data:
                    duration = flight_data['arrival_datetime'] - flight_data['departure_datetime']
                    flight_data['duration_minutes'] = int(duration.total_seconds() / 60)
                
                # Извлекаем координаты из текста маршрута
                route_text = str(row.get('Текст исходного маршрута', ''))
                coords = self._extract_coordinates_from_text(route_text)
                if coords:
                    flight_data['departure_coords'] = coords
                    flight_data['arrival_coords'] = coords  # Обычно одинаковые для БВС
                
                # Дополнительные поля
                flight_data['raw_route'] = route_text
                flight_data['eet'] = str(row.get('EET', ''))
                
                # Обогащаем данными о регионе из geojson
                flight_data = self._enrich_with_region_data(flight_data)
                
                flights.append(flight_data)
                
            except Exception as e:
                logger.error(f"Error processing detailed row {idx}: {e}")
        
        return flights
    
    def _process_aggregated_format(self, df: pd.DataFrame, region_name: str) -> List[Dict[str, Any]]:
        """Обрабатывает агрегированный формат"""
        flights = []
        
        for idx, row in df.iterrows():
            try:
                center_name = str(row.get('Центр ЕС ОрВД', ''))
                shr_msg = self._clean_message(row.get('SHR', ''))
                dep_msg = self._clean_message(row.get('DEP', ''))
                arr_msg = self._clean_message(row.get('ARR', ''))
                
                if not shr_msg:
                    continue
                
                flight_data = self.parser.parse_flight_messages(shr_msg, dep_msg, arr_msg)
                
                if 'error' not in flight_data:
                    flight_data['region_name'] = center_name
                    flight_data['source_sheet'] = 'Aggregated'
                    
                    # Обогащаем данными о регионе из geojson
                    flight_data = self._enrich_with_region_data(flight_data)
                    
                    flights.append(flight_data)
                    
            except Exception as e:
                logger.error(f"Error processing aggregated row {idx}: {e}")
        
        return flights
    
    def _process_2025_format(self, df: pd.DataFrame, sheet_name: str) -> List[Dict[str, Any]]:
        """Обрабатывает формат 2025.xlsx с колонками ['Центр ЕС ОрВД', 'SHR', 'DEP', 'ARR']"""
        flights = []
        
        logger.info(f"Processing 2025 format sheet '{sheet_name}' with {len(df)} rows")
        
        for idx, row in df.iterrows():
            try:
                center_name = str(row.get('Центр ЕС ОрВД', '')).strip()
                shr_msg = self._clean_message(row.get('SHR', ''))
                dep_msg = self._clean_message(row.get('DEP', ''))
                arr_msg = self._clean_message(row.get('ARR', ''))
                
                # Пропускаем пустые строки
                if not shr_msg or not center_name:
                    continue
                
                # Парсим сообщения с помощью улучшенного парсера
                flight_data = self.parser.parse_flight_messages_2025(shr_msg, dep_msg, arr_msg)
                
                if 'error' not in flight_data:
                    # Добавляем информацию о центре
                    flight_data['region_name'] = center_name
                    flight_data['source_sheet'] = sheet_name
                    flight_data['center_name'] = center_name
                    
                    # Обогащаем данными о регионе из geojson
                    flight_data = self._enrich_with_region_data(flight_data)
                    
                    flights.append(flight_data)
                else:
                    logger.warning(f"Failed to parse 2025 flight in row {idx}: {flight_data['error']}")
                    
            except Exception as e:
                logger.error(f"Error processing 2025 format row {idx}: {e}")
        
        logger.info(f"Successfully processed {len(flights)} flights from 2025 format")
        return flights
    
    def _clean_message(self, message: Any) -> str:
        """Очищает сообщение от лишних символов"""
        if pd.isna(message) or message is None:
            return ""
        
        message = str(message).strip()
        
        # Удаляем специальные символы
        message = message.replace('_x000D_', '\n')
        message = message.replace('\\n', '\n')
        
        return message
    
    def _extract_coordinates_from_text(self, text: str) -> Optional[tuple]:
        """Извлекает координаты из текста маршрута"""
        try:
            # Ищем координаты в различных форматах
            coord_patterns = [
                r'(\d{4}N\d{5}E)',
                r'(\d{6}N\d{7}E)',
                r'(\d{4,6}[NS]\d{5,7}[EW])'
            ]
            
            for pattern in coord_patterns:
                matches = re.findall(pattern, text)
                if matches:
                    return self.parser._parse_coordinates(matches[0])
            
            return None
            
        except Exception as e:
            logger.debug(f"Could not extract coordinates from text: {e}")
            return None
    
    def create_flight_record(self, flight_data: Dict[str, Any]) -> Dict[str, Any]:
        """Создает запись полета для сохранения в БД"""
        import json
        
        record = {
            'flight_id': flight_data.get('flight_id'),
            'registration': flight_data.get('registration'),
            'aircraft_type': flight_data.get('aircraft_type'),
            'operator': flight_data.get('operator'),
            'sid': flight_data.get('sid'),
            'raw_shr_message': flight_data.get('raw_shr_message'),
            'raw_dep_message': flight_data.get('raw_dep_message'),
            'raw_arr_message': flight_data.get('raw_arr_message'),
            'remarks': flight_data.get('remarks'),
            'center_name': flight_data.get('center_name'),
            'source_sheet': flight_data.get('source_sheet'),
            'data_format': '2025' if flight_data.get('center_name') else '2024',
            # Добавляем поля региона из geojson
            'region_cartodb_id': flight_data.get('region_cartodb_id'),
            'region_name_latin': flight_data.get('region_name_latin')
        }
        
        # Обрабатываем координаты
        if 'departure_coords' in flight_data and flight_data['departure_coords']:
            record['departure_lat'] = flight_data['departure_coords'][0]
            record['departure_lon'] = flight_data['departure_coords'][1]
        
        if 'arrival_coords' in flight_data and flight_data['arrival_coords']:
            record['arrival_lat'] = flight_data['arrival_coords'][0]
            record['arrival_lon'] = flight_data['arrival_coords'][1]
        elif 'destination_coords' in flight_data and flight_data['destination_coords']:
            record['arrival_lat'] = flight_data['destination_coords'][0]
            record['arrival_lon'] = flight_data['destination_coords'][1]
        
        # Обрабатываем времена
        if 'departure_datetime' in flight_data:
            record['departure_time'] = flight_data['departure_datetime']
        
        if 'actual_departure_datetime' in flight_data:
            record['actual_departure_time'] = flight_data['actual_departure_datetime']
        
        if 'arrival_datetime' in flight_data:
            record['arrival_time'] = flight_data['arrival_datetime']
        
        if 'actual_arrival_datetime' in flight_data:
            record['actual_arrival_time'] = flight_data['actual_arrival_datetime']
        
        if 'duration_minutes' in flight_data:
            record['duration_minutes'] = flight_data['duration_minutes']
        
        # Обрабатываем высоты (новые поля для 2025.xlsx)
        if 'min_altitude' in flight_data:
            record['min_altitude'] = flight_data['min_altitude']
        
        if 'max_altitude' in flight_data:
            record['max_altitude'] = flight_data['max_altitude']
        
        # Обрабатываем контактные данные (уже унифицированные в парсере)
        if 'phone_numbers' in flight_data and flight_data['phone_numbers']:
            record['phone_numbers'] = json.dumps(flight_data['phone_numbers'], ensure_ascii=False)
        
        return record