import { ref, computed } from 'vue'

// Auth state
const token = ref(localStorage.getItem('auth_token') || null)
const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))

export function useAuth() {
    const isAuthenticated = computed(() => !!token.value)

    const login = async (credentials) => {
        try {
            // const response = await fetch('https://imdibil.ru/api/auth/login', {
            //     method: 'POST',
            //     headers: {
            //         'Content-Type': 'application/json',
            //     },
            //     body: JSON.stringify(credentials),
            // })
            //
            // if (!response.ok) {
            //     throw new Error('Неверные учетные данные')
            // }
            //
            // const data = await response.json()

            // Store token and user data

            let data = {
                token: "test",
                user: {
                    name: "test",
                    email: "test",
                    role: "admin"
                }
            }

            token.value = data.token
            user.value = data.user

            localStorage.setItem('auth_token', data.token)
            localStorage.setItem('user', JSON.stringify(data.user))

            return { success: true }
        } catch (error) {
            return { success: false, error: error.message }
        }
    }

    const logout = () => {
        token.value = null
        user.value = null
        localStorage.removeItem('auth_token')
        localStorage.removeItem('user')
    }

    const getToken = () => token.value

    const getUser = () => user.value

    return {
        isAuthenticated,
        login,
        logout,
        getToken,
        getUser,
        user: computed(() => user.value)
    }
}