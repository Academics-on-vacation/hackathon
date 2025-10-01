<template>
  <div class="history-page">
    <!-- Заголовок страницы -->
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">История полетов</h1>
        <p class="page-description">Полный список всех выполненных рейсов БПЛА</p>
      </div>
      <div class="header-stats">
        <div class="stat-card">
          <div class="stat-icon">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/>
            </svg>
          </div>
          <div class="stat-info">
            <span class="stat-value">{{ totalFlights }}</span>
            <span class="stat-label">Всего рейсов</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Панель управления -->
    <div class="control-panel">
      <!-- Поиск -->
      <div class="search-section">
        <div class="search-box">
          <svg class="search-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
          </svg>
          <input
              v-model="searchQuery"
              type="text"
              placeholder="Поиск по ID, типу БПЛА, оператору..."
              class="search-input"
              @input="onSearch"
          >
          <button v-if="searchQuery" @click="clearSearch" class="clear-search">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>
      </div>

      <!-- Фильтры -->
      <div class="filters-section">
        <div class="filter-group">
          <label class="filter-label">Тип БПЛА:</label>
          <select v-model="filters.uavType" @change="applyFilters" class="filter-select">
            <option value="">Все типы</option>
            <option v-for="type in uavTypes" :key="type" :value="type">{{ type }}</option>
          </select>
        </div>

        <div class="filter-group">
          <label class="filter-label">Регион:</label>
          <select v-model="filters.region" @change="applyFilters" class="filter-select">
            <option value="">Все регионы</option>
            <option v-for="region in regions" :key="region.id" :value="region.id">{{ region.name }}</option>
          </select>
        </div>

<!--        <div class="filter-group">-->
<!--          <label class="filter-label">Период:</label>-->
<!--          <select v-model="filters.period" @change="applyFilters" class="filter-select">-->
<!--            <option value="all">За все время</option>-->
<!--            <option value="today">Сегодня</option>-->
<!--            <option value="week">За неделю</option>-->
<!--            <option value="month">За месяц</option>-->
<!--            <option value="year">За год</option>-->
<!--          </select>-->
<!--        </div>-->

<!--        <div class="filter-group">-->
<!--          <label class="filter-label">Статус:</label>-->
<!--          <select v-model="filters.status" @change="applyFilters" class="filter-select">-->
<!--            <option value="">Все статусы</option>-->
<!--            <option value="completed">Завершены</option>-->
<!--            <option value="active">Активные</option>-->
<!--            <option value="cancelled">Отменены</option>-->
<!--          </select>-->
<!--        </div>-->

        <button @click="resetFilters" class="reset-filters-btn">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
          </svg>
          Сбросить
        </button>
      </div>
    </div>

    <!-- Таблица рейсов -->
    <div class="table-container">
      <div class="table-header">
        <div class="table-actions">
<!--          <button @click="exportToCSV" class="action-btn">-->
<!--            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">-->
<!--              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>-->
<!--            </svg>-->
<!--            Экспорт CSV-->
<!--          </button>-->
          <div class="records-info">
            Показано {{ displayedFlights.length }} из {{ filteredFlights.length }} рейсов
          </div>
        </div>
      </div>

      <div class="table-wrapper">
        <table class="flights-table">
          <thead>
          <tr>
            <th @click="sortBy('sid')" class="sortable">
              <div class="th-content">
                ID рейса
                <span class="sort-indicator" :class="getSortClass('sid')">
                    {{ getSortSymbol('sid') }}
                  </span>
              </div>
            </th>
            <th @click="sortBy('uav_type')" class="sortable">
              <div class="th-content">
                Тип БПЛА
                <span class="sort-indicator" :class="getSortClass('uav_type')">
                    {{ getSortSymbol('uav_type') }}
                  </span>
              </div>
            </th>
            <th @click="sortBy('dep.date')" class="sortable">
              <div class="th-content">
                Дата вылета
                <span class="sort-indicator" :class="getSortClass('dep.date')">
                    {{ getSortSymbol('dep.date') }}
                  </span>
              </div>
            </th>
            <th @click="sortBy('arr.date')" class="sortable">
              <div class="th-content">
                Дата прибытия
                <span class="sort-indicator" :class="getSortClass('arr.date')">
                    {{ getSortSymbol('arr.date') }}
                  </span>
              </div>
            </th>
            <th @click="sortBy('duration_min')" class="sortable">
              <div class="th-content">
                Длительность
                <span class="sort-indicator" :class="getSortClass('duration_min')">
                    {{ getSortSymbol('duration_min') }}
                  </span>
              </div>
            </th>
            <th @click="sortBy('region')" class="sortable">
              <div class="th-content">
                Регион
                <span class="sort-indicator" :class="getSortClass('region')">
                    {{ getSortSymbol('region') }}
                  </span>
              </div>
            </th>
            <th @click="sortBy('operator')" class="sortable">
              <div class="th-content">
                Оператор
                <span class="sort-indicator" :class="getSortClass('operator')">
                    {{ getSortSymbol('operator') }}
                  </span>
              </div>
            </th>
            <th>Действия</th>
          </tr>
          </thead>
          <tbody>
          <tr v-for="flight in displayedFlights" :key="flight.sid" class="flight-row">
            <td class="flight-id">
              <span class="id-text">{{ flight.sid }}</span>
            </td>
            <td>
              <span class="uav-type-badge">{{ flight.uav_type }}</span>
            </td>
            <td>
              <div class="date-time">
                <div class="date">{{ formatDate(flight.dep.date) }}</div>
                <div class="time">{{ flight.dep.time_hhmm }}</div>
              </div>
            </td>
            <td>
              <div class="date-time">
                <div class="date">{{ formatDate(flight.arr.date) }}</div>
                <div class="time">{{ flight.arr.time_hhmm }}</div>
              </div>
            </td>
            <td>
              <div class="duration-cell">
                <div class="duration-value">{{ formatDuration(flight.duration_min) }}</div>
