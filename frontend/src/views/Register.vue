<template>
  <div class="login-bg">
    <div class="card">
      <div class="brand">
        <div class="logo">📝</div>
        <div class="brand-text">
          <h1 class="title">Crear cuenta en <span>TalentAI</span></h1>
          <p class="subtitle">Regístrate para comenzar</p>
        </div>
      </div>

      <form class="form" @submit.prevent="onSubmit" novalidate>
        <!-- NOMBRE -->
        <label class="sr-only" for="name">Nombre</label>
        <div class="field" :class="{ invalid: nameError }">
          <span class="icon" aria-hidden="true">
            <svg viewBox="0 0 24 24"><path d="M12 12a5 5 0 1 0-5-5 5 5 0 0 0 5 5Zm0 2c-4.42 0-8 2.24-8 5v1h16v-1c0-2.76-3.58-5-8-5Z"/></svg>
          </span>
          <input id="name" ref="nameRef" v-model.trim="nombre" placeholder="Nombre completo" @blur="validateName"/>
          <small v-if="nameError" class="msg-error">{{ nameError }}</small>
        </div>

        <!-- CORREO -->
        <label class="sr-only" for="email">Correo electrónico</label>
        <div class="field" :class="{ invalid: emailError }">
          <span class="icon" aria-hidden="true">
            <svg viewBox="0 0 24 24"><path d="M20 4H4a2 2 0 0 0-2 2v1l10 6 10-6V6a2 2 0 0 0-2-2Z"/><path d="M22 8.24 12 14 2 8.24V18a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2Z"/></svg>
          </span>
          <input id="email" v-model.trim="correo" type="email" placeholder="Correo electrónico" inputmode="email" autocomplete="username" @blur="validateEmail"/>
          <small v-if="emailError" class="msg-error">{{ emailError }}</small>
        </div>

        <!-- CONTRASEÑA -->
        <label class="sr-only" for="password">Contraseña</label>
        <div class="field" :class="{ invalid: passError }">
          <span class="icon" aria-hidden="true">
            <svg viewBox="0 0 24 24"><path d="M17 9h-1V7a4 4 0 0 0-8 0v2H7a2 2 0 0 0-2 2v7a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-7a2 2 0 0 0-2-2Zm-6 7.73V17a1 1 0 0 1 2 0v-.27a1.75 1.75 0 1 1-2 0ZM9 7a3 3 0 0 1 6 0v2H9Z"/></svg>
          </span>
          <input id="password" v-model="contrasena" :type="show ? 'text' : 'password'" placeholder="Contraseña (mín. 6)" autocomplete="new-password" @keyup="onKey" @blur="validatePass"/>
          <button type="button" class="show" @click="show=!show" :aria-label="show ? 'Ocultar contraseña' : 'Mostrar contraseña'">{{ show ? '🙈' : '👁️' }}</button>
          <small v-if="passError || capsOn" class="msg-hint">
            <template v-if="passError">{{ passError }}</template>
            <template v-if="capsOn"> • Mayúsculas activadas</template>
          </small>
        </div>

        <!-- CONFIRMAR -->
        <label class="sr-only" for="confirm">Confirmar contraseña</label>
        <div class="field" :class="{ invalid: confirmError }">
          <span class="icon" aria-hidden="true">
            <svg viewBox="0 0 24 24"><path d="M12 17a1 1 0 0 1-.71-.29l-3-3a1 1 0 0 1 1.42-1.42L12 14.59l2.29-2.3a1 1 0 1 1 1.42 1.42l-3 3A1 1 0 0 1 12 17Z"/><path d="M17 9h-1V7a4 4 0 0 0-8 0v2H7a2 2 0 0 0-2 2v7a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-7a2 2 0 0 0-2-2Z"/></svg>
          </span>
          <input id="confirm" v-model="confirm" :type="show ? 'text' : 'password'" placeholder="Confirmar contraseña" autocomplete="new-password" @blur="validateConfirm"/>
          <small v-if="confirmError" class="msg-error">{{ confirmError }}</small>
        </div>

        <!-- TÉRMINOS -->
        <label class="terms">
          <input type="checkbox" v-model="terms" />
          <span>Acepto los <a class="link" href="#" @click.prevent>términos y condiciones</a></span>
        </label>

        <!-- CTA -->
        <button class="cta" type="submit" :disabled="loading || !terms || hasErrors">
          <span v-if="!loading">Crear cuenta</span>
          <span v-else class="spinner">Creando…</span>
        </button>

        <!-- ERROR -->
        <p v-if="error" class="error" role="alert">{{ error }}</p>

        <!-- ALT -->
        <p class="hint">
          ¿Ya tienes cuenta?
          <RouterLink class="link" to="/login">Inicia sesión</RouterLink>
        </p>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../utils/api'

const router = useRouter()
const nombre = ref('')
const correo = ref('')
const contrasena = ref('')
const confirm = ref('')
const terms = ref(false)
const show = ref(false)
const loading = ref(false)
const error = ref('')
const capsOn = ref(false)

const nameError = ref('')
const emailError = ref('')
const passError = ref('')
const confirmError = ref('')
const nameRef = ref(null)

