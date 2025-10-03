<template>
  <AppLayout>
    <div class="chat-page">
      <div class="info-box">
        <h2>Chat Milhena</h2>
        <p>Il widget chat è disponibile nell'angolo in basso a destra di ogni pagina.</p>
        <p>Clicca sull'icona blu per iniziare a chattare.</p>
      </div>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import AppLayout from '../layouts/AppLayout.vue'
</script>

<style scoped>
.chat-page {
  padding: 40px;
  max-width: 800px;
  margin: 0 auto;
}

.info-box {
  background: #f3f4f6;
  padding: 32px;
  border-radius: 12px;
  text-align: center;
}

.info-box h2 {
  font-size: 24px;
  font-weight: 600;
  color: #111;
  margin-bottom: 16px;
}

.info-box p {
  font-size: 14px;
  color: #666;
  margin-bottom: 8px;
}
</style>
