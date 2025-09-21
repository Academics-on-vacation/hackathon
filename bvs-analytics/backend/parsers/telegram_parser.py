import re
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
import logging

logger = logging.getLogger(__name__)

class TelegramParser:
    """Парсер телеграмм полетов БВС"""
    
    def __init__(self):
        # Паттерны для извлечения данных
        self.coord_pattern = r'(\d{4,6})([NS])(\d{5,7})([EW])'
        self.time_pattern = r'ZZZZ(\d{4})'
        self.date_pattern = r'DOF/(\d{6})'
        self.reg_pattern = r'REG/([A-Z0-9\-]+)'
        self.typ_pattern = r'TYP/([A-Z0-9]+)'
        self.opr_pattern = r'OPR/([^\\n\r]+?)(?=\s+REG/|\s+TYP/|\s+RMK/|$)'
        self.sid_pattern = r'SID/(\d+)'
        self.dep_coord_pattern = r'DEP/(\d{4,6}[NS]\d{5,7}[EW])'
        self.dest_coord_pattern = r'DEST/(\d{4,6}[NS]\d{5,7}[EW])'
    
    def parse_shr_message(self, message: str) -> Dict[str, Any]:
        """Парсит SHR сообщение (план полета)"""
        try:
            result = {
                'message_type': 'SHR',
                'registration': self._extract_registration(message),
                'aircraft_type': self._extract_aircraft_type(message),
                'operator': self._extract_operator(message),
                'departure_coords': self._extract_coordinates(message, 'DEP'),
                'destination_coords': self._extract_coordinates(message, 'DEST'),
                'flight_date': self._extract_date(message),
                'departure_time': self._extract_departure_time(message),
                'sid': self._extract_sid(message),
                'raw_message': message.strip()
            }
            
            # Вычисляем datetime для вылета
            if result['flight_date'] and result['departure_time']:
                result['departure_datetime'] = self._combine_date_time(
                    result['flight_date'], result['departure_time']
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Error parsing SHR message: {e}")
            return {'error': str(e), 'raw_message': message}
    
    def parse_dep_message(self, message: str) -> Dict[str, Any]:
        """Парсит DEP сообщение (вылет)"""
        try:
            result = {
                'message_type': 'DEP',
                'registration': self._extract_registration(message),
                'flight_date': self._extract_date(message),
                'departure_time': self._extract_departure_time(message),
                'departure_coords': self._extract_coordinates(message, 'DEP'),
                'destination_coords': self._extract_coordinates(message, 'DEST'),
                'raw_message': message.strip()
            }
            
            if result['flight_date'] and result['departure_time']:
                result['departure_datetime'] = self._combine_date_time(
                    result['flight_date'], result['departure_time']
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Error parsing DEP message: {e}")
            return {'error': str(e), 'raw_message': message}
    
    def parse_arr_message(self, message: str) -> Dict[str, Any]:
        """Парсит ARR сообщение (посадка)"""
        try:
            # Ищем время посадки в ARR сообщении
            arr_time_pattern = r'ARR-[^-]+-[^-]+-[^-]+-ZZZZ(\d{4})'
            arr_time_match = re.search(arr_time_pattern, message)
            
            result = {
                'message_type': 'ARR',
                'registration': self._extract_registration(message),
                'flight_date': self._extract_date(message),
                'arrival_time': arr_time_match.group(1) if arr_time_match else None,
                'departure_coords': self._extract_coordinates(message, 'DEP'),
                'destination_coords': self._extract_coordinates(message, 'DEST'),
                'raw_message': message.strip()
            }
            
            if result['flight_date'] and result['arrival_time']:
                result['arrival_datetime'] = self._combine_date_time(
                    result['flight_date'], result['arrival_time']
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Error parsing ARR message: {e}")
            return {'error': str(e), 'raw_message': message}
    
    def _extract_coordinates(self, message: str, coord_type: str) -> Optional[Tuple[float, float]]:
        """Извлекает координаты из сообщения"""
        pattern = f'{coord_type}/(\d{{4,6}}[NS]\d{{5,7}}[EW])'
        match = re.search(pattern, message)
        if match:
            return self._parse_coordinates(match.group(1))
        return None
    
    def _parse_coordinates(self, coord_str: str) -> Tuple[float, float]:
        """Конвертирует координаты в десятичные градусы"""
        match = re.match(self.coord_pattern, coord_str)
        
        if not match:
            raise ValueError(f"Invalid coordinate format: {coord_str}")
        
        lat_str, lat_dir, lon_str, lon_dir = match.groups()
        
        # Парсинг широты
        if len(lat_str) == 4:  # DDMM
            lat = int(lat_str[:2]) + int(lat_str[2:4])/60
        elif len(lat_str) == 6:  # DDMMSS
            lat = int(lat_str[:2]) + int(lat_str[2:4])/60 + int(lat_str[4:6])/3600
        else:
            raise ValueError(f"Invalid latitude format: {lat_str}")
        
        if lat_dir == 'S':
            lat = -lat
        
        # Парсинг долготы
        if len(lon_str) == 5:  # DDDMM
            lon = int(lon_str[:3]) + int(lon_str[3:5])/60
        elif len(lon_str) == 7:  # DDDMMSS
            lon = int(lon_str[:3]) + int(lon_str[3:5])/60 + int(lon_str[5:7])/3600
        else:
            raise ValueError(f"Invalid longitude format: {lon_str}")
        
        if lon_dir == 'W':
            lon = -lon
        
        return lat, lon
    
    def _extract_registration(self, message: str) -> Optional[str]:
        """Извлекает регистрационный номер"""
        match = re.search(self.reg_pattern, message)
        return match.group(1) if match else None
    
    def _extract_aircraft_type(self, message: str) -> Optional[str]:
        """Извлекает тип БВС"""
        match = re.search(self.typ_pattern, message)
        return match.group(1) if match else None
    
    def _extract_operator(self, message: str) -> Optional[str]:
        """Извлекает оператора"""
        match = re.search(self.opr_pattern, message)
        if match:
            operator = match.group(1).strip()
            # Очищаем от лишних символов
            operator = re.sub(r'\s+', ' ', operator)
            return operator
        return None
    
    def _extract_date(self, message: str) -> Optional[str]:
        """Извлекает дату полета"""
        match = re.search(self.date_pattern, message)
        if match:
            date_str = match.group(1)
            # Конвертируем YYMMDD в YYYY-MM-DD
            year = "20" + date_str[:2]
            month = date_str[2:4]
            day = date_str[4:6]
            return f"{year}-{month}-{day}"
        return None
    
    def _extract_departure_time(self, message: str) -> Optional[str]:
        """Извлекает время вылета"""
        match = re.search(self.time_pattern, message)
        if match:
            time_str = match.group(1)
            hours = time_str[:2]
            minutes = time_str[2:4]
            return f"{hours}:{minutes}"
        return None
    
    def _extract_sid(self, message: str) -> Optional[str]:
        """Извлекает System ID"""
        match = re.search(self.sid_pattern, message)
        return match.group(1) if match else None
    
    def _combine_date_time(self, date_str: str, time_str: str) -> datetime:
        """Объединяет дату и время в datetime объект"""
        try:
            date_part = datetime.strptime(date_str, "%Y-%m-%d").date()
            time_part = datetime.strptime(time_str, "%H:%M").time()
            return datetime.combine(date_part, time_part)
        except ValueError as e:
            logger.error(f"Error combining date {date_str} and time {time_str}: {e}")
            raise
    
    def calculate_duration(self, departure_dt: datetime, arrival_dt: datetime) -> int:
        """Вычисляет длительность полета в минутах"""
        if not departure_dt or not arrival_dt:
            return 0
        
        duration = arrival_dt - departure_dt
        
        # Если посадка на следующий день
        if duration.total_seconds() < 0:
            duration = arrival_dt + timedelta(days=1) - departure_dt
        
        return int(duration.total_seconds() / 60)
    
    def parse_flight_messages(self, shr_msg: str, dep_msg: str = None, arr_msg: str = None) -> Dict[str, Any]:
        """Парсит все сообщения полета и объединяет данные"""
        result = {}
        
        # Парсим SHR сообщение (основное)
        if shr_msg and isinstance(shr_msg, str) and shr_msg.strip():
            shr_data = self.parse_shr_message(shr_msg)
            result.update(shr_data)
        
        # Парсим DEP сообщение
        if dep_msg and isinstance(dep_msg, str) and dep_msg.strip():
            dep_data = self.parse_dep_message(dep_msg)
            # Обновляем время вылета если есть в DEP
            if 'departure_datetime' in dep_data:
                result['actual_departure_datetime'] = dep_data['departure_datetime']
        
        # Парсим ARR сообщение
        if arr_msg and isinstance(arr_msg, str) and arr_msg.strip():
            arr_data = self.parse_arr_message(arr_msg)
            if 'arrival_datetime' in arr_data:
                result['arrival_datetime'] = arr_data['arrival_datetime']
        
        # Вычисляем длительность полета
        if 'departure_datetime' in result and 'arrival_datetime' in result:
            result['duration_minutes'] = self.calculate_duration(
                result['departure_datetime'], 
                result['arrival_datetime']
            )
        
        # Сохраняем исходные сообщения
        result['raw_shr_message'] = shr_msg
        result['raw_dep_message'] = dep_msg
        result['raw_arr_message'] = arr_msg
        
        return result