onMounted(() => nameRef.value?.focus())

// Validaciones
const validateName = () => {
  if (!nombre.value) { nameError.value = ''; return }
  nameError.value = nombre.value.trim().length >= 2 ? '' : 'Ingresa tu nombre'
}
const validateEmail = () => {
  if (!correo.value) { emailError.value = ''; return }
  const ok = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(correo.value)
  emailError.value = ok ? '' : 'Ingresa un correo válido'
}
const validatePass = () => {
  if (!contrasena.value) { passError.value = ''; return }
  passError.value = contrasena.value.length >= 6 ? '' : 'Mínimo 6 caracteres'
}
const validateConfirm = () => {
  if (!confirm.value) { confirmError.value = ''; return }
  confirmError.value = contrasena.value === confirm.value ? '' : 'Las contraseñas no coinciden'
}
const onKey = (e) => { capsOn.value = e.getModifierState && e.getModifierState('CapsLock') }

// Computed para saber si hay errores
const hasErrors = computed(() => {
  return !!(nameError.value || emailError.value || passError.value || confirmError.value)
})

// Submit
const onSubmit = async () => {
  error.value = ''
  validateName(); validateEmail(); validatePass(); validateConfirm()
  if (hasErrors.value || !terms.value) return

  loading.value = true
  try {
    await api.post('/auth/register', { nombre: nombre.value, correo: correo.value, contrasena: contrasena.value })
    localStorage.setItem('remember_email', correo.value)
    router.push('/login')
  } catch (e) {
    error.value = e?.response?.data?.detail || 'No se pudo crear la cuenta'
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
}

.login-bg{ min-height:100vh; display:grid; place-items:center; background: radial-gradient(1200px 600px at 30% -200px, var(--bg1), var(--bg2)); padding: 24px; }
.card{ width: 520px; max-width: calc(100vw - 32px); background: var(--card); -webkit-backdrop-filter: var(--glass); backdrop-filter: var(--glass); border-radius: 18px; box-shadow: 0 24px 46px rgba(2,6,23,.10), 0 2px 8px rgba(2,6,23,.08); padding: 26px 26px 22px; }
.brand{ display:flex; gap:12px; align-items:center; justify-content:center; margin-bottom: 6px; }
.logo{ width: 42px; height: 42px; border-radius: 12px; display:grid; place-items:center; background: #fff; box-shadow: 0 6px 16px rgba(2,6,23,.08); font-size: 20px; }
.brand-text{ text-align:center; }
.title{ margin:0 0 4px; font-size: 28px; color: var(--text); font-weight: 800; line-height: 1.1; }
.title span{ color: var(--primary); }
.subtitle{ margin:0 0 14px; color: var(--muted); font-size: 14px; text-align:center; }
.form{ display:grid; gap: 14px; }
.field{ position: relative; display: grid; }
.field input{ padding: 12px 44px; border: 1px solid #e5e7eb; border-radius: 12px; outline: none; font-size: 14px; transition: box-shadow .15s, border-color .15s, background .15s; background: rgba(255,255,255,.92); }
.field input:focus{ border-color: var(--primary); box-shadow: 0 0 0 4px var(--ring); }
.field.invalid input{ border-color: var(--danger); box-shadow: 0 0 0 4px rgba(180,35,24,.12); }
.icon{ position:absolute; inset: 0 auto 0 12px; display:grid; place-items:center; width: 24px; color:#9ca3af; }
.icon svg{ width:20px; height:20px; fill: currentColor; }
.show{ position:absolute; inset: 0 8px 0 auto; width: 36px; border:0; background:transparent; cursor:pointer; font-size: 16px; }
.msg-error{ color: var(--danger); font-size: 12px; margin-top: 6px; padding-left: 4px; }
.msg-hint{ color: #7a7f87; font-size: 12px; margin-top: 6px; padding-left: 4px; }
.terms{ display:flex; align-items:center; gap:8px; color:#364152; font-size: 13px; margin-top: 2px; }
.cta{ margin-top: 4px; background: var(--primary); color:#0b0000; border: 0; border-radius: 12px; padding: 12px 16px; font-weight: 700; font-size: 14px; box-shadow: 0 10px 26px rgba(11,74,166,.28); transition: transform .05s ease, background .15s ease, box-shadow .15s ease; }
.cta:hover{ background: var(--primary-600); }
.cta:active{ transform: translateY(1px); }
.cta:disabled{ opacity:.6; cursor:not-allowed; }
.hint{ margin-top: 8px; font-size: 13px; color: var(--muted); text-align:center; }
.link{ color: var(--primary); font-weight: 700; text-decoration: none; }
.link:hover{ text-decoration: underline; }
.error{ margin-top: 8px; color: var(--danger); background: var(--danger-bg); border: 1px solid var(--danger-bd); padding: 8px 10px; border-radius: 10px; font-size: 13px; text-align:center; }
.sr-only{ position:absolute !important; height:1px; width:1px; overflow:hidden; clip:rect(1px, 1px, 1px, 1px); white-space: nowrap; }
</style>
