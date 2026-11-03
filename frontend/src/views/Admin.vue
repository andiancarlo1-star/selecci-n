<template>
  <div class="wrap">
    <header class="header">
      <div>
        <h2>Panel de Administración</h2>
        <small class="muted">Gestiona reclutadores, vacantes, postulaciones y candidatos</small>
      </div>
      <button class="logout-btn" @click="logout" title="Cerrar sesión">⏻</button>
    </header>

    <nav class="tabs">
      <button :class="tabBtn('reclutadores')" @click="tab='reclutadores'">Reclutadores</button>
      <button :class="tabBtn('vacantes')" @click="tab='vacantes'">Vacantes</button>
      <button :class="tabBtn('postulaciones')" @click="tab='postulaciones'">Postulaciones</button>
      <button :class="tabBtn('candidatos')" @click="tab='candidatos'">Candidatos</button>
    </nav>

    <div v-if="error" class="alert error">
      <strong>Error:</strong> {{ error }}
    </div>
    <div v-if="msg" class="alert ok">{{ msg }}</div>

    <!-- RECLUTADORES -->
    <section v-show="tab==='reclutadores'" class="card">
      <h3>Crear reclutador</h3>
      <form @submit.prevent="createRecruiter" class="form">
        <input v-model="reclutador.nombre" placeholder="Nombre" />
        <input v-model="reclutador.correo" placeholder="Correo" />
        <input v-model="reclutador.contrasena" type="password" placeholder="Contraseña" />
        <input v-model="reclutador.area_especialidad" placeholder="Área de Especialidad" />
        <input v-model="reclutador.telefono" placeholder="Teléfono (opcional)" />
        <button type="submit">Crear</button>
      </form>

      <div class="card" style="margin-top:12px">
        <div class="card-head">
          <h3>Listado de reclutadores</h3>
          <div class="tools">
            <input v-model="rq" placeholder="Buscar (nombre/correo)" @keyup.enter="loadReclutadores" />
            <button @click="loadReclutadores">Buscar</button>
            <label>pág.</label>
            <input type="number" v-model.number="rPage" min="1" @change="loadReclutadores" />
          </div>
        </div>

        <div v-if="loading.reclutadores" class="skeleton">Cargando reclutadores…</div>

        <table v-else class="table">
          <thead>
            <tr>
              <th>ID</th><th>Nombre</th><th>Correo</th><th>Especialidad</th><th>Teléfono</th><th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in reclutadores" :key="r.id">
              <td>{{ r.id }}</td>
              <td>{{ r.nombre }}</td>
              <td>{{ r.correo }}</td>
              <td>{{ r.area_especialidad || '-' }}</td>
              <td>{{ r.telefono || '-' }}</td>
              <td>
                <button @click="deleteRecruiter(r.id, r.nombre)">Eliminar</button>
              </td>
            </tr>
            <tr v-if="reclutadores.length===0">
              <td colspan="6" class="muted">No hay reclutadores</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- VACANTES -->
    <section v-show="tab==='vacantes'" class="card">
      <div class="card-head">
        <h3>Vacantes</h3>
        <div class="tools">
          <button @click="loadVacantes">Refrescar</button>
          <label>pág.</label>
          <input type="number" v-model.number="vPage" min="1" @change="loadVacantes" />
        </div>
      </div>
      <div v-if="loading.vacantes" class="skeleton">Cargando vacantes…</div>
      <table v-else class="table">
        <thead>
          <tr>
            <th>ID</th><th>Título</th><th>Estado</th><th>Reclutador</th><th># Postulaciones</th><th>Fecha</th>
          </tr>
        </thead>
       <tbody>
          <tr v-for="v in vacantes" :key="v.id">
             <td>{{ v.id }}</td>
            <td>{{ v.titulo }}</td>
            <td><span :class="badge(v.estado)">{{ v.estado }}</span></td>
            <td>{{ v.reclutador_nombre }} <small class="muted">({{ v.reclutador_correo }})</small></td>
            <td style="text-align:center">{{ v.total_postulaciones }}</td>
            <td>{{ v.fecha_publicacion }}</td>
            <td>
              <button @click="deleteVacante(v.id, v.titulo)">Eliminar</button>
            </td>
          </tr>
            <tr v-if="vacantes.length===0">
                <td colspan="7" class="muted">No hay vacantes</td>
            </tr>
        </tbody>
      </table>
    </section>

    <!-- POSTULACIONES -->
    <section v-show="tab==='postulaciones'" class="card">
      <div class="card-head">
        <h3>Postulaciones</h3>
        <div class="tools">
             <input v-model="pQuery" placeholder="Buscar candidato o vacante" @keyup.enter="loadPostulaciones" />
              <button @click="loadPostulaciones">Buscar</button>
              <button @click="() => { pQuery=''; loadPostulaciones() }">Limpiar</button>
                <label>pág.</label>
            <input type="number" v-model.number="pPage" min="1" @change="loadPostulaciones" />
        </div>
      </div>
      <div v-if="loading.postulaciones" class="skeleton">Cargando postulaciones…</div>
      <table v-else class="table">
        <thead>
          <tr>
            <th>ID</th><th>Vacante</th><th>Candidato</th><th>Correo</th><th>Estado</th><th>Fecha</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="p in postulaciones" :key="p.id">
            <td>{{ p.id }}</td>
            <td>#{{ p.vacante_id }} - {{ p.vacante }}</td>
            <td>{{ p.candidato_nombre }}</td>
            <td>{{ p.candidato_correo }}</td>
            <td><span :class="badge(p.estado)">{{ p.estado }}</span></td>
            <td>{{ p.fecha_postulacion }}</td>
          </tr>
          <tr v-if="postulaciones.length===0">
            <td colspan="6" class="muted">No hay postulaciones</td>
          </tr>
        </tbody>
      </table>
    </section>

    <!-- CANDIDATOS -->
    <section v-show="tab==='candidatos'" class="card">
      <div class="card-head">
        <h3>Candidatos</h3>
        <div class="tools">
          <input v-model="q" placeholder="Buscar (nombre/correo)" @keyup.enter="loadCandidatos" />
          <button @click="loadCandidatos">Buscar</button>
          <button @click="() => { q=''; loadCandidatos() }">Limpiar</button>
          <label>pág.</label>
          <input type="number" v-model.number="cPage" min="1" @change="loadCandidatos" />
        </div>
      </div>
      <div v-if="loading.candidatos" class="skeleton">Cargando candidatos…</div>
      <table v-else class="table">
        <thead>
          <tr>
            <th>ID</th><th>Nombre</th><th>Correo</th><th>Estado</th><th>CV</th><th>LinkedIn</th><th>Portafolio</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="c in candidatos" :key="c.id">
            <td>{{ c.id }}</td>
            <td>{{ c.nombre }}</td>
            <td>{{ c.correo }}</td>
            <td>{{ c.estado }}</td>
            <td>
              <button v-if="c.cv_url" @click="downloadAuthenticated(c.cv_url)">Ver CV</button>
              <span v-else class="muted">-</span>
            </td>
            <td><a v-if="c.linkedin" :href="c.linkedin" target="_blank" rel="noopener">Perfil</a><span v-else class="muted">-</span></td>
            <td><a v-if="c.portafolio" :href="c.portafolio" target="_blank" rel="noopener">Sitio</a><span v-else class="muted">-</span></td>
          </tr>
          <tr v-if="candidatos.length===0">
            <td colspan="7" class="muted">No hay candidatos</td>
          </tr>
        </tbody>
      </table>
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api, { API_BASE, downloadAuthenticated } from '../utils/api'

