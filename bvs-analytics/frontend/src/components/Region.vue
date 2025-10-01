<template>
       <DroneLoader :loading="!loaded" />


      <div class="mb-8">
        <h1 class="text-3xl font-bold text-gray-900 mb-2">Аналитика полетов БПЛА - {{r_name}}</h1>
        <p class="text-gray-600">Мониторинг и анализ полетной активности беспилотных летательных аппаратов</p>
      </div>

      <!-- Фильтры - улучшенные -->
      <div class="bg-white p-6 rounded-2xl shadow-lg mb-8 border border-gray-100">
        <div class="flex flex-col sm:flex-row gap-4 items-end">
          <div class="flex-1">
            <label class="block text-sm font-medium text-gray-700 mb-2">Период анализа</label>
            <div class="flex gap-4">
              <div class="flex-1">
                <input type="date" v-model="filters.startDate"
                       class="w-full px-4 py-3 border border-gray-300 rounded-lg ">
              </div>
              <div class="flex-1">
                <input type="date" v-model="filters.endDate"
                       class="w-full px-4 py-3 border border-gray-300 rounded-lg ">
              </div>
            </div>
          </div>
          <div class="flex gap-2">
            <button @click="applyFilters"
                    class="text-white rounded-lg bg-blue-600 px-6 py-3 font-medium">
              Применить
            </button>
            <button @click="resetFilters"
                    class="text-white rounded-lg bg-gray-600 px-6 py-3 font-medium">
              Сбросить
            </button>
          </div>
        </div>
      </div>

  <!-- Карточки с метриками - улучшенные -->
  <div class="grid grid-cols-1 md:grid-cols-5 gap-6 mb-8">
    <!--        bg-gradient-to-br from-blue-500 to-blue-600-->
    <div class="bg-blue-600 text-white p-6 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1">
      <div class="flex items-center justify-between">
        <div>
          <p class="text-blue-100 text-sm font-medium">Всего полетов</p>
          <p class="text-3xl font-bold mt-2">{{ totalFlights.toLocaleString() }}</p>
        </div>
        <div class="bg-blue-400 p-3 rounded-full">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"/>
          </svg>
        </div>
      </div>
    </div>

    <!--        bg-gradient-to-br from-green-500 to-green-600-->
    <div class="bg-green-600 text-white p-6 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1">
      <div class="flex items-center justify-between">
        <div>
          <p class="text-green-100 text-sm font-medium">Общая длительность</p>
          <p class="text-3xl font-bold mt-2">{{ totalDuration.toLocaleString() }}ч</p>
        </div>
        <div class="bg-green-400 p-3 rounded-full">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
          </svg>
        </div>
      </div>
    </div>

    <!--        bg-gradient-to-br from-purple-500 to-purple-600-->
    <div class="bg-purple-600 text-white p-6 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1">
      <div class="flex items-center justify-between">
        <div>
          <p class="text-purple-100 text-sm font-medium">Средняя длительность</p>
          <p class="text-3xl font-bold mt-2">{{ avgDuration }}мин</p>
        </div>
        <div class="bg-purple-400 p-3 rounded-full">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 3.055A9.001 9.001 0 1020.945 13H11V3.055z"/>
          </svg>
        </div>
      </div>
    </div>

    <!--        bg-gradient-to-br from-orange-500 to-orange-600-->
    <div class="bg-orange-600 text-white p-6 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1">
      <div class="flex items-center justify-between">
        <div>
          <p class="text-orange-100 text-sm font-medium">Типы БПЛА</p>
          <p class="text-3xl font-bold mt-2">{{ uniqueUAVTypes }}</p>
        </div>
        <div class="bg-orange-400 p-3 rounded-full">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/>
          </svg>
        </div>
      </div>
    </div>

    <!--        bg-gradient-to-br from-red-500 to-red-600-->
    <div class="bg-red-600 text-white p-6 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1">
      <div class="flex items-center justify-between">
        <div>
          <p class="text-red-100 text-sm font-medium">Ошибок</p>
          <p class="text-3xl font-bold mt-2">{{ flightCenters }}</p>
        </div>
        <div class="bg-red-400 p-3 rounded-full">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/>
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"/>
          </svg>
        </div>
      </div>
    </div>
  </div>
  <div class="bg-white p-6 rounded-2xl shadow-lg mb-8 border border-gray-100">
    <h2 class="text-xl font-semibold mb-4 text-gray-900">Карта полетной активности</h2>
    <RegionMap v-if="loaded" :region-stats="regionStats" @region-click="handleRegionClick"
               :regions="regions" :id="props.id"/>
  </div>


  <div class="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-8">
    <div class="bg-white p-6 rounded-2xl shadow-lg border border-gray-100">
      <LineChart :data="chartData.byHour" title="Активность по времени суток"/>
    </div>
    <div class="bg-white p-6 rounded-2xl shadow-lg border border-gray-100">
      <BarChart :data="chartData.byWeekday" title="Динамика полетов по дням недели"/>
    </div>
    <div class="bg-white p-6 rounded-2xl shadow-lg border border-gray-100">
      <BarChart :data="chartData.byMonth" title="Динамика полетов по месяцам"/>
    </div>
  </div>

  <div class="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8 ">
    <div class="bg-white p-6 rounded-2xl shadow-lg border border-gray-100">
      <DoughnutChart :data="chartData.byType" title="Распределение по типам БПЛА"/>
    </div>
    <div class="bg-white p-6 rounded-2xl shadow-lg border border-gray-100">
      <OperatorsRanking :operators="stats.operators" title="Рейтинг операторов по активности"/>
    </div>
  </div>

  <div>
    <FlightsTopVue :flights="stats.flights" :items-per-page="20"></FlightsTopVue>
  </div>
