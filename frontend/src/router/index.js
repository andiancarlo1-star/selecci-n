import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Admin from '../views/Admin.vue'
import Login from '../views/Login.vue'
import Recruiter from '../views/Recruiter.vue'
import Register from '../views/Register.vue'
import Candidate from '../views/Candidate.vue'
import Reset from '../views/Reset.vue'
import Evaluation from '../views/Evaluation.vue'
import RecruiterApplications from '../views/RecruiterApplications.vue'

const routes = [
  { 
    path: '/', 
    name: 'Home', 
    component: Home,
    alias: '/inicio'
  },
  { 
    path: '/login', 
    name: 'Login', 
    component: Login,
    alias: '/iniciar-sesion'
  },
  { 
    path: '/register', 
    name: 'Register', 
    component: Register,
    alias: '/registro'
  },
  { 
    path: '/reset', 
    name: 'Reset', 
    component: Reset,
    alias: '/restablecer'
  },

  { 
    path: '/admin',
    name: 'Admin',
    component: Admin,
    meta: { requiresAuth: true, role: 'admin' },
    alias: '/administrador'
  },

  { 
    path: '/recruiter',
    name: 'Recruiter',
    component: Recruiter,
    meta: { requiresAuth: true, role: 'reclutador' },
    alias: '/reclutador'
  },

  {
    path: '/recruiter/vacantes/:id/postulaciones',
    name: 'RecruiterApplications',
    component: RecruiterApplications,
    meta: { requiresAuth: true, role: 'reclutador' },
    alias: '/reclutador/vacantes/:id/postulaciones'
  },

  {
    path: '/candidate',
    name: 'Candidate',
    component: Candidate,
    meta: { requiresAuth: true, role: 'candidato' },
    alias: '/candidato'
  },

  {
    path: '/evaluacion/:vacanteId',
    name: 'Evaluation',
    component: Evaluation,
    props: true,
    meta: { requiresAuth: true, role: 'candidato' },
    alias: '/evaluacion/:vacanteId'
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  const role = localStorage.getItem('role')

  if (to.meta.requiresAuth && !token) return next('/login')
  if (to.meta.role && role !== to.meta.role) return next('/')

  next()
})

export default router
