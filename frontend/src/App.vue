<template>
  <div>
    <NavBar />
    <router-view />
  </div>
</template>

<script setup>
import NavBar from './components/NavBar.vue'
</script>

<style>
body { font-family: system-ui, Arial, sans-serif; margin: 0; }
nav a { text-decoration: none; }
button { cursor: pointer; }
</style>
