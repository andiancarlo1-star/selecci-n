<template>
  <div class="page">
    <!-- Header -->
    <div class="head">
      <div class="left">
        <div class="avatar">{{ initials }}</div>
        <div>
          <h2 class="title">Panel del Candidato</h2>
          <p class="muted">Gestiona tu perfil, CV, vacantes y postulaciones</p>
        </div>
      </div>
      <div class="right">
        <button class="btn ghost" @click="reloadAll" :disabled="loading.any">↻ Refrescar</button>
        <button class="btn logout" @click="logout">Cerrar Sesión</button>
      </div>
    </div>

    <div class="grid">
      <!-- Perfil + CV -->
      <section class="card">
        <h3 class="card-title">Mi Perfil</h3>
        <div class="profile">
          <div class="row">
            <label>Nombre</label><span>{{ me?.nombre || '—' }}</span>
          </div>
          <div class="row">
            <label>Correo</label><span>{{ me?.correo || '—' }}</span>
          </div>
          <div class="row">
            <label>Estado</label>
            <span class="badge" :class="badge(me?.estado)">{{ me?.estado || '—' }}</span>
          </div>
        </div>

        <div class="cv">
          <h4>Mi CV</h4>
          <div class="cv-actions">
            <input ref="fileRef" type="file" accept=".pdf,.doc,.docx" @change="onPick" hidden />
            <button class="btn" @click="pickFile" :disabled="loading.upload">Subir/Actualizar CV</button>
            <button v-if="cvUrl" class="btn link" @click="downloadCv">Ver CV actual</button>
          </div>
          <p class="hint">Formatos permitidos: PDF, DOC, DOCX. Tamaño máximo: 5 MB.</p>
          <p v-if="uploadMsg" class="ok">{{ uploadMsg }}</p>
          <p v-if="uploadErr" class="error">{{ uploadErr }}</p>
        </div>
      </section>

      <!-- Mis Postulaciones -->
      <section class="card">
              <div class="card-head">
                <h3 class="card-title">Mis Postulaciones</h3>
                <div class="tools">
                  <label>Pág.</label>
                  <input type="number" v-model.number="page" min="1" @change="loadPostulaciones" />
                </div>
              </div>

              <div v-if="loading.post" class="skeleton">Cargando postulaciones…</div>

              <div v-else class="table-container">
                <table class="table">
                  <thead>
                    <tr>
                      <th>Vacante</th>
                      <th>Estado</th>
                      <th>Fecha</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="p in postulacionesPag" :key="p.id_vacante + '-' + (p.fecha_postulacion || '')">
                      <td>#{{ p.id_vacante }} - {{ p.titulo || p.vacante || '—' }}</td>
                      <td><span class="badge" :class="badge(p.estado)">{{ p.estado }}</span></td>
                      <td>{{ fmtDate(p.fecha_postulacion) }}</td>
                    </tr>
                    <tr v-if="postulacionesPag.length===0">
                      <td colspan="3" class="muted">Aún no te has postulado.</td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <!-- Paginación -->
              <div class="pagination" v-if="totalPages > 1">
                <button @click="prevPage" :disabled="page === 1">Anterior</button>
                <span>Página {{ page }} de {{ totalPages }}</span>
                <button @click="nextPage" :disabled="page === totalPages">Siguiente</button>
              </div>
            </section>
          
      <!-- Vacantes Disponibles -->
      <section class="card vacancy-section">
            <div class="card-head">
              <h3 class="card-title">Vacantes Disponibles</h3>
              <div class="tools">
                <input v-model="search" placeholder="Buscar…" @keyup.enter="loadVacantes" />
                <select v-model="filtroModalidad">
                  <option value="">Modalidad</option>
                  <option value="presencial">Presencial</option>
                  <option value="hibrido">Híbrido</option>
                  <option value="remoto">Remoto</option>
                </select>
                <button class="btn ghost" @click="loadVacantes" :disabled="loading.vac">Buscar</button>
              </div>
            </div>

            <div v-if="loading.vac" class="skeleton">Cargando vacantes…</div>

            <div v-else class="vacancy-list">
              <article v-for="v in vacantes" :key="v.id" class="vacancy-item">
                <div class="vacancy-content">
                  <span class="vacancy-id">Vacante #{{ v.id }}</span>
                  <h4>{{ v.titulo }}</h4>
                  <div class="vacancy-meta">
                    <span><strong>Ubicación</strong>{{ v.ubicacion || 'No especificada' }}</span>
                    <span><strong>Modalidad</strong>{{ v.tipo_contrato || 'No especificada' }}</span>
                    <span><strong>Postulaciones</strong>{{ v.total_postulaciones ?? 0 }}</span>
                  </div>
                </div>
                <div class="vacancy-actions">
                  <button class="btn ghost small" @click="openVacancyInfo(v)">Ver detalles</button>
                  <button class="btn small" @click="postular(v.id)" :disabled="loading.postularId===v.id || alreadyApplied(v)">
                    {{ loading.postularId===v.id ? 'Postulando…' : alreadyApplied(v) ? 'Ya aplicaste' : 'Postular' }}
                  </button>
                </div>
              </article>
              <p v-if="vacantes.length===0" class="empty-vacancies">No hay vacantes activas en este momento.</p>
            </div>

            <!-- Paginación -->
            <div class="pagination" v-if="vacTotalPages > 1">
                <button class="btn small" @click="prevVacPage" :disabled="vacPage===1">← Anterior</button>
                <span class="page-info">Página {{ vacPage }} de {{ vacTotalPages }}</span>
                <button class="btn small" @click="nextVacPage" :disabled="vacPage===vacTotalPages">Siguiente →</button>
             </div>
          </section>

      <!-- Ayuda -->
      <section class="card">
        <h3 class="card-title">Ayuda rápida</h3>
        <ul class="muted">
          <li>Sube tu CV actualizado para mejores posibilidades.</li>
          <li>Al postularte, se abrirá una evaluación con 3 preguntas y 2 pruebas.</li>
          <li>Puedes volver a esta página cuando quieras para ver tus postulaciones.</li>
        </ul>
      </section>
    </div>

    <div v-if="selectedVacante" class="modal-backdrop" @click.self="closeVacancyInfo">
      <div class="modal vacancy-modal" role="dialog" aria-modal="true" aria-labelledby="vacancy-info-title">
        <div class="modal-head">
          <h3 id="vacancy-info-title">{{ selectedVacante.titulo }}</h3>
          <button class="btn ghost" @click="closeVacancyInfo" aria-label="Cerrar información">✕</button>
        </div>
        <div class="vacancy-detail">
          <p><strong>Descripción</strong></p>
          <p>{{ selectedVacante.descripcion || 'No especificada' }}</p>
          <p><strong>Requisitos</strong></p>
          <p>{{ selectedVacante.requisitos || 'No especificados' }}</p>
          <p><strong>Ubicación:</strong> {{ selectedVacante.ubicacion || 'No especificada' }}</p>
          <p><strong>Modalidad:</strong> {{ selectedVacante.tipo_contrato || 'No especificada' }}</p>
          <p><strong>Salario:</strong> {{ salaryRange(selectedVacante) }}</p>
        </div>
        <div class="actions">
          <button class="btn ghost" @click="closeVacancyInfo">Cerrar</button>
          <button class="btn" @click="postularFromInfo(selectedVacante)" :disabled="loading.postularId === selectedVacante.id || alreadyApplied(selectedVacante)">
            {{ loading.postularId === selectedVacante.id ? 'Postulando…' : alreadyApplied(selectedVacante) ? 'Ya aplicaste' : 'Postular' }}
          </button>
        </div>
      </div>
    </div>

    <!-- MODAL: Evaluación IA -->
    <div v-if="evalOpen" class="modal-backdrop" @click.self="closeEval">
      <div class="modal">
        <div class="modal-head">
          <h3>Evaluación – Vacante #{{ currentVacanteId }}</h3>
          <button class="btn ghost" @click="closeEval">✕</button>
        </div>

        <div v-if="!evaluation" class="skeleton">Preparando evaluación…</div>
        <div v-else class="eval-body">
          <div class="eval-section">
            <h4>Preguntas (3)</h4>
            <div v-for="q in evaluation.questions" :key="q.id" class="qa">
              <label class="q">{{ q.prompt }}</label>
              <textarea v-model="answers[q.id]" class="input" rows="5" :placeholder="q.hint || 'Escribe tu respuesta…'"></textarea>
              <div class="meta">Tipo: {{ q.type }} · Peso: {{ q.weight }}</div>
            </div>
          </div>

          <div class="eval-section">
            <h4>Pruebas técnicas (2)</h4>
            <div v-for="t in evaluation.technical_tests" :key="t.id" class="qa">
              <div class="q"><strong>{{ t.title }}</strong></div>
              <p class="inst">{{ t.instructions }}</p>
              <textarea v-model="answers[t.id]" class="input" rows="7"
                :placeholder="t.files_allowed ? 'Puedes pegar enlaces a repositorios/archivos y/o el código aquí…' : 'Describe tu solución aquí…'"></textarea>
              <div class="meta">Esperado: {{ t.expected_outcome }} · Tiempo: {{ t.time_limit_min || 30 }} min · Peso: {{ t.weight }}</div>
            </div>
          </div>

          <div class="actions">
            <button class="btn" :disabled="loading.submit" @click="submitEval">
              {{ loading.submit ? 'Enviando…' : 'Enviar evaluación' }}
            </button>
            <span v-if="submitErr" class="error inline">{{ submitErr }}</span>
          </div>

          <div v-if="score" class="score-card">
            <h4>Resultado</h4>
            <p><strong>Puntaje:</strong> {{ score.total_obtained }}/{{ score.total_max }} ({{ score.percentage }}%)</p>
            <p><strong>Recomendación:</strong> <span class="badge" :class="recBadge(score.recommendation)">{{ score.recommendation }}</span></p>
            <details class="muted">
              <summary>Ver desglose</summary>
              <ul>
                <li v-for="d in score.details" :key="d.id">
                  <strong>{{ d.title || d.id }}</strong> — {{ d.score }}/{{ d.weight }} · <em>{{ d.comments }}</em>
                </li>
              </ul>
            </details>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api, { API_BASE, downloadAuthenticated } from '../utils/api'

