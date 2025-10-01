<template>
  <div id="app">
    <!-- Layout with sidebar for authenticated routes -->
    <div v-if="showLayout" class="flex h-screen bg-gray-50">
      <!-- Боковое меню -->
      <aside class="w-64 bg-gradient-to-b from-blue-800 to-blue-900 text-white shadow-xl">
        <div class="p-6 border-b border-blue-700">
          <h2 class="text-xl font-bold">Аналитика БПЛА</h2>
          <!-- User info -->
          <div v-if="user" class="mt-3 flex items-center gap-2 text-sm text-blue-200">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
            </svg>
            <span>{{ user.email || user.name }}</span>
          </div>
        </div>
        <nav class="mt-6">
          <ul class="space-y-1 px-3">
            <li>
              <router-link to="/" class="flex items-center px-4 py-3 rounded-lg hover:bg-blue-700 transition-all duration-200"
                           active-class="bg-blue-700 text-white shadow-sm">
                <svg class="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/>
                </svg>
                Дашборд
              </router-link>
            </li>
            <li>
              <a href="#" class="flex items-center px-4 py-3 rounded-lg hover:bg-blue-700 transition-all duration-200">
                <svg class="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M9 19l3 3m0 0l3-3m-3 3V10"/>
                </svg>
                Загрузка данных
              </a>
            </li>
            <li>
              <router-link to="/history" class="flex items-center px-4 py-3 rounded-lg hover:bg-blue-700 transition-all duration-200"
                           active-class="bg-blue-700 text-white shadow-sm">
                <svg class="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
                </svg>
                История
              </router-link>
            </li>
          </ul>

          <!-- Logout button at bottom -->
          <div class="bottom-0 left-0 right-0 p-3 border-t border-blue-700">
            <button @click="handleLogout"
                    class="flex items-center w-full px-4 py-3 rounded-lg hover:bg-blue-700 transition-all duration-200 text-left">
              <svg class="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/>
              </svg>
              Выход
            </button>
          </div>
        </nav>
      </aside>

      <!-- Основная область с sidebar -->
      <main class="flex-1 overflow-y-auto p-8">
        <router-view />
      </main>
    </div>

    <!-- Full-width layout for login and other public pages -->
    <div v-else>
      <router-view />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuth } from '@/stores/authStore'

const router = useRouter()
const route = useRoute()
const { logout, user: authUser } = useAuth()

const user = computed(() => authUser.value)

// Show sidebar layout only for authenticated routes
const showLayout = computed(() => {
  // Hide layout for login and other public routes
  return route.meta.requiresAuth !== false
})

const handleLogout = () => {
  logout()
  router.push('/login')
}
</script>