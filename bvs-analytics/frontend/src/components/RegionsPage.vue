<template>
  <div class="regions-container">
    <!-- Хедер -->
    <div class="regions-header">
      <div class="header-content">
        <h1 class="header-title">Регионы мониторинга</h1>
        <p class="header-description">Статистика полетов БПЛА по регионам</p>
      </div>
    </div>

    <!-- Панель управления -->
    <div class="control-panel">
      <div class="search-box">
        <div class="search-input-wrapper">
          <svg class="search-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
          </svg>
          <input
              v-model="searchQuery"
              type="text"
              placeholder="Поиск региона..."
              class="search-input"
          />
        </div>
      </div>


    </div>

    <!-- Таблица регионов -->
    <div class="table-container">
      <table class="regions-table">
        <thead>
        <tr>
          <th class="text-left">
            <button @click="sortBy('name')" class="sortable-header">
              Регион
              <span class="sort-indicator" v-if="sortByField === 'name'">
                  {{ sortOrder === 'asc' ? '↑' : '↓' }}
                </span>
            </button>
          </th>
          <th class="text-right">
            <button @click="sortBy('flights')" class="sortable-header">
              Полетов
              <span class="sort-indicator" v-if="sortByField === 'flights'">
                  {{ sortOrder === 'asc' ? '↑' : '↓' }}
                </span>
            </button>
          </th>
          <th class="text-right">
            <button @click="sortBy('duration')" class="sortable-header">
              Общее время
              <span class="sort-indicator" v-if="sortByField === 'duration'">
                  {{ sortOrder === 'asc' ? '↑' : '↓' }}
                </span>
            </button>
          </th>
          <th class="text-right">
            <button @click="sortBy('avgDuration')" class="sortable-header">
              Среднее время
              <span class="sort-indicator" v-if="sortByField === 'avgDuration'">
                  {{ sortOrder === 'asc' ? '↑' : '↓' }}
                </span>
            </button>
          </th>
          <th class="text-right">
            <button @click="sortBy('lastActivity')" class="sortable-header">
              Последняя активность
              <span class="sort-indicator" v-if="sortByField === 'lastActivity'">
                  {{ sortOrder === 'asc' ? '↑' : '↓' }}
                </span>
            </button>
          </th>
          <th class="text-center">Действия</th>
        </tr>
        </thead>
        <tbody>
        <tr
            v-for="region in sortedRegions"
            :key="region.region_id"
            class="region-row"
            @click="goToRegionStats(region.region_id)"
        >
          <td class="region-cell">
            <div class="region-info">
              <div class="region-color" :style="{ backgroundColor: region.color }"></div>
              <div class="region-details">
                <div class="region-name">{{ region.name }}</div>
                <div class="region-id">ID: {{ region.region_id }}</div>
              </div>
            </div>
          </td>
          <td class="text-right">
            <span class="number-value">{{ region.flights }}</span>
          </td>
          <td class="text-right">
            <span class="duration-value">{{ formatDuration(region.duration) }}</span>
          </td>
          <td class="text-right">
            <span class="duration-value">{{ formatDuration(region.avgDuration) }}</span>
          </td>
          <td class="text-right">
            <div class="activity-cell">
              <span class="activity-date">{{ formatDate(region.lastActivity) }}</span>
              <div class="activity-indicator" :class="getActivityClass(region.lastActivity)"></div>
            </div>
          </td>
          <td class="text-center">
              <div class="action-buttons">
                <button @click="viewRegion(region.region_id)" class="btn-view" title="Просмотр деталей">
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
                  </svg>
                </button>
            </div>
          </td>
        </tr>
        </tbody>
      </table>

      <div v-if="loading" class="loading-state">
        <div class="loading-spinner"></div>
        <span>Загрузка данных...</span>
      </div>
      <!-- Пустое состояние -->
      <div v-else-if="sortedRegions.length === 0" class="empty-state">
        <div class="empty-content">
          <svg class="empty-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/>
          </svg>
          <h3 class="empty-title">Регионы не найдены</h3>
          <p class="empty-description">Попробуйте изменить параметры поиска</p>
        </div>
      </div>
    </div>

    <!-- Пагинация -->
    <div v-if="sortedRegions.length > 0" class="pagination">
      <div class="pagination-info">
        Показано {{ sortedRegions.length }} из {{ totalRegions }} регионов
      </div>
    </div>

    <!-- Загрузка -->
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