<!--                <div class="duration-bar">-->
<!--                  <div-->
<!--                      class="duration-fill"-->
<!--                      :style="{ width: getDurationPercentage(flight.duration_min) + '%' }"-->
<!--                  ></div>-->
<!--                </div>-->
              </div>
            </td>
            <td>
              <span class="region-badge">{{ flight.region_name }}</span>
            </td>
            <td>
              <span class="operator">{{ flight.operator || 'Не указан' }}</span>
            </td>
            <td>
              <div class="action-buttons">
                <button @click="viewFlight(flight)" class="btn-view" title="Просмотр деталей">
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

        <!-- Состояние загрузки -->
        <div v-if="loading" class="loading-state">
          <div class="loading-spinner"></div>
          <span>Загрузка данных...</span>
        </div>

        <!-- Пустое состояние -->
        <div v-else-if="filteredFlights.length === 0" class="empty-state">
<!--          <svg class="empty-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">-->
<!--            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>-->
<!--          </svg>-->
          <h3>Рейсы не найдены</h3>
          <p>Попробуйте изменить параметры поиска или фильтры</p>
        </div>
      </div>

      <!-- Пагинация -->
      <div v-if="filteredFlights.length > 0" class="pagination">
        <div class="pagination-info">
          Показано с {{ startItem }} по {{ endItem }} из {{ filteredFlights.length }} записей
        </div>

        <div class="pagination-controls">
          <button
              @click="prevPage"
              :disabled="currentPage === 1"
              class="pagination-btn"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
            </svg>
          </button>

          <div class="page-numbers">
            <button
                v-for="page in visiblePages"
                :key="page"
                @click="goToPage(page)"
                :class="['page-btn', { active: page === currentPage }]"
            >
              {{ page }}
            </button>

            <span v-if="showEllipsis" class="page-ellipsis">...</span>
          </div>

          <button
              @click="nextPage"
              :disabled="currentPage === totalPages"
              class="pagination-btn"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
            </svg>
          </button>
        </div>

        <div class="page-size-selector">
          <label>Записей на странице:</label>
          <select v-model="pageSize" @change="onPageSizeChange" class="page-size-select">
            <option value="10">10</option>
            <option value="25">25</option>
            <option value="50">50</option>
            <option value="100">100</option>
          </select>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

// Данные
const flights = ref([])
const loading = ref(true)

// Поиск и фильтры
const searchQuery = ref('')
const filters = ref({
  uavType: '',
  region: '',
  period: 'all',
  status: ''
})

// Сортировка
const sortField = ref('dep.date')
const sortDirection = ref('desc')

// Пагинация
const currentPage = ref(1)
const pageSize = ref(25)

// Загрузка данных
onMounted(async () => {
  await loadFlights()
})

const loadFlights = async () => {
  loading.value = true
  try {
    // Загрузка данных из API
    const response = await fetch('https://imdibil.ru/api/flights')
    const data = await response.json()
    flights.value = data.flights || []
  } catch (error) {
    console.error('Ошибка загрузки данных:', error)
    // Заглушка для демонстрации
    flights.value = generateDemoData()
  } finally {
    loading.value = false
  }
}

