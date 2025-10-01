import { createRouter, createWebHistory } from 'vue-router'
import { useAuth } from '@/stores/authStore'
import Dashboard from "@/components/Dashboard.vue"
import Region from "@/components/Region.vue"
import Flight from "@/components/Flight.vue"
import History from "@/components/History.vue"
import Login from "@/components/Login.vue"

const routes = [
    {
        path: '/login',
        name: 'Login',
        component: Login,
        meta: { requiresAuth: false }
    },
    {
        path: '/',
        name: 'Dashboard',
        component: Dashboard,
        props: true,
        meta: { requiresAuth: true }
    },
    {
        path: '/region/:id',
        name: 'Region',
        component: Region,
        props: true,
        meta: { requiresAuth: true }
    },
    {
        path: '/flight/:id',
        name: 'Flight',
        component: Flight,
        props: true,
        meta: { requiresAuth: true }
    },
    {
        path: '/history',
        name: 'History',
        component: History,
        props: true,
        meta: { requiresAuth: true, requiresRole: "admin" }
    }
]

const router = createRouter({
    history: createWebHistory(),
    routes,
})

// Navigation guard for authentication
router.beforeEach((to, from, next) => {
    const { isAuthenticated } = useAuth()

    // Check if route requires authentication
    if (to.meta.requiresAuth && !isAuthenticated.value) {
        // Redirect to login if not authenticated
        next({ name: 'Login', query: { redirect: to.fullPath } })
    } else if (to.name === 'Login' && isAuthenticated.value) {
        // Redirect to dashboard if already logged in
        next({ name: 'Dashboard' })
    } else {
        next()
    }
})

export default router