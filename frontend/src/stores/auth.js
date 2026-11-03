import { defineStore } from 'pinia'
import api from '../utils/api'
import router from '../router'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    initialized: false,
  }),
  actions: {
    async hydrate() {
      const token = localStorage.getItem('token')
      if (!token) { 
        this.initialized = true
        return
      }
      try {
        const { data } = await api.get('/auth/me')
        if (data?.ok) this.user = data.user
      } catch (e) {
        localStorage.removeItem('token')
      } finally {
        this.initialized = true
      }
    },

    async login(email, password) {
  try {
    // Capturar la respuesta del login
    const { data } = await api.post('/auth/login', { correo: email, contrasena: password })

    // Guardar token en localStorage
    localStorage.setItem('token', data.access_token)

    // Obtener usuario actual
    const me = await api.get('/auth/me')
    this.user = me.data.user

    // Redirigir según rol
    const role = this.user.tipo
    if (role === 'admin') router.push('/admin')
    else if (role === 'reclutador') router.push('/recruiter')
    else router.push('/candidate')

  } catch (e) {
    console.error('Login failed:', e)
    throw new Error(e?.response?.data?.detail || 'Credenciales inválidas')
  }
},
    async register(nombre, email, password) {
      const { data } = await api.post('/auth/register', { nombre, correo: email, contrasena: password })
      return data
    },

    logout() {
      localStorage.removeItem('token')
      this.user = null
      router.push('/login')  // Redirigir a login
    }
  }
})
