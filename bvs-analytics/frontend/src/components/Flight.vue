<template>
  <DroneLoader v-if="!loaded"></DroneLoader>
  <div v-else class="flight-analytics-container">
    <!-- Хедер с навигацией -->
    <div class="analytics-header">
      <div class="header-title">
        <h1>Детальная аналитика полета ID: {{ flight.sid }}</h1>
      </div>

    </div>

    <!-- Основные метрики полета -->
    <div class="metrics-grid">
      <div class="metric-card">
        <div class="metric-icon bg-blue-100">
          <svg class="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
          </svg>
        </div>
        <div class="metric-content">
          <span class="metric-label">Длительность полета</span>
          <span class="metric-value">{{ formatDuration(flight.duration_min) }}</span>
        </div>
      </div>


      <div class="metric-card">
        <div class="metric-icon bg-purple-100">
          <svg class="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"/>
          </svg>
        </div>
        <div class="metric-content">
          <span class="metric-label">Тип БПЛА</span>
          <span class="metric-value">{{ flight.uav_type }}</span>
        </div>
      </div>

      <div class="metric-card" v-bind:class="(!flight || !calculatedDistance) ? 'col-span-2' : ''">
        <div class="metric-icon bg-orange-100">
          <svg class="w-6 h-6 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/>
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"/>
          </svg>
        </div>
        <div class="metric-content">
          <span class="metric-label">Регион</span>
          <span class="metric-value">{{ getRegionName(flight.region) }}</span>
        </div>
      </div>
      <div class="metric-card" v-if="flight && calculatedDistance > 0">
        <div class="metric-icon bg-orange-100">
          <svg class="w-6 h-6 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/>
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"/>
          </svg>
        </div>
        <div class="metric-content">
          <span class="metric-label">Расстояние</span>
          <span class="metric-value">{{ calculateDistance() }} км</span>
        </div>
      </div>
    </div>

    <!-- Карта маршрута -->
    <div class="section-card">
      <FlightMap :flight="flight" :zone="zone"/>
    </div>

    <!-- Детальная статистика -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Временная статистика -->
      <div class="section-card">
        <div class="section-header">
          <h2>Временная статистика</h2>
        </div>
        <div class="stats-grid">
          <div class="stat-item">
            <span class="stat-label">Время вылета</span>
            <span class="stat-value">{{ flight.dep.time_hhmm }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">Время прибытия</span>
            <span class="stat-value">{{ flight.arr.time_hhmm }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">Дней в полете</span>
            <span class="stat-value">{{ Math.floor(flight.duration_min / 1440) }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">Часов в полете</span>
            <span class="stat-value">{{ Math.floor(flight.duration_min / 60) }}</span>
          </div>
        </div>
      </div>

      <!-- Информация о полете и операторе -->
      <div class="section-card">
        <div class="section-header">
          <h2>Информация о полете</h2>
        </div>

        <!-- Карточка оператора -->
        <div class="operator-card" v-if="flight.operator">
          <div class="operator-header">
            <div class="operator-avatar">
              <svg class="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
              </svg>
            </div>
            <div class="operator-info">
              <h3 class="operator-name">{{ flight.operator }}</h3>
              <span class="operator-role">Оператор БПЛА</span>
            </div>
          </div>

          <div class="operator-details">
            <div class="detail-item">
              <svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/>
              </svg>
              <span>{{ flight.center_name || 'ЦУП не указан' }}</span>
            </div>
          </div>
        </div>

        <!-- Дополнительные параметры -->
        <div class="flight-params-grid">
          <div class="param-card">
            <div class="param-icon bg-blue-50">
              <svg class="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 6l3 1m0 0l-3 9a5.002 5.002 0 006.001 0M6 7l3 9M6 7l6-2m6 2l3-1m-3 1l-3 9a5.002 5.002 0 006.001 0M18 7l3 9m-3-9l-6-2m0-2v2m0 16V5m0 16H9m3 0h3"/>
              </svg>
            </div>
            <div class="param-content">
              <span class="param-label">Высота полета</span>
              <span class="param-value">~{{ calculateAltitude() }} м</span>
            </div>
          </div>

          <div class="param-card">
            <div class="param-icon bg-orange-50">
              <svg class="w-5 h-5 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
              </svg>
            </div>
            <div class="param-content">
              <span class="param-label">Дата полета</span>
              <span class="param-value">{{ formatDate(flight.dep?.date) }}</span>
            </div>
            <div class="param-content">
              <span class="param-label">Дата полета</span>
              <span class="param-value">{{  }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Сравнение с аналогичными полетами -->
<!--    <div class="section-card">-->
<!--      <div class="section-header">-->
<!--        <h2>Сравнение с аналогичными полетами</h2>-->
<!--      </div>-->
<!--      <FlightComparison :flight="flight" :similar-flights="similarFlights" />-->
<!--    </div>-->


  </div>
</template>

<script setup>
import {computed, onMounted, ref} from 'vue'
import {useRoute} from 'vue-router'
import DroneLoader from "@/components/DroneLoader.vue";
import FlightMap from "@/components/maps/FlightMap.vue";

// Компоненты (нужно будет создать)
// import FlightMap from './FlightMap.vue'
// import ActivityChart from './ActivityChart.vue'
// import TelemetryViewer from './TelemetryViewer.vue'
// import FlightComparison from './FlightComparison.vue'
//
const route = useRoute()
const flight = ref({})
const loaded = ref(false)
const mapView = ref('route')
const telemetryView = ref('chart')
const similarFlights = ref([])
const zone = ref({})
// Загрузка данных полета
onMounted(async () => {
  const flightId = route.params.id
  console.log(flightId)
  await loadFlightData(flightId)
  await loadSimilarFlights()

  loaded.value = true
})

const loadFlightData = async (flightId) => {
  // Загрузка данных полета по ID
  // Временные данные для примера
  const resp = await fetch('https://imdibil.ru/api/flight/'+flightId)
  const data = await resp.json()

  flight.value = data

  const zone_resp = await fetch('https://imdibil.ru/api/zone/'+flightId)
  zone.value = await zone_resp.json()
  console.log(zone.value)
  console.log(flight.value)

}
const calculatedDistance = computed(() => {
  if (flight.dep.lat && flight.arr.lat)
  {
    return calculateDistance(
        flight.dep.lat, flight.dep.lon,
        flight.arr.lat, flight.arr.lon
    )
  } else return 0

})


const loadSimilarFlights = async () => {
  // Загрузка похожих полетов
  similarFlights.value = [
    // Массив похожих полетов
  ]
}

// Вспомогательные функции
const formatDuration = (minutes) => {
  const days = Math.floor(minutes / 1440)
  const hours = Math.floor((minutes % 1440) / 60)
  const mins = minutes % 60
  if (days) {
    return `${days}д ${hours}ч ${mins}м`
  } else
  {
    return `${hours}ч ${mins}м`
  }
}

const formatDate = (dateString) => {
  try {
    return new Date(dateString).toLocaleDateString('ru-RU')
  } catch (e) {
    return  ""
  }
}

const formatDateRange = (start, end) => {
  return `${formatDate(start)} - ${formatDate(end)}`
}

const formatCoordinates = (lat, lon) => {
  return `${lat.toFixed(4)}°, ${lon.toFixed(4)}°`
}

const getRegionName = (regionId) => {
  const regions = {
    11: 'Дальневосточный федеральный округ',
    // ... другие регионы
  }
  return regions[regionId] || `${regionId}`
}

const calculateDistance = () => {
  // Простой расчет расстояния между точками
  const R = 6371 // Радиус Земли в км
  const dLat = (flight.value.arr.lat - flight.value.dep.lat) * Math.PI / 180
  const dLon = (flight.value.arr.lon - flight.value.dep.lon) * Math.PI / 180
  const a =
      Math.sin(dLat/2) * Math.sin(dLat/2) +
      Math.cos(flight.value.dep.lat * Math.PI / 180) *
      Math.cos(flight.value.arr.lat * Math.PI / 180) *
      Math.sin(dLon/2) * Math.sin(dLon/2)
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a))
  return Math.round(R * c)
}

const calculateSpeed = () => {
  const distance = calculateDistance()
  const hours = flight.value.duration_min / 60
  return hours > 0 ? Math.round(distance / hours) : 0
}

const calculateAltitude = () => {
  // Упрощенный расчет высоты (можно заменить реальными данными)
  return Math.round(1000 + Math.random() * 2000)
}

const exportReport = () => {
  console.log('Экспорт отчета для полета:', flight.value.sid)
}

const shareFlight = () => {
  console.log('Поделиться данными полета:', flight.value.sid)
}
</script>

<style scoped>
.flight-analytics-container {
  @apply min-h-screen bg-gray-50 p-6;
}

.analytics-header {
  @apply flex items-center justify-between mb-8 p-6 bg-white rounded-2xl shadow-lg border border-gray-100;
}

.back-btn {
  @apply flex items-center gap-2 px-4 py-2 text-gray-600 hover:text-gray-900 transition-colors;
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



.metric-card {
  @apply flex items-center gap-4 p-6 bg-white rounded-2xl shadow-lg border border-gray-100;
}

.metric-icon {
  @apply p-3 rounded-xl;
}

.metric-content {
  @apply flex flex-col;
}

.metric-label {
  @apply text-gray-600 text-sm;
}

.metric-value {
  @apply text-2xl font-bold text-gray-900;
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

.point-marker.departure { @apply bg-green-500; }
.point-marker.arrival { @apply bg-red-500; }

.point-details {
  @apply text-sm;
}

.route-stats {
  @apply flex flex-col justify-center gap-2;
}

.stat {
  @apply flex justify-between items-center;
}

.stats-grid {
  @apply grid grid-cols-2 gap-4;
}

.stat-item {
  @apply flex justify-between items-center py-3 border-b border-gray-100;
}

.stat-label {
  @apply text-gray-600;
}

.stat-value {
  @apply font-semibold text-gray-900;
}

.tech-params {
  @apply space-y-3;
}

.param-group {
  @apply flex justify-between items-center py-2 border-b border-gray-100;
}

.status-badge {
  @apply px-2 py-1 rounded-full text-xs font-medium;
}

.status-badge.completed {
  @apply bg-green-100 text-green-800;
}

.efficiency-metrics {
  @apply mt-6;
}

.efficiency-grid {
  @apply space-y-3;
}

.efficiency-item {
  @apply flex items-center gap-3;
}

.efficiency-label {
  @apply text-sm text-gray-600 w-32;
}

.efficiency-bar {
  @apply flex-1 h-2 bg-gray-200 rounded-full overflow-hidden;
}

.efficiency-fill {
  @apply h-full bg-gradient-to-r from-green-400 to-blue-500 rounded-full;
}

.efficiency-value {
  @apply text-sm font-semibold text-gray-700 w-12 text-right;
}

.action-buttons {
  @apply flex gap-4 justify-center mt-8;
}

.btn-primary {
  @apply flex items-center gap-2 px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors font-medium;
}

.btn-secondary {
  @apply flex items-center gap-2 px-6 py-3 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors font-medium;
}


.metrics-grid {
  @apply grid grid-cols-4  gap-6 mb-8;
}

/* Адаптивность */
@media (max-width: 768px) {
  .analytics-header {
    @apply flex-col gap-4 items-stretch;
  }

  .metrics-grid {
    @apply grid-cols-1;
  }

  .route-info {
    @apply grid-cols-1;
  }

  .action-buttons {
    @apply flex-col;
  }
}


/* Стили для карточки оператора */
.operator-card {
  @apply bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl p-4 mb-6 border border-blue-100;
}

.operator-header {
  @apply flex items-center gap-3 mb-3;
}

.operator-avatar {
  @apply w-12 h-12 bg-white rounded-full flex items-center justify-center shadow-sm border border-blue-200;
}

.operator-info {
  @apply flex flex-col;
}

.operator-name {
  @apply font-semibold text-gray-900 text-lg;
}

.operator-role {
  @apply text-gray-600 text-sm;
}

.operator-details {
  @apply flex items-center gap-2 text-gray-700;
}

.detail-item {
  @apply flex items-center gap-2 text-sm;
}

/* Стили для параметров полета */
.flight-params-grid {
  @apply grid grid-cols-2 gap-4;
}

.param-card {
  @apply flex items-center gap-3 p-3 bg-gray-50 rounded-lg border border-gray-200;
}

.param-icon {
  @apply p-2 rounded-lg;
}

.param-content {
  @apply flex flex-col;
}

.param-label {
  @apply text-gray-600 text-xs;
}

.param-value {
  @apply font-semibold text-gray-900 text-sm;
}

.status-completed {
  @apply text-green-600;
}

/* Адаптивность */
@media (max-width: 768px) {
  .flight-params-grid {
    @apply grid-cols-1;
  }

  .operator-header {
    @apply flex-col text-center;
  }
}
</style>