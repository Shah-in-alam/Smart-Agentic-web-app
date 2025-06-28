<script setup>
import UploadZone from './components/UploadZone.vue'
</script>

<template>
  <div class="app">
    <main>
      <UploadZone />
    </main>
  </div>
</template>

<style scoped>
.app {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
  text-align: center;
}

header {
  margin-bottom: 3rem;
}

header h1 {
  color: #2c3e50;
  margin-bottom: 0.5rem;
}

header p {
  color: #7f8c8d;
  font-size: 1.1rem;
}

main {
  display: flex;
  justify-content: center;
}
</style>