// Реактивные данные
const loading = ref(true)
const searchQuery = ref('')
const sortByField = ref('flights')
const sortOrder = ref('desc')
const regions = ref([])

// Тестовые данные регионов
const mockRegions = [
  {
    region_id: 11,
    name: 'Дальневосточный федеральный округ',
    color: '#3B82F6',
    flights: 156,
    duration: 12540,
    avgDuration: 80,
    activeUAVs: 12,
    lastActivity: new Date('2024-01-20T14:30:00'),
    isFavorite: true
  }
]

// Вычисляемые свойства
const filteredRegions = computed(() => {
  return regions.value.filter(region =>
      region.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      region.region_id.toString().includes(searchQuery.value)
  )
})

const sortedRegions = computed(() => {
  const regions = [...filteredRegions.value]

  return regions.sort((a, b) => {
    let aValue, bValue

    switch (sortByField.value) {
      case 'name':
        aValue = a.name
        bValue = b.name
        break
      case 'flights':
        aValue = a.flights
        bValue = b.flights
        break
      case 'duration':
        aValue = a.duration
        bValue = b.duration
        break
      case 'avgDuration':
        aValue = a.avgDuration
        bValue = b.avgDuration
        break
      case 'activeUAVs':
        aValue = a.activeUAVs
        bValue = b.activeUAVs
        break
      case 'lastActivity':
        aValue = new Date(a.lastActivity)
        bValue = new Date(b.lastActivity)
        break
      default:
        aValue = a.flights
        bValue = b.flights
    }

    if (sortOrder.value === 'asc') {
      return aValue < bValue ? -1 : aValue > bValue ? 1 : 0
    } else {
      return aValue > bValue ? -1 : aValue < bValue ? 1 : 0
    }
  })
})

const totalRegions = computed(() => regions.value.length)
const totalFlights = computed(() => regions.value.reduce((sum, region) => sum + region.flights, 0))
const totalDuration = computed(() => regions.value.reduce((sum, region) => sum + region.duration, 0))

// Методы
const sortBy = (field) => {
  if (sortByField.value === field) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortByField.value = field
    sortOrder.value = 'desc'
  }
}

const formatDuration = (minutes) => {
  const hours = Math.floor(minutes / 60)
  const mins = Math.floor(minutes % 60)
  if (hours > 0) {
    return `${hours}ч ${mins}м`
  }
  return `${mins}м`
}

const formatDate = (date) => {
  return new Date(date).toLocaleDateString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  })
}

const getActivityClass = (lastActivity) => {
  const daysDiff = (new Date() - new Date(lastActivity)) / (1000 * 60 * 60 * 24)
  if (daysDiff < 1) return 'activity-high'
  if (daysDiff < 3) return 'activity-medium'
  return 'activity-low'
}

const toggleFavorite = (regionId) => {
  const region = regions.value.find(r => r.region_id === regionId)
  if (region) {
    region.isFavorite = !region.isFavorite
  }
}

const goToRegionStats = (regionId) => {
  router.push(`/region/${regionId}`)
}



// Загрузка данных
onMounted(async () => {
  // Имитация загрузки данных
  let response = await fetch('https://imdibil.ru/api/regions')
  let data = await response.json()
  regions.value = data
  regions.value.forEach((r) => {
    r.lastActivity = new Date(r.last_flight)
    r.color = "#3B82F6"
  });
  console.log(regions.value)
  loading.value = false
})

function viewRegion(regionId)
{
  router.push('region/'+regionId)
}
</script>

<style scoped>
.regions-container {
  @apply min-h-screen bg-gray-50 p-6;
}

.regions-header {
  @apply mb-6 p-6 bg-white rounded-xl shadow-sm border border-gray-200;
}

.header-content {
  @apply mb-4;
}

.header-title {
  @apply text-2xl font-bold text-gray-900 mb-2;
}

