<template>
  <div class="ranking-container">
    <h3 class="text-lg font-semibold mb-4 text-gray-900">{{ title }}</h3>
    <div class="space-y-3">
      <div v-for="(operator, index) in sortedOperators" :key="operator.name"
           class="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors duration-200">
        <div class="flex items-center">
          <div class="w-8 h-8 flex items-center justify-center rounded-full"
               :class="getRankColor(index)">
            <span class="text-white font-bold text-sm">{{ index + 1 }}</span>
          </div>
          <div class="ml-3">
            <p class="font-medium text-gray-900">{{ operator.name }}</p>
            <p class="text-sm text-gray-500">{{ operator.flights }} полетов</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  operators: Object,
  title: String
})

const sortedOperators = computed(() => {
  if (!props.operators) return []

  return Object.entries(props.operators)
      .map(([name, data]) => ({
        name,
        flights: data || 0,
      }))
      .sort((a, b) => b.flights - a.flights)
      .slice(0, 5)
})

const getRankColor = (index) => {
  const colors = [
    'bg-gradient-to-r from-yellow-500 to-yellow-600', // 1 место
    'bg-gradient-to-r from-gray-400 to-gray-500',     // 2 место
    'bg-gradient-to-r from-orange-700 to-orange-800', // 3 место
    'bg-blue-400',     // остальные
  ]

  return index < 3 ? colors[index] : colors[3]
}
</script>