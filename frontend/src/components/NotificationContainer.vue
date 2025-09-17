<template>
  <Teleport to="body">
    <div class="notification-container">
      <TransitionGroup name="notification">
        <div
          v-for="notification in notifications"
          :key="notification.id"
          :class="[
            'notification',
            `notification--${notification.type}`
          ]"
        >
          <div class="notification__icon">
            <Icon v-if="notification.type === 'success'" icon="lucide:check-circle" />
            <Icon v-else-if="notification.type === 'error'" icon="lucide:x-circle" />
            <Icon v-else-if="notification.type === 'warning'" icon="lucide:alert-triangle" />
            <Icon v-else icon="lucide:info" />
          </div>
          <div class="notification__message">
            {{ notification.message }}
          </div>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { Icon } from '@iconify/vue'
import { useNotification } from '../composables/useNotification'

const { notifications } = useNotification()
</script>

<style scoped>
.notification-container {
  position: fixed;
  top: 120px;
  right: 20px;
  z-index: 99999;
  pointer-events: none;
}

.notification {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  margin-bottom: 12px;
  min-width: 300px;
  max-width: 500px;
  border-radius: 12px;
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  box-shadow:
    0 8px 32px rgba(0, 0, 0, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
  pointer-events: auto;
  animation: slideIn 0.3s ease-out;
}

/* Success */
.notification--success {
  background: linear-gradient(135deg,
    rgba(16, 185, 129, 0.15) 0%,
    rgba(5, 150, 105, 0.1) 100%);
  border: 1px solid rgba(16, 185, 129, 0.3);
  border-left: 4px solid #10b981;
}

.notification--success .notification__icon {
  color: #10b981;
  filter: drop-shadow(0 0 8px rgba(16, 185, 129, 0.5));
}

/* Error */
.notification--error {
  background: linear-gradient(135deg,
    rgba(239, 68, 68, 0.15) 0%,
    rgba(220, 38, 38, 0.1) 100%);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-left: 4px solid #ef4444;
}

.notification--error .notification__icon {
  color: #ef4444;
  filter: drop-shadow(0 0 8px rgba(239, 68, 68, 0.5));
}

/* Info */
.notification--info {
  background: linear-gradient(135deg,
    rgba(59, 130, 246, 0.15) 0%,
    rgba(37, 99, 235, 0.1) 100%);
  border: 1px solid rgba(59, 130, 246, 0.3);
  border-left: 4px solid #3b82f6;
}

.notification--info .notification__icon {
  color: #3b82f6;
  filter: drop-shadow(0 0 8px rgba(59, 130, 246, 0.5));
}

/* Warning */
.notification--warning {
  background: linear-gradient(135deg,
    rgba(251, 146, 60, 0.15) 0%,
    rgba(249, 115, 22, 0.1) 100%);
  border: 1px solid rgba(251, 146, 60, 0.3);
  border-left: 4px solid #fb923c;
}

.notification--warning .notification__icon {
  color: #fb923c;
  filter: drop-shadow(0 0 8px rgba(251, 146, 60, 0.5));
}

.notification__icon {
  font-size: 20px;
  flex-shrink: 0;
}

.notification__message {
  color: #f3f4f6;
  font-size: 14px;
  line-height: 1.5;
  flex: 1;
}

/* Animations */
@keyframes slideIn {
  from {
    transform: translateX(110%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

.notification-enter-active,
.notification-leave-active {
  transition: all 0.3s ease;
}

.notification-enter-from {
  transform: translateX(110%);
  opacity: 0;
}

.notification-leave-to {
  transform: translateX(110%);
  opacity: 0;
}
</style>