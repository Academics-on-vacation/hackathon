<template>
  <div class="upload-container">
    <!-- Хедер -->
    <div class="upload-header">
      <div class="header-content">
        <h1 class="header-title">Загрузка данных полетов</h1>
        <p class="header-description">Загрузите XLSX файл с телеметрией и данными о полетах</p>
      </div>
    </div>

    <!-- Основная область загрузки -->
    <div class="upload-main">
      <div class="upload-card">
        <!-- Область перетаскивания -->
        <div
            class="drop-zone"
            :class="{
            'drop-zone-active': isDragOver,
            'drop-zone-error': hasError,
            'drop-zone-disabled': isUploading
          }"
            @dragover.prevent="handleDragOver"
            @dragleave.prevent="handleDragLeave"
            @drop.prevent="handleDrop"
            @click="triggerFileInput"
        >
          <div class="drop-zone-content">
            <div class="upload-icon">
              <svg class="w-12 h-12" :class="isUploading ? 'text-gray-300' : 'text-gray-400'" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"/>
              </svg>
            </div>

            <div class="upload-text">
              <template v-if="selectedFile">
                <h3 class="upload-title text-blue-600">{{ selectedFile.name }}</h3>
                <p class="upload-subtitle">{{ formatFileSize(selectedFile.size) }}</p>
              </template>
              <template v-else>
                <h3 class="upload-title">
                  {{ isDragOver ? 'Отпустите файл здесь' : 'Перетащите файл сюда' }}
                </h3>
                <p class="upload-subtitle">или</p>
                <button class="browse-btn" :disabled="isUploading">
                  Выберите файл
                </button>
              </template>
            </div>

            <div class="file-requirements">
              <p class="requirements-text">Поддерживаемые форматы: .xlsx, .xls</p>
              <p class="requirements-text">Максимальный размер: 50MB</p>
            </div>
          </div>

          <input
              ref="fileInput"
              type="file"
              accept=".xlsx,.xls"
              @change="handleFileSelect"
              class="file-input"
              :disabled="isUploading"
          />
        </div>

        <!-- Прогресс загрузки -->
        <div v-if="isUploading" class="upload-progress">
          <div class="progress-header">
            <span class="progress-text">Загрузка файла...</span>
            <span class="progress-percentage">{{ uploadProgress }}%</span>
          </div>
          <div class="progress-bar">
            <div
                class="progress-fill"
                :style="{ width: uploadProgress + '%' }"
            ></div>
          </div>
        </div>

        <!-- Кнопки действий -->
        <div v-if="selectedFile && !isUploading" class="action-buttons">
          <button
              @click="uploadFile"
              class="upload-btn"
          >
            Загрузить файл
          </button>

          <button
              @click="clearFile"
              class="clear-btn"
          >
            Отмена
          </button>
        </div>

        <!-- Сообщения об ошибках -->
        <div v-if="errorMessage" class="error-message">
          <div class="error-icon">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
          </div>
          <span>{{ errorMessage }}</span>
        </div>

        <!-- Успешная загрузка -->
        <div v-if="uploadSuccess" class="success-message">
          <div class="success-icon">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
          </div>
          <div class="success-content">
            <h4>Файл успешно загружен!</h4>
            <p>Данные обрабатываются и скоро будут доступны</p>
          </div>
          <button @click="resetUpload" class="success-action-btn">
            Загрузить другой файл
          </button>
        </div>
      </div>

      <!-- Информационная панель -->
      <div class="info-panel">
        <h3 class="info-title">Требования к файлу</h3>
        <div class="info-content">
          <div class="info-item">
            <div class="info-icon">
              <svg class="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
              </svg>
            </div>
            <div class="info-text">
              <strong>Формат данных:</strong> Excel (.xlsx, .xls)
            </div>
          </div>

          <div class="info-item">
            <div class="info-icon">
              <svg class="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4"/>
              </svg>
            </div>
            <div class="info-text">
              <strong>Структура:</strong> Данные должны быть в первом листе
            </div>
          </div>

          <div class="info-item">
            <div class="info-icon">
              <svg class="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
              </svg>
            </div>
            <div class="info-text">
              <strong>Важно:</strong> Формат данных как в датасете за 2025 год
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- История загрузок -->
<!--    <div class="upload-history">-->
<!--      <div class="section-card">-->
<!--        <div class="section-header">-->
<!--          <h2>История загрузок</h2>-->
<!--          <button @click="refreshHistory" class="refresh-btn" :disabled="isLoadingHistory">-->
<!--            <svg class="w-4 h-4" :class="{'animate-spin': isLoadingHistory}" fill="none" stroke="currentColor" viewBox="0 0 24 24">-->
<!--              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>-->
<!--            </svg>-->
<!--            Обновить-->
<!--          </button>-->
<!--        </div>-->
<!---->
<!--        <div class="history-table-container">-->
<!--          <table class="history-table">-->
<!--            <thead>-->
<!--            <tr>-->
<!--              <th class="text-left">Файл</th>-->
<!--              <th class="text-left">Размер</th>-->
<!--              <th class="text-left">Статус</th>-->
<!--              <th class="text-left">Дата загрузки</th>-->
<!--              <th class="text-left">Записей</th>-->
<!--              <th class="text-right">Действия</th>-->
<!--            </tr>-->
<!--            </thead>-->
<!--            <tbody>-->
<!--            <tr v-if="uploadHistory.length === 0">-->
<!--              <td colspan="6" class="empty-state">-->
<!--                <div class="empty-content">-->
<!--                  <svg class="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">-->
<!--                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>-->
<!--                  </svg>-->
<!--                  <p>Нет данных о загрузках</p>-->
<!--                </div>-->
<!--              </td>-->
<!--            </tr>-->
<!--            <tr v-for="item in uploadHistory" :key="item.id" class="history-row">-->
<!--              <td class="file-cell">-->
<!--                <div class="file-info">-->
<!--                  <div class="file-icon">-->
<!--                    <svg class="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">-->
<!--                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>-->
<!--                    </svg>-->
<!--                  </div>-->
<!--                  <div class="file-details">-->
<!--                    <div class="file-name">{{ item.fileName }}</div>-->
<!--                    <div class="file-type">{{ item.fileType }}</div>-->
<!--                  </div>-->
<!--                </div>-->
<!--              </td>-->
<!--              <td class="size-cell">-->
<!--                {{ formatFileSize(item.fileSize) }}-->
<!--              </td>-->
<!--              <td class="status-cell">-->
<!--                  <span class="status-badge" :class="`status-${item.status}`">-->
<!--                    {{ getStatusText(item.status) }}-->
<!--                  </span>-->
<!--              </td>-->
<!--              <td class="date-cell">-->
<!--                {{ formatDate(item.uploadDate) }}-->
<!--              </td>-->
<!--              <td class="records-cell">-->
<!--                {{ item.recordsProcessed || 0 }} зап.-->
<!--              </td>-->
<!--              <td class="actions-cell">-->
<!--                <div class="action-buttons">-->
<!--                  <button-->
<!--                      v-if="item.status === 'completed'"-->
<!--                      @click="downloadFile(item.id)"-->
<!--                      class="action-btn download-btn"-->
<!--                      title="Скачать"-->
<!--                  >-->
<!--                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">-->
<!--                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>-->
<!--                    </svg>-->
<!--                  </button>-->
<!--                  <button-->
<!--                      @click="viewDetails(item.id)"-->
<!--                      class="action-btn view-btn"-->
<!--                      title="Подробности"-->
<!--                  >-->
<!--                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">-->
<!--                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>-->
<!--                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>-->
<!--                    </svg>-->
<!--                  </button>-->
<!--                  <button-->
<!--                      @click="deleteFile(item.id)"-->
<!--                      class="action-btn delete-btn"-->
<!--                      title="Удалить"-->
<!--                  >-->
<!--                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">-->
<!--                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>-->
<!--                    </svg>-->
<!--                  </button>-->
<!--                </div>-->
<!--              </td>-->
<!--            </tr>-->
<!--            </tbody>-->
<!--          </table>-->
<!--        </div>-->

        <!-- Пагинация -->
