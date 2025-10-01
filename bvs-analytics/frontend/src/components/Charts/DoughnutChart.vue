<template>
  <div className="chart-container">
    <h3 className="text-lg font-semibold mb-4 text-gray-900">{{ title }}</h3>
    <div className="relative h-80">
      <canvas ref="chartCanvas"></canvas>
    </div>
  </div>
</template>

<script setup>
import {ref, onMounted, watch} from 'vue'
import Chart from 'chart.js/auto'

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
      type: 'doughnut',
      data: props.data,
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'right',
            labels: {
              boxWidth: 12,
              padding: 15
            }
          }
        },
        cutout: '60%'
      }
    })
  }
}

onMounted(initChart)
watch(() => props.data, initChart, {deep: true})
</script>