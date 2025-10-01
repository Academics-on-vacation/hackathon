import json
import re
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple, Optional
import pandas as pd


class FlightParser:
    """Парсер данных о полетах из Excel"""

    RU2EN = str.maketrans({
        "С": "N", "Ю": "S", "В": "E", "З": "W",
        "с": "N", "ю": "S", "в": "E", "з": "W"
    })

    def __init__(self, aerodromes_path: str = 'aerodroms.json', zones_path: str = 'ltsa.json', region_locator=None):
        self.aerodromes = self._load_aerodromes(aerodromes_path)
        self.zones = self._load_zones(zones_path)
        self.region_locator = region_locator

    def _load_aerodromes(self, path: str) -> Dict[str, Dict[str, Any]]:
        """Загрузка справочника аэродромов"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Warning: Aerodromes file not found: {path}")
            return {}

    def _load_zones(self, path: str) -> List[Dict[str, Any]]:
        """Загрузка справочника зон"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Warning: Zones file not found: {path}")
            return []

    def get_flight_region(self, flight: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Определение региона для полёта

        Приоритеты поиска:
        1. Координаты аэропорта вылета
        2. Координаты аэропорта прилёта
        3. Координаты зоны (полигон или центр круга)
        4. Поиск в окрестностях аэропортов

        Args:
            flight: словарь с данными полета

        Returns:
            Словарь с информацией о регионе или None
        """
        if self.region_locator is None:
            return None

        region = None

        # Приоритет 1: Координаты аэропортов
        dep_lat, dep_lon = flight["dep"]["lat"], flight["dep"]["lon"]
        arr_lat, arr_lon = flight["arr"]["lat"], flight["arr"]["lon"]

        if dep_lat and dep_lon:
            region = self.region_locator.get_region(dep_lat, dep_lon)

        if region is None and arr_lat and arr_lon:
            region = self.region_locator.get_region(arr_lat, arr_lon)

        # Приоритет 2: Координаты зоны
        if region is None:
            zone = flight.get('zone', {})
            zone_type = zone.get('type')
            zone_data = zone.get('data')

            if zone_type == 'polygon' and zone_data:
                # Проверяем все координаты полигона
                for coord in zone_data.get('coordinates', []):
                    if coord.get('lat') is not None and coord.get('lon') is not None:
                        region = self.region_locator.get_region(
                            coord['lat'], coord['lon']
                        )
                        if region is not None:
                            break

            elif zone_type == 'circle' and zone_data:
                # Проверяем центр круговой зоны
                center = zone_data.get('center', {})
                if center.get('lat') is not None and center.get('lon') is not None:
                    region = self.region_locator.get_region(
                        center['lat'], center['lon']
                    )

            elif zone_type == 'named' and zone_data:
                # Для именованных зон пытаемся найти координаты
                zones = zone_data.get('zones', [])
                for z in zones:
                    if z.get('type') == 'circle':
                        center = z.get('center', [])
                        if len(center) == 2:
                            region = self.region_locator.get_region(center[0], center[1])
                            if region:
                                break
                    elif z.get('type') == 'polygon':
                        coords = z.get('coordinates', [[]])
                        if coords and len(coords[0]) > 0:
                            first_coord = coords[0]
                            if len(first_coord) == 2:
                                region = self.region_locator.get_region(
                                    first_coord[0], first_coord[1]
                                )
                                if region:
                                    break

        # Приоритет 3: Поиск в окрестностях аэропортов
        if region is None:
            region = self._search_region_in_vicinity(dep_lat, dep_lon, arr_lat, arr_lon)

        return region

    def _search_region_in_vicinity(self, dep_lat: Optional[float],
                                   dep_lon: Optional[float],
                                   arr_lat: Optional[float],
                                   arr_lon: Optional[float]) -> Optional[Dict[str, Any]]:
        """
        Поиск региона в окрестностях координат аэропортов

        Args:
            dep_lat, dep_lon: координаты вылета
            arr_lat, arr_lon: координаты прилёта

        Returns:
            Словарь с информацией о регионе или None
        """
        if self.region_locator is None:
            return None

        # Определяем базовые координаты для поиска
        lat, lon = None, None
        if dep_lat and dep_lon:
            lat, lon = dep_lat, dep_lon
        elif arr_lat and arr_lon:
            lat, lon = arr_lat, arr_lon

        if lat is None or lon is None:
            return None

        # Направления поиска (8 направлений)
        directions = [
            (1, 1), (1, -1), (-1, 1), (-1, -1),
            (1, 0), (-1, 0), (0, 1), (0, -1)
        ]

        # Поиск с постепенным увеличением радиуса
        for delta in [0.01, 0.05, 0.1, 0.15, 0.2, 0.25, 0.5, 1, 2, 3, 5]:
            for dir_lat, dir_lon in directions:
                check_lat = lat + dir_lat * delta
                check_lon = lon + dir_lon * delta

                region = self.region_locator.get_region(check_lat, check_lon)
                if region is not None:
                    return region

        return None

    @staticmethod
    def parse_latlon(compact: str) -> Tuple[Optional[float], Optional[float]]:
        if not isinstance(compact, str):
            return (None, None)

        s = compact.strip().upper().translate(FlightParser.RU2EN)

        # Строгое регулярное выражение для координат
        m = re.match(r'^(\d{4}|\d{6})([NS])(\d{5}|\d{7})([EW])$', s)
        if not m:
            return (None, None)

        lat_str, ns, lon_str, ew = m.groups()

        try:
            # Парсинг широты
            if len(lat_str) == 4:  # DDMM
                dd, mm, ss = int(lat_str[:2]), int(lat_str[2:4]), 0
            else:  # DDMMSS
                dd, mm, ss = int(lat_str[:2]), int(lat_str[2:4]), int(lat_str[4:6])

            lat = dd + mm / 60 + ss / 3600
            if ns == "S":
                lat = -lat

            # Парсинг долготы
            if len(lon_str) == 5:  # DDDMM
                ddd, mm, ss = int(lon_str[:3]), int(lon_str[3:5]), 0
            else:  # DDDMMSS
                ddd, mm, ss = int(lon_str[:3]), int(lon_str[3:5]), int(lon_str[5:7])

            lon = ddd + mm / 60 + ss / 3600
            if ew == "W":
                lon = -lon

            # Проверка валидности координат
            if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                return (None, None)

            return (round(lat, 6), round(lon, 6))

        except (ValueError, IndexError):
            return (None, None)

    @staticmethod
    def parse_date_yymmdd(s: str) -> Optional[datetime]:
        if not s:
            return None
        s = str(s).strip()
        if not re.fullmatch(r"\d{6}", s):
            return None
        yy, mm, dd = int(s[:2]), int(s[2:4]), int(s[4:6])
        try:
            return datetime(2000 + yy, mm, dd).date()
        except ValueError:
            return None

    @staticmethod
    def parse_time_hhmm(s: str) -> Optional[Tuple[int, int]]:
        """Парсинг времени из формата HHMM"""
        if s is None:
            return None
        s = f"{int(s):04d}" if isinstance(s, int) else str(s).strip()
        if not re.fullmatch(r"\d{4}", s):
            return None
        hh, mm = int(s[:2]), int(s[2:4])
        if hh > 23 or mm > 59:
            return None
        return (hh, mm)

    @staticmethod
    def parse_block(text: str) -> Dict[str, Any]:
        """Парсинг блока данных из текста"""
        from collections import defaultdict
        res = defaultdict(list)

        if not isinstance(text, str) or not text.strip():
            return {}

        t = text.strip()
        if t.startswith("(") and t.endswith(")"):
            t = t[1:-1]

        for raw_line in t.splitlines():
            line = raw_line.strip()
            if not line:
                continue

            # Формат с дефисом: -KEY VALUE
            if line.startswith("-"):
                m = re.match(r"^-([A-Z0-9]+)\s*(.*)$", line, flags=re.I)
                if m:
                    key, rest = m.group(1).upper(), m.group(2).strip()
                    res[key].append(rest)
                    continue

            # Формат KEY/VALUE
            for token in re.split(r"\s+", line):
                if "/" in token:
                    k, v = token.split("/", 1)
                    res[k.upper()].append(v.strip().rstrip("/"))

        return {k: (v[0] if len(v) == 1 else v) for k, v in res.items()}

    def lookup_aerodrome(self, code: str) -> Optional[Dict[str, Any]]:
        if not code or code == "ZZZZ":
            return None

        code = code.strip().upper()
        aerodrome = self.aerodromes.get(code)

        if aerodrome:
            return {
                'code': code,
                'name': aerodrome.get('title'),
                'lat': aerodrome['coords'][0],
                'lon': aerodrome['coords'][1]
            }
        return None

    def extract_coordinates_from_text(self, text: str) -> Optional[Tuple[float, float]]:
        """Извлечение координат из текста"""
        if not text:
            return None

        # Поиск координат в формате DDMM(SS)N/SDDDMM(SS)E/W
        coord_match = re.search(
            r'((\d{4}|\d{6})([NSСЮсю])(\d{5}|\d{7})([EWВЗвз]))',
            text
        )

        if coord_match:
            lat, lon = self.parse_latlon(coord_match.group(1))
            if lat is not None and lon is not None:
                return (lat, lon)

        return None

    def parse_operator(self, shr_text: str) -> str|None:
        oper = re.search(r'OPR\/([A-Z|a-z|A-Я|а-я|0-9|\n|\ |+|-]+)(\ \w+\/)', shr_text)
        if oper:
            return oper.group(1).replace('\n', ' ')
        else:
            return None

    def parse_zone(self, shr_text: str) -> Dict[str, Any]:
        if not isinstance(shr_text, str):
            return {'type': 'unknown', 'data': None}

        # 1. Круговая зона (R радиус)
        round_zone = re.search(
            r'/ZONA (ZONA )?(R\d+,?\d+)\s?((\d{4}|\d{6})([NS])(\d{5}|\d{7})([EW]))/',
            shr_text
        )
        if round_zone and round_zone.group(3):
            zlat, zlon = self.parse_latlon(round_zone.group(3))
            radius = float(round_zone.group(2).replace('R', '').replace(',', '.'))
            return {
                'type': 'circle',
                'data': {
                    'center': {'lat': zlat, 'lon': zlon},
                    'radius_nm': radius
                }
            }

        # 2. Зона с координатами (многоугольник)
        polygon_zone = re.search(
            r'ZONA\s+((?:\d{4,6}[NS]\d{5,7}[EW]\s*)+)',
            shr_text,
            re.IGNORECASE | re.MULTILINE
        )
        if polygon_zone:
            coords_text = polygon_zone.group(1)
            coords_text = re.sub(r'\s+', ' ', coords_text).strip()

            if ' ' in coords_text:
                coord_strings = coords_text.split(' ')
            else:
                coord_strings = re.findall(r'\d{4,6}[NS]\d{5,7}[EW]', coords_text)

            coords = []
            for z in coord_strings:
                zlat, zlon = self.parse_latlon(z)
                if zlat is not None and zlon is not None:
                    coords.append({'lat': zlat, 'lon': zlon})

            if coords:
                return {
                    'type': 'polygon',
                    'data': {
                        'coordinates': coords
                    }
                }

        # 3. Кодовое обозначение зоны
        name_zone = re.search(r'/ZONA\s+([A-Z]+\s*\d+[A-Z]*)\s*/', shr_text, re.IGNORECASE)
        if name_zone:
            zone_name = name_zone.group(1).strip()
            zone_data = next((z for z in self.zones if z.get('rvmname') == zone_name), None)

            if zone_data:
                return {
                    'type': 'named',
                    'data': {
                        'name': zone_name,
                        'zones': zone_data.get('zones', [])
                    }
                }
            return {
                'type': 'named',
                'data': {
                    'name': zone_name
                }
            }

        # 4. Ничего не найдено
        return {'type': 'unknown', 'data': None}

    def parse_row(self, center_name: str, shr_text: str,
                  dep_text: str, arr_text: str) -> Dict[str, Any]:
        """Парсинг одной строки из Excel и определение региона"""
        dep = self.parse_block(dep_text)
        arr = self.parse_block(arr_text)
        shr = self.parse_block(shr_text)

        # Базовая информация
        sid = dep.get("SID") or arr.get("SID") or shr.get("SID")
        uav_type = shr.get("TYP") or dep.get("TYP") or arr.get("TYP")
        operator = self.parse_operator(shr_text)
        if operator is None:
            operator = shr.get("OPR")
        # Даты и времена
        add, atd = dep.get("ADD"), dep.get("ATD")
        ada, ata = arr.get("ADA"), arr.get("ATA")
        dep_date = self.parse_date_yymmdd(add)
        arr_date = self.parse_date_yymmdd(ada)
        dep_hm = self.parse_time_hhmm(atd)
        arr_hm = self.parse_time_hhmm(ata)

        # Временные метки
        start_ts = end_ts = None
        if dep_date and dep_hm:
            start_ts = datetime(dep_date.year, dep_date.month, dep_date.day,
                                dep_hm[0], dep_hm[1])
        if arr_date and arr_hm:
            end_ts = datetime(arr_date.year, arr_date.month, arr_date.day,
                              arr_hm[0], arr_hm[1])
            if start_ts and end_ts and end_ts < start_ts:
                end_ts += timedelta(days=1)

        # Обработка аэродромов и координат
        adepz = dep.get("ADEPZ")
        adarrz = arr.get("ADARRZ")

        # Извлечение координат из полей аэродромов
        if adarrz:
            coord_match = re.search(
                r'((\d{4}|\d{6})([NSСЮсю])(\d{5}|\d{7})([EWВЗвз]))',
                adarrz
            )
            if coord_match:
                adarrz = coord_match.group(1)
            else:
                adarrz = None

        if adepz:
            coord_match = re.search(
                r'((\d{4}|\d{6})([NSСЮсю])(\d{5}|\d{7})([EWВЗвз]))',
                adepz
            )
            if coord_match:
                adepz = coord_match.group(1)
            else:
                adepz = None

        # Если нет координат, ищем в тексте SHR
        if not adepz and not adarrz:
            dep_match = re.search(
                r'DEP\/((\d{4}|\d{6})([NS])(\d{5}|\d{7})([EW]))',
                shr_text,
                re.MULTILINE
            )
            if dep_match:
                adepz = dep_match.group(1)

            arr_match = re.search(
                r'DEST\/((\d{4}|\d{6})([NS])(\d{5}|\d{7})([EW]))',
                shr_text,
                re.MULTILINE
            )
            if arr_match:
                adarrz = arr_match.group(1)

            # Произвольный взлёт/посадка
            if not adepz or not adarrz:
                proizvol = re.search(
                    r'ВЗЛЕТ И ПОСАДКА\s+((\d{4}|\d{6})([NS])(\d{5}|\d{7})([EW]))',
                    shr_text,
                    re.MULTILINE
                )
                if proizvol:
                    adarrz = adepz = proizvol.group(1)

        # Парсинг зоны
        zona = self.parse_zone(shr_text)

        # Если всё ещё нет координат, берём из зоны
        if not adepz or not adarrz:
            if zona['type'] == 'circle' and zona['data']:
                center = zona['data']['center']
                if not adepz:
                    adepz = f"{abs(center['lat']):06.2f}{'N' if center['lat'] >= 0 else 'S'}" \
                            f"{abs(center['lon']):07.2f}{'E' if center['lon'] >= 0 else 'W'}"
                if not adarrz:
                    adarrz = adepz
            elif zona['type'] == 'polygon' and zona['data']:
                coords = zona['data']['coordinates']
                if coords and not adepz:
                    first_coord = coords[0]
                    adepz = f"{abs(first_coord['lat']):06.2f}{'N' if first_coord['lat'] >= 0 else 'S'}" \
                            f"{abs(first_coord['lon']):07.2f}{'E' if first_coord['lon'] >= 0 else 'W'}"
                if not adarrz:
                    adarrz = adepz

        # Обработка вылета
        adep = dep.get("ADEP")
        adarr = arr.get("ADARR")
        dep_aerodrome = self.lookup_aerodrome(adep) if adep and adep != "ZZZZ" else None
        if dep_aerodrome:
            dep_lat, dep_lon = dep_aerodrome['lat'], dep_aerodrome['lon']
            dep_code, dep_name = dep_aerodrome['code'], dep_aerodrome['name']
        else:
            dep_lat, dep_lon = self.parse_latlon(adepz) if adepz else (None, None)
            dep_code, dep_name = None, None

        # Обработка прилёта
        arr_aerodrome = self.lookup_aerodrome(adarr) if adarr and adarr != "ZZZZ" else None
        if arr_aerodrome:
            arr_lat, arr_lon = arr_aerodrome['lat'], arr_aerodrome['lon']
            arr_code, arr_name = arr_aerodrome['code'], arr_aerodrome['name']
        else:
            arr_lat, arr_lon = self.parse_latlon(adarrz) if adarrz else (None, None)
            arr_code, arr_name = None, None

        # Создание объекта полета
        flight_data = {
            "sid": sid,
            "center_name": center_name or None,
            "uav_type": uav_type,
            "operator": operator,
            "zone": zona,
            "dep": {
                "date": dep_date.isoformat() if dep_date else None,
                "time_hhmm": f"{dep_hm[0]:02d}{dep_hm[1]:02d}" if dep_hm else None,
                "lat": dep_lat,
                "lon": dep_lon,
                "aerodrome_code": dep_code,
                "aerodrome_name": dep_name,
            },
            "arr": {
                "date": arr_date.isoformat() if arr_date else None,
                "time_hhmm": f"{arr_hm[0]:02d}{arr_hm[1]:02d}" if arr_hm else None,
                "lat": arr_lat,
                "lon": arr_lon,
                "aerodrome_code": arr_code,
                "aerodrome_name": arr_name,
            },
            "start_ts": start_ts.isoformat() if start_ts else None,
            "end_ts": end_ts.isoformat() if end_ts else None,
            "duration_min": int((end_ts - start_ts).total_seconds() // 60)
            if start_ts and end_ts else None,
        }

        # Определение региона
        region = self.get_flight_region(flight_data)
        if region is not None:
            flight_data["region_id"] = region['cartodb_id']
            flight_data["region_name"] = region['region']
        else:
            flight_data["region_id"] = None
            flight_data["region_name"] = "Не определено"

        return flight_data