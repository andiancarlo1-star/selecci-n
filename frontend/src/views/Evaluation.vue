<template>
  <div class="page eval">
    <header class="head">
      <h2>Evaluación – Vacante #{{ vacanteId }}</h2>
      <div class="spacer"></div>
      <button class="btn ghost" @click="$router.back()">← Volver</button>
    </header>

    <div v-if="loading.init" class="skeleton">Preparando evaluación…</div>
    <p v-if="initErr" class="error">{{ initErr }}</p>

    <div v-if="evaluation" class="container">
      <section class="card">
        <h3>Preguntas (3)</h3>
        <div v-for="q in evaluation.questions" :key="q.id" class="qa">
          <label class="q">{{ q.prompt }}</label>
          <textarea v-model="answers[q.id]" class="input" rows="6" :placeholder="q.hint || 'Escribe tu respuesta…'"></textarea>
          <div class="meta">Tipo: {{ q.type }} · Peso: {{ q.weight }}</div>
        </div>
      </section>

      <section class="card">
        <h3>Pruebas técnicas (2)</h3>
        <div v-for="t in evaluation.technical_tests" :key="t.id" class="qa">
          <div class="q"><strong>{{ t.title }}</strong></div>
          <p class="inst">{{ t.instructions }}</p>
          <textarea
            v-model="answers[t.id]" class="input" rows="8"
            :placeholder="t.files_allowed ? 'Pega enlaces a repos/archivos y/o el código…' : 'Describe tu solución…'"></textarea>
          <div class="meta">Esperado: {{ t.expected_outcome }} · Tiempo: {{ t.time_limit_min || 30 }} min · Peso: {{ t.weight }}</div>
        </div>
      </section>

      <section class="card actions">
        <button class="btn" :disabled="loading.submit" @click="submit">
          {{ loading.submit ? 'Enviando…' : 'Enviar evaluación' }}
        </button>
        <span v-if="submitErr" class="error inline">{{ submitErr }}</span>
      </section>

      <section v-if="score" class="card result">
        <h3>Resultado</h3>
        <p><strong>Puntaje:</strong> {{ score.total_obtained }}/{{ score.total_max }} ({{ score.percentage }}%)</p>
        <p><strong>Recomendación:</strong>
          <span class="badge" :class="recBadge(score.recommendation)">{{ score.recommendation }}</span>
        </p>
        <details class="muted">
          <summary>Ver desglose</summary>
          <ul>
            <li v-for="d in score.details" :key="d.id">
              <strong>{{ d.title || d.id }}</strong> — {{ d.score }}/{{ d.weight }} · <em>{{ d.comments }}</em>
            </li>
          </ul>
        </details>
        <div class="end-actions">
          <button class="btn ghost" @click="$router.push('/candidate')">Volver a mi panel</button>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import api, { API_BASE } from '../utils/api'

const route = useRoute()
const vacanteId = route.params.vacanteId

const loading = ref({ init: false, submit: false })
const initErr = ref('')
const submitErr = ref('')
const evaluation = ref(null)
const answers = ref({})
const score = ref(null)

const recBadge = (r) => ({
  green: r?.startsWith('Apto'),
  yellow: r?.startsWith('Potencial'),
  red: r?.startsWith('No apto'),
})

const loadEvaluation = async () => {
  loading.value.init = true
  initErr.value = ''
  evaluation.value = null
  answers.value = {}
  score.value = null
  try {
    // registra postulación (si ya existía, el backend lo ignora) y devuelve evaluación IA
    const { data } = await api.post(`/candidate/vacantes/${vacanteId}/postular`)
    const ev = data?.ai?.evaluation || data?.evaluation
    if (!ev) throw new Error('No se pudo obtener la evaluación')
    evaluation.value = ev
    for (const q of ev.questions) answers.value[q.id] = ''
    for (const t of ev.technical_tests) answers.value[t.id] = ''
  } catch (e) {
    initErr.value = e?.response?.data?.detail || e.message || 'No se pudo iniciar la evaluación'
  } finally {
    loading.value.init = false
  }
}

const submit = async () => {
  if (!evaluation.value) return
  loading.value.submit = true
  submitErr.value = ''
  score.value = null
  try {
    const payload = { answers: Object.entries(answers.value).map(([id, response]) => ({ id, response })) }
    const { data } = await api.post(`/candidate/vacantes/${vacanteId}/evaluar`, payload)
    score.value = data
  } catch (e) {
    submitErr.value = e?.response?.data?.detail || 'No se pudo enviar la evaluación'
  } finally {
    loading.value.submit = false
  }
}

onMounted(loadEvaluation)
watch(() => route.params.vacanteId, loadEvaluation)
</script>

<style scoped>
.page.eval { min-height: 100vh; background: #f6f8fb; padding: 24px; }
.head { max-width: 980px; margin: 0 auto 16px; display: flex; align-items: center; gap: 12px; }
.head .spacer { flex: 1 }
.container { max-width: 980px; margin: 0 auto; display: grid; gap: 16px; }
.card { background: #fff; border: 1px solid #e5e7eb; border-radius: 16px; padding: 16px; box-shadow: 0 8px 24px rgba(0,0,0,.06); }
.qa { display: grid; gap: 8px; margin-bottom: 12px; }
.q { font-weight: 600; color: #0f172a; }
.inst { color: #334155; margin: 0 }
.input { width: 100%; padding: 10px; border-radius: 8px; border: 1px solid #d1d5db; resize: vertical; font-family: ui-sans-serif, system-ui, "Segoe UI", Roboto; }
.meta { color: #64748b; font-size: 12px; }
.actions { display: flex; align-items: center; gap: 10px; }
.result .end-actions { margin-top: 10px; display: flex; justify-content: flex-end; }
.btn { padding: 10px 16px; border-radius: 10px; border: 0; background: #0b4aa6; color: #fff; font-weight: 700; cursor: pointer; box-shadow: 0 6px 16px rgba(11,74,166,.25); }
.btn:hover { background: #093b87; }
.btn.ghost { background: #fff; color: #0b4aa6; border: 1px solid #cbd5e1; box-shadow: none; }
.skeleton { max-width: 980px; margin: 0 auto; padding: 14px; background: repeating-linear-gradient(90deg,#f5f5f5,#f5f5f5 10px,#ececec 10px,#ececec 20px); border-radius: 8px; }
.error { color: #b42318; background: #feecec; border: 1px solid #f8c7c4; padding: 8px 12px; border-radius: 8px; }
.error.inline { margin-left: 10px; }
.badge { padding: 4px 10px; border-radius: 999px; font-size: 12px; border: 1px solid #eee; font-weight: 600; }
.badge.green { background: #e9f9ef; color: #167c3b; border-color: #bfe8cf; }
.badge.yellow { background: #fff6e5; color: #9a6b00; border-color: #ffe0a8; }
.badge.red { background: #ffefef; color: #9c2929; border-color: #ffc7c7; }
</style>
