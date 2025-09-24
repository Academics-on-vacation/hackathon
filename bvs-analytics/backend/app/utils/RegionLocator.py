import json
from pathlib import Path
from shapely.geometry import shape, Point
from shapely.strtree import STRtree

class RegionLocator:
    def __init__(self, geojson_path: str):
        self.geojson_path = Path(geojson_path)
        self._load_regions()

    def _load_regions(self):
        with open(self.geojson_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.geoms = []
        self.regions = []

        for feature in data["features"]:
            geom = shape(feature["geometry"])
            props = feature.get("properties", {})
            self.geoms.append(geom)
            self.regions.append(props)

        self.tree = STRtree(self.geoms)

    def get_region(self, lat, lon):
        """
        Возвращает информацию о регионе по координатам, включая cartodb_id и name_latin
        """
        point = Point(lon, lat)
        candidate_idxs = self.tree.query(point)
        for idx in candidate_idxs:
            geom = self.geoms[idx]
            if geom.contains(point):
                region_info = self.regions[idx].copy()
                # Убеждаемся, что cartodb_id и name_latin присутствуют в результате
                result = {
                    'name': region_info.get('name'),
                    'cartodb_id': region_info.get('cartodb_id'),
                    'name_latin': region_info.get('name_latin'),
                    'created_at': region_info.get('created_at'),
                    'updated_at': region_info.get('updated_at')
                }
                # Добавляем все остальные поля из исходных данных
                for key, value in region_info.items():
                    if key not in result:
                        result[key] = value
                return result
        return None


if __name__ == "__main__":
    # Используем правильный путь к файлу russia.geojson
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    geojson_path = os.path.join(current_dir, "..", "..", "..", "data", "russia.geojson")
    locator = RegionLocator(geojson_path)

    # Москва
    lat, lon = 55.7558, 37.6176
    region = locator.get_region(lat, lon)
    print("Москва →", region)
    if region:
        print(f"  cartodb_id: {region.get('cartodb_id')}")
        print(f"  name_latin: {region.get('name_latin')}")

    # Сочи
    lat, lon = 43.6028, 39.7342
    region = locator.get_region(lat, lon)
    print("Сочи →", region)
    if region:
        print(f"  cartodb_id: {region.get('cartodb_id')}")
        print(f"  name_latin: {region.get('name_latin')}")