<!--        <div v-if="uploadHistory.length > 0" class="pagination">-->
<!--          <button-->
<!--              @click="prevPage"-->
<!--              :disabled="currentPage === 1"-->
<!--              class="pagination-btn"-->
<!--          >-->
<!--            Назад-->
<!--          </button>-->
<!--          <span class="pagination-info">-->
<!--            Страница {{ currentPage }} из {{ totalPages }}-->
<!--          </span>-->
<!--          <button-->
<!--              @click="nextPage"-->
<!--              :disabled="currentPage === totalPages"-->
<!--              class="pagination-btn"-->
<!--          >-->
<!--            Вперед-->
<!--          </button>-->
<!--        </div>-->
<!--      </div>-->
<!--    </div>-->
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'

// Реактивные данные
const fileInput = ref(null)
const isDragOver = ref(false)
const isUploading = ref(false)
const uploadProgress = ref(0)
const errorMessage = ref('')
const uploadSuccess = ref(false)
const hasError = ref(false)
const isLoadingHistory = ref(false)

const selectedFile = ref(null)
const uploadHistory = ref([])
const currentPage = ref(1)
const itemsPerPage = ref(5)

// Вычисляемые свойства
const totalPages = computed(() => {
  return Math.ceil(uploadHistory.value.length / itemsPerPage.value)
})

