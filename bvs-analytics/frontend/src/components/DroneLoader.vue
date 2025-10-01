<template>
  <div v-if="loading" class="loader-overlay">
    <div class="loader-container">
      <!-- Анимированный дрон -->
      <div class="drone">
        <div class="drone-body">
          <div class="propeller propeller-left">
            <div class="blade"></div>
          </div>
          <div class="propeller propeller-right">
            <div class="blade"></div>
          </div>
          <div class="camera"></div>
        </div>
        <div class="landing-skid left"></div>
        <div class="landing-skid right"></div>
      </div>

      <!-- Круг локатора -->
      <div class="radar">
        <div class="radar-circle">
          <div class="radar-sweep"></div>
        </div>
      </div>

      <!-- Текст загрузки -->
      <div class="loader-text">
        <span class="text">Загрузка данных полетов</span>
<!--        <span class="dots">-->
<!--          <span class="dot">.</span>-->
<!--          <span class="dot">.</span>-->
<!--          <span class="dot">.</span>-->
<!--        </span>-->
      </div>

      <!-- Прогресс-бар -->
      <div class="progress-bar">
        <div class="progress-fill" :style="{ width: progress + '%' }"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  loading: {
    type: Boolean,
    default: true
  }
})

const progress = ref(0)
let progressInterval = null

onMounted(() => {
  // Анимация прогресса
  progressInterval = setInterval(() => {
    if (progress.value < 95) {
      progress.value += Math.random() * 15
    }
  }, 300)
})

onUnmounted(() => {
  if (progressInterval) {
    clearInterval(progressInterval)
  }
})
</script>

<style scoped>
.loader-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 9999;
  font-family: 'Arial', sans-serif;
}

.loader-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 40px;
}

/* Стили дрона */
.drone {
  position: relative;
  width: 120px;
  height: 80px;
  animation: float 3s ease-in-out infinite;
}

.drone-body {
  position: relative;
  width: 80px;
  height: 30px;
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
  border-radius: 10px;
  margin: 0 auto;
  box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4);
}

.propeller {
  position: absolute;
  top: -15px;
  width: 25px;
  height: 25px;
  background: #64748b;
  border-radius: 50%;
  display: flex;
  justify-content: center;
  align-items: center;
}

.propeller-left {
  left: -10px;
}

.propeller-right {
  right: -10px;
}

.blade {
  width: 20px;
  height: 4px;
  background: #cbd5e1;
  border-radius: 2px;
  animation: spin 0.8s linear infinite;
}

.camera {
  position: absolute;
  bottom: -8px;
  left: 50%;
  transform: translateX(-50%);
  width: 12px;
  height: 8px;
  background: #1e293b;
  border-radius: 4px;
}

.landing-skid {
  position: absolute;
  bottom: -15px;
  width: 4px;
  height: 15px;
  background: #94a3b8;
  border-radius: 2px;
}

.landing-skid.left {
  left: 25%;
}

.landing-skid.right {
  right: 25%;
}

/* Стили локатора */
.radar {
  position: relative;
  width: 200px;
  height: 200px;
}

.radar-circle {
  width: 100%;
  height: 100%;
  border: 3px solid #3b82f6;
  border-radius: 50%;
  position: relative;
  overflow: hidden;
}

.radar-circle::before {
  content: '';
  position: absolute;
  width: 100%;
  height: 100%;
  border: 1px solid rgba(59, 130, 246, 0.3);
  border-radius: 50%;
  top: 0;
  left: 0;
}

.radar-circle::after {
  content: '';
  position: absolute;
  width: 80%;
  height: 80%;
  border: 1px solid rgba(59, 130, 246, 0.2);
  border-radius: 50%;
  top: 10%;
  left: 10%;
}

.radar-sweep {
  position: absolute;
  width: 50%;
  height: 3px;
  background: linear-gradient(90deg, transparent 0%, #3b82f6 50%, transparent 100%);
  top: 50%;
  left: 50%;
  transform-origin: left center;
  animation: sweep 2s infinite;
  animation-timing-function: linear;
}

/* Текст загрузки */
.loader-text {
  display: flex;
  align-items: center;
  gap: 5px;
  color: #e2e8f0;
  font-size: 18px;
  font-weight: 500;
}

.dots {
  display: inline-flex;
}

.dot {
  animation: bounce 1.4s infinite ease-in-out both;
}

.dot:nth-child(1) { animation-delay: -0.32s; }
.dot:nth-child(2) { animation-delay: -0.16s; }
.dot:nth-child(3) { animation-delay: 0s; }

/* Прогресс-бар */
.progress-bar {
  width: 300px;
  height: 6px;
  background: rgba(59, 130, 246, 0.2);
  border-radius: 3px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #3b82f6 0%, #60a5fa 100%);
  border-radius: 3px;
  transition: width 0.3s ease;
  box-shadow: 0 0 10px rgba(59, 130, 246, 0.6);
}

/* Анимации */
@keyframes float {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-10px); }
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

@keyframes sweep {
  0% { transform: rotate(0deg); }
  50% { transform: rotate(100deg); }
  100% { transform: rotate(360deg); }
}

@keyframes bounce {
  0%, 80%, 100% {
    transform: scale(0);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

/* Адаптивность */
@media (max-width: 768px) {
  .drone {
    transform: scale(0.8);
  }

  .radar {
    width: 150px;
    height: 150px;
  }

  .loader-text {
    font-size: 16px;
  }

  .progress-bar {
    width: 250px;
  }
}
</style>