const router = useRouter()
const tab = ref('reclutadores')
const msg = ref(null)
const error = ref(null)
const loading = ref({ reclutadores: false, vacantes: false, postulaciones: false, candidatos: false })
const pageSize = 20

// ---------------- RECLUTADORES ----------------
const reclutador = ref({ nombre: '', correo: '', contrasena: '', area_especialidad: '', telefono: '' })
const reclutadores = ref([])
const rPage = ref(1)
const rq = ref('')

// ---------------- VACANTES ----------------
const vacantes = ref([])
const vPage = ref(1)

// ---------------- POSTULACIONES ----------------
const postulaciones = ref([])
const pPage = ref(1)
const pQuery = ref('')

// ---------------- CANDIDATOS ----------------
const candidatos = ref([])
const cPage = ref(1)
const q = ref('')

// ---------------- HELPERS ----------------
const abs = (u) => (u?.startsWith?.('http') ? u : `${API_BASE}${u || ''}`)
const tabBtn = (name) => ({ 'tab': true, 'active': tab.value === name })
const badge = (state) => ({
  'badge': true,
  'green': state === 'activa' || state === 'aceptado' || state === 'alto',
  'yellow': state === 'pendiente' || state === 'medio' || state === 'hibrido',
  'red': state === 'cerrada' || state === 'descartado' || state === 'bajo'
})
const guardError = (fn) => async (...args) => {
  try {
    error.value = null
    await fn(...args)
  } catch (e) {
    console.error(e)
    error.value = e?.response?.data?.detail || e?.message || 'Error inesperado'
  }
}

