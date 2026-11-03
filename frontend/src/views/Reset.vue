<template>
  <div class="login-bg">
    <div class="card">
      <div class="brand">
        <div class="logo">🔑</div>
        <div class="brand-text">
          <h1 class="title">Recuperar acceso</h1>
          <p class="subtitle">Ingresa tu correo y te enviaremos instrucciones</p>
        </div>
      </div>

      <form class="form" @submit.prevent="onSubmit" novalidate>
        <label class="sr-only" for="email">Correo</label>
        <div class="field" :class="{ invalid: emailError }">
          <span class="icon" aria-hidden="true">
            <svg viewBox="0 0 24 24"><path d="M20 4H4a2 2 0 0 0-2 2v1l10 6 10-6V6a2 2 0 0 0-2-2Z"/><path d="M22 8.24 12 14 2 8.24V18a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2Z"/></svg>
          </span>
          <input id="email" ref="emailRef" v-model.trim="correo" type="email" placeholder="Tu correo" inputmode="email" required @blur="validateEmail"/>
          <small v-if="emailError" class="msg-error">{{ emailError }}</small>
        </div>

        <button class="cta" type="submit" :disabled="loading || !!emailError">
          <span v-if="!loading">Enviar instrucciones</span>
          <span v-else class="spinner">Enviando…</span>
        </button>

        <p v-if="ok" class="ok">Si el correo existe, te enviaremos un enlace para restablecer tu contraseña.</p>
        <p v-if="warning" class="warn">{{ warning }}</p>
        <p v-if="error" class="error" role="alert">{{ error }}</p>

        <p class="hint">
          ¿La recordaste?
          <RouterLink class="link" to="/login">Volver a iniciar sesión</RouterLink>
        </p>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../utils/api'

const correo = ref('')
const loading = ref(false)
const ok = ref(false)
const warning = ref('')
const error = ref('')
const emailError = ref('')
const emailRef = ref(null)

onMounted(() => emailRef.value?.focus())

const validateEmail = () => {
  if (!correo.value) { emailError.value = 'El correo es obligatorio'; return }
  const ok = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(correo.value)
  emailError.value = ok ? '' : 'Ingresa un correo válido'
}

const onSubmit = async () => {
  warning.value = ''; error.value = ''; ok.value = false
  validateEmail()
  if (emailError.value) return
  loading.value = true
  try {
    await api.post('/auth/reset-request', { correo: correo.value })
    ok.value = true
  } catch (e) {
    const status = e?.response?.status
    if (status === 404) {
      // Backend aún no implementado
      warning.value = 'La función de recuperación aún no está disponible. Contacta al administrador o intenta más tarde.'
      ok.value = true
    } else {
      error.value = e?.response?.data?.detail || 'No se pudo procesar la solicitud'
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
:root {
  --bg1: #e0f3ff;
  --bg2: #c2e7ff;
  --card: rgba(255,255,255,.86);
  --glass: blur(10px) saturate(120%);
  --text: #0f172a;
  --muted: #6b7280;
  --primary: #0b4aa6;
  --primary-600: #0a3f8f;
  --ring: rgba(13,110,253,.25);
  --danger: #b42318;
  --danger-bg: #feecec;
  --danger-bd: #f8c7c4;
  --ok-bg: #e9f9ef;
  --ok-bd: #bfe8cf;
  --ok-tx: #167c3b;
  --warn-bg:#fff6e5;
  --warn-bd:#ffe0a8;
  --warn-tx:#9a6b00;
}

.login-bg{ min-height:100vh; display:grid; place-items:center; background: radial-gradient(1200px 600px at 30% -200px, var(--bg1), var(--bg2)); padding: 24px; }
.card{ width: 520px; max-width: calc(100vw - 32px); background: var(--card); -webkit-backdrop-filter: var(--glass); backdrop-filter: var(--glass); border-radius: 18px; box-shadow: 0 24px 46px rgba(2,6,23,.10), 0 2px 8px rgba(2,6,23,.08); padding: 26px 26px 22px; }
.brand{ display:flex; gap:12px; align-items:center; justify-content:center; margin-bottom: 6px; }
.logo{ width: 42px; height: 42px; border-radius: 12px; display:grid; place-items:center; background: #fff; box-shadow: 0 6px 16px rgba(2,6,23,.08); font-size: 20px; }
.brand-text{ text-align:center; }
.title{ margin:0 0 4px; font-size: 26px; color: var(--text); font-weight: 800; line-height: 1.1; }
.title span{ color: var(--primary); }
.subtitle{ margin:0 0 14px; color: var(--muted); font-size: 14px; text-align:center; }
.form{ display:grid; gap: 14px; }
.field{ position: relative; display: grid; }
.field input{ padding: 12px 44px; border: 1px solid #e5e7eb; border-radius: 12px; outline: none; font-size: 14px; transition: box-shadow .15s, border-color .15s, background .15s; background: rgba(255,255,255,.92); }
.field input:focus{ border-color: var(--primary); box-shadow: 0 0 0 4px var(--ring); }
.field.invalid input{ border-color: var(--danger); box-shadow: 0 0 0 4px rgba(180,35,24,.12); }
.icon{ position:absolute; inset: 0 auto 0 12px; display:grid; place-items:center; width: 24px; color:#9ca3af; }
.icon svg{ width:20px; height:20px; fill: currentColor; }
.cta{ margin-top: 4px; background: var(--primary); color:#fff; border: 0; border-radius: 12px; padding: 12px 16px; font-weight: 700; font-size: 14px; box-shadow: 0 10px 26px rgba(11,74,166,.28); transition: transform .05s ease, background .15s ease, box-shadow .15s ease; }
.cta:hover{ background: var(--primary-600); }
.cta:active{ transform: translateY(1px); }
.cta:disabled{ opacity:.6; cursor:not-allowed; }
.hint{ margin-top: 8px; font-size: 13px; color: var(--muted); text-align:center; }
.link{ color: var(--primary); font-weight: 700; text-decoration: none; }
.link:hover{ text-decoration: underline; }
.error{ margin-top: 8px; color: var(--danger); background: var(--danger-bg); border: 1px solid var(--danger-bd); padding: 8px 10px; border-radius: 10px; font-size: 13px; text-align:center; }
.ok{ margin-top: 8px; color: var(--ok-tx); background: var(--ok-bg); border: 1px solid var(--ok-bd); padding: 8px 10px; border-radius: 10px; font-size: 13px; text-align:center; }
.warn{ margin-top: 8px; color: var(--warn-tx); background: var(--warn-bg); border: 1px solid var(--warn-bd); padding: 8px 10px; border-radius: 10px; font-size: 13px; text-align:center; }
.sr-only{ position:absolute !important; height:1px; width:1px; overflow:hidden; clip:rect(1px, 1px, 1px, 1px); white-space: nowrap; }
</style>
