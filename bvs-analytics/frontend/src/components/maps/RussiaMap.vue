<template>
  <div class="map-container">
    <l-map
        ref="map"
        :zoom="zoom"
        :center="center"
        :use-global-leaflet="false"
        @ready="onMapReady"
    >
<!--      url="	https://cartodb-basemaps-{s}.global.ssl.fastly.net/dark_all/{z}/{x}/{y}.png"-->
            <l-tile-layer
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            ></l-tile-layer>

        <l-geo-json
            v-for="region in regions"
            :key="region.properties?.cartodb_id || region.id"
            :geojson="region"
            :options-style="getStyle(region)"
            @click="onRegionClick(region)"
            @mouseover="onRegionHover(region)"
            @mouseout="onRegionHoverOut(region)"
        >
          <l-popup>
            <div class="p-3 min-w-[250px]">
              <h3 class="font-bold text-lg text-blue-800 mb-2">{{ getRegionName(region) }}</h3>
              <div v-if="getRegionStats(region)" class="space-y-2">
                <div class="flex justify-between">
                  <span class="text-gray-600">Полетов:</span>
                  <strong class="text-blue-600">{{ getRegionStats(region).flights.toLocaleString() }}</strong>
                </div>
                <div class="flex justify-between">
                  <span class="text-gray-600">Длительность:</span>
                  <strong class="text-green-600">{{ getRegionStats(region).duration }} ч</strong>
                </div>
                <div class="flex justify-between">
                  <span class="text-gray-600">Средняя длительность:</span>
                  <strong class="text-purple-600">{{ getRegionStats(region).avgDuration }} мин</strong>
                </div>
                <div class="flex justify-between">
                    <a class="px-6 py-2 bg-green-600 text-white text-decoration-none rounded w-full text-center hover:-translate-y-1" style="color: white" :href="'/region/'+region.properties.cartodb_id" target="_blank">
                      Посмотреть подробнее
                    </a>
                </div>
              </div>
              <!--            <div v-else class="text-gray-500 text-sm py-2">-->
              <!--              <div class="flex justify-between mb-1">-->
              <!--                <span>Статус:</span>-->
              <!--                <span class="text-yellow-600">Нет данных</span>-->
              <!--              </div>-->
              <!--              <div class="text-xs">Информация появится в ближайшее время</div>-->
              <!--            </div>-->
            </div>
          </l-popup>
        </l-geo-json>


      <!-- Маршруты полетов -->
      <!--      <l-geo-json-->
      <!--          v-if="showRoutes && routesData.features.length"-->
      <!--          :geojson="routesData"-->
      <!--          :options-style="getRouteStyle"-->
      <!--      ></l-geo-json>-->

<!--       Точки полетов с индивидуальными попапами-->
<!--      <template v-if="showPoints && selectedRegion && filteredPoints">-->
<!--        <l-geo-json-->
<!--            v-for="data in filteredPoints.features"-->
<!--            :key="`point-${data.properties.sid}`"-->
<!--            :geojson="data"-->
<!--            :options-style="getPointStyle"-->
<!--            :options="geoJsonOptions"-->
<!--        >-->
<!--        </l-geo-json>-->
<!--      </template>-->

      <!-- Зоны круговых полетов с индивидуальными попапами -->
      <!--      <l-geo-json-->
      <!--          v-if="showZones && zonesData.features.length"-->
      <!--          :geojson="zonesData"-->
      <!--          :options-style="getZoneStyle"-->
      <!--          :options="geoJsonOptions"-->
      <!--      >-->
      <!--        <l-popup v-for="feature in zonesData.features" :key="`zone-popup-${feature.properties.flightId}`">-->
      <!--          <div class="flight-popup p-3 max-w-sm">-->
      <!--            <FlightsPopup :flight="getFlightByFeature(feature)" />-->
      <!--          </div>-->
      <!--        </l-popup>-->
      <!--      </l-geo-json>-->
    </l-map>

    <!-- Легенда карты -->
    <!--    <div class="absolute bottom-4 left-4 bg-white p-4 rounded-lg shadow-lg z-1000 border">-->
    <!--      <h4 class="font-bold mb-3 text-gray-800">Активность полетов БПЛА</h4>-->
    <!--      <div class="space-y-2">-->
    <!--        <div class="flex items-center">-->
    <!--          <div class="w-4 h-4 bg-green-600 mr-3 border border-gray-300"></div>-->
    <!--          <span class="text-sm">Высокая (700+)</span>-->
    <!--        </div>-->
    <!--        <div class="flex items-center">-->
    <!--          <div class="w-4 h-4 bg-green-400 mr-3 border border-gray-300"></div>-->
    <!--          <span class="text-sm">Средняя (300-700)</span>-->
    <!--        </div>-->
    <!--        <div class="flex items-center">-->
    <!--          <div class="w-4 h-4 bg-green-200 mr-3 border border-gray-300"></div>-->
    <!--          <span class="text-sm">Низкая (1-300)</span>-->
    <!--        </div>-->
    <!--        <div class="flex items-center">-->
    <!--          <div class="w-4 h-4 bg-gray-200 mr-3 border border-gray-300"></div>-->
    <!--          <span class="text-sm">Нет данных</span>-->
    <!--        </div>-->
    <!--      </div>-->
    <!--      <div class="mt-3 pt-3 border-t">-->
    <!--        <div class="text-xs text-gray-500">Данные за: {{ currentDate }}</div>-->
    <!--      </div>-->
    <!--    </div>-->

    <!-- Информация о выбранном регионе -->
    <!--    <div v-if="selectedRegion" class="absolute top-4 right-4 bg-white p-4 rounded-lg shadow-lg z-1000 border max-w-sm">-->
    <!--      <h4 class="font-bold text-lg mb-2 text-blue-800">{{ selectedRegion.name }}</h4>-->
    <!--      <div class="space-y-1 text-sm">-->
    <!--        <div class="flex justify-between">-->
    <!--          <span>Рейтинг активности:</span>-->
    <!--          <strong>#{{ getRegionRank(selectedRegion.id) }}</strong>-->
    <!--        </div>-->
    <!--        <div class="flex justify-between">-->
    <!--          <span>Всего полетов:</span>-->
    <!--          <strong>{{ selectedRegion.flights.toLocaleString() }}</strong>-->
    <!--        </div>-->
    <!--        <div class="flex justify-between">-->
    <!--          <span>Накопленная длительность:</span>-->
    <!--          <strong>{{ selectedRegion.duration }} ч</strong>-->
    <!--        </div>-->
    <!--      </div>-->
    <!--      <button-->
    <!--          @click="selectedRegion = null"-->
    <!--          class="mt-3 w-full bg-gray-100 hover:bg-gray-200 text-gray-800 py-1 rounded text-xs"-->
    <!--      >-->
    <!--        Закрыть-->
    <!--      </button>-->
    <!--    </div>-->
  </div>
