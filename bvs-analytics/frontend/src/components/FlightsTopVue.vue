<template>
  <div class="flights-top-container">
    <!-- Заголовок с иконкой -->
    <div class="header">
      <div class="header-icon">
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"/>
        </svg>
      </div>
      <h3 class="header-title">{{ title }}</h3>
      <div class="header-badge">{{ flights.length }} полетов</div>
    </div>

    <!-- Фильтры и сортировка -->
    <div class="filters">
      <div class="filter-group">
        <label class="filter-label">Сортировка:</label>
        <select v-model="sortBy" class="filter-select">
          <option value="duration">По длительности</option>
          <option value="date">По дате</option>
          <option value="region">По региону</option>
        </select>
      </div>
      <div class="filter-group">
        <label class="filter-label">Тип БПЛА:</label>
        <select v-model="filterType" class="filter-select">
          <option value="all">Все типы</option>
          <option v-for="type in uniqueTypes" :key="type" :value="type">{{ type }}</option>
        </select>
      </div>
    </div>

    <!-- Список полетов -->
    <div class="flights-list">
      <div v-for="(flight, index) in paginatedFlights" :key="flight.sid"
           class="flight-card" @click="selectFlight(flight)"
           :class="{ 'selected': selectedFlight?.sid === flight.sid }">

        <!-- Место в топе -->
        <div class="flight-rank">
          <div class="rank-badge" :class="getRankClass(index + 1)">
            #{{ index + 1 + (currentPage - 1) * itemsPerPage }}
          </div>
        </div>

        <!-- Основная информация о полете -->
        <div class="flight-main">
          <div class="flight-header">
            <span class="uav-type">{{ flight.uav_type }}</span>
            <span class="flight-duration">{{ formatDuration(flight.duration_min) }}</span>
          </div>

          <div class="flight-route">
            <div class="route-point">
              <div class="point-marker departure"></div>
              <div class="point-info">
                <div class="point-name">Вылет</div>
                <div class="point-details">
                  {{ formatDate(flight.dep.date) }} в {{ flight.dep.time_hhmm }}
                </div>
                <div class="point-coords">
                  {{ flight.dep.lat.toFixed(4) }}, {{ flight.dep.lon.toFixed(4) }}
                </div>
              </div>
            </div>

            <div class="route-line">
              <div class="route-dash"></div>
              <div class="route-dash"></div>
              <div class="route-dash"></div>
            </div>

            <div class="route-point">
              <div class="point-marker arrival"></div>
              <div class="point-info">
                <div class="point-name">Прибытие</div>
                <div class="point-details">
                  {{ formatDate(flight.arr.date) }} в {{ flight.arr.time_hhmm }}
                </div>
                <div class="point-coords">
                  {{ flight.arr.lat.toFixed(4) }}, {{ flight.arr.lon.toFixed(4) }}
                </div>
              </div>
            </div>
          </div>


        </div>

        <!-- Индикатор длительности -->
        <div class="flight-chart">
          <div class="duration-bar">
            <div class="duration-fill" :style="{ width: getDurationPercentage(flight.duration_min) + '%' }"></div>
          </div>
          <div class="duration-text">{{ Math.round(flight.duration_min / 60) }}ч</div>


          <a class="bg-green-600 text-white text-decoration-none rounded w-full text-center hover:-translate-y-1" style="color: white" :href="'/flight/'+flight.sid" target="_blank">
            Подробнее
          </a>
        </div>

      </div>
    </div>

    <!-- Пагинация -->
    <div class="pagination">
      <button @click="prevPage" :disabled="currentPage === 1" class="pagination-btn">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
        </svg>
      </button>

      <span class="pagination-info">
        Страница {{ currentPage }} из {{ totalPages }}
      </span>

      <button @click="nextPage" :disabled="currentPage === totalPages" class="pagination-btn">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
        </svg>
      </button>
    </div>

    <!-- Детали выбранного полета -->
  </div>
</template>

<script setup>
import {ref, computed, onMounted, watch} from 'vue'

const props = defineProps({
  flights: {
    type: Array,
    default: () => []
  },
  title: {
    type: String,
    default: 'Топ самых длительных полетов'
  },
  itemsPerPage: {
    type: Number,
    default: 5
  }
})

const sortBy = ref('duration')
const filterType = ref('all')
const currentPage = ref(1)
const selectedFlight = ref(null)


// Уникальные типы БПЛА для фильтра
const uniqueTypes = computed(() => {
  return [...new Set(props.flights.map(f => f.uav_type))].filter(Boolean)
})

// Отфильтрованные и отсортированные полеты
const processedFlights = computed(() => {
  let filtered = props.flights

  // Фильтрация по типу БПЛА
  if (filterType.value !== 'all') {
    filtered = filtered.filter(f => f.uav_type === filterType.value)
  }

  // Сортировка
  filtered = [...filtered].sort((a, b) => {
    switch (sortBy.value) {
      case 'duration':
        return b.duration_min - a.duration_min
      case 'date':
        return new Date(b.dep.date) - new Date(a.dep.date)
      case 'region':
        return a.region - b.region
      default:
        return 0
    }
  })

  return filtered
})

// Пагинация
const totalPages = computed(() => Math.ceil(processedFlights.value.length / props.itemsPerPage))
const paginatedFlights = computed(() => {
  const start = (currentPage.value - 1) * props.itemsPerPage
  const end = start + props.itemsPerPage
  return processedFlights.value.slice(start, end)
})

// Методы
const formatDuration = (minutes) => {
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)
  const remainingHours = hours % 24

  if (days > 0) {
    return `${days}д ${remainingHours}ч`
  }
  return `${hours}ч ${minutes % 60}м`
}

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleDateString('ru-RU')
}