const me = ref(null)
const cvUrl = ref('')
const uploadMsg = ref('')
const downloadCv = () => downloadAuthenticated('/cv/mio/archivo')
const uploadErr = ref('')
const postulaciones = ref([])
const page = ref(1)
const pageSize = 3

const vacantes = ref([])
const search = ref('')
const filtroModalidad = ref('')
const vacPage = ref(1)
const vacPageSize = 5
const vacTotalPages = ref(1) 
const selectedVacante = ref(null)

const prevVacPage = async () => {
  if (vacPage.value > 1) {
    vacPage.value--
    await loadVacantes()
  }
}
const nextVacPage = async () => {
  if (vacPage.value < vacTotalPages.value) {
    vacPage.value++
    await loadVacantes()
  }
}

const evalOpen = ref(false)
const currentVacanteId = ref(null)
const evaluation = ref(null)   // { questions[], technical_tests[] }
const answers = ref({})        // { [id]: string }
const score = ref(null)
const submitErr = ref('')

const postulacionesPag = computed(() => postulaciones.value)
const appliedVacancyIds = computed(() => new Set(
  postulaciones.value
    .filter(p => p.estado === 'evaluado')
    .map(p => Number(p.id_vacante))
))
const alreadyApplied = (vacante) => Boolean(vacante.aplicada) || appliedVacancyIds.value.has(Number(vacante.id))

