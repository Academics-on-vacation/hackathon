<template>
  <!-- Панель управления -->
  <div class="section-header">
    <h2>Маршрут полета</h2>
    <div class="section-actions">
      <button @click="toggleAnimation" class="control-btn tab-btn" :class="{ active: isAnimating }">
        {{ isAnimating ? 'Пауза' : 'Запуск' }}
      </button>
      <button @click="resetAnimation" class="control-btn tab-btn">Сброс</button>
      <button @click="fitToBounds" class="control-btn tab-btn">Обзор маршрута</button>
    </div>
    <div class="section-actions">
      <button class="tab-btn" :class="{ active: mapStyle === 'osm' }" @click="mapStyle = 'osm'; changeMapStyle()">
        Маршрут
      </button>
      <button class="tab-btn" :class="{ active: mapStyle === 'terrain' }"
              @click="mapStyle = 'terrain'; changeMapStyle()">
        Рельеф
      </button>
      <button class="tab-btn" :class="{ active: mapStyle === 'satellite' }"
              @click="mapStyle = 'satellite'; changeMapStyle()">
        Спутник
      </button>
    </div>
  </div>


  <!-- Контейнер для карты -->
  <div ref="mapContainer" class="map-container"></div>

  <!-- Панель прогресса -->
  <div class="progress-panel">
    <div class="progress-info">
      <span>Прогресс: {{ animationProgress.toFixed(1) }}%</span>
      <span>Время: {{ formatTime(animationProgress * flight.duration_min / 100) }}</span>
    </div>
    <div class="progress-bar">
      <div
          class="progress-fill"
          :style="{ width: animationProgress + '%' }"
      ></div>
    </div>

    <div class="coordinates-display">
      <div class="coordinate">
        <div class="point-indicator departure"></div>
        <div>
          <strong>A: Вылет</strong>
          <div>{{ flight.dep.lat.toFixed(6) }}, {{ flight.dep.lon.toFixed(6) }}</div>
          <small>{{ formatDateTime(flight.dep.date, flight.dep.time_hhmm) }}</small>
        </div>
      </div>

      <div class="coordinate" v-if="currentPosition">
        <div class="point-indicator current"></div>
        <div>
          <strong>Текущее положение</strong>
          <div>{{ currentPosition.lat.toFixed(6) }}, {{ currentPosition.lng.toFixed(6) }}</div>
        </div>
      </div>

      <div class="coordinate">
        <div class="point-indicator arrival"></div>
        <div>
          <strong>B: Прибытие</strong>
          <div>{{ flight.arr.lat.toFixed(6) }}, {{ flight.arr.lon.toFixed(6) }}</div>
          <small>{{ formatDateTime(flight.arr.date, flight.arr.time_hhmm) }}</small>
        </div>
      </div>
    </div>
  </div>

  <!-- Легенда -->
  <div class="map-legend">
    <div class="legend-item">
      <div class="legend-icon departure"></div>
      <span>Точка вылета (A)</span>
    </div>
    <div class="legend-item">
      <div class="legend-icon arrival"></div>
      <span>Точка прибытия (B)</span>
    </div>
    <div class="legend-item">
      <div class="legend-icon route"></div>
      <span>Маршрут полета</span>
    </div>
    <div class="legend-item" v-if="isAnimating">
      <div class="legend-icon drone"></div>
      <span>Текущее положение</span>
    </div>
  </div>


</template>

<script setup>
import {ref, onMounted, onUnmounted, computed, watch} from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

// Fix for default markers in Leaflet
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
})

const props = defineProps({
  flight: {
    type: Object,
    required: true
  },
  zone: {
    type: Object,
    required: false
  }
})

// Состояние карты
const mapContainer = ref(null)
let map = null
let routeLayer = null
let departureMarker = null
let arrivalMarker = null
let droneMarker = null
let animationInterval = null

// Данные анимации
const isAnimating = ref(false)
const animationProgress = ref(0)
const mapStyle = ref('osm')
const currentPosition = ref(null)

// Тайлы для разных стилей карты
const tileLayers = {
  osm: L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors',
    maxZoom: 19
  }),

  satellite: L.tileLayer('https://{s}.google.com/vt/lyrs=s&x={x}&y={y}&z={z}', {
    attribution: '© Google Satellite',
    subdomains: ['mt0', 'mt1', 'mt2', 'mt3'],
    maxZoom: 20
  }),

  terrain: L.tileLayer('https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenTopoMap',
    maxZoom: 17
  })
}

