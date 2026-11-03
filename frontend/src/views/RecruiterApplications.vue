<template>
  <div class="wrap">
    <!-- Header -->
    <header class="header">
      <div>
        <h2>Postulaciones · Vacante #{{ id }}</h2>
        <small class="muted">Candidatos, CVs y resultados de evaluación</small>
      </div>
      <div class="actions">
        <button class="btn" @click="goBack">← Volver</button>
        <button class="btn ghost" @click="load" :disabled="loading">↻ Refrescar</button>
        <button class="btn" @click="exportCSV" :disabled="loading || postulaciones.length===0">⬇︎ Exportar CSV</button>
      </div>
    </header>

    <div v-if="error" class="alert error">{{ error }}</div>

    <div class="card">
      <div class="tools">
        <input v-model="q" placeholder="Buscar por nombre/correo/estado…" @keyup.enter="load" />
        <button class="btn ghost" @click="load" :disabled="loading">Buscar</button>
      </div>

      <div v-if="loading" class="skeleton">Cargando postulaciones…</div>

      <div v-else>
        <pre v-if="postulaciones.length===0" style="color:#333; background:#f5f5f5; padding:10px;">
No se encontraron postulaciones. Datos crudos: {{ postulaciones }}
        </pre>

        <table v-if="postulaciones.length>0" class="table">
          <thead>
            <tr>
              <th>#</th>
              <th>Candidato</th>
              <th>Correo</th>
              <th>CV</th>
              <th>LinkedIn</th>
              <th>Portafolio</th>
              <th>Estado</th>
              <th>Puntaje</th>
              <th>Nivel</th>
              <th>Fecha eval.</th>
              <th>Reporte</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(p, i) in filtered" :key="p.postulacion_id">
              <td>{{ i + 1 }}</td>
              <td>{{ p.nombre || '—' }}</td>
              <td><a :href="`mailto:${p.correo}`">{{ p.correo || '—' }}</a></td>

              <td class="nowrap">
                <button v-if="p.cv_url" class="link" @click="downloadAuthenticated(p.cv_url)">Ver</button>
                <span v-else>—</span>
                <span v-if="p.cv_url">&nbsp;|&nbsp;</span>
                <button
                  v-if="p.candidato_id"
                  class="link btn-link"
                  :disabled="p.downloadingCV"
                  @click="downloadCV(p)"
                >
                  {{ p.downloadingCV ? 'Descargando…' : 'Descargar' }}
                </button>
              </td>

              <td>
                <a v-if="p.linkedin" class="link" :href="abs(p.linkedin)" target="_blank" rel="noopener">Abrir</a>
                <span v-else>—</span>
              </td>
              <td>
                <a v-if="p.portafolio" class="link" :href="abs(p.portafolio)" target="_blank" rel="noopener">Abrir</a>
                <span v-else>—</span>
              </td>

              <td><span :class="badge(p.estado_postulacion)">{{ p.estado_postulacion }}</span></td>
              <td>{{ p.puntaje ?? '—' }}</td>
              <td><span :class="nivelBadge(p.nivel)">{{ p.nivel || '—' }}</span></td>
              <td>{{ fmtDate(p.fecha_evaluacion) }}</td>

              <td class="nowrap">
                <button
                  v-if="p.postulacion_id && !p.no_permiso"
                  class="link btn-link"
                  :disabled="p.downloadingEval"
                  @click="viewReporte(p)"
                >
                  {{ p.downloadingEval ? 'Cargando…' : 'Ver PDF' }}
                </button>
                <span v-else>—</span>
              </td>

              <!-- Acciones -->
              <td class="nowrap">
                <button class="btn-small green" @click="cambiarEstado(p, 'aceptado')" :disabled="p.loadingAccion">Aceptar</button>
                <button class="btn-small red" @click="cambiarEstado(p, 'rechazado')" :disabled="p.loadingAccion">Rechazar</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import api, { API_BASE, downloadAuthenticated } from '../utils/api'

const route = useRoute()
const router = useRouter()
const id = route.params.id

const postulaciones = ref([])
const q = ref('')
const loading = ref(false)
const error = ref(null)

const abs = (u) => !u ? '' : (u.startsWith('http') ? u : `${API_BASE}${u.startsWith('/') ? u : `/${u}`}`)
const badge = (s) => ({ badge: true, green: s==='evaluado'||s==='aceptado', red: s==='rechazado', yellow: s==='pendiente' })
const nivelBadge = (n) => ({ badge: true, green: n==='alto', yellow: n==='medio', red: n==='bajo' })
const fmtDate = (d) => d ? new Date(d).toLocaleString() : '—'

const filtered = computed(() => {
  if (!q.value) return postulaciones.value
  const s = q.value.toLowerCase()
  return postulaciones.value.filter(p =>
    (p.nombre||'').toLowerCase().includes(s) ||
    (p.correo||'').toLowerCase().includes(s) ||
    (p.estado_postulacion||'').toLowerCase().includes(s) ||
    (p.nivel||'').toLowerCase().includes(s)
  )
})