</template>

<script setup>
import {ref, computed, onMounted, watch, createApp} from 'vue'
import {LMap, LTileLayer, LGeoJson, LPopup} from '@vue-leaflet/vue-leaflet'
import FlightsPopup from "@/components/FlightsPopup.vue";
import 'leaflet/dist/leaflet.css'

// Исправление для иконок Leaflet
import L from 'leaflet'

delete L.Icon.Default.prototype._getIconUrl

L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://birthday.imdibil.ru/map-marker.svg',
  iconUrl: 'https://birthday.imdibil.ru/map-marker.svg',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
})

const props = defineProps({
  regionStats: {
    type: Object,
    default: () => ({})
  },
  flightsData: {
    type: Object,
    default: () => ({flights: []})
  },
  regions: {
    type: Object,
    default: () => ({flights: []})
  }
})

const emit = defineEmits(['region-click'])

const map = ref(null)
const zoom = ref(4)
const center = ref([61.5240, 105.3188])
const regions = ref([])
const hoveredRegion = ref(null)
const selectedRegion = ref(null)

const selectedFlight = ref(null)

const popup = ref(null)

const showRegions = ref(true)
const showPoints = ref(true)
const showRoutes = ref(true)
const showZones = ref(true)

const currentDate = new Date().toLocaleDateString('ru-RU', {
  year: 'numeric',
  month: 'long'
})

// Используем переданную статистику или нашу симуляцию
const regionStats = computed(() =>
    Object.keys(props.regionStats).length > 0 ? props.regionStats : {}
)

const getRegionName = (region) => {
  return region.properties?.name || 'Неизвестный регион'
}

const getRegionId = (region) => {
  // Пытаемся найти ID региона разными способами
  return region.properties?.cartodb_id ||
      region.properties?.id ||
      region.id ||
      Object.keys(regionStats.value).find(key =>
          regionStats.value[key].name === getRegionName(region)
      )
}

const getRegionStats = (region) => {
  const regionId = getRegionId(region)
  return regionStats.value[regionId] || null
}

const getRegionRank = (regionId) => {
  const sorted = Object.entries(regionStats.value)
      .sort(([, a], [, b]) => b.flights - a.flights)
      .map(([id]) => id)

  return sorted.indexOf(regionId) + 1 || '-'
}