.header-description {
  @apply text-gray-600;
}

.header-stats {
  @apply flex gap-6;
}

.stat-item {
  @apply flex flex-col items-start;
}

.stat-value {
  @apply text-xl font-bold text-gray-900;
}

.stat-label {
  @apply text-gray-600 text-sm;
}

/* Панель управления */
.control-panel {
  @apply flex justify-between items-center mb-4 p-4 bg-white rounded-xl shadow-sm border border-gray-200;
}

.search-box {
  @apply flex-1 max-w-md;
}

.search-input-wrapper {
  @apply relative;
}

.search-icon {
  @apply absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400;
}

.search-input {
  @apply w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm;
}

.export-btn {
  @apply flex items-center gap-2 px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors text-sm;
}

/* Таблица */
.table-container {
  @apply bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden;
}

.regions-table {
  @apply w-full border-collapse;
}

.regions-table th {
  @apply px-4 py-3 bg-gray-50 text-xs font-medium text-gray-500 uppercase tracking-wider border-b border-gray-200;
}

.regions-table td {
  @apply px-4 py-3 border-b border-gray-200;
}

.sortable-header {
  @apply flex items-center gap-1 w-full text-left font-medium hover:text-gray-700 transition-colors;
}

.sort-indicator {
  @apply text-blue-500 font-bold;
}

.region-row {
  @apply hover:bg-gray-50 cursor-pointer transition-colors;
}

.region-cell {
  @apply min-w-80;
}

.region-info {
  @apply flex items-center gap-3;
}

.region-color {
  @apply w-3 h-8 rounded-full flex-shrink-0;
}

.region-details {
  @apply min-w-0;
}

.region-name {
  @apply font-medium text-gray-900 truncate;
}

.region-id {
  @apply text-gray-500 text-xs;
}

.number-value {
  @apply font-semibold text-gray-900;
}

.duration-value {
  @apply font-semibold text-blue-600;
}

.uav-count {
  @apply font-semibold text-green-600;
}

.activity-cell {
  @apply flex items-center justify-end gap-2;
}

.activity-date {
  @apply text-gray-600 text-sm;
}

.activity-indicator {
  @apply w-2 h-2 rounded-full;
}

.activity-high {
  @apply bg-green-500;
}

.activity-medium {
  @apply bg-yellow-500;
}

.activity-low {
  @apply bg-red-500;
}

.action-buttons {
  @apply flex justify-center gap-1;
}

.action-btn {
  @apply p-1 rounded transition-colors;
}

.view-btn {
  @apply text-blue-600 hover:bg-blue-50;
}

.favorite-btn {
  @apply text-gray-400 hover:text-yellow-500 hover:bg-yellow-50;
}

.favorite-btn.favorited {
  @apply text-yellow-500;
}

/* Пустое состояние */
.empty-state {
  @apply py-12;
}

.empty-content {
  @apply text-center max-w-md mx-auto;
}

.empty-icon {
  @apply w-12 h-12 text-gray-400 mx-auto mb-4;
}

.empty-title {
  @apply text-lg font-semibold text-gray-900 mb-2;
}

.empty-description {
  @apply text-gray-600 text-sm;
}

/* Пагинация */
.pagination {
  @apply flex justify-between items-center mt-4 p-4 bg-white rounded-xl shadow-sm border border-gray-200;
}

.pagination-info {
  @apply text-gray-600 text-sm;
}

/* Загрузка */
.loading-overlay {
  @apply fixed inset-0 bg-white bg-opacity-80 flex flex-col items-center justify-center z-50;
}

.loading-spinner {
  @apply w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mb-2;
}

/* Адаптивность */
@media (max-width: 1024px) {
  .table-container {
    @apply overflow-x-auto;
  }

  .regions-table {
    @apply min-w-full;
  }
}

@media (max-width: 768px) {
  .control-panel {
    @apply flex-col gap-4 items-stretch;
  }

  .search-box {
    @apply max-w-none;
  }

  .header-stats {
    @apply justify-between;
  }

  .stat-item {
    @apply items-center;
  }
}

.loading-state {
  @apply flex items-center justify-center gap-3 py-12;
}
</style>