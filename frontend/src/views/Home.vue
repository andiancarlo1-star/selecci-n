<template>
    <div class="hero-section">
      <h1 class="title">🚀 Bienvenido a <span>TalentAI</span></h1>
      <p class="subtitle">
        Tu plataforma inteligente para conectar el mejor talento con las mejores oportunidades.
      </p>
      <div class="action-buttons">
        <button v-if="!auth.user" class="btn primary" @click="$router.push('/login')">
          Iniciar Sesión
        </button>
        <button v-if="!auth.user" class="btn secondary" @click="$router.push('/register')">
          Registrarse
        </button>
        <div v-if="auth.user" class="welcome">
          <p>Hola, <strong>{{ auth.user.nombre }}</strong> 👋</p>
          <p>Rol: <span class="badge">{{ auth.user.tipo }}</span></p>
          <button class="btn logout" @click="logout">Cerrar Sesión</button>
        </div>
      </div>
    </div>

    <div class="features">
      <div class="feature-card">
        <h3>🔍 Búsqueda Inteligente</h3>
        <p>Encuentra oportunidades adaptadas a tu perfil usando IA avanzada.</p>
      </div>
      <div class="feature-card">
        <h3>💼 Gestión de Vacantes</h3>
        <p>Publica, administra y analiza vacantes con facilidad.</p>
      </div>
      <div class="feature-card">
        <h3>📊 Seguimiento de Postulaciones</h3>
        <p>Control total sobre el estado de cada proceso de selección.</p>
      </div>
    </div>
</template>

<script setup>
import { useAuthStore } from '../stores/auth'
const auth = useAuthStore()

const logout = () => {
  auth.logout()
}
</script>

<style scoped>
.home-container {
  padding: 30px;
  max-width: 1100px;
  margin: auto;
  background: linear-gradient(135deg, #e0f3ff, #c2e7ff);
  min-height: 100vh;
  border-radius: 12px;
  box-shadow: inset 0 0 20px rgba(0,0,0,0.05);
}

.hero-section {
  text-align: center;
  margin-bottom: 40px;
}

.title {
  font-size: 2.2rem;
  margin-bottom: 10px;
  color: #151515;
}
.title span {
  color: #d4af37;
}

.subtitle {
  font-size: 1.1rem;
  color: #333;
  margin-bottom: 20px;
}

.action-buttons {
  margin-top: 20px;
}

.btn {
  padding: 10px 18px;
  border: none;
  border-radius: 6px;
  font-size: 1rem;
  cursor: pointer;
  margin: 5px;
  transition: 0.3s ease;
}

.btn.primary {
  background: #d4af37;
  color: #fff;
}
.btn.primary:hover {
  background: #b8932f;
}

.btn.secondary {
  background: #151515;
  color: #fff;
}
.btn.secondary:hover {
  background: #000;
}

.btn.logout {
  background: #ff5e5e;
  color: #fff;
}
.btn.logout:hover {
  background: #e34d4d;
}

.features {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 20px;
}

.feature-card {
  background: #fff;
  padding: 20px;
  border-radius: 10px;
  border: 1px solid #eee;
  text-align: center;
  box-shadow: 0 4px 8px rgba(0,0,0,0.05);
  transition: transform 0.2s ease;
}
.feature-card:hover {
  transform: translateY(-3px);
}
.feature-card h3 {
  margin-bottom: 10px;
  color: #151515;
}
.feature-card p {
  color: #666;
}

.badge {
  background: #86ee69;
  padding: 3px 8px;
  border-radius: 12px;
  font-size: 0.85rem;
  color: #167c3b;
}
.welcome {
  margin-top: 10px;
}
</style>