// Вычисляемые свойства
const totalFlights = computed(() => flights.value.length)

const uavTypes = computed(() => {
  return [...new Set(flights.value.map(f => f.uav_type))].filter(Boolean).sort()
})

const regions = computed(() => {
  let list = {}
  flights.value.forEach((f) => {
    list[f.region] = f.region_name
  });

  let list_ret = [];
  Object.keys(list).forEach((id) => {
    list_ret.push({id: id, name: list[id]})
  });
  return list_ret
})

// Фильтрация и поиск
const filteredFlights = computed(() => {
  let filtered = flights.value

  // Поиск
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(flight =>
        flight.sid.toLowerCase().includes(query)
        // flight.uav_type.toLowerCase().includes(query) ||
        // (flight.operator && flight.operator.toLowerCase().includes(query)) ||
        // flight.center_name.toLowerCase().includes(query)
    )
  }

  // Фильтры
  if (filters.value.uavType) {
    filtered = filtered.filter(flight => flight.uav_type === filters.value.uavType)
  }

  if (filters.value.region) {
    filtered = filtered.filter(flight => flight.region === parseInt(filters.value.region))
  }

  if (filters.value.period !== 'all') {
    const now = new Date()
    let startDate

    switch (filters.value.period) {
      case 'today':
        startDate = new Date(now.setHours(0, 0, 0, 0))
        break
      case 'week':
        startDate = new Date(now.setDate(now.getDate() - 7))
        break
      case 'month':
        startDate = new Date(now.setMonth(now.getMonth() - 1))
        break
      case 'year':
        startDate = new Date(now.setFullYear(now.getFullYear() - 1))
        break
    }

    filtered = filtered.filter(flight => new Date(flight.dep.date) >= startDate)
  }

  return filtered
})

// Сортировка
const sortedFlights = computed(() => {
  const sorted = [...filteredFlights.value]

  return sorted.sort((a, b) => {
    let aValue, bValue

    if (sortField.value === 'dep.date') {
      aValue = new Date(a.dep.date + 'T' + a.dep.time_hhmm)
      bValue = new Date(b.dep.date + 'T' + b.dep.time_hhmm)
    } else if (sortField.value === 'arr.date') {
      aValue = new Date(a.arr.date + 'T' + a.arr.time_hhmm)
      bValue = new Date(b.arr.date + 'T' + b.arr.time_hhmm)
    } else if (sortField.value.includes('.')) {
      // Для вложенных свойств
      const keys = sortField.value.split('.')
      aValue = keys.reduce((obj, key) => obj[key], a)
      bValue = keys.reduce((obj, key) => obj[key], b)
    } else {
      aValue = a[sortField.value]
      bValue = b[sortField.value]
    }

    if (sortDirection.value === 'asc') {
      return aValue > bValue ? 1 : -1
    } else {
      return aValue < bValue ? 1 : -1
    }
  })
})

// Пагинация
const totalPages = computed(() => Math.ceil(sortedFlights.value.length / pageSize.value))

const displayedFlights = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return sortedFlights.value.slice(start, end)
})

const startItem = computed(() => (currentPage.value - 1) * pageSize.value + 1)
const endItem = computed(() => Math.min(currentPage.value * pageSize.value, sortedFlights.value.length))

const visiblePages = computed(() => {
  const pages = []
  const total = totalPages.value
  const current = currentPage.value

  if (total <= 7) {
    for (let i = 1; i <= total; i++) pages.push(i)
  } else {
    if (current <= 4) {
      for (let i = 1; i <= 5; i++) pages.push(i)
      pages.push('...')
      pages.push(total)
    } else if (current >= total - 3) {
      pages.push(1)
      pages.push('...')
      for (let i = total - 4; i <= total; i++) pages.push(i)
    } else {
      pages.push(1)
      pages.push('...')
      for (let i = current - 1; i <= current + 1; i++) pages.push(i)
      pages.push('...')
      pages.push(total)
    }
  }

  return pages
})

const showEllipsis = computed(() => totalPages.value > 7)

// Методы
const sortBy = (field) => {
  if (sortField.value === field) {
    sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortField.value = field
    sortDirection.value = 'desc'
  }
  currentPage.value = 1
}

const getSortClass = (field) => {
  if (sortField.value === field) {
    return sortDirection.value === 'asc' ? 'sort-asc' : 'sort-desc'
  }
  return ''
}

