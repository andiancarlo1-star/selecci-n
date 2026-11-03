<template>
  <div class="wrap">
    <!-- Header -->
    <header class="header">
      <div>
        <h2>Panel de Reclutador</h2>
        <small class="muted">Gestiona tus vacantes y postulaciones</small>
      </div>
      <button class="logout-btn" @click="logout" title="Cerrar sesión">⏻</button>
    </header>

    <!-- Alertas -->
    <div v-if="msg" class="alert ok">{{ msg }}</div>
    <div v-if="error" class="alert error">{{ error }}</div> 

    <!-- Crear vacante -->
    <section class="card">
      <h3>Publicar nueva vacante</h3>
      <form @submit.prevent="createVacante" class="form">
        <input v-model="nuevaVacante.titulo" placeholder="Título de la vacante" required />
        <textarea v-model="nuevaVacante.descripcion" placeholder="Descripción de la vacante" rows="4" required></textarea>
        <textarea v-model="nuevaVacante.requisitos" placeholder="Requisitos / habilidades" rows="3"></textarea>
        <input v-model="nuevaVacante.ubicacion" placeholder="Ubicación (ciudad, país)" />
        <select v-model="nuevaVacante.tipo_contrato">
          <option value="">Modalidad</option>
          <option value="presencial">Presencial</option>
          <option value="remoto">Remoto</option>
          <option value="hibrido">Híbrido</option>
        </select>
        <input v-model="nuevaVacante.salario_min" type="number" placeholder="Salario mínimo" />
        <input v-model="nuevaVacante.salario_max" type="number" placeholder="Salario máximo" />
        <button type="submit" class="cta" :disabled="loadingAccion">
          <span v-if="!loadingAccion">Publicar</span>
          <span v-else>Cargando…</span>
        </button>
      </form>
    </section>

    <!-- Mis vacantes -->
    <section class="card">
      <h3>Mis Vacantes</h3>
      <div v-if="loading" class="skeleton">Cargando vacantes…</div>
      <div v-else class="vacantes-list">
        <div v-for="v in vacantes" :key="v.id" class="vacante-card">
          <div class="vacante-header">
            <h4>{{ v.titulo }}</h4>
            <span :class="badge(v.estado)">{{ v.estado }}</span>
          </div>
          <p><strong>Descripción:</strong> {{ v.descripcion }}</p>
          <p v-if="v.requisitos"><strong>Requisitos:</strong> {{ v.requisitos }}</p>
          <p v-if="v.ubicacion"><strong>Ubicación:</strong> {{ v.ubicacion }}</p>
          <p v-if="v.tipo_contrato"><strong>Modalidad:</strong> {{ v.tipo_contrato }}</p>
          <p v-if="v.salario_min || v.salario_max">
            <strong>Salario:</strong> {{ v.salario_min || 0 }} - {{ v.salario_max || 0 }}
          </p>
          <div class="vacante-actions">
            <button v-if="v.estado === 'activa'" class="btn-small red" @click="cerrarVacante(v.id)" :disabled="loadingAccion">Cerrar</button>
            <button v-else class="btn-small green" @click="abrirVacante(v.id)" :disabled="loadingAccion">Abrir</button>
            <button class="btn-small default" @click="verPostulaciones(v.id)">Ver postulaciones</button>
          </div>
        </div>
        <div v-if="vacantes.length===0" class="muted">No tienes vacantes publicadas</div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../utils/api'

const router = useRouter()
const vacantes = ref([])
const nuevaVacante = ref({
  titulo: '',
  descripcion: '',
  requisitos: '',
  ubicacion: '',
  tipo_contrato: '', // <-- backend espera tipo_contrato
  salario_min: '',
  salario_max: ''
})
const loading = ref(false)
const loadingAccion = ref(false)
const msg = ref(null)
const error = ref(null)

// Logout
const logout = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('role')
  router.push('/login')
}

// Badge según estado
const badge = (estado) => ({
  badge: true,
  green: estado === 'activa',
  red: estado === 'cerrada' || estado === 'inactiva',
})

// Cargar vacantes
const loadVacantes = async () => {
  try {
    loading.value = true
    const { data } = await api.get('/reclutador/vacantes')
    vacantes.value = data.vacantes || []
  } catch (e) {
    error.value = e?.response?.data?.detail || 'Error cargando vacantes'
  } finally {
    loading.value = false
  }
}