// ---------------- CERRAR SESIÓN ----------------
const logout = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('role')
  router.push('/login')
}

// ---------------- HELPER CARGA CON PAGINACIÓN ----------------
const loadData = guardError(async (endpoint, page, query, setList, loadingKey) => {
  loading[loadingKey] = true
  const { data } = await api.get(endpoint, {
    params: {
      page,
      page_size: pageSize,
      q: query || undefined
    }
  })
  setList(data.items || data)
  loading[loadingKey] = false
})

// ---------------- FUNCIONES ----------------
// RECLUTADORES
const loadReclutadores = () => loadData('/admin/reclutadores', rPage.value, rq.value, val => {
  reclutadores.value = val.map(r => ({
    id: r.id ?? r.reclutador_id ?? r.usuario_id, // toma el primer valor que exista
    nombre: r.nombre,
    correo: r.correo,
    area_especialidad: r.area_especialidad || '',
    telefono: r.telefono || ''
  }))
}, 'reclutadores')

const createRecruiter = guardError(async () => {
  if (!reclutador.value.nombre || !reclutador.value.correo || !reclutador.value.contrasena || !reclutador.value.area_especialidad) {
    throw new Error('Completa nombre, correo, contraseña y área de especialidad')
  }
  const { data } = await api.post('/admin/create-recruiter', reclutador.value)
  msg.value = data?.message || 'Reclutador creado'
  reclutador.value = { nombre:'', correo:'', contrasena:'', area_especialidad:'', telefono:'' }
  loadReclutadores()
})

const deleteRecruiter = guardError(async (reclutador_id, nombre) => {
  if (!reclutador_id) {
    throw new Error(`ID de reclutador no definido para: ${nombre}`)
  }
  if (!confirm(`¿Eliminar reclutador "${nombre}"? Esta acción no se puede deshacer.`)) return
  await api.delete(`/admin/delete-recruiter/${reclutador_id}`)
  msg.value = `Reclutador "${nombre}" eliminado correctamente`
  loadReclutadores()
})

const deleteVacante = guardError(async (vacante_id, titulo) => {
  if (!vacante_id) {
    throw new Error(`ID de vacante no definido para: ${titulo}`)
  }
  if (!confirm(`¿Eliminar vacante "${titulo}"? Esta acción no se puede deshacer.`)) return
  await api.delete(`/admin/delete-vacante/${vacante_id}`)
  msg.value = `Vacante "${titulo}" eliminada correctamente`
  loadVacantes()
})

