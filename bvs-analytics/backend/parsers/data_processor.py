from datetime import datetime

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
from .flight_parser import FlightParser
logger = logging.getLogger(__name__)

class DataProcessor:
    """Обработчик данных из Excel файлов"""
    
    def __init__(self):
        # self.parser = TelegramParser()

        current_dir = os.path.dirname(os.path.abspath(__file__))
        geojson_path = os.path.join(current_dir, "..", "data", "russia.geojson")
        aerodromes_path = os.path.join(current_dir, "..", "data", "aerodroms.json")
        zones_path = os.path.join(current_dir, "..", "data", "ltsa.json")
        try:
            self.region_locator = RegionLocator(geojson_path)
            logger.info(f"RegionLocator initialized with geojson: {geojson_path}")
        except Exception as e:
            logger.error(f"Failed to initialize RegionLocator: {e}")
            self.region_locator = None
        self.parser = FlightParser(aerodromes_path, zones_path, self.region_locator)
        # Инициализируем RegionLocator с правильным путем к russia.geojson


    
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
        logger.info(f"Processing sheet '{sheet_name}' with {len(df)} rows")
        logger.info(f"Columns: {list(df.columns)}")
        
        # Определяем формат листа по колонкам
        if self._check_file_format(df):
            flights = self._process_data(df, sheet_name)
        else:
            logger.warning(f"Unknown format for sheet '{sheet_name}'")
        
        return flights

    def _check_file_format(self, df: pd.DataFrame) -> bool:
        """Checks if file format is correct. Test column names."""
        columns = [col for col in df.columns]
        # Корректный формат: ['Центр ЕС ОрВД', 'SHR', 'DEP', 'ARR']
        return (len(columns) == 4 and
                'Центр ЕС ОрВД' in columns and
                'SHR' in columns and
                'DEP' in columns and
                'ARR' in columns)

    def _process_data(self, df: pd.DataFrame, sheet_name: str) -> List[Dict[str, Any]]:
        """Обработка файла с колонками ['Центр ЕС ОрВД', 'SHR', 'DEP', 'ARR']"""
        flights = []
        logger.info(f"Processing sheet '{sheet_name}' with {len(df)} rows")
        
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
                # flight_data = self.parser.parse_flight_messages_2025(shr_msg, dep_msg, arr_msg)
                flight_data = self.parser.parse_row(center_name, shr_msg, dep_msg, arr_msg)

                if 'error' not in flight_data:
                    # Добавляем информацию о центре
                    flight_data['center_name'] = center_name
                    
                    # Обогащаем данными о регионе из geojson
                    # flight_data = self._enrich_with_region_data(flight_data)
                    
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
    
    def create_flight_record(self, flight_data: Dict[str, Any]) -> Dict[str, Any]:
        """Создает запись полета для сохранения в БД"""
        import json
        record = {
            # 'flight_id': flight_data.get('flight_id'),
            # 'registration': flight_data.get('registration'),
            'uav_type': flight_data.get('uav_type'),
            'operator': flight_data.get('operator'),
            'sid': flight_data.get('sid'),
            # 'raw_shr_message': flight_data.get('raw_shr_message'),
            # 'raw_dep_message': flight_data.get('raw_dep_message'),
            # 'raw_arr_message': flight_data.get('raw_arr_message'),
            # 'remarks': flight_data.get('remarks'),
            'center_name': flight_data.get('center_name'),
            # 'source_sheet': flight_data.get('source_sheet'),
            # 'data_format': '2025' if flight_data.get('center_name') else '2024',
            # Добавляем поля региона из geojson
            # 'region_cartodb_id': flight_data.get('region_cartodb_id'),
            # 'region_name_latin': flight_data.get('region_name')

            # "dep_date": datetime.strptime(flight_data.get('dep').get('date'), '%Y-%m-%d').date() if flight_data.get('dep').get('date') else "",
            "dep_date": flight_data.get('dep').get('date'),

            # "dep_time": datetime.strptime( flight_data.get('dep').get('time_hhmm'), '%H%M').time()  if flight_data.get('dep').get('time_hhmm') else "",
            "dep_time": flight_data.get('dep').get('time_hhmm'),

            "dep_lat": flight_data.get('dep').get('lat'),
            "dep_lon": flight_data.get('dep').get('lon'),
            "dep_aerodrome_code": flight_data.get('dep').get('aerodrome_code'),
            "dep_aerodrome_name": flight_data.get('dep').get('aerodrome_name'),

            # "arr_date": datetime.strptime(flight_data.get('arr').get('date'), '%Y-%m-%d').date()  if flight_data.get('arr').get('date') else "",
            "arr_date": flight_data.get('arr').get('date'),

            # "arr_time": datetime.strptime(flight_data.get('arr').get('time_hhmm'), '%H%M').time()  if flight_data.get('arr').get('time_hhmm') else "",
            "arr_time": flight_data.get('arr').get('time_hhmm'),

            "arr_lat": flight_data.get('arr').get('lat'),
            "arr_lon": flight_data.get('arr').get('lon'),
            "arr_aerodrome_code": flight_data.get('arr').get('aerodrome_code'),
            "arr_aerodrome_name": flight_data.get('arr').get('aerodrome_name'),
            "start_ts": flight_data.get('start_ts'),
            "end_ts": flight_data.get('start_ts'),
            "duration_min": flight_data.get('duration_min'),
            # "zone_data": json.dumps(flight_data.get('zone', {}), ensure_ascii=False) if flight_data.get('zone') else None,
            "zone_data": flight_data.get('zone', {}),
            "region_id": flight_data.get('region_id'),
            "region_name": flight_data.get('region_name')
        }
        

        return record

    def parse_time(self, time_str: Optional[str]) -> Optional[str]:
        """
        Преобразование времени из формата HHMM в HH:MM:SS

        Args:
            time_str: строка вида "1430"

        Returns:
            Строка вида "14:30:00" или None
        """
        if not time_str:
            return None

        time_str = str(time_str).strip()
        if len(time_str) == 4 and time_str.isdigit():
            return f"{time_str[:2]}:{time_str[2:]}:00"
        return None