// Расчетные параметры
const calculatedDistance = computed(() => {
  return calculateDistance(
      props.flight.dep.lat, props.flight.dep.lon,
      props.flight.arr.lat, props.flight.arr.lon
  )
})

const calculatedSpeed = computed(() => {
  const hours = props.flight.duration_min / 60
  return hours > 0 ? Math.round(calculatedDistance.value / hours) : 0
})

// Инициализация карты
const initMap = () => {
  if (!mapContainer.value) return

  // Создание карты
  map = L.map(mapContainer.value).setView(
      [props.flight.dep.lat, props.flight.dep.lon],
      10
  )

  // Добавление базового слоя
  tileLayers[mapStyle.value].addTo(map)

  document.querySelector('.leaflet-control-attribution').remove()
  // Создание маршрута
  createRoute()

  // Установка видимой области
  fitToBounds()


}

// Создание маршрута и маркеров
const createRoute = () => {
  // Очистка предыдущих слоев
  if (routeLayer) {
    map.removeLayer(routeLayer)
  }
  if (departureMarker) {
    map.removeLayer(departureMarker)
  }
  if (arrivalMarker) {
    map.removeLayer(arrivalMarker)
  }

  // Координаты точек
  const depPoint = [props.flight.dep.lat, props.flight.dep.lon]
  const arrPoint = [props.flight.arr.lat, props.flight.arr.lon]

  // Линия маршрута
  routeLayer = L.polyline([depPoint, arrPoint], {
    color: '#ff0000',
    weight: 6,
    opacity: 0.9,
    dashArray: '7, 7'
  }).addTo(map)

  // Маркер точки вылета
  console.log(depPoint, arrPoint)
  // departureMarker = L.marker(depPoint, {
  //   icon: L.divIcon({
  //     className: 'departure-marker',
  //     html: '<div style="background-color: #22c55e; width: 20px; height: 20px; border-radius: 50%; border: 3px solid white; box-shadow: 0 2px 6px rgba(0,0,0,0.3);"></div>',
  //     iconSize: [20, 20],
  //     iconAnchor: [10, 10]
  //   })
  // }).addTo(map)
  //     .bindPopup(`
  //     <strong>Точка вылета (A)</strong><br/>
  //     Ш: ${props.flight.dep.lat.toFixed(6)}°<br/>
  //     Д: ${props.flight.dep.lon.toFixed(6)}°<br/>
  //     Время: ${formatDateTime(props.flight.dep.date, props.flight.dep.time_hhmm)}
  //   `)
  //
  // // Маркер точки прибытия
  // arrivalMarker = L.marker(arrPoint, {
  //   icon: L.divIcon({
  //     className: 'arrival-marker',
  //     html: '<div style="background-color: #ef4444; width: 20px; height: 20px; border-radius: 50%; border: 3px solid white; box-shadow: 0 2px 6px rgba(0,0,0,0.3);"></div>',
  //     iconSize: [20, 20],
  //     iconAnchor: [10, 10]
  //   })
  // }).addTo(map)
  //     .bindPopup(`
  //     <strong>Точка прибытия (B)</strong><br/>
  //     Ш: ${props.flight.arr.lat.toFixed(6)}°<br/>
  //     Д: ${props.flight.arr.lon.toFixed(6)}°<br/>
  //     Время: ${formatDateTime(props.flight.arr.date, props.flight.arr.time_hhmm)}
  //   `)

  // Маркер для анимации дрона
  droneMarker = L.marker(depPoint, {
    icon: L.divIcon({
      className: 'drone-marker',
      html: `
        <div style="
          background-color: #3b82f6;
          width: 16px;
          height: 16px;
          border-radius: 50%;
          border: 3px solid white;
          box-shadow: 0 2px 8px rgba(59, 130, 246, 0.8);
          animation: pulse 1.5s infinite;
        "></div>
      `,
      iconSize: [16, 16],
      iconAnchor: [8, 8]
    })
  })

  for (let test in props.zone.features[0]['geometry']['coordinates'])
  {
    console.log(props.zone.features[0]['geometry']['coordinates'][test])
  }
  // 5446N02024E
  if (props.zone)
  {
    console.log(props.zone)
    L.geoJSON(props.zone, {
      fillColor: 'rgba(255,0,0,0.65)',
      weight: 2,
      opacity: 1,
      color: 'rgba(255,0,0,0.76)',
      dashArray:  '3',
      fillOpacity:  0.7
    }).addTo(map)
  }


}