// VACANTES
const loadVacantes = () => loadData('/admin/vacantes', vPage.value, null, val => vacantes.value = val, 'vacantes')

// POSTULACIONES
const loadPostulaciones = () => loadData('admin/postulaciones-detalle', pPage.value, pQuery.value, val => postulaciones.value = val, 'postulaciones')

// CANDIDATOS
const loadCandidatos = () => loadData('admin/candidatos', cPage.value, q.value, val => candidatos.value = val, 'candidatos')

// ---------------- CARGAR AL MONTAR ----------------
onMounted(() => {
  loadReclutadores()
  loadVacantes()
  loadPostulaciones()
  loadCandidatos()
})
</script>

<style scoped>
/* Contenedor principal */
.wrap {
  padding: 20px;
  max-width: 1400px;
  margin: auto;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  background: #f7f9fc;
}

/* Header */
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.header h2 {
  margin: 0;
  font-size: 1.8rem;
  color: #333;
}
.muted {
  color: #666;
  font-size: 0.9rem;
}
.logout-btn {
  background: #e74c3c;
  color: #fff;
  border: none;
  cursor: pointer;
  padding: 8px 14px;
  border-radius: 6px;
  font-weight: bold;
  transition: background 0.2s;
}
.logout-btn:hover {
  background: #c0392b;
}

/* Tabs */
.tabs {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}
.tab {
  padding: 10px 18px;
  border: none;
  cursor: pointer;
  background: #e0e4e8;
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.2s;
}
.tab.active {
  background: #3498db;
  color: #fff;
  box-shadow: 0 2px 6px rgba(0,0,0,0.15);
}

/* Card */
.card {
  border-radius: 10px;
  padding: 20px;
  margin-bottom: 20px;
  background: #fff;
  box-shadow: 0 2px 10px rgba(0,0,0,0.05);
}
.card-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.tools {
  display: flex;
  gap: 8px;
  align-items: center;
}
.tools input {
  padding: 6px 10px;
  border-radius: 6px;
  border: 1px solid #ccc;
  width: 120px;
}
.tools button {
  padding: 6px 12px;
  border-radius: 6px;
  border: none;
  background: #3498db;
  color: #fff;
  cursor: pointer;
  transition: background 0.2s;
}
.tools button:hover {
  background: #2980b9;
}

/* Table */
.table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 10px;
}
.table th, .table td {
  border: 1px solid #e1e4e8;
  padding: 10px;
  text-align: left;
}
.table th {
  background: #f0f3f7;
  font-weight: 600;
}
.table tbody tr:hover {
  background: #f7f9fc;
}

/* Badge estados */
.badge {
  padding: 4px 10px;
  border-radius: 8px;
  color: #fff;
  font-weight: 500;
  font-size: 0.85rem;
  text-transform: capitalize;
}
.badge.green { background: #27ae60; }
.badge.yellow { background: #f39c12; }
.badge.red { background: #c0392b; }

/* Alertas */
.alert {
  padding: 10px 14px;
  margin: 12px 0;
  border-radius: 8px;
  font-weight: 500;
}
.alert.error { background: #fdecea; color: #c0392b; }
.alert.ok { background: #eafaf1; color: #27ae60; }

/* Form inputs */
.form input, .form button {
  margin-bottom: 10px;
}
.form input {
  width: 100%;
  padding: 8px 12px;
  border-radius: 6px;
  border: 1px solid #ccc;
}
.form button {
  background: #2ecc71;
  color: #fff;
  border: none;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.2s;
}
.form button:hover {
  background: #27ae60;
}

/* Skeleton loading */
.skeleton {
  background: #e1e4e8;
  border-radius: 6px;
  height: 40px;
  animation: pulse 1.2s infinite;
  margin: 10px 0;
}
@keyframes pulse {
  0% { opacity: 1; }
  50% { opacity: 0.4; }
  100% { opacity: 1; }
}
</style>