const getSortSymbol = (field) => {
  if (sortField.value !== field) return '↕'
  return sortDirection.value === 'asc' ? '↑' : '↓'
}

const onSearch = () => {
  currentPage.value = 1
}

const clearSearch = () => {
  searchQuery.value = ''
  currentPage.value = 1
}

const applyFilters = () => {
  currentPage.value = 1
}

const resetFilters = () => {
  filters.value = {
    uavType: '',
    region: '',
    period: 'all',
    status: ''
  }
  searchQuery.value = ''
  currentPage.value = 1
}

// Пагинация
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

const goToPage = (page) => {
  if (page !== '...') {
    currentPage.value = page
  }
}

const onPageSizeChange = () => {
  currentPage.value = 1
}

// Действия с рейсами
const viewFlight = (flight) => {
  router.push(`/flight/${flight.sid}`)
}

const showOnMap = (flight) => {
  // Реализация показа на карте
  console.log('Показать на карте:', flight)
}

const exportToCSV = () => {
  // Реализация экспорта в CSV
  console.log('Экспорт в CSV')
}

// Вспомогательные функции
const formatDate = (dateString) => {
  return new Date(dateString).toLocaleDateString('ru-RU')
}

const formatDuration = (minutes) => {
  const days = Math.floor(minutes / 1440)
  const hours = Math.floor((minutes % 1440) / 60)
  const mins = minutes % 60
  if (days > 0) return `${days}д ${hours}ч`
  return `${hours}ч ${mins}м`
}

const getRegionName = (regionId) => {
  const regionMap = {
    11: 'ДВФО',
    77: 'Москва',
    78: 'СПб',
  }
  return regionMap[regionId] || `Регион ${regionId}`
}

const getDurationPercentage = (duration) => {
  const maxDuration = Math.max(...flights.value.map(f => f.duration_min))
  return (duration / maxDuration) * 100
}

// Демо-данные
const generateDemoData = () => {
  const types = ['BLA', 'DJI Mavic', 'Orlan-10', 'Zala 421']
  const operators = ['Иванов А.С.', 'Петров В.И.', 'Сидоров М.К.', null]
  const regions = [11, 77, 78]

  return Array.from({ length: 150 }, (_, i) => ({
    sid: `FL${String(i + 1).padStart(6, '0')}`,
    uav_type: types[Math.floor(Math.random() * types.length)],
    operator: operators[Math.floor(Math.random() * operators.length)],
    center_name: ['Хабаровский', 'Московский', 'Петербургский'][Math.floor(Math.random() * 3)],
    dep: {
      date: `2024-${String(Math.floor(Math.random() * 12) + 1).padStart(2, '0')}-${String(Math.floor(Math.random() * 28) + 1).padStart(2, '0')}`,
      time_hhmm: `${String(Math.floor(Math.random() * 24)).padStart(2, '0')}:${String(Math.floor(Math.random() * 60)).padStart(2, '0')}`,
      lat: 45 + Math.random() * 10,
      lon: 130 + Math.random() * 20
    },
    arr: {
      date: `2024-${String(Math.floor(Math.random() * 12) + 1).padStart(2, '0')}-${String(Math.floor(Math.random() * 28) + 1).padStart(2, '0')}`,
      time_hhmm: `${String(Math.floor(Math.random() * 24)).padStart(2, '0')}:${String(Math.floor(Math.random() * 60)).padStart(2, '0')}`,
      lat: 45 + Math.random() * 10,
      lon: 130 + Math.random() * 20
    },
    duration_min: Math.floor(Math.random() * 1000) + 60,
    region: regions[Math.floor(Math.random() * regions.length)]
  }))
}

// Наблюдатели
watch([sortField, sortDirection], () => {
  currentPage.value = 1
})
</script>

<style scoped>
.history-page {
  @apply min-h-screen bg-gray-50 p-6;
}

.page-header {
  @apply flex justify-between items-start mb-6;
}

.header-content h1 {
  @apply text-3xl font-bold text-gray-900 mb-2;
}

.header-content p {
  @apply text-gray-600;
}

.header-stats {
  @apply flex gap-4;
}

.stat-card {
  @apply flex items-center gap-3 p-4 bg-white rounded-lg shadow-sm border border-gray-200;
}

.stat-icon {
  @apply p-2 bg-blue-100 rounded-lg text-blue-600;
}

.stat-value {
  @apply text-2xl font-bold text-gray-900 block;
}

.stat-label {
  @apply text-sm text-gray-600;
}

.control-panel {
  @apply bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6;
}

.search-section {
  @apply mb-4;
}

