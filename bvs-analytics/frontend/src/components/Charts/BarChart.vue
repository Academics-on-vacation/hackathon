<template>
  <div className="bg-white p-4 rounded-lg shadow">
    <h3 className="text-lg font-medium mb-4">{{ title }}</h3>
    <div className="chart-container" style="height: 300px;">
      <canvas ref="chartCanvas"></canvas>
    </div>
  </div>
</template>

<script setup>
import {ref, onMounted, watch, nextTick} from 'vue'
import {Chart, BarController, CategoryScale, LinearScale, BarElement, Tooltip, Legend} from 'chart.js'

// Регистрируем необходимые компоненты Chart.js
Chart.register(BarController, CategoryScale, LinearScale, BarElement, Tooltip, Legend)

const props = defineProps({
  data: Object,
  title: String
})

const chartCanvas = ref(null)
let chartInstance = null

const initChart = () => {
  if (chartInstance) {
    chartInstance.destroy()
  }

  if (chartCanvas.value && props.data) {
    chartInstance = new Chart(chartCanvas.value, {
      type: 'bar',
      data: props.data,
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: true,
            position: 'top'
          }
        },
        scales: {
          y: {
            beginAtZero: true
          }
        }
      }
    })
  }
}

onMounted(() => {
  nextTick(() => {
    initChart()
  })
})

watch(() => props.data, () => {
  nextTick(() => {
    initChart()
  })
}, {deep: true})
</script>