// Загрузка истории при монтировании
onMounted(() => {
  loadUploadHistory()
})

// Обработчики событий drag and drop
const handleDragOver = (event) => {
  if (isUploading.value) return
  isDragOver.value = true
  hasError.value = false
}

const handleDragLeave = () => {
  isDragOver.value = false
}

const handleDrop = (event) => {
  if (isUploading.value) return
  isDragOver.value = false
  const files = Array.from(event.dataTransfer.files)
  if (files.length > 0) {
    processFile(files[0])
  }
}

// Обработчик выбора файла через input
const handleFileSelect = (event) => {
  const files = Array.from(event.target.files)
  if (files.length > 0) {
    processFile(files[0])
  }
}

// Триггер клика по скрытому input
const triggerFileInput = () => {
  if (!isUploading.value) {
    fileInput.value?.click()
  }
}

// Обработка выбранного файла
const processFile = (file) => {
  errorMessage.value = ''
  hasError.value = false

  const isValidType = file.name.match(/\.(xlsx|xls)$/i)
  const isValidSize = file.size <= 50 * 1024 * 1024 // 50MB

  if (!isValidType) {
    errorMessage.value = 'Файл имеет неподдерживаемый формат. Используйте .xlsx или .xls'
    hasError.value = true
    return
  }

  if (!isValidSize) {
    errorMessage.value = 'Файл превышает максимальный размер 50MB'
    hasError.value = true
    return
  }

  selectedFile.value = file

  // Очищаем input для возможности повторного выбора того же файла
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}

// Форматирование размера файла
const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// Очистка выбранного файла
const clearFile = () => {
  selectedFile.value = null
  errorMessage.value = ''
  hasError.value = false
}

// Загрузка файла на сервер
const uploadFile = async () => {
  if (!selectedFile.value) return

  isUploading.value = true
  uploadProgress.value = 0
  errorMessage.value = ''
  uploadSuccess.value = false

  try {
    // Имитация прогресса загрузки
    for (let progress = 0; progress <= 100; progress += 10) {
      await new Promise(resolve => setTimeout(resolve, 200))
      uploadProgress.value = progress
    }

    // Здесь будет реальный вызов API для загрузки
    await uploadFileToServer(selectedFile.value)

    uploadSuccess.value = true
    // Добавляем в историю
    addToHistory(selectedFile.value)
    selectedFile.value = null

  } catch (error) {
    errorMessage.value = 'Произошла ошибка при загрузке файла'
    hasError.value = true
  } finally {
    isUploading.value = false
    uploadProgress.value = 0
  }
}