</template>

<script setup>
import {ref, computed, onMounted} from 'vue'
import BarChart from './Charts/BarChart.vue'
import LineChart from './Charts/LineChart.vue'
import DoughnutChart from './Charts/DoughnutChart.vue'
import OperatorsRanking from './OperatorsRanking.vue'
import DroneLoader from "@/components/DroneLoader.vue";
import RegionMap from "@/components/maps/RegionMap.vue";
import FlightsTopVue from "@/components/FlightsTopVue.vue";

const filters = ref({
  startDate: '2025-01-01',
  endDate: '2025-06-01'
})

onMounted(() => {
  console.log(props.id)
  loadRegions()
})

const loaded = ref(false)

// Вычисляемые метрики
const totalFlights = computed(() => Object.values(regionStats.value).reduce((sum, r) => sum + r.flights, 0))
const totalDuration = computed(() => Object.values(regionStats.value).reduce((sum, r) => sum + r.duration, 0))
const avgDuration = computed(() => Math.round(totalDuration.value / totalFlights.value))
const uniqueUAVTypes = computed(() => Object.keys(stats.value.types || {}).length)
const flightCenters = computed(() => Object.keys(stats.value.operators || {}).length)
const r_name = ref(null)

// Данные для графиков
const chartData = computed(() => ({
  topByCount: {
    labels: Object.values(regionStats.value).sort((a, b) => b.flights - a.flights).map(r => r.name.substring(0, 20)).slice(0, 15),
    datasets: [{
      label: 'Количество полетов',
      data: Object.values(regionStats.value).sort((a, b) => b.flights - a.flights).map(r => r.flights).slice(0, 15),
      backgroundColor: '#3b82f6'
    }]
  },
  topByDuration: {
    labels: Object.values(regionStats.value).sort((a, b) => b.duration - a.duration).map(r => r.name.substring(0, 20)).slice(0, 15),
    datasets: [{
      label: 'Длительность (часы)',
      data: Object.values(regionStats.value).sort((a, b) => b.duration - a.duration).map(r => r.duration).slice(0, 15),
      backgroundColor: '#10b981'
    }]
  },
  byHour: {
    labels: Object.keys(stats.value.times || {}),
    datasets: [{
      label: 'Полетов в час',
      data: Object.values(stats.value.times || {}),
      borderColor: '#8b5cf6',
      tension: 0.1
    }]
  },
  byWeekday: {
    labels: Object.keys(stats.value.weekdays || {}),
    datasets: [{
      label: 'Количество',
      data: Object.values(stats.value.weekdays || {}),
      backgroundColor: '#3b82f6'
    }]
  },
  byMonth: {
    labels: Object.keys(stats.value.months || {}),
    datasets: [{
      label: 'Количество',
      data: Object.values(stats.value.months || {}),
      backgroundColor: '#10b981'
    }]
  },
  byType: {
    labels: Object.keys(stats.value.types || {}),
    datasets: [{
      data: Object.values(stats.value.types || {}),
      backgroundColor: [
        '#3b82f6', '#10b981', '#8b5cf6', '#f59e0b', '#ef4444',
        '#06b6d4', '#84cc16', '#f97316', '#6366f1', '#ec4899'
      ]
    }]
  }
}))

const flightsData = ref({
  meta: {
    source_excel: "2025.xlsx",
    sheet: "Result_1",
    parsed_rows: 76902,
    generated_at: "2025-09-24T07:56:39.645875Z"
  },
  flights: []
})

const regions = ref({})
const stats = ref({
  weekdays: {},
  times: {},
  months: {},
  types: {},
  operators: {}
})

const regionStats = ref({})

const handleRegionClick = (region) => {
  console.log('Выбран регион:', region.properties.name, region.properties.cartodb_id)
}

const props = defineProps({
  id : String
})

const loadRegions = async () => {
  try {

    const response_fl = await fetch('https://imdibil.ru/api/flights_stats/region/'+props.id)
    console.log('https://imdibil.ru/api/flights_stats/region/'+props.id)
    const data_fl = await response_fl.json()
    flightsData.value = data_fl.flights
    regionStats.value = data_fl.regions

    regions.value = data_fl.current
    r_name.value = data_fl.name
    stats.value = {
      weekdays: data_fl.weekdays,
      months: data_fl.month,
      times: data_fl.times,
      types: data_fl.types,
      operators: data_fl.operators,
      flights: data_fl.top,
    }

    loaded.value = true
  } catch (error) {
    console.error('Ошибка загрузки данных:', error)
  }
}

const applyFilters = () => {
  console.log('Фильтры применены:', filters.value)
  // Здесь будет запрос к API с фильтрами
}

const resetFilters = () => {
  filters.value = {
    startDate: '2024-01-01',
    endDate: '2024-01-31'
  }
  console.log('Фильтры сброшены')
}
</script>