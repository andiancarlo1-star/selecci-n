<template>
  <header class="nav-wrap">
    <nav class="nav">
      <!-- Brand -->
      <div class="brand" @click="$router.push('/')">
        <div class="logo">🤖</div>
        <div class="brand-text">
          <strong>TalentAI</strong>
          <small>Selección con IA</small>
        </div>
      </div>

      <!-- Toggle (mobile) -->
      <button class="toggle" @click="open = !open" aria-label="Abrir menú">
        <span :class="{open}"></span><span :class="{open}"></span><span :class="{open}"></span>
      </button>

      <!-- Links -->
      <div class="links" :class="{ open }">
        <RouterLink :class="linkClass('/')" to="/">Inicio</RouterLink>

        <template v-if="!auth.user">
          <RouterLink :class="linkClass('/login')" to="/login">Login</RouterLink>
          <RouterLink :class="linkClass('/register')" to="/register">Registro</RouterLink>
        </template>

        <template v-else>
          <RouterLink
            v-if="auth.user.tipo==='candidato'"
            :class="linkClass('/candidate')"
            to="/candidate"
          >Candidato</RouterLink>

          <RouterLink
            v-if="auth.user.tipo==='reclutador'"
            :class="linkClass('/recruiter')"
            to="/recruiter"
          >Reclutador</RouterLink>

          <RouterLink
            v-if="auth.user.tipo==='admin'"
            :class="linkClass('/admin')"
            to="/admin"
          >Admin</RouterLink>

          <div class="divider" role="separator"></div>

          <!-- Perfil compacto -->
          <div class="user">
            <div class="avatar">{{ initials }}</div>
            <div class="info">
              <span class="name" :title="auth.user.nombre">{{ shortName }}</span>
              <span class="role">{{ auth.user.tipo }}</span>
            </div>
          </div>

          <button class="logout" @click="logout">Salir</button>
        </template>
      </div>
    </nav>
  </header>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const auth = useAuthStore()
const open = ref(false)

const linkClass = (to) => ({
  link: true,
  active: route.path === to
})

const logout = () => {
  auth.logout()
  open.value = false
}

const initials = computed(() => {
  if (!auth.user?.nombre) return 'U'
  return auth.user.nombre
    .split(' ')
    .map(p => p[0]?.toUpperCase())
    .slice(0,2)
    .join('') || 'U'
})

const shortName = computed(() => {
  const n = auth.user?.nombre || ''
  return n.length > 18 ? n.slice(0, 18) + '…' : n
})
</script>

<style scoped>
:root{
  --nav-bg1:#e0f3ff;
  --nav-bg2:#c2e7ff;
  --text:#0f172a;
  --muted:#5b667a;
  --primary:#0b4aa6;
  --primary-600:#0a3f8f;
  --ring:rgba(13,110,253,.25);
  --white:#fff;
  --line:#e6edf3;
}

.nav-wrap{
  background: linear-gradient(135deg, var(--nav-bg1), var(--nav-bg2));
  border-bottom: 1px solid var(--line);
  position: sticky;
  top: 0;
  z-index: 50;
}

.nav{
  max-width: 1180px;
  margin: 0 auto;
  padding: 10px 16px;
  display: grid;
  grid-template-columns: 1fr auto;
  align-items: center;
  gap: 12px;
}

/* Brand */
.brand{
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  user-select: none;
}
.logo{
  width: 36px; height: 36px; display: grid; place-items: center;
  background: var(--white);
  border-radius: 10px;
  box-shadow: 0 4px 14px rgba(2,6,23,.08);
  font-size: 18px;
}
.brand-text strong{ color: var(--text); font-size: 16px; line-height: 1; display: block;}
.brand-text small{ color: var(--muted); font-size: 12px; }

/* Toggle (mobile) */
.toggle{
  display: none;
  border: 0; background: transparent; cursor: pointer;
  width: 38px; height: 38px; border-radius: 8px;
}
.toggle span{
  display:block; width:22px; height:2px; background:#1f2a44; margin:5px auto; transition:.2s;
}
.toggle span.open:nth-child(1){ transform: translateY(7px) rotate(45deg); }
.toggle span.open:nth-child(2){ opacity:0; }
.toggle span.open:nth-child(3){ transform: translateY(-7px) rotate(-45deg); }

/* Links */
.links{
  display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
}
.link{
  padding: 8px 10px;
  color: #1f2a44;
  text-decoration: none;
  border-radius: 8px;
  transition: background .15s, color .15s, box-shadow .15s;
}
.link:hover{
  background: rgba(255,255,255,.65);
  box-shadow: 0 2px 10px rgba(2,6,23,.06);
}
.link.active{
  background: var(--white);
  color: var(--primary);
  box-shadow: 0 2px 10px rgba(2,6,23,.08), inset 0 0 0 2px rgba(11,74,166,.08);
}

/* Divider */
.divider{
  width: 1px; height: 22px; background: #c7d8e7; margin: 0 4px;
}

/* User compact */
.user{
  display: flex; align-items: center; gap: 8px; padding: 4px 6px; border-radius: 10px;
  background: rgba(255,255,255,.7);
  border: 1px solid rgba(10, 63, 143, .08);
}
.avatar{
  width: 30px; height: 30px; border-radius: 8px; background: var(--primary);
  color: #fff; display:grid; place-items:center; font-weight: 700; font-size: 12px;
}
.info{
  display:flex; flex-direction: column; line-height: 1.1;
}
.name{ color: var(--text); font-size: 12px; }
.role{
  color: var(--primary-600); font-size: 11px; text-transform: capitalize;
}

/* Logout */
.logout{
  margin-left: 4px;
  background: var(--primary);
  color: #fff;
  border: 0;
  padding: 8px 10px;
  border-radius: 8px;
  font-weight: 700;
  cursor: pointer;
  transition: background .15s, transform .05s, box-shadow .15s;
  box-shadow: 0 8px 20px rgba(11,74,166,.25);
}
.logout:hover{ background: var(--primary-600); }
.logout:active{ transform: translateY(1px); }

/* Responsive */
@media (max-width: 860px){
  .nav{ grid-template-columns: 1fr auto; }
  .toggle{ display: inline-block; }
  .links{
    position: absolute; left: 0; right: 0; top: 58px;
    background: linear-gradient(135deg, var(--nav-bg1), var(--nav-bg2));
    border-bottom: 1px solid var(--line);
    padding: 10px 16px 14px;
    display: grid; gap: 8px;
    transform-origin: top center;
    transform: scaleY(0);
    opacity: 0;
    pointer-events: none;
    transition: transform .18s ease, opacity .18s ease;
  }
  .links.open{
    transform: scaleY(1);
    opacity: 1;
    pointer-events: all;
  }
  .divider{ display: none; }
  .logout{ width: 100%; }
}
</style>