// Анимация полета
const startAnimation = () => {
  if (animationInterval) return

  isAnimating.value = true
  droneMarker.addTo(map)

  animationInterval = setInterval(() => {
    if (animationProgress.value < 100) {
      animationProgress.value += 0.5
      updateDronePosition()
    } else {
      stopAnimation()
    }
  }, 50)
}

const stopAnimation = () => {
  isAnimating.value = false
  if (animationInterval) {
    clearInterval(animationInterval)
    animationInterval = null
  }
}

const resetAnimation = () => {
  stopAnimation()
  animationProgress.value = 0
  updateDronePosition()
}

const toggleAnimation = () => {
  if (isAnimating.value) {
    stopAnimation()
  } else {
    startAnimation()
  }
}

const updateDronePosition = () => {
  const progress = animationProgress.value / 100
  const currentLat = props.flight.dep.lat + (props.flight.arr.lat - props.flight.dep.lat) * progress
  const currentLon = props.flight.dep.lon + (props.flight.arr.lon - props.flight.dep.lon) * progress

  currentPosition.value = {lat: currentLat, lng: currentLon}

  droneMarker.setLatLng([currentLat, currentLon])
  droneMarker.bindPopup(`
    <strong>Текущее положение БПЛА</strong><br/>
    Прогресс: ${animationProgress.value.toFixed(1)}%<br/>
    Координаты: ${currentLat.toFixed(6)}, ${currentLon.toFixed(6)}<br/>
    Время: ${formatTime(animationProgress.value * props.flight.duration_min / 100)}
  `)
}

// Управление картой
const changeMapStyle = () => {
  if (!map) return

  // Удаляем все тайлы
  map.eachLayer(layer => {
    if (layer instanceof L.TileLayer) {
      map.removeLayer(layer)
    }
  })

  // Добавляем новый слой
  tileLayers[mapStyle.value].addTo(map)

  // Восстанавливаем маршрут и маркеры
  createRoute()
  if (isAnimating.value) {
    droneMarker.addTo(map)
  }
}

const fitToBounds = () => {
  if (!map || !departureMarker || !arrivalMarker) return

  const bounds = L.latLngBounds([
    [props.flight.dep.lat, props.flight.dep.lon],
    [props.flight.arr.lat, props.flight.arr.lon]
  ])

  map.fitBounds(bounds, {padding: [20, 20]})
}

// Вспомогательные функции
const calculateDistance = (lat1, lon1, lat2, lon2) => {
  const R = 6371
  const dLat = (lat2 - lat1) * Math.PI / 180
  const dLon = (lon2 - lon1) * Math.PI / 180
  const a =
      Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
      Math.sin(dLon / 2) * Math.sin(dLon / 2)
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
  return Math.round(R * c * 10) / 10
}

const formatDuration = (minutes) => {
  const days = Math.floor(minutes / 1440)
  const hours = Math.floor((minutes % 1440) / 60)
  const mins = minutes % 60
  if (days > 0) return `${days}д ${hours}ч`
  return `${hours}ч ${mins}м`
}

const formatDateTime = (date, time) => {
  return `${new Date(date).toLocaleDateString('ru-RU')} ${time}`
}

const formatTime = (minutes) => {
  const hours = Math.floor(minutes / 60)
  const mins = Math.floor(minutes % 60)
  return `${hours.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}`
}

onMounted(() => {
  initMap()

})

onUnmounted(() => {
  stopAnimation()
  if (map) {
    map.remove()
  }
})

watch(() => props.flight, () => {
  if (map) {
    map.remove()
    initMap()

  }
}, {deep: true})
</script>

<style scoped>
.flight-map-container {
  @apply bg-white rounded-2xl shadow-lg border border-gray-200 overflow-hidden h-full flex flex-col;
}

.map-controls {
  @apply flex justify-between items-start p-4 bg-gray-50 border-b border-gray-200;
}

.controls-left h3 {
  @apply text-lg font-semibold text-gray-900 mb-2;
}

.flight-info {
  @apply flex gap-3 flex-wrap;
}

.info-badge {
  @apply px-3 py-1 bg-white border border-gray-300 rounded-full text-sm text-gray-700;
}

.controls-right {
  @apply flex flex-col gap-3 items-end;
}

.control-group {
  @apply flex items-center gap-2;
}