const load = async () => {
  loading.value = true
  error.value = null
  try {
    if (!id) throw new Error('ID de vacante no definido')
    const { data } = await api.get(`/reclutador/vacantes/${id}/postulaciones`)
    postulaciones.value = (data.data || []).map(p => ({
      ...p,
      no_permiso: false,
      downloadingCV: false,
      downloadingEval: false,
      loadingAccion: false
    }))
  } catch (e) {
    error.value = e?.response?.data?.detail || e.message || 'No se pudieron cargar las postulaciones'
  } finally { loading.value = false }
}

const downloadCV = async (p) => {
  try {
    p.downloadingCV = true
    const res = await api.get(`/reclutador/candidatos/${p.candidato_id}/cv/download`, { responseType: 'blob' })
    const blobUrl = URL.createObjectURL(new Blob([res.data]))
    window.open(blobUrl, '_blank')
  } catch (e) {
    alert(e?.response?.data?.detail || e.message || 'No se pudo abrir el CV')
  } finally { p.downloadingCV = false }
}

const viewReporte = async (p) => {
  try {
    p.downloadingEval = true
    const res = await api.get(`/reclutador/postulaciones/${p.postulacion_id}/evaluacion/pdf`, { responseType: 'blob' })
    const blobUrl = URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }))
    window.open(blobUrl, '_blank')
  } catch (e) {
    if (e.response?.status === 403) p.no_permiso = true
    alert(e?.response?.data?.detail || e.message || 'No se pudo abrir el PDF')
  } finally { p.downloadingEval = false }
}

const cambiarEstado = async (p, estado) => {
  try {
    p.loadingAccion = true
    const { data } = await api.post(`/reclutador/postulaciones/${p.postulacion_id}/estado`, { estado })
    p.estado_postulacion = estado
    alert(data.message || `Estado cambiado a ${estado}`)
  } catch (e) {
    alert(e?.response?.data?.detail || 'No se pudo cambiar el estado')
  } finally { p.loadingAccion = false }
}

const goBack = () => router.push('/reclutador')

const exportCSV = () => {
  const rows = [
    ['postulacion_id','vacante_id','nombre','correo','estado','puntaje','nivel','fecha_evaluacion','cv_url','linkedin','portafolio'],
    ...filtered.value.map(p => [
      p.postulacion_id, p.vacante_id, p.nombre||'', p.correo||'', p.estado_postulacion||'',
      p.puntaje ?? '', p.nivel || '', p.fecha_evaluacion || '', p.cv_url || '', p.linkedin || '', p.portafolio || ''
    ])
  ]
  const csv = rows.map(r => r.map(x => `"${String(x).replace(/"/g,'""')}"`).join(',')).join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `postulaciones_vacante_${id}.csv`
  a.click()
  URL.revokeObjectURL(url)
}

onMounted(load)
</script>

<style scoped>
.wrap { padding: 20px; max-width: 1200px; margin: auto; display: grid; gap: 16px; }
.header { display:flex; justify-content:space-between; align-items:center; }
.muted { color:#666; font-size:0.9rem; }
.actions { display:flex; gap:8px; }
.btn { padding:8px 12px; border-radius:8px; border:1px solid #cbd5e1; background:#0b4aa6; color:#fff; font-weight:600; cursor:pointer; }
.btn.ghost { background:#fff; color:#0b4aa6; }
.card { background:#fff; border:1px solid #e2e8f0; border-radius:12px; padding:12px; }
.tools { display:flex; gap:8px; margin-bottom:8px; }
.tools input { padding:8px 10px; border:1px solid #d1d5db; border-radius:8px; min-width: 260px; }
.table { width:100%; border-collapse: collapse; }
.table th, .table td { border:1px solid #edf2f7; padding:8px; text-align:left; }
.table th { background:#f8fafc; }
.skeleton { background:#e5e7eb; height:42px; border-radius:8px; animation:pulse 1.2s infinite; display:flex; align-items:center; padding:0 10px; }
@keyframes pulse { 0%{opacity:1} 50%{opacity:.45} 100%{opacity:1} }
.badge { padding:2px 8px; border-radius:999px; font-size:12px; border:1px solid #eee; }
.badge.green { background:#e9f9ef; color:#167c3b; border-color:#bfe8cf; }
.badge.yellow { background:#fff6e5; color:#9a6b00; border-color:#ffe0a8; }
.badge.red { background:#ffefef; color:#9c2929; border-color:#ffc7c7; }
.link { color:#0b4aa6; text-decoration: underline; }
.btn-link { background: none; border: none; color: #0b4aa6; text-decoration: underline; cursor: pointer; padding: 0; }
.nowrap { white-space: nowrap; }
.alert { padding:10px 12px; border-radius:8px; }
.alert.error { background:#feecec; color:#b42318; border:1px solid #f8c7c4; }
.btn-small { padding:4px 8px; border:none; border-radius:6px; cursor:pointer; font-size:0.8rem; transition: all 0.2s; }
.btn-small.green { background:#2ecc71; color:#fff; }
.btn-small.red { background:#e74c3c; color:#fff; }
.btn-small.yellow { background:#f1c40f; color:#fff; }
.btn-small.green:hover { background:#27ae60; }
.btn-small.red:hover { background:#c0392b; }
.btn-small.yellow:hover { background:#d4ac0d; }
</style>
