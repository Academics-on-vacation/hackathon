<template>
  <div class="radar">
    <div class="radar-circle">
      <div class="radar-sweep"></div>
    </div>
  </div>
</template>

<style scoped>

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