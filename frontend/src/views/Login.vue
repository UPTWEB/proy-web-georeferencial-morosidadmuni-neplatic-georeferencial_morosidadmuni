<template>
  <div class="login-container">
    <div class="login-card">
      <h2>Neplatic</h2>
      <p>Sistema Georeferencial de Morosidad</p>
      <form @submit.prevent="handleLogin">
        <div class="form-group">
          <label for="username">Usuario</label>
          <input type="text" id="username" v-model="username" required autofocus />
        </div>
        <div class="form-group">
          <label for="password">Contraseña</label>
          <input type="password" id="password" v-model="password" required />
        </div>
        <button type="submit" :disabled="loading">
          <span v-if="loading" class="spinner"></span>
          {{ loading ? 'Ingresando...' : 'Ingresar' }}
        </button>
        <div v-if="errorMessage" class="error">{{ errorMessage }}</div>
      </form>
    </div>
  </div>
</template>

<script>
import api from '../api'

export default {
  name: 'Login',
  data() {
    return {
      username: '',
      password: '',
      loading: false,
      errorMessage: ''
    }
  },
  methods: {
    async handleLogin() {
      this.loading = true
      this.errorMessage = ''
      try {
        const response = await api.post('/login', {
          username: this.username,
          password: this.password
        })
        if (response.data && response.data.token) {
          localStorage.setItem('token', response.data.token)
          localStorage.setItem('usuario', JSON.stringify(response.data.usuario))
          window.location.href = '/dashboard'
        } else {
          this.errorMessage = 'Respuesta inválida del servidor'
        }
      } catch (error) {
        console.error(error)
        if (!error.response) {
          this.errorMessage = 'Error de conexión. Verifica que el servidor esté activo.'
        } else if (error.response.status === 401 || error.response.status === 403) {
          this.errorMessage = 'Usuario o contraseña incorrectos, o cuenta inactiva.'
        } else {
          this.errorMessage = error.response?.data?.error || 'Ocurrió un error inesperado al iniciar sesión.'
        }
      } finally {
        this.loading = false
      }
    }
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #1a472a, #0d2818);
}
.login-card {
  background: white;
  padding: 2rem;
  border-radius: 12px;
  box-shadow: 0 10px 25px rgba(0,0,0,0.2);
  width: 100%;
  max-width: 400px;
  text-align: center;
}
.login-card h2 {
  color: #1a472a;
  margin-bottom: 0.5rem;
}
.login-card p {
  color: #666;
  margin-bottom: 1.5rem;
}
.form-group {
  margin-bottom: 1rem;
  text-align: left;
}
.form-group label {
  display: block;
  margin-bottom: 0.25rem;
  font-weight: 500;
  color: #333;
}
.form-group input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 1rem;
  transition: border-color 0.3s;
}
.form-group input:focus {
  outline: none;
  border-color: #1a472a;
}
button {
  width: 100%;
  padding: 0.75rem;
  background: #1a472a;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 1rem;
  cursor: pointer;
  transition: background 0.3s;
}
button:hover:not(:disabled) {
  background: #0d2818;
}
button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}
.error {
  margin-top: 1rem;
  color: #d32f2f;
  font-size: 0.875rem;
  background: #fde7e9;
  padding: 0.5rem;
  border-radius: 4px;
}
.spinner {
  display: inline-block;
  width: 12px;
  height: 12px;
  border: 2px solid rgba(255,255,255,0.3);
  border-radius: 50%;
  border-top-color: white;
  animation: spin 1s ease-in-out infinite;
  margin-right: 0.5rem;
  vertical-align: middle;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>