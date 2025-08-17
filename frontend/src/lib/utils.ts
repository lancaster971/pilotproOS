import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDate(date: Date | string | number) {
  try {
    if (!date) return 'N/A'
    const dateObj = new Date(date)
    if (isNaN(dateObj.getTime())) return 'Invalid Date'
    
    return new Intl.DateTimeFormat('it-IT', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(dateObj)
  } catch (error) {
    console.error('formatDate error:', error, 'for date:', date)
    return 'N/A'
  }
}

export function formatNumber(num: number) {
  return new Intl.NumberFormat('it-IT').format(num)
}

export function truncate(str: string, length: number) {
  return str.length > length ? str.substring(0, length) + '...' : str
}

export function getStatusColor(status: string) {
  const statusColors: Record<string, string> = {
    success: 'text-green-500 bg-green-500/10',
    error: 'text-red-500 bg-red-500/10',
    running: 'text-blue-500 bg-blue-500/10',
    waiting: 'text-yellow-500 bg-yellow-500/10',
    stopped: 'text-gray-500 bg-gray-500/10',
  }
  return statusColors[status.toLowerCase()] || 'text-gray-500 bg-gray-500/10'
}

export function getWorkflowTypeColor(type: string) {
  const typeColors: Record<string, string> = {
    critical: 'text-red-600 bg-red-100 dark:bg-red-900/20',
    production: 'text-blue-600 bg-blue-100 dark:bg-blue-900/20',
    development: 'text-green-600 bg-green-100 dark:bg-green-900/20',
    test: 'text-yellow-600 bg-yellow-100 dark:bg-yellow-900/20',
    audit: 'text-purple-600 bg-purple-100 dark:bg-purple-900/20',
  }
  return typeColors[type.toLowerCase()] || 'text-gray-600 bg-gray-100 dark:bg-gray-900/20'
}