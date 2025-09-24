"""
Модуль для унификации телефонных номеров
"""

import re
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)


def normalize_phone_number(phone: str) -> Optional[str]:
    """
    Унифицирует телефонный номер в формат 7XXXXXXXXXX (7 + 10 цифр)
    
    Поддерживаемые форматы:
    - +7XXXXXXXXXX
    - 8XXXXXXXXXX  
    - 7XXXXXXXXXX
    - +7 XXX XXX XX XX
    - 8 (XXX) XXX-XX-XX
    - и другие варианты с пробелами, скобками, дефисами
    
    Args:
        phone: Исходный телефонный номер
        
    Returns:
        Унифицированный номер в формате 7XXXXXXXXXX или None если номер некорректный
    """
    if not phone or not isinstance(phone, str):
        return None
    
    # Удаляем все символы кроме цифр
    digits_only = re.sub(r'[^\d]', '', phone.strip())
    
    # Проверяем различные форматы
    if len(digits_only) == 11:
        # Формат: 8XXXXXXXXXX или 7XXXXXXXXXX
        if digits_only.startswith('8'):
            return '7' + digits_only[1:]
        elif digits_only.startswith('7'):
            return digits_only
    elif len(digits_only) == 10:
        # Формат: XXXXXXXXXX (без кода страны)
        return '7' + digits_only
    elif len(digits_only) == 12 and digits_only.startswith('7'):
        # Возможно лишняя цифра в начале
        return digits_only[1:] if digits_only[1] == '7' else None
    
    # Если номер не соответствует ожидаемым форматам
    logger.debug(f"Could not normalize phone number: {phone} (digits: {digits_only})")
    return None


def normalize_phone_numbers(phone_list: List[str]) -> List[str]:
    """
    Унифицирует список телефонных номеров
    
    Args:
        phone_list: Список исходных номеров
        
    Returns:
        Список унифицированных номеров (без None значений)
    """
    if not phone_list:
        return []
    
    normalized = []
    for phone in phone_list:
        normalized_phone = normalize_phone_number(phone)
        if normalized_phone:
            normalized.append(normalized_phone)
    
    return normalized