const getStyle = (region) => {
  const stats = getRegionStats(region)
  const flightCount = stats ? stats.flights : 0

  let fillColor = 'rgba(229,231,235,0.22)' // Серый - нет данных

  if (flightCount > 0) {
    if (flightCount < 100) fillColor = 'rgba(211,252,225,0.82)'
    else if (flightCount < 300) fillColor = 'rgba(165,224,187,0.68)'
    else if (flightCount < 800) fillColor = 'rgba(127,213,158,0.75)'
    else if (flightCount < 2000) fillColor = 'rgba(82,187,121,0.7)'
    else fillColor = 'rgba(16,128,56,0.73)'
  }

  const isHovered = hoveredRegion.value === region
  const isSelected = selectedRegion.value && getRegionId(region) === selectedRegion.value.id

  return {
    fillColor: isSelected ? 'rgba(255,0,0,0.65)' : fillColor,
    weight: isHovered || isSelected ? 4 : 2,
    opacity: 1,
    color: isSelected ? 'rgba(255,0,0,0.76)' : (isHovered ? 'rgba(127,255,0,0.62)' : 'rgba(55,65,81,0.55)'),
    dashArray: isSelected ? '5,5' : '3',
    fillOpacity: isHovered || isSelected ? 0.9 : 0.7
  }
}

const onMapReady = () => {
  console.log('Карта России готова')
  document.querySelector('.leaflet-control-attribution').remove()
}

const onRegionClick = (region) => {
  const stats = getRegionStats(region)
  // console.log(region, stats)
  if (stats) {
    selectedRegion.value = {...stats, id: getRegionId(region)}
  }

  console.log('here')
  emit('region-click', region)

  if (!selectedRegion.value) {
    console.log("Error!!!!")
    return [];
  }
  console.log('HERE!')

  const regionId = selectedRegion.value.id;
  console.log(regionId)
  // const response = fetch('https://imdibil.ru/api/flights/' + regionId)
  //     .then(response => response.json())
  //     .then(data => {
  //       filteredPoints.value = createPointsGeoJSON(data.flights)
  //       flights.value = data.flights
  //       console.log(filteredPoints.value)
  //     });

}

const onRegionHover = (region) => {
  hoveredRegion.value = region
}

const onRegionHoverOut = () => {
  hoveredRegion.value = null
}

const onPointClick = (event) => {
  const feature = event.layer.feature
  const flight = processedFlights.value.find(f => f.sid === feature.properties.flightId)

  if (flight) {
    selectedFlight.value = flight
    // Показываем попап на карте
    const latlng = event.latlng
    popup.value.setLatLng(latlng)
  }
}


// Функция для получения полета по фиче


// Стили для разных элементов
const getRegionStyle = (region) => ({
  fillColor: '#e5e7eb',
  weight: 1,
  opacity: 0.7,
  color: '#374151',
  fillOpacity: 0.3
})

const getPointStyle = (feature) => ({
  // radius: 1,
  // fillColor: feature.properties.type === 'departure' ? '#3b82f6' : '#10b981',
  // color: '#AAA',
  // weight: 2,
  // opacity: 1,
  // fillOpacity: 0.1,
  // icon: "https://birthday.imdibil.ru/map-marker.svg"
})

const getRouteStyle = () => ({
  color: '#ef4444',
  weight: 2,
  opacity: 0.7,
  dashArray: '5,5'
})

const getZoneStyle = () => ({
  radius: 8,
  fillColor: '#8b5cf6',
  color: '#fff',
  weight: 2,
  opacity: 1,
  fillOpacity: 0.8
})

// Обработчики событий


// Загрузка границ регионов
const loadRegions = async () => {
  // console.log(props.regions)
  regions.value = props.regions
}

const filteredPoints = ref(null);
const flights = ref(null);


onMounted(() => {

  loadRegions()
})

// Автоматическое изменение центра карты при получении данных
// watch(processedFlights, (newFlights) => {
//   if (newFlights.length > 0 && map.value && map.value.leafletObject) {
//     const points = newFlights.flatMap(flight => [
//       ...(flight.dep ? [[flight.dep.lon, flight.dep.lat]] : []),
//       ...(flight.arr ? [[flight.arr.lon, flight.arr.lat]] : [])
//     ]);
//
//     if (points.length > 0) {
//       const lats = points.map(p => p[1]);
//       const lons = points.map(p => p[0]);
//       const centerLat = (Math.min(...lats) + Math.max(...lats)) / 2;
//       const centerLon = (Math.min(...lons) + Math.max(...lons)) / 2;
//
//       map.value.leafletObject.setView([centerLat, centerLon], 6);
//     }
//   }
// }, { immediate: true });
const geoJsonOptions = {
  onEachFeature: (feature, layer) => {
    layer.bindPopup(() => {
      const container = document.createElement("div");
      const app = createApp(FlightsPopup, {flight: getFlightByFeature(feature)});
      app.mount(container);
      return container;
    });
  }
};


const getFlightByFeature = (feature) => {
  return flights.value.find(f => f.sid === feature.properties.flightId)
}
</script>

<style scoped>
.map-container {
  height: 600px;
  width: 100%;
  position: relative;
}

:deep(.leaflet-popup) {
  z-index: 1000;
}

:deep(.leaflet-interactive) {
  cursor: pointer;
  transition: all 0.2s ease;
}

:deep(.leaflet-popup-content) {
  margin: 12px;
  font-family: system-ui, -apple-system, sans-serif;
}


</style>