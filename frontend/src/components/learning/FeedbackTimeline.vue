<template>
  <div class="feedback-timeline">
    <div class="timeline-header">
      <h3>Recent Feedback</h3>
      <div class="timeline-subtitle">Last 20 user interactions</div>
    </div>

    <!-- ALWAYS RENDER - Debug mode -->
    <Timeline :value="events" align="left" class="custom-timeline">
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
  padding: 16px;
  border: 1px solid #2a2a2a;
  max-height: 350px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.timeline-header {
  margin-bottom: 12px;
}

.timeline-header h3 {
  font-size: 14px;
  font-weight: 600;
  color: #ffffff;
  margin: 0 0 4px 0;
}

.timeline-subtitle {
  font-size: 11px;
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
  padding: 0 0 12px 16px;
  font-size: 11px !important;
}

.custom-timeline :deep(.p-timeline-event-opposite) {
  display: none;
}

.custom-timeline :deep(.p-timeline-event-connector) {
  background: #2a2a2a;
}

/* FORCE small fonts in all timeline content */
.custom-timeline :deep(*) {
  font-size: 11px !important;
}

/* Timeline marker */
.timeline-marker {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
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
  border-radius: 6px;
  padding: 8px 12px;
  border: 1px solid #2a2a2a;
}

.content-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.feedback-badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 9px !important;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.3px;
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
  font-size: 9px !important;
  color: #666666;
}

.content-body {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.content-row {
  display: flex;
  gap: 6px;
  font-size: 10px !important;
}

.label {
  font-weight: 600;
  color: #888888;
  min-width: 65px;
  font-size: 10px !important;
}

.value {
  color: #e5e5e5;
  flex: 1;
  word-break: break-word;
  font-size: 10px !important;
  line-height: 1.3 !important;
}

.category-tag {
  display: inline-flex;
  align-items: center;
  padding: 2px 6px;
  background: #2a2a2a;
  border-radius: 3px;
  font-size: 10px !important;
  color: #2563eb;
}

.reformulation-status {
  display: inline-flex;
  align-items: center;
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 9px !important;
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
    padding: 12px;
    max-height: 400px;
  }

  .timeline-header h3 {
    font-size: 13px;
  }

  .timeline-marker {
    width: 24px;
    height: 24px;
    font-size: 12px;
  }

  .timeline-content {
    padding: 8px 10px;
  }

  .content-row {
    flex-direction: column;
    gap: 3px;
  }

  .label {
    min-width: auto;
    font-size: 9px !important;
  }

  .value {
    font-size: 9px !important;
  }
}
</style>