// Функция загрузки на сервер (заглушка)
const uploadFileToServer = async (file) => {
  // Имитация загрузки
  await new Promise(resolve => setTimeout(resolve, 1000))

  // Здесь будет реальный код загрузки
  return { success: true, message: 'File uploaded successfully' }
}

// Сброс состояния загрузки
const resetUpload = () => {
  selectedFile.value = null
  uploadProgress.value = 0
  uploadSuccess.value = false
  errorMessage.value = ''
  hasError.value = false
}

// История загрузок
const loadUploadHistory = async () => {
  isLoadingHistory.value = true
  try {
    // Имитация загрузки истории
    await new Promise(resolve => setTimeout(resolve, 500))

    // Тестовые данные
    uploadHistory.value = [
      {
        id: 1,
        fileName: 'flight_data_2024.xlsx',
        fileType: 'XLSX',
        fileSize: 2457612,
        status: 'completed',
        uploadDate: new Date('2024-01-15T10:30:00'),
        recordsProcessed: 1567
      },
      {
        id: 2,
        fileName: 'telemetry_january.xls',
        fileType: 'XLS',
        fileSize: 1876543,
        status: 'completed',
        uploadDate: new Date('2024-01-10T14:20:00'),
        recordsProcessed: 892
      },
      {
        id: 3,
        fileName: 'uav_data_analysis.xlsx',
        fileType: 'XLSX',
        fileSize: 3456789,
        status: 'processing',
        uploadDate: new Date('2024-01-08T09:15:00'),
        recordsProcessed: 0
      },
      {
        id: 4,
        fileName: 'flight_logs_2023.xlsx',
        fileType: 'XLSX',
        fileSize: 4561234,
        status: 'error',
        uploadDate: new Date('2024-01-05T16:45:00'),
        recordsProcessed: 0
      },
      {
        id: 5,
        fileName: 'drone_metrics.xls',
        fileType: 'XLS',
        fileSize: 1234567,
        status: 'completed',
        uploadDate: new Date('2024-01-02T11:20:00'),
        recordsProcessed: 543
      }
    ]
  } catch (error) {
    console.error('Ошибка загрузки истории:', error)
  } finally {
    isLoadingHistory.value = false
  }
}

const refreshHistory = () => {
  loadUploadHistory()
}

const addToHistory = (file) => {
  const newItem = {
    id: uploadHistory.value.length + 1,
    fileName: file.name,
    fileType: file.name.split('.').pop().toUpperCase(),
    fileSize: file.size,
    status: 'completed',
    uploadDate: new Date(),
    recordsProcessed: Math.floor(Math.random() * 2000) + 500
  }
  uploadHistory.value.unshift(newItem)
}

const getStatusText = (status) => {
  const statusMap = {
    'completed': 'Завершено',
    'processing': 'В обработке',
    'error': 'Ошибка'
  }
  return statusMap[status] || status
}

