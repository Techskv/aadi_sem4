import axios from 'axios'

const api = axios.create({
    baseURL: '/api'
})

api.interceptors.request.use((config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
        config.headers.Authorization = `Bearer ${token}`
    }

    if (config.data instanceof FormData) {
        if (config.headers.delete) {
            config.headers.delete('Content-Type')
        } else {
            delete config.headers['Content-Type']
        }
    } else if (!config.headers['Content-Type']) {
        config.headers['Content-Type'] = 'application/json'
    }

    console.log(`[API Request] ${config.method?.toUpperCase()} ${config.url}`)
    return config
}, (error) => {
    return Promise.reject(error)
})

api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            // Token expired or invalid — clear and redirect to login
            const wasLoggedIn = !!localStorage.getItem('access_token')
            localStorage.removeItem('access_token')
            localStorage.removeItem('refresh_token')
            if (wasLoggedIn) {
                // Small delay to let any pending state updates settle
                setTimeout(() => {
                    window.location.href = '/login'
                }, 100)
            }
        }
        console.error('[API Error]', error.response?.status, error.response?.data || error.message)
        return Promise.reject(error)
    }
)

export default api