const totalPages = computed(() => Math.ceil(postulaciones.value.length / pageSize))

const prevPage = () => { if (page.value > 1) page.value-- }
const nextPage = () => { if (page.value < totalPages.value) page.value++ }

const loading = ref({
  any: false, me: false, cv: false, upload: false,
  post: false, vac: false, postularId: null, submit: false
})
const fileRef = ref(null)

const abs = (u) => (u?.startsWith?.('http') ? u : `${API_BASE}${u || ''}`)
const initials = computed(() => {
  const n = me.value?.nombre || ''
  return n ? n.split(' ').map(p => p[0]).slice(0,2).join('').toUpperCase() : 'U'
})
const badge = (s) => ({
  green: s === 'activo' || s === 'aceptado' || s === 'activa' || s === 'alto',
  yellow: s === 'pendiente' || s === 'medio' || s === 'hibrido',
  red: s === 'inactivo' || s === 'descartado' || s === 'cerrada' || s === 'bajo'
})

const recBadge = (r) => ({
  green: r?.startsWith('Apto'),
  yellow: r?.startsWith('Potencial'),
  red: r?.startsWith('No apto')
})

const fmtDate = (d) => {
  if (!d) return '—'
  try { return new Date(d).toLocaleString() } catch { return d }
}

const salaryRange = (vacante) => {
  const min = vacante.salario_min
  const max = vacante.salario_max
  if (min == null && max == null) return 'No especificado'
  if (min == null) return `Hasta ${max}`
  if (max == null) return `Desde ${min}`
  return `${min} – ${max}`
}

