// API Helper with automatic token injection
import { useAuth } from './stores/authStore'

const API_BASE_URL = 'https://imdibil.ru/api'

export async function apiRequest(endpoint, options = {}) {
    const { getToken } = useAuth()
    const token = getToken()

    const headers = {
        'Content-Type': 'application/json',
        ...options.headers,
    }

    // Add authorization header if token exists
    if (token) {
        headers['Authorization'] = `Bearer ${token}`
    }

    const config = {
        ...options,
        headers,
    }

    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, config)

        // Handle 401 Unauthorized - token expired or invalid
        if (response.status === 401) {
            const { logout } = useAuth()
            logout()
            window.location.href = '/login'
            throw new Error('Unauthorized')
        }

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`)
        }

        return await response.json()
    } catch (error) {
        console.error('API Request Error:', error)
        throw error
    }
}

// Convenience methods
export const api = {
    get: (endpoint) => apiRequest(endpoint, { method: 'GET' }),

    post: (endpoint, data) => apiRequest(endpoint, {
        method: 'POST',
        body: JSON.stringify(data),
    }),

    put: (endpoint, data) => apiRequest(endpoint, {
        method: 'PUT',
        body: JSON.stringify(data),
    }),

    delete: (endpoint) => apiRequest(endpoint, { method: 'DELETE' }),
}