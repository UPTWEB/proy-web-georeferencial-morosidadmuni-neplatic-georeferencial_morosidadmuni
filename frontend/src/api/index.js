import axios from 'axios'

/**
 * Configuración central de Axios para peticiones HTTP al backend.
 * Define la URL base y se encarga de inyectar los tokens de autenticación
 * de manera automática en cada petición (Interceptors).
 */
const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' }
})

/**
 * Interceptor de Solicitudes (Request Interceptor).
 * Adjunta el JWT guardado en localStorage a la cabecera Authorization 
 * para garantizar el acceso seguro a endpoints protegidos.
 */
api.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

/**
 * Interceptor de Respuestas (Response Interceptor).
 * Captura errores globales. Si el backend devuelve 401 (No autorizado/Token expirado),
 * limpia la sesión local y expulsa al usuario hacia el Login para proteger el sistema.
 */
api.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('usuario')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api