const openVacancyInfo = (vacante) => { selectedVacante.value = vacante }
const closeVacancyInfo = () => { selectedVacante.value = null }
const postularFromInfo = async (vacante) => {
  closeVacancyInfo()
  await postular(vacante.id)
}

const loadMe = async () => {
  loading.value.me = true
  try {
    const { data } = await api.get('/auth/me')
    me.value = data?.user || data
  } finally {
    loading.value.me = false
  }
}

const loadCV = async () => {
  loading.value.cv = true
  uploadMsg.value = ''; uploadErr.value = ''
  try {
    const { data } = await api.get('/cv/mio')
    cvUrl.value = data?.cv_url || ''
  } catch (e) {
    if (e?.response?.status === 404) cvUrl.value = ''
    else uploadErr.value = e?.response?.data?.detail || 'No se pudo obtener el CV'
  } finally {
    loading.value.cv = false
  }
}

const loadPostulaciones = async () => {
  loading.value.post = true
  try {
    // Ajustado para el router /candidate
    const { data } = await api.get('/candidate/mis-postulaciones', { params: { page: page.value, page_size: pageSize } })
    postulaciones.value = data?.data || data || []
  } finally {
    loading.value.post = false
  }
}

const loadVacantes = async () => {
  loading.value.vac = true
  try {
    const { data } = await api.get('/candidate/vacantes', {
      params: {
        page: vacPage.value,
        page_size: vacPageSize,
        q: search.value || undefined,
        modalidad: filtroModalidad.value || undefined
      }
    })
    
    vacantes.value = data?.items || []

    // Si backend da total_items:
    if (data?.total_items) {
      vacTotalPages.value = Math.ceil(data.total_items / vacPageSize)
    } else {
      // Inferir: si recibimos menos items que vacPageSize => última página
      vacTotalPages.value = vacPage.value
      if (vacantes.value.length === vacPageSize) vacTotalPages.value++  // posible siguiente página
    }

  } finally {
    loading.value.vac = false
  }
}