// Crear vacante
const createVacante = async () => {
  try {
    loadingAccion.value = true
    error.value = null
    msg.value = null
    if (!nuevaVacante.value.titulo || !nuevaVacante.value.descripcion) {
      throw new Error('Completa título y descripción')
    }
    const { data } = await api.post('/reclutador/vacantes', nuevaVacante.value)
    msg.value = data.message || 'Vacante publicada'
    nuevaVacante.value = { titulo:'', descripcion:'', requisitos:'', ubicacion:'', tipo_contrato:'', salario_min:'', salario_max:'' }
    await loadVacantes()
  } catch (e) {
    error.value = e?.response?.data?.detail || 'Error creando vacante'
  } finally {
    loadingAccion.value = false
  }
}

// Abrir/Cerrar vacante
const cerrarVacante = async (id) => {
  try {
    loadingAccion.value = true
    const { data } = await api.post(`/reclutador/vacantes/${id}/cerrar`)
    msg.value = data.message
    await loadVacantes()
  } catch (e) {
    error.value = e?.response?.data?.detail || 'Error cerrando vacante'
  } finally {
    loadingAccion.value = false
  }
}

const abrirVacante = async (id) => {
  try {
    loadingAccion.value = true
    const { data } = await api.post(`/reclutador/vacantes/${id}/abrir`)
    msg.value = data.message
    await loadVacantes()
  } catch (e) {
    error.value = e?.response?.data?.detail || 'Error abriendo vacante'
  } finally {
    loadingAccion.value = false
  }
}

// Ver postulaciones (solo ejemplo)
const verPostulaciones = (id) => {
  router.push(`/reclutador/vacantes/${id}/postulaciones`)
}

// Al montar
onMounted(loadVacantes)
</script>

<style scoped>
.wrap { padding: 20px; max-width: 1200px; margin: auto; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f7f9fc; display: grid; gap: 20px; }
.header { display:flex; justify-content:space-between; align-items:center; }
.header h2 { margin:0; font-size:1.8rem; color:#333; }
.muted { color:#666; font-size:0.9rem; }
.logout-btn { width:42px; height:42px; border-radius:50%; border:none; background-color:#e74c3c; color:#fff; font-size:18px; cursor:pointer; display:flex; align-items:center; justify-content:center; box-shadow:0 2px 6px rgba(0,0,0,0.2); transition: background 0.2s; }
.logout-btn:hover { background-color:#c0392b; }
.card { border-radius:10px; padding:20px; background:#fff; box-shadow:0 2px 10px rgba(0,0,0,0.05); }
.form { display:grid; gap:10px; max-width:500px; }
.form input, .form textarea, .form select { padding:10px 12px; border:1px solid #ccc; border-radius:8px; font-size:0.95rem; }
textarea { resize: vertical; }
.cta { background:#3498db; color:#fff; padding:10px 18px; border-radius:8px; border:none; cursor:pointer; font-weight:500; transition: background 0.2s; }
.cta:hover { background:#2980b9; }
.cta:disabled { opacity:0.6; cursor:not-allowed; }
.vacantes-list { display:grid; gap:15px; margin-top:10px; }
.vacante-card { background:#fff; padding:15px; border-radius:10px; box-shadow:0 2px 6px rgba(0,0,0,0.05); }
.vacante-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:10px; }
.vacante-actions { margin-top:10px; display:flex; gap:6px; flex-wrap:wrap; }
.badge { padding:4px 10px; border-radius:12px; font-size:0.85rem; font-weight:500; text-transform:capitalize; }
.badge.green { background:#27ae60; color:#fff; }
.badge.red { background:#c0392b; color:#fff; }
.btn-small { padding:6px 10px; border:none; border-radius:6px; cursor:pointer; font-size:0.85rem; transition: all 0.2s; }
.btn-small.red { background:#e74c3c; color:#fff; }
.btn-small.green { background:#2ecc71; color:#fff; }
.btn-small.default { background:#3498db; color:#fff; }
.btn-small.red:hover { background:#c0392b; }
.btn-small.green:hover { background:#27ae60; }
.btn-small.default:hover { background:#2980b9; }
.alert { padding:12px 16px; border-radius:8px; font-weight:500; margin-bottom:12px; }
.alert.ok { background:#eafaf1; color:#27ae60; border:1px solid #2ecc71; }
.alert.error { background:#fdecea; color:#c0392b; border:1px solid #e74c3c; }
.skeleton { background:#e1e4e8; border-radius:6px; height:40px; animation:pulse 1.2s infinite; margin:10px 0; }
@keyframes pulse { 0% { opacity:1; } 50% { opacity:0.4; } 100% { opacity:1; } }
</style>
