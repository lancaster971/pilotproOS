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
[data-theme="vscode"] .chat-page {
  padding: 40px;
  max-width: 800px;
  margin: 0 auto;
}

[data-theme="vscode"] .info-box {
  background: var(--vscode-bg-secondary);
  padding: 32px;
  border-radius: 12px;
  text-align: center;
}

[data-theme="vscode"] .info-box h2 {
  font-size: 24px;
  font-weight: 600;
  color: var(--vscode-text-inverse);
  margin-bottom: 16px;
}

[data-theme="vscode"] .info-box p {
  font-size: 14px;
  color: var(--vscode-text-secondary);
  margin-bottom: 8px;
}
</style>
