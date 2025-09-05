<template>
  <div class="flow-root">
    <ul role="list" class="space-y-6">
      <li v-for="(event, eventIdx) in events" :key="event.id || eventIdx" class="relative flex gap-x-4">
        <div
          :class="[
            eventIdx === events.length - 1 ? 'h-6' : '-bottom-6',
            'absolute left-0 top-0 flex w-6 justify-center'
          ]"
        >
          <div class="w-px bg-border"></div>
        </div>
        <div
          :class="[
            'relative flex h-6 w-6 flex-none items-center justify-center rounded-full ring-1 ring-border',
            getEventBackgroundColor(event)
          ]"
        >
          <slot name="marker" :item="event" :index="eventIdx">
            <div :class="['h-1.5 w-1.5 rounded-full', getEventDotColor(event)]"></div>
          </slot>
        </div>
        <div class="flex-auto py-0.5 text-xs leading-5">
          <div class="flex justify-between gap-x-4">
            <slot name="content" :item="event" :index="eventIdx">
              <div>
                <div class="font-medium text-text">{{ event.title }}</div>
                <p class="text-text-muted">{{ event.description }}</p>
              </div>
              <div class="flex-none text-xs text-text-muted">
                {{ event.time }}
              </div>
            </slot>
          </div>
        </div>
      </li>
    </ul>
  </div>
</template>

<script setup lang="ts">
interface TimelineEvent {
  id?: string | number
  title: string
  description?: string
  time?: string
  type?: string
  [key: string]: any
}

interface Props {
  events: TimelineEvent[]
  layout?: 'vertical' | 'horizontal'
}

const props = withDefaults(defineProps<Props>(), {
  layout: 'vertical'
})

const getEventBackgroundColor = (event: TimelineEvent) => {
  switch (event.type) {
    case 'success':
      return 'bg-success ring-success/30'
    case 'error':
    case 'danger':
      return 'bg-error ring-error/30'
    case 'warning':
      return 'bg-warning ring-warning/30'
    case 'info':
      return 'bg-primary ring-primary/30'
    default:
      return 'bg-surface ring-border'
  }
}

const getEventDotColor = (event: TimelineEvent) => {
  switch (event.type) {
    case 'success':
      return 'bg-success'
    case 'error':
    case 'danger':
      return 'bg-error'
    case 'warning':
      return 'bg-warning'
    case 'info':
      return 'bg-primary'
    default:
      return 'bg-text-muted'
  }
}
</script>