.control-group label {
  @apply text-sm text-gray-700;
}

.style-select {
  @apply px-3 py-1 border border-gray-300 rounded-lg text-sm;
}

.animation-controls {
  @apply flex gap-2;
}

.control-btn {
  @apply px-3 py-1 bg-white border border-gray-300 rounded-lg text-sm hover:bg-gray-50 transition-colors;
}

.control-btn.active {
  @apply bg-blue-50 border-blue-300 text-blue-700;
}

.map-container {
  @apply flex-1 min-h-[400px];
}

.progress-panel {
  @apply p-4 border-t border-gray-200 bg-gray-50;
}

.progress-info {
  @apply flex justify-between text-sm text-gray-700 mb-2;
}

.progress-bar {
  @apply w-full h-2 bg-gray-200 rounded-full overflow-hidden mb-3;
}

.progress-fill {
  @apply h-full bg-gradient-to-r from-green-400 to-blue-500 rounded-full transition-all duration-100;
}

.coordinates-display {
  @apply grid grid-cols-1 md:grid-cols-3 gap-4;
}

.coordinate {
  @apply flex items-center gap-3 p-3 bg-white rounded-lg border border-gray-200;
}

.point-indicator {
  @apply w-4 h-4 rounded-full border-2 border-white shadow-sm;
}

.point-indicator.departure {
  @apply bg-green-500;
}

.point-indicator.current {
  @apply bg-blue-500;
}

.point-indicator.arrival {
  @apply bg-red-500;
}

.coordinate strong {
  @apply text-sm font-medium text-gray-900;
}

.coordinate div {
  @apply text-xs text-gray-600;
}

.coordinate small {
  @apply text-xs text-gray-500;
}

.map-legend {
  @apply absolute bottom-4 left-4 bg-white/90 backdrop-blur-sm rounded-lg p-3 shadow-lg border border-gray-200;
  z-index: 1000;
}

.legend-item {
  @apply flex items-center gap-2 mb-2 last:mb-0;
}

.legend-icon {
  @apply w-3 h-3 rounded-full border-2 border-white shadow-sm;
}

.legend-icon.departure {
  @apply bg-green-500;
}

.legend-icon.arrival {
  @apply bg-red-500;
}

.legend-icon.route {
  @apply bg-blue-500;
}

.legend-icon.drone {
  @apply bg-blue-500;
}

/* Анимации для Leaflet маркеров */
:deep(.departure-marker) {
  animation: pulse 2s infinite;
}

:deep(.arrival-marker) {
  animation: pulse 2s infinite;
}

:deep(.drone-marker) {
  z-index: 1000;
}

@keyframes pulse {
  0% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.1);
  }
  100% {
    transform: scale(1);
  }
}

/* Адаптивность */
@media (max-width: 768px) {
  .map-controls {
    @apply flex-col gap-4;
  }

  .controls-right {
    @apply items-stretch;
  }

  .animation-controls {
    @apply justify-center;
  }

  .coordinates-display {
    @apply grid-cols-1;
  }
}


.map-container {
  @apply relative;
}

.route-info {
  @apply grid grid-cols-1 md:grid-cols-3 gap-4 mt-4 p-4 bg-gray-50 rounded-lg;
}

.route-point {
  @apply flex items-center gap-3;
}

.point-marker {
  @apply w-4 h-4 rounded-full;
}

.point-marker.departure {
  @apply bg-green-500;
}

.point-marker.arrival {
  @apply bg-red-500;
}

.point-details {
  @apply text-sm;
}

.route-stats {
  @apply flex flex-col justify-center gap-2;
}

.stat {
  @apply flex justify-between items-center;
}


.header-title h1 {
  @apply text-3xl font-bold text-gray-900;
}

.flight-id {
  @apply text-gray-600 text-sm;
}

.header-actions {
  @apply flex gap-3;
}

.action-btn {
  @apply flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors;
}


.section-card {
  @apply bg-white rounded-2xl shadow-lg border border-gray-100 p-6 mb-6;
}

.section-header {
  @apply flex justify-between items-center mb-6;
}

.section-header h2 {
  @apply text-xl font-semibold text-gray-900;
}

.section-actions {
  @apply flex gap-2;
}

.tab-btn {
  @apply px-4 py-2 text-sm font-medium rounded-lg border border-gray-300 hover:bg-gray-50 transition-colors;
}

.tab-btn.active {
  @apply bg-blue-500 text-white border-blue-500;
}

</style>