const formatDate = (date) => {
  return new Date(date).toLocaleDateString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// Действия с файлами
const downloadFile = (id) => {
  console.log('Скачать файл:', id)
}

const viewDetails = (id) => {
  console.log('Просмотр деталей:', id)
}

const deleteFile = (id) => {
  uploadHistory.value = uploadHistory.value.filter(item => item.id !== id)
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
</script>

<style scoped>
/* Стили из предыдущего компонента остаются, добавляем только новые */

.upload-history {
  @apply mt-8;
}

.section-card {
  @apply bg-white rounded-2xl shadow-lg border border-gray-100 p-6;
}

.section-header {
  @apply flex justify-between items-center mb-6;
}

.section-header h2 {
  @apply text-xl font-semibold text-gray-900;
}

.refresh-btn {
  @apply flex items-center gap-2 px-3 py-2 text-gray-600 hover:text-gray-900 transition-colors disabled:opacity-50;
}

.history-table-container {
  @apply overflow-x-auto;
}

.history-table {
  @apply w-full border-collapse;
}

.history-table th {
  @apply px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-b border-gray-200;
}

.history-table td {
  @apply px-4 py-3 border-b border-gray-200;
}

.history-row {
  @apply hover:bg-gray-50 transition-colors;
}

.empty-state {
  @apply text-center py-8;
}

.empty-content {
  @apply flex flex-col items-center gap-2 text-gray-500;
}

/* Стили для ячеек таблицы */
.file-cell {
  @apply min-w-60;
}

.file-info {
  @apply flex items-center gap-3;
}

.file-details {
  @apply min-w-0;
}

.file-name {
  @apply font-medium text-gray-900 truncate;
}

.file-type {
  @apply text-gray-500 text-xs;
}

.size-cell {
  @apply text-gray-600 whitespace-nowrap;
}

.status-cell {
  @apply whitespace-nowrap;
}

.status-badge {
  @apply px-2 py-1 rounded-full text-xs font-medium;
}

.status-completed {
  @apply bg-green-100 text-green-800;
}

.status-processing {
  @apply bg-yellow-100 text-yellow-800;
}

.status-error {
  @apply bg-red-100 text-red-800;
}

.date-cell {
  @apply text-gray-600 whitespace-nowrap;
}

.records-cell {
  @apply text-gray-600 text-center;
}

.actions-cell {
  @apply text-right;
}

.action-buttons {
  @apply flex justify-end gap-1;
}

.action-btn {
  @apply p-1 rounded-lg transition-colors;
}

.download-btn {
  @apply text-blue-600 hover:bg-blue-50;
}

.view-btn {
  @apply text-gray-600 hover:bg-gray-50;
}

.delete-btn {
  @apply text-red-600 hover:bg-red-50;
}

/* Пагинация */
.pagination {
  @apply flex items-center justify-between mt-6 pt-4 border-t border-gray-200;
}

.pagination-btn {
  @apply px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed;
}

.pagination-info {
  @apply text-gray-600 text-sm;
}

/* Анимация */
.animate-spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* Адаптивность */
@media (max-width: 768px) {
  .history-table {
    @apply text-sm;
  }

  .history-table th,
  .history-table td {
    @apply px-2 py-2;
  }

  .file-info {
    @apply flex-col items-start gap-1;
  }

  .action-buttons {
    @apply flex-col gap-0;
  }
}

.upload-container {
  @apply min-h-screen bg-gray-50 p-6;
}

.upload-header {
  @apply mb-8 p-6 bg-white rounded-2xl shadow-lg border border-gray-100;
}

.header-content {
  @apply text-center;
}

.header-title {
  @apply text-3xl font-bold text-gray-900 mb-2;
}

.header-description {
  @apply text-gray-600 text-lg;
}

.upload-main {
  @apply grid grid-cols-1 lg:grid-cols-3 gap-6;
}

.upload-card {
  @apply lg:col-span-2 bg-white rounded-2xl shadow-lg border border-gray-100 p-6;
}

.info-panel {
  @apply bg-white rounded-2xl shadow-lg border border-gray-100 p-6 h-fit;
}

.info-title {
  @apply text-xl font-semibold text-gray-900 mb-4;
}

.info-content {
  @apply space-y-4;
}

.info-item {
  @apply flex items-start gap-3;
}

.info-icon {
  @apply mt-0.5 flex-shrink-0;
}

.info-text {
  @apply text-gray-700 text-sm;
}

/* Drop Zone Styles */
.drop-zone {
  @apply border-2 border-dashed border-gray-300 rounded-2xl p-8 text-center cursor-pointer transition-all duration-200;
}

.drop-zone:hover {
  @apply border-gray-400 bg-gray-50;
}

.drop-zone-active {
  @apply border-blue-500 bg-blue-50;
}

.drop-zone-error {
  @apply border-red-500 bg-red-50;
}

.drop-zone-content {
  @apply flex flex-col items-center justify-center gap-4;
}

.upload-icon {
  @apply text-gray-400;
}

.upload-text {
  @apply space-y-2;
}

.upload-title {
  @apply text-xl font-semibold text-gray-900;
}

.upload-subtitle {
  @apply text-gray-600;
}

.browse-btn {
  @apply px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors font-medium;
}

.file-requirements {
  @apply mt-4 space-y-1;
}

.requirements-text {
  @apply text-gray-500 text-sm;
}

.file-input {
  @apply hidden;
}

/* Progress Bar */
.upload-progress {
  @apply mt-6;
}

.progress-header {
  @apply flex justify-between items-center mb-2;
}

.progress-text {
  @apply text-gray-700 font-medium;
}

.progress-percentage {
  @apply text-blue-600 font-semibold;
}

.progress-bar {
  @apply w-full h-2 bg-gray-200 rounded-full overflow-hidden;
}

.progress-fill {
  @apply h-full bg-blue-500 rounded-full transition-all duration-300;
}

/* Files List */
.files-list {
  @apply mt-6;
}

.files-list-title {
  @apply text-lg font-semibold text-gray-900 mb-4;
}

.files-grid {
  @apply space-y-3;
}

.file-item {
  @apply flex items-center gap-4 p-4 bg-gray-50 rounded-xl border border-gray-200 transition-all duration-200;
}

.file-item-uploading {
  @apply border-blue-200 bg-blue-50;
}

.file-item-success {
  @apply border-green-200 bg-green-50;
}

.file-item-error {
  @apply border-red-200 bg-red-50;
}

.file-icon {
  @apply flex-shrink-0;
}

.file-info {
  @apply flex-1 min-w-0;
}

.file-name {
  @apply font-medium text-gray-900 truncate;
}

.file-size {
  @apply text-gray-500 text-sm mt-1;
}

.file-progress {
  @apply mt-2;
}

.file-progress-bar {
  @apply w-full h-1 bg-gray-200 rounded-full overflow-hidden;
}

.file-progress-fill {
  @apply h-full bg-blue-500 rounded-full transition-all duration-300;
}

.file-error {
  @apply text-red-600 text-sm mt-1;
}

.file-actions {
  @apply flex items-center gap-2;
}

.remove-btn {
  @apply p-1 text-gray-400 hover:text-red-500 transition-colors;
}

.status-icon {
  @apply p-1 rounded-full;
}

.status-icon.success {
  @apply text-green-500;
}

.status-icon.error {
  @apply text-red-500;
}

/* Action Buttons */
.action-buttons {
  @apply flex gap-3 mt-6;
}

.upload-btn {
  @apply flex-1 px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed;
}

.clear-btn {
  @apply px-6 py-3 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed;
}

/* Messages */
.error-message {
  @apply flex items-center gap-3 p-4 bg-red-50 border border-red-200 rounded-xl text-red-700 mt-4;
}

.success-message {
  @apply flex items-center justify-between p-6 bg-green-50 border border-green-200 rounded-xl mt-4;
}

.success-content h4 {
  @apply font-semibold text-green-800 mb-1;
}

.success-content p {
  @apply text-green-700 text-sm;
}

.success-action-btn {
  @apply px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors text-sm font-medium;
}

/* Адаптивность */
@media (max-width: 768px) {
  .upload-main {
    @apply grid-cols-1;
  }

  .action-buttons {
    @apply flex-col;
  }

  .success-message {
    @apply flex-col items-stretch gap-4;
  }

  .file-item {
    @apply flex-col items-stretch gap-3;
  }
}
</style>