.search-box {
  @apply relative max-w-md;
}

.search-icon {
  @apply absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400;
}

.search-input {
  @apply w-full pl-10 pr-10 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent;
}

.clear-search {
  @apply absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600;
}

.filters-section {
  @apply flex items-center gap-4 flex-wrap;
}

.filter-group {
  @apply flex items-center gap-2;
}

.filter-label {
  @apply text-sm font-medium text-gray-700 whitespace-nowrap;
}

.filter-select {
  @apply px-3 py-1 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent;
}

.reset-filters-btn {
  @apply flex items-center gap-2 px-3 py-1 text-sm text-gray-600 hover:text-gray-900 transition-colors;
}

.table-container {
  @apply bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden;
}

.table-header {
  @apply p-4 border-b border-gray-200;
}

.table-actions {
  @apply flex justify-between items-center;
}

.action-btn {
  @apply flex items-center gap-2 px-3 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors text-sm;
}

.records-info {
  @apply text-sm text-gray-600;
}

.table-wrapper {
  @apply overflow-x-auto;
}

.flights-table {
  @apply w-full border-collapse;
}

.flights-table th {
  @apply bg-gray-50 px-4 py-3 text-left text-sm font-semibold text-gray-900 border-b border-gray-200;
}

.flights-table td {
  @apply px-4 py-3 border-b border-gray-200;
}

.sortable {
  @apply cursor-pointer hover:bg-gray-100 transition-colors;
}

.th-content {
  @apply flex items-center gap-2;
}

.sort-indicator {
  @apply text-gray-400;
}

.sort-asc {
  @apply text-blue-600;
}

.sort-desc {
  @apply text-blue-600;
}

.flight-row {
  @apply hover:bg-gray-50 transition-colors;
}

.flight-id .id-text {
  @apply font-mono text-sm text-gray-900;
}

.uav-type-badge {
  @apply inline-flex px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded-full;
}

.date-time .date {
  @apply text-sm text-gray-900;
}

.date-time .time {
  @apply text-xs text-gray-500;
}

.duration-cell {
  @apply flex items-center gap-3;
}

.duration-value {
  @apply text-sm text-gray-900 whitespace-nowrap;
}

.duration-bar {
  @apply flex-1 h-2 bg-gray-200 rounded-full overflow-hidden;
}

.duration-fill {
  @apply h-full bg-gradient-to-r from-green-400 to-blue-500 rounded-full;
}

.region-badge {
  @apply inline-flex px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded-full;
}

.operator {
  @apply text-sm text-gray-900;
}

.action-buttons {
  @apply flex gap-2;
}

.btn-view, .btn-map {
  @apply p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors;
}

.loading-state {
  @apply flex items-center justify-center gap-3 py-12;
}

.loading-spinner {
  @apply w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin;
}

.empty-state {
  @apply flex flex-col items-center justify-center py-12 text-center;
}

.empty-icon {
  @apply w-16 h-16 text-gray-300 mb-4;
}

.empty-state h3 {
  @apply text-lg font-semibold text-gray-900 mb-2;
}

.empty-state p {
  @apply text-gray-600;
}

.pagination {
  @apply flex justify-between items-center p-4 border-t border-gray-200;
}

.pagination-info {
  @apply text-sm text-gray-600;
}

.pagination-controls {
  @apply flex items-center gap-2;
}

.pagination-btn {
  @apply p-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed;
}

.page-numbers {
  @apply flex items-center gap-1;
}

.page-btn {
  @apply w-8 h-8 border border-gray-300 rounded-lg text-sm hover:bg-gray-50;
}

.page-btn.active {
  @apply bg-blue-500 text-white border-blue-500;
}

.page-ellipsis {
  @apply px-2 text-gray-500;
}

.page-size-selector {
  @apply flex items-center gap-2;
}

.page-size-select {
  @apply px-2 py-1 border border-gray-300 rounded-lg text-sm;
}

/* Адаптивность */
@media (max-width: 1024px) {
  .page-header {
    @apply flex-col gap-4;
  }

  .filters-section {
    @apply grid grid-cols-2 gap-3;
  }

  .filter-group {
    @apply flex-col items-stretch;
  }
}

@media (max-width: 768px) {
  .pagination {
    @apply flex-col gap-4;
  }

  .table-actions {
    @apply flex-col gap-3 items-stretch;
  }

  .flights-table {
    @apply text-xs;
  }

  .flights-table th,
  .flights-table td {
    @apply px-2 py-2;
  }
}
</style>