const postular = async (id) => {
  if (alreadyApplied({ id })) return
  loading.value.postularId = id
  evaluation.value = null
  answers.value = {}
  score.value = null
  submitErr.value = ''
  try {
    const { data } = await api.post(`/candidate/vacantes/${id}/postular`)
    currentVacanteId.value = id
    evaluation.value = data?.ai?.evaluation || data?.evaluation
    if (!evaluation.value) throw new Error('No se recibió la evaluación')
    // Prellenar estructura de answers
    for (const q of evaluation.value.questions) answers.value[q.id] = ''
    for (const t of evaluation.value.technical_tests) answers.value[t.id] = ''
    evalOpen.value = true
    await loadPostulaciones()
    await loadVacantes()
  } catch (e) {
    alert(e?.response?.data?.detail || e.message || 'Error al postularse')
  } finally {
    loading.value.postularId = null
  }
}

const submitEval = async () => {
  if (!currentVacanteId.value || !evaluation.value) return
  loading.value.submit = true
  submitErr.value = ''
  score.value = null
  try {
    const payload = {
      answers: Object.entries(answers.value).map(([id, response]) => ({ id, response }))
    }
    const { data } = await api.post(`/candidate/vacantes/${currentVacanteId.value}/evaluar`, payload)
    score.value = data
    await Promise.all([loadPostulaciones(), loadVacantes()])
  } catch (e) {
    submitErr.value = e?.response?.data?.detail || 'No se pudo enviar la evaluación'
  } finally {
    loading.value.submit = false
  }
}

const closeEval = () => {
  evalOpen.value = false
  currentVacanteId.value = null
  evaluation.value = null
  answers.value = {}
  score.value = null
  submitErr.value = ''
}

