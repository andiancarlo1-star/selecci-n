<template>
  <div class="login-bg">
    <div class="card">
      <h1 class="title">Bienvenido a <span>TalentAI</span></h1>
      <p class="subtitle">Inicia sesión para continuar</p>

      <form class="form" @submit.prevent="onSubmit">
        <div class="field">
          <span class="icon">
            <svg viewBox="0 0 24 24"><path d="M12 12a5 5 0 1 0-5-5 5 5 0 0 0 5 5Zm0 2c-4.42 0-8 2.24-8 5v1h16v-1c0-2.76-3.58-5-8-5Z"/></svg>
          </span>
          <input
            v-model="correo"
            type="email"
            placeholder="Correo electrónico"
            autocomplete="username"
            required
          />
        </div>

        <div class="field">
          <span class="icon">
            <svg viewBox="0 0 24 24"><path d="M17 9h-1V7a4 4 0 0 0-8 0v2H7a2 2 0 0 0-2 2v7a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-7a2 2 0 0 0-2-2Zm-6 7.73V17a1 1 0 0 1 2 0v-.27a1.75 1.75 0 1 1-2 0ZM9 7a3 3 0 0 1 6 0v2H9Z"/></svg>
          </span>
          <input
            v-model="contrasena"
            :type="show ? 'text' : 'password'"
            placeholder="Contraseña"
            autocomplete="current-password"
            required
          />
          <button type="button" class="show" @click="show=!show">{{ show ? '🔓' : '🔐' }}</button>
        </div>

        <button class="cta" type="submit" :disabled="loading">
          <span v-if="!loading">Iniciar sesión</span>
          <span v-else>Cargando…</span>
        </button>

        <p class="hint">
          ¿No tienes una cuenta?
          <RouterLink class="link" to="/register">Regístrate aquí</RouterLink>
        </p>

        <p v-if="error" class="error">{{ error }}</p>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '../utils/api'

const router = useRouter()
const correo = ref('')
const contrasena = ref('')
const show = ref(false)
const loading = ref(false)
const error = ref('')

const onSubmit = async () => {
  error.value = ''
  loading.value = true
  try {
    const { data } = await api.post('/auth/login', { correo: correo.value, contrasena: contrasena.value })
    localStorage.setItem('token', data.access_token)

    const me = await api.get('/auth/me')
    const user = me.data?.user || me.data
    const role = user?.tipo
    localStorage.setItem('role', role || '')

    if (role === 'admin') router.push('/admin')
    else if (role === 'reclutador') router.push('/recruiter')
    else router.push('/candidate')
  } catch (e) {
    error.value = e?.response?.data?.detail || 'Credenciales inválidas'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
:root {
  --bg1: #e0f3ff;
  --bg2: #c2e7ff;
  --card: #fff;
  --text: #0f172a;
  --muted: #6b7280;
  --primary: #0b4aa6;
  --primary-600: #0a3f8f;
  --ring: rgba(13, 110, 253, .25);
}

.login-bg{
  min-height:100vh;
  display:grid;
  place-items:center;
  background: linear-gradient(135deg, var(--bg1), var(--bg2));
  padding: 20px;
}

.card{
  width: 420px;
  max-width: calc(100vw - 32px);
  background: var(--card);
  border-radius: 16px;
  box-shadow: 0 20px 40px rgba(2,6,23,.08), 0 2px 6px rgba(2,6,23,.1);
  padding: 28px;
}

.title{
  margin:0 0 6px;
  font-size: 28px;
  text-align:center;
  color: var(--text);
  font-weight: 800;
}
.title span{ color: var(--primary); }
.subtitle{
  margin:0 0 18px;
  text-align:center;
  color: var(--muted);
  font-size: 14px;
}

.form{ display:grid; gap: 14px; }

.field{
  position: relative;
  display: grid;
}
.field input{
  padding: 12px 44px;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  outline: none;
  font-size: 14px;
  transition: box-shadow .15s, border-color .15s;
}
.field input:focus{
  border-color: var(--primary);
  box-shadow: 0 0 0 4px var(--ring);
}
.icon{
  position:absolute; inset: 0 auto 0 12px;
  display:grid; place-items:center;
  width: 24px;
  color:#9ca3af;
}
.icon svg{ width:20px; height:20px; fill: currentColor; }
.show{
  position:absolute; inset: 0 8px 0 auto;
  width: 36px; border:0; background:transparent; cursor:pointer;
  font-size: 16px;
}

.cta{
  margin-top: 8px;
  background: var(--primary);
  color:#130e0e;
  border: 0;
  border-radius: 10px;
  padding: 12px 16px;
  font-weight: 700;
  font-size: 14px;
  box-shadow: 0 6px 20px rgba(11,74,166,.25);
}
.cta:hover{ background: var(--primary-600); }
.cta:disabled{ opacity:.6; cursor:not-allowed; }

.hint{
  margin-top: 8px;
  font-size: 13px;
  color: var(--muted);
  text-align:center;
}
.link{ color: var(--primary); font-weight: 700; text-decoration: none; }
.link:hover{ text-decoration: underline; }

.error{
  margin-top: 6px;
  color: #b42318;
  background: #feecec;
  border: 1px solid #f8c7c4;
  padding: 8px 10px;
  border-radius: 8px;
  font-size: 13px;
  text-align:center;
}
</style>