const getRegionName = (regionId) => {
  return regions[regionId] || `Регион ${regionId}`
}

const getDurationPercentage = (duration) => {
  const maxDuration = Math.max(...props.flights.map(f => f.duration_min))
  return (duration / maxDuration) * 100
}

const getRankClass = (rank) => {
  if (rank === 1) return 'rank-gold'
  if (rank === 2) return 'rank-silver'
  if (rank === 3) return 'rank-bronze'
  return 'rank-other'
}

const selectFlight = (flight) => {
  selectedFlight.value = flight
}

const nextPage = () => {
  if (currentPage.value < totalPages.value) {
    currentPage.value++
  }
}

const prevPage = () => {
  if (currentPage.value > 1) {
    currentPage.value--
  }
}

// Сброс пагинации при изменении фильтров
watch([sortBy, filterType], () => {
  currentPage.value = 1
})
</script>

<style scoped>
.flights-top-container {
  @apply bg-white rounded-2xl shadow-lg border border-gray-100 p-6;
}

.header {
  @apply flex items-center justify-between mb-6 pb-4 border-b border-gray-200;
}

.header-icon {
  @apply p-2 bg-blue-100 rounded-lg text-blue-600;
}

.header-title {
  @apply text-xl font-semibold text-gray-900 flex-1 ml-4;
}

.header-badge {
  @apply bg-gray-100 text-gray-600 px-3 py-1 rounded-full text-sm font-medium;
}

.filters {
  @apply flex gap-4 mb-6 flex-wrap;
}

.filter-group {
  @apply flex items-center gap-2;
}

.filter-label {
  @apply text-sm font-medium text-gray-700 whitespace-nowrap;
}

.filter-select {
  @apply px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm;
}

.flights-list {
  @apply space-y-3;
}

.flight-card {
  @apply flex items-center gap-4 p-4 border border-gray-200 rounded-xl cursor-pointer transition-all duration-200 hover:shadow-md hover:border-blue-200;
}

.flight-card.selected {
  @apply border-blue-500 bg-blue-50 shadow-md;
}

.flight-rank {
  @apply flex-shrink-0;
}

.rank-badge {
  @apply w-12 h-12 rounded-full flex items-center justify-center font-bold text-white text-sm;
}

.rank-gold { @apply bg-yellow-500; }
.rank-silver { @apply bg-gray-400; }
.rank-bronze { @apply bg-orange-600; }
.rank-other { @apply bg-gray-300 text-gray-700; }

.flight-main {
  @apply flex-1 min-w-0;
}

.flight-header {
  @apply flex justify-between items-center mb-3;
}

.uav-type {
  @apply bg-blue-100 text-blue-800 px-2 py-1 rounded text-sm font-medium;
}

.flight-duration {
  @apply text-lg font-bold text-gray-900;
}

.flight-route {
  @apply grid grid-cols-[1fr_auto_1fr] items-center gap-3 mb-3;
}

.route-point {
  @apply flex items-center gap-3;
}

.point-marker {
  @apply w-3 h-3 rounded-full border-2 border-white shadow;
}

.point-marker.departure { @apply bg-green-500; }
.point-marker.arrival { @apply bg-red-500; }

.point-info {
  @apply flex-1;
}

.point-name {
  @apply text-sm font-medium text-gray-700;
}

.point-details {
  @apply text-sm text-gray-600;
}

.point-coords {
  @apply text-xs text-gray-500;
}

.route-line {
  @apply flex flex-col items-center;
}

.route-dash {
  @apply w-1 h-1 bg-gray-300 rounded-full my-1;
}

.flight-meta {
  @apply grid grid-cols-3 gap-4 text-sm;
}

.meta-item {
  @apply flex items-center gap-2;
}

.meta-label {
  @apply text-gray-500 font-medium;
}

.meta-value {
  @apply text-gray-900 truncate;
}

.flight-chart {
  @apply flex flex-col items-end gap-2 w-24 flex-shrink-0;
}

.duration-bar {
  @apply w-full h-2 bg-gray-200 rounded-full overflow-hidden;
}

.duration-fill {
  @apply h-full bg-gradient-to-r from-blue-500 to-blue-600 rounded-full transition-all duration-300;
}

.duration-text {
  @apply text-sm font-medium text-gray-700;
}

.pagination {
  @apply flex items-center justify-center gap-4 mt-6 pt-4 border-t border-gray-200;
}

.pagination-btn {
  @apply p-2 rounded-lg border border-gray-300 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors;
}

.pagination-info {
  @apply text-sm text-gray-600;
}

.flight-details {
  @apply mt-6 p-4 bg-gray-50 rounded-lg border border-gray-200;
}

.details-header {
  @apply flex justify-between items-center mb-4;
}

.details-header h4 {
  @apply text-lg font-semibold text-gray-900;
}

.close-btn {
  @apply p-1 hover:bg-gray-200 rounded transition-colors;
}

.detail-grid {
  @apply grid grid-cols-2 gap-4;
}

.detail-item {
  @apply flex justify-between items-center py-2 border-b border-gray-100;
}

.detail-item label {
  @apply text-gray-600 font-medium;
}

.detail-item span {
  @apply text-gray-900;
}

/* Адаптивность */
@media (max-width: 1024px) {
  .flight-route {
    @apply grid-cols-1 gap-2;
  }

  .route-line {
    @apply hidden;
  }

  .flight-meta {
    @apply grid-cols-1 gap-2;
  }

  .detail-grid {
    @apply grid-cols-1;
  }
}

@media (max-width: 768px) {
  .flight-card {
    @apply flex-col items-stretch;
  }

  .flight-chart {
    @apply w-full flex-row items-center;
  }

  .duration-bar {
    @apply flex-1;
  }

  .filters {
    @apply flex-col;
  }
}
</style>