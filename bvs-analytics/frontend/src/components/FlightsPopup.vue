<template>
  <div class="flight-popup-content">
    <h3 class="font-bold text-lg mb-2 text-blue-800">Информация о полете</h3>

    <div v-if="flight" class="space-y-3">
      <!-- Основная информация -->

      <div class="grid grid-cols-2 gap-2 text-sm">
        <span class="text-gray-600">ID:</span>
        <strong class="text-blue-600">{{ flight.sid }}</strong>

        <span class="text-gray-600">Тип БПЛА:</span>
        <strong>{{ flight.uav_type || 'Не указан' }}</strong>

        <span class="text-gray-600">Центр:</span>
        <strong>{{ flight.center_name || 'Не указан' }}</strong>

        <span class="text-gray-600">Дата:</span>
        <strong>{{ flight.dep?.date || 'Нет данных' }}</strong>
      </div>

      <!-- Время полета -->
      <div class="bg-blue-50 p-2 rounded">
        <h4 class="font-semibold text-blue-700 mb-1">Время полета</h4>
        <div class="grid grid-cols-2 gap-1 text-xs">
          <span>Вылет:</span>
          <strong>{{ flight.dep?.time_hhmm || '--:--' }}</strong>
          <span>Прибытие:</span>
          <strong>{{ flight.arr?.time_hhmm || '--:--' }}</strong>
          <span>Длительность:</span>
          <strong>{{ flight.duration_min ? flight.duration_min + ' мин' : 'Не завершен' }}</strong>
        </div>
      </div>

      <!-- Координаты -->
      <div v-if="flight.dep" class="bg-green-50 p-2 rounded">
        <h4 class="font-semibold text-green-700 mb-1">Координаты вылета</h4>
        <div class="text-xs flex flex-row justify-between">
          <div>Ш: {{ flight.dep?.lat != null ? flight.dep.lat.toFixed(2) : '—'  }}°</div>
          <div>Д: {{ flight.dep?.lon != null ? flight.dep.lon.toFixed(2) : '—'  }}°</div>
        </div>
      </div>

      <div v-if="flight.arr && !isCircularFlight" class="bg-orange-50 p-2 rounded">
        <h4 class="font-semibold text-orange-700 mb-1">Координаты прибытия</h4>
        <div class="text-xs">
          <div>Ш: {{ flight.arr.lat != null ? flight.arr.lat.toFixed(4) : '—'  }}°</div>
          <div>Д: {{ flight.arr.lon != null ? flight.arr.lat.toFixed(4): '—'  }}°</div>
        </div>
      </div>

      <!-- Зона полета -->
      <div v-if="flight.shr?.zone_radius_nm" class="bg-purple-50 p-2 rounded">
        <h4 class="font-semibold text-purple-700 mb-1">Зона полета</h4>
        <div class="text-xs">
          <div>Радиус: {{ flight.shr.zone_radius_nm }} мор. миль</div>
          <div v-if="flight.shr.window_start_hhmm">Время: {{ flight.shr.window_start_hhmm }} - {{ flight.shr.window_end_hhmm }}</div>
        </div>
      </div>

      <!-- Дополнительная информация -->
      <div v-if="flight.operator || flight.regs" class="bg-gray-50 p-2 rounded">
        <h4 class="font-semibold text-gray-700 mb-1">Дополнительно</h4>
        <div class="text-xs space-y-1">
          <div v-if="flight.operator">
            <span class="font-medium">Оператор:</span> {{ flight.operator }}
          </div>
          <div v-if="flight.regs && flight.regs.length">
            <span class="font-medium">Регистрации:</span> {{ flight.regs.join(', ') }}
          </div>
        </div>
      </div>
    </div>

    <div v-else class="text-gray-500 text-sm">
      Информация о полете не найдена
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  flight: {
    type: Object,
    default: null
  }
})

const isCircularFlight = computed(() => {
  if (!props.flight || !props.flight.dep || !props.flight.arr) return false
  return props.flight.dep.lat === props.flight.arr.lat &&
      props.flight.dep.lon === props.flight.arr.lon
})
</script>

<style scoped>
.flight-popup-content {
  max-width: 300px;
  max-height: 500px;
  overflow-y: auto;
}

.flight-popup-content::-webkit-scrollbar {
  width: 6px;
}

.flight-popup-content::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.flight-popup-content::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.flight-popup-content::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}
</style>