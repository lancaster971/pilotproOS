<template>
  <div class="feedback-timeline">
    <div class="timeline-header">
      <h3>Recent Feedback</h3>
      <div class="timeline-subtitle">Last 20 user interactions</div>
    </div>

    <div v-if="isLoading" class="timeline-loading">
      <i class="pi pi-spin pi-spinner" style="font-size: 2rem"></i>
      <p>Loading feedback...</p>
    </div>

    <div v-else-if="error" class="timeline-error">
      <i class="pi pi-exclamation-triangle"></i>
      <p>{{ error }}</p>
    </div>

    <div v-else-if="events.length === 0" class="timeline-empty">
      <i class="pi pi-inbox" style="font-size: 2rem"></i>
      <p>No feedback events yet</p>
      <span class="empty-hint">User feedback will appear here</span>
    </div>

    <Timeline v-else :value="events" align="left" class="custom-timeline">
      <template #marker="slotProps">
        <div :class="['timeline-marker', slotProps.item.feedback]">
          <Icon
            :icon="slotProps.item.feedback === 'positive' ? 'mdi:thumb-up' : 'mdi:thumb-down'"
          />
        </div>
      </template>

      <template #content="slotProps">
        <div class="timeline-content">
          <div class="content-header">
            <span :class="['feedback-badge', slotProps.item.feedback]">
              {{ slotProps.item.feedback === 'positive' ? 'Positive' : 'Negative' }}
            </span>
            <span class="timestamp">{{ formatRelativeTime(slotProps.item.timestamp) }}</span>
          </div>

          <div class="content-body">
            <div class="content-row">
              <span class="label">Query:</span>
              <span class="value">{{ truncate(slotProps.item.query, 60) }}</span>
            </div>
            <div class="content-row" v-if="slotProps.item.classification">
              <span class="label">Category:</span>
              <span class="category-tag">{{ formatCategory(slotProps.item.classification) }}</span>
            </div>
            <div class="content-row" v-if="slotProps.item.reformulation_shown">
              <span class="label">Reformulation:</span>
              <span :class="['reformulation-status', slotProps.item.reformulation_accepted ? 'accepted' : 'shown']">
                {{ slotProps.item.reformulation_accepted ? 'Accepted' : 'Shown' }}
              </span>
            </div>
          </div>
        </div>
      </template>
    </Timeline>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import Timeline from 'primevue/timeline'
import { Icon } from '@iconify/vue'
import type { FeedbackEvent } from '../../types/learning'

const props = defineProps<{
  events: FeedbackEvent[]
  isLoading?: boolean
  error?: string | null
}>()

// Format relative time (e.g., "2 hours ago")
const formatRelativeTime = (timestamp: string): string => {
  const date = new Date(timestamp)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMinutes = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMinutes / 60)
  const diffDays = Math.floor(diffHours / 24)

  if (diffMinutes < 1) return 'Just now'
  if (diffMinutes === 1) return '1 minute ago'
  if (diffMinutes < 60) return `${diffMinutes} minutes ago`
  if (diffHours === 1) return '1 hour ago'
  if (diffHours < 24) return `${diffHours} hours ago`
  if (diffDays === 1) return 'Yesterday'
  if (diffDays < 7) return `${diffDays} days ago`

  // Fallback to absolute date
  return date.toLocaleDateString('it-IT', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// Format category name
const formatCategory = (category: string): string => {
  return category
    .replace(/_/g, ' ')
    .split(' ')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

// Truncate text with ellipsis
const truncate = (text: string, length: number): string => {
  if (!text) return ''
  if (text.length <= length) return text
  return text.substring(0, length) + '...'
}
</script>

<style scoped>
.feedback-timeline {
  background: #1a1a1a;
  border-radius: 12px;
  padding: 20px;
  border: 1px solid #2a2a2a;
  max-height: 600px;
  overflow-y: auto;
}

.timeline-header {
  margin-bottom: 20px;
}

.timeline-header h3 {
  font-size: 18px;
  font-weight: 600;
  color: #ffffff;
  margin: 0 0 6px 0;
}

.timeline-subtitle {
  font-size: 13px;
  color: #888888;
}

.timeline-loading,
.timeline-error,
.timeline-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: #888888;
  padding: 60px 20px;
}

.timeline-error {
  color: #ef4444;
}

.timeline-error i {
  font-size: 2rem;
}

.timeline-loading p,
.timeline-error p,
.timeline-empty p {
  margin: 0;
  font-size: 14px;
}

.empty-hint {
  font-size: 12px;
  color: #666666;
}

/* Custom PrimeVue Timeline styling */
.custom-timeline :deep(.p-timeline-event-content) {
  padding: 0 0 20px 20px;
}

.custom-timeline :deep(.p-timeline-event-opposite) {
  display: none;
}

.custom-timeline :deep(.p-timeline-event-connector) {
  background: #2a2a2a;
}

/* Timeline marker */
.timeline-marker {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  border: 2px solid;
}

.timeline-marker.positive {
  background: rgba(16, 185, 129, 0.15);
  color: #10b981;
  border-color: #10b981;
}

.timeline-marker.negative {
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
  border-color: #ef4444;
}

/* Timeline content */
.timeline-content {
  background: #0a0a0a;
  border-radius: 8px;
  padding: 12px 16px;
  border: 1px solid #2a2a2a;
}

.content-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.feedback-badge {
  display: inline-flex;
  align-items: center;
  padding: 3px 10px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.feedback-badge.positive {
  background: rgba(16, 185, 129, 0.15);
  color: #10b981;
  border: 1px solid rgba(16, 185, 129, 0.3);
}

.feedback-badge.negative {
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
  border: 1px solid rgba(239, 68, 68, 0.3);
}

.timestamp {
  font-size: 11px;
  color: #666666;
}

.content-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.content-row {
  display: flex;
  gap: 8px;
  font-size: 13px;
}

.label {
  font-weight: 600;
  color: #888888;
  min-width: 80px;
}

.value {
  color: #e5e5e5;
  flex: 1;
  word-break: break-word;
}

.category-tag {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  background: #2a2a2a;
  border-radius: 4px;
  font-size: 12px;
  color: #2563eb;
}

.reformulation-status {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
}

.reformulation-status.shown {
  background: rgba(245, 158, 11, 0.15);
  color: #f59e0b;
  border: 1px solid rgba(245, 158, 11, 0.3);
}

.reformulation-status.accepted {
  background: rgba(16, 185, 129, 0.15);
  color: #10b981;
  border: 1px solid rgba(16, 185, 129, 0.3);
}

/* Scrollbar styling */
.feedback-timeline::-webkit-scrollbar {
  width: 6px;
}

.feedback-timeline::-webkit-scrollbar-track {
  background: transparent;
}

.feedback-timeline::-webkit-scrollbar-thumb {
  background: #2a2a2a;
  border-radius: 3px;
}

.feedback-timeline::-webkit-scrollbar-thumb:hover {
  background: #3a3a3a;
}

/* Mobile responsive */
@media (max-width: 768px) {
  .feedback-timeline {
    padding: 16px;
    max-height: 500px;
  }

  .timeline-header h3 {
    font-size: 16px;
  }

  .timeline-marker {
    width: 28px;
    height: 28px;
    font-size: 14px;
  }

  .timeline-content {
    padding: 10px 12px;
  }

  .content-row {
    flex-direction: column;
    gap: 4px;
  }

  .label {
    min-width: auto;
  }
}
</style>