const pickFile = () => fileRef.value?.click()
const onPick = async (e) => {
  const file = e.target.files?.[0]
  if (!file) return
  uploadMsg.value = ''; uploadErr.value = ''

  const okExt = /\.(pdf|doc|docx)$/i.test(file.name)
  if (!okExt) { uploadErr.value = 'Formato no soportado (usa PDF/DOC/DOCX)'; e.target.value=''; return }
  if (file.size > 5 * 1024 * 1024) { uploadErr.value = 'El archivo supera 5 MB'; e.target.value=''; return }

  loading.value.upload = true
  try {
    const fd = new FormData()
    fd.append('file', file)
    await api.post('/cv/upload', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
    uploadMsg.value = 'CV cargado correctamente'
    await loadCV()
  } catch (err) {
    uploadErr.value = err?.response?.data?.detail || 'Error subiendo el CV'
  } finally {
    loading.value.upload = false
    e.target.value = ''
  }
}

const reloadAll = async () => {
  loading.value.any = true
  try {
    await Promise.all([loadMe(), loadCV(), loadPostulaciones(), loadVacantes()])
  } finally {
    loading.value.any = false
  }
}

const logout = () => {
  localStorage.removeItem('token')
  window.location.href = '/login'
}

onMounted(reloadAll)
</script>

<style scoped>
:root {
  --bg1: #f0f4f8;
  --bg2: #d9e2ec;
  --card: #ffffff;
  --text: #102a43;
  --muted: #627d98;
  --primary: #0b4aa6;
  --primary-600: #093b87;
  --ok: #167c3b;
  --err: #b42318;
  --badge-green: #e9f9ef;
  --badge-green-bd: #bfe8cf;
  --badge-green-tx: #167c3b;
  --badge-yellow: #fff6e5;
  --badge-yellow-bd: #ffe0a8;
  --badge-yellow-tx: #9a6b00;
  --badge-red: #ffefef;
  --badge-red-bd: #ffc7c7;
  --badge-red-tx: #9c2929;
}

.page {
  min-height: 100vh;
  background: linear-gradient(135deg, var(--bg1), var(--bg2));
  padding: 24px;
  font-family: "Inter", sans-serif;
}

.head {
  max-width: 1180px;
  margin: 0 auto 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.left { display: flex; align-items: center; gap: 12px; }

.avatar {
  width: 50px; height: 50px; border-radius: 12px;
  background: var(--primary); color: #1b1212;
  display: grid; place-items: center;
  font-weight: 800; font-size: 1.2rem;
  box-shadow: 0 6px 16px rgba(11, 74, 166, 0.25);
}

.title { margin: 0; font-size: 1.5rem; color: var(--text); }
.muted { color: var(--muted); margin: 0; font-size: 0.95rem; }

.grid {
  max-width: 1180px; margin: 0 auto;
  display: grid; grid-template-columns: 1fr 1fr; gap: 20px;
}
@media (max-width: 980px) { .grid { grid-template-columns: 1fr; } }

.card {
  background: var(--card); border-radius: 16px; border: 1px solid #e1e8ed;
  padding: 20px; box-shadow: 0 16px 32px rgba(0,0,0,0.08);
  transition: transform .2s ease, box-shadow .2s ease;
}
.card:hover { transform: translateY(-4px); box-shadow: 0 20px 40px rgba(0,0,0,0.12); }
.card-title { margin: 0 0 12px; color: var(--text); font-size: 1.25rem; font-weight: 600; }
.card-head { display:flex; align-items:center; justify-content:space-between; gap:12px; }
.vacancy-section { grid-column: 1 / -1; }

.profile { display: grid; gap: 10px; margin-bottom: 16px; }
.row { display: flex; gap: 12px; }
.row label { width: 120px; color: #364152; font-weight: 500; }

.cv h4 { margin: 0 0 8px; }
.cv-actions { display:flex; gap:10px; flex-wrap:wrap; align-items:center; }
.hint { color: var(--muted); font-size: 12px; margin-top: 6px; }

.btn {
  padding: 10px 16px; border-radius: 10px; border: 0;
  background: var(--primary); color: #2a1e1e; font-weight: 700; cursor: pointer;
  transition: all .2s ease; box-shadow: 0 6px 16px rgba(11,74,166,0.25);
}
.btn:hover { background: var(--primary-600); transform: translateY(-1px); box-shadow: 0 8px 20px rgba(11,74,166,0.3); }
.btn.ghost { background:#fff; color: var(--primary); border:1px solid #cbd5e1; box-shadow:none; }
.btn.link { background:#fff; color: var(--primary); border:1px solid #cbd5e1; }
.right .btn.logout {
  background:#fff; color: var(--err); border:1px solid #f8c7c4; margin-left:8px; transition: all .2s ease;
}
.right .btn.logout:hover { background: var(--err); color:#fff; box-shadow:0 6px 16px rgba(180,35,24,0.3); transform: translateY(-1px); }

.table { width:100%; border-collapse: collapse; margin-top: 12px; }
.table th, .table td { padding: 10px; border: 1px solid #edf2f7; text-align: left; }
.vacancy-list { display: grid; gap: 12px; margin-top: 16px; }
.vacancy-item {
  display: flex; align-items: center; justify-content: space-between; gap: 20px;
  padding: 16px 18px; border: 1px solid #dce7f1; border-radius: 14px;
  background: linear-gradient(135deg, #fff, #f8fbff);
}
.vacancy-item:hover { border-color: #a9c6e8; box-shadow: 0 7px 18px rgba(11, 74, 166, .08); }
.vacancy-content { min-width: 0; }
.vacancy-id { color: var(--primary); font-weight: 700; font-size: .8rem; }
.vacancy-content h4 { margin: 4px 0 12px; color: var(--text); font-size: 1.1rem; }
.vacancy-meta { display: flex; flex-wrap: wrap; gap: 8px; }
.vacancy-meta span { display: grid; gap: 2px; padding: 7px 10px; background: #eef5fc; border-radius: 8px; color: #486581; font-size: .82rem; }
.vacancy-meta strong { color: #243b53; font-size: .72rem; text-transform: uppercase; letter-spacing: .02em; }
.vacancy-actions { display: flex; flex-wrap: wrap; justify-content: flex-end; gap: 8px; flex-shrink: 0; }
.empty-vacancies { margin: 0; padding: 24px; text-align: center; color: var(--muted); border: 1px dashed #cbd5e1; border-radius: 12px; }
.btn.small { padding: 8px 12px; font-size: .82rem; }
@media (max-width: 640px) {
  .vacancy-item { align-items: stretch; flex-direction: column; gap: 14px; }
  .vacancy-actions { justify-content: stretch; }
  .vacancy-actions .btn { flex: 1; }
}

.skeleton {
  padding: 12px;
  background: repeating-linear-gradient(90deg, #f5f5f5, #f5f5f5 10px, #ececec 10px, #ececec 20px);
  border-radius: 8px;
}

.badge {
  padding: 4px 10px; border-radius: 999px; font-size: 12px;
  border: 1px solid #eee; font-weight: 600;
}
.badge.green { background: var(--badge-green); color: var(--badge-green-tx); border-color: var(--badge-green-bd); }
.badge.yellow{ background: var(--badge-yellow);color: var(--badge-yellow-tx);border-color: var(--badge-yellow-bd); }
.badge.red   { background: var(--badge-red);   color: var(--badge-red-tx);   border-color: var(--badge-red-bd); }

.ok { margin-top:6px; color:var(--ok); background:#e9f9ef; border:1px solid #bfe8cf; padding:8px 12px; border-radius:8px; font-size:13px; }
.error { margin-top:6px; color:var(--err); background:#feecec; border:1px solid #f8c7c4; padding:8px 12px; border-radius:8px; font-size:13px; }
.error.inline { margin-left: 10px; }

.tools { display:flex; gap:8px; align-items:center; }
.tools input, .tools select {
  padding: 6px; border:1px solid #ddd; border-radius: 8px;
}
.tools input[type="number"] { width:64px; }

.modal-backdrop {
  position: fixed; inset: 0; background: rgba(0,0,0,.35);
  display: grid; place-items: center; z-index: 1000;
}
.modal {
  width: min(980px, 92vw); max-height: 90vh; overflow: auto;
  background: #fff; border-radius: 16px; border: 1px solid #e1e8ed; padding: 16px 16px 24px;
  box-shadow: 0 24px 64px rgba(0,0,0,.25);
}
.vacancy-modal { width: min(640px, 92vw); }
.vacancy-detail { display: grid; gap: 6px; color: #334155; }
.vacancy-detail p { margin: 0; white-space: pre-line; }
.vacancy-detail p:nth-child(odd) { margin-top: 8px; color: #0f172a; }
.modal-head { display:flex; justify-content: space-between; align-items:center; margin-bottom: 8px; }
.eval-body { display: grid; gap: 16px; }
.eval-section { background:#fafafa; border:1px solid #eee; border-radius:12px; padding:12px; }
.qa { display:grid; gap:8px; margin-bottom: 10px; }
.q { font-weight: 600; color:#0f172a; }
.inst { color:#334155; margin:0; }
.input {
  width: 100%; padding: 10px; border-radius: 8px; border:1px solid #d1d5db; font-family: inherit; resize: vertical;
}
.meta { color:#64748b; font-size:12px; }
.actions { display:flex; gap:10px; align-items:center; justify-content:flex-start; margin-top: 4px; }
.score-card { margin-top: 10px; background:#f8fafc; border:1px solid #e2e8f0; border-radius: 12px; padding: 12px; }

.pagination {
  display: flex;
  justify-content: center; /* centra los botones */
  align-items: center;
  gap: 12px;
  margin-top: 24px; /* más espacio respecto a la tabla */
}

.pagination button {
  padding: 8px 16px;
  border-radius: 10px;
  border: none;
  background: var(--primary);
  color: black;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 6px 16px rgba(11,74,166,0.25);
}

.pagination button:hover:not(:disabled) {
  background: var(--primary-600);
  transform: translateY(-1px);
  box-shadow: 0 8px 20px rgba(11,74,166,0.3);
}

.pagination button:disabled {
  background: #cbd5e1;
  cursor: not-allowed;
  box-shadow: none;
}

.pagination span {
  font-weight: 500;
  color: var(--text);
}

</style>
