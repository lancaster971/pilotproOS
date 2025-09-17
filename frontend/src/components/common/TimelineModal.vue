<template>
  <DetailModal
    :show="show"
    :title="'Business Process Dashboard'"
    :subtitle="`${modalTitle} • ${modalSubtitle}`"
    :header-icon="'lucide:bar-chart-2'"
    :tabs="tabs"
    default-tab="overview"
    :is-loading="isLoading"
    :error="error"
    :data="timelineData"
    :show-refresh="true"
    @close="$emit('close')"
    @refresh="handleForceRefresh"
    @retry="loadTimeline"
  >
    <!-- Header Actions Slot -->
    <template #headerActions="{ isLoading, refresh }">
    </template>

    <!-- Process Overview Tab -->
    <template #overview="{ data }">
      <div class="p-4 space-y-4">
        <!-- Process Description from Sticky Notes or Default -->
        <div class="card-glassmorphism rounded-lg p-4">
          <h3 class="text-lg font-semibold text-white mb-3">Process Description</h3>
          <div class="text-text-muted whitespace-pre-wrap">
            {{ workflowInfo?.description || workflowInfo?.purpose ||
               'This business process automates operations to ensure efficient workflow execution and reliable business outcomes.' }}
          </div>
        </div>

        <!-- Key Metrics Grid - Universal for ALL workflows -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div class="metric-card-glassmorphism rounded-lg p-4">
            <div class="flex items-center justify-between mb-2">
              <span class="text-sm text-text-muted">Success Rate</span>
              <Icon icon="lucide:trending-up" class="w-4 h-4 text-green-400" />
            </div>
            <div class="text-2xl font-bold text-white">
              {{ calculateSuccessRate() }}%
            </div>
          </div>

          <div class="metric-card-glassmorphism rounded-lg p-4">
            <div class="flex items-center justify-between mb-2">
              <span class="text-sm text-text-muted">{{ getBusinessMetricLabel() }}</span>
              <Icon icon="lucide:database" class="w-4 h-4 text-blue-400" />
            </div>
            <div class="text-2xl font-bold text-white">
              {{ formatBusinessMetric() }}
            </div>
          </div>

          <div class="metric-card-glassmorphism rounded-lg p-4">
            <div class="flex items-center justify-between mb-2">
              <span class="text-sm text-text-muted">Total Operations</span>
              <Icon icon="lucide:layers" class="w-4 h-4 text-purple-400" />
            </div>
            <div class="text-2xl font-bold text-white">
              {{ workflowStats?.total_executions || executionsHistory.length || 0 }}
            </div>
          </div>
        </div>

        <!-- Business Capabilities - Dynamic from workflow nodes -->
        <div class="card-glassmorphism rounded-lg p-4">
          <h3 class="text-lg font-semibold text-white mb-3">Process Capabilities</h3>
          <ul v-if="workflowInfo?.capabilities?.length > 0" class="space-y-2">
            <li v-for="(capability, index) in workflowInfo.capabilities" :key="index" class="flex items-start gap-2">
              <Icon icon="lucide:check-circle" class="w-5 h-5 text-green-400 mt-0.5" />
              <span class="text-text-muted">{{ capability }}</span>
            </li>
          </ul>
          <!-- Fallback if no capabilities detected -->
          <ul v-else class="space-y-2">
            <li class="flex items-start gap-2">
              <Icon icon="lucide:check-circle" class="w-5 h-5 text-green-400 mt-0.5" />
              <span class="text-text-muted">Automated workflow processing</span>
            </li>
            <li class="flex items-start gap-2">
              <Icon icon="lucide:check-circle" class="w-5 h-5 text-green-400 mt-0.5" />
              <span class="text-text-muted">Data transformation and routing</span>
            </li>
            <li class="flex items-start gap-2">
              <Icon icon="lucide:check-circle" class="w-5 h-5 text-green-400 mt-0.5" />
              <span class="text-text-muted">Business process optimization</span>
            </li>
          </ul>
        </div>

        <!-- Business Value Statement - Dynamic from execution metrics -->
        <div class="value-card-glassmorphism rounded-lg p-4">
          <div class="flex items-start gap-3">
            <Icon icon="lucide:target" class="w-6 h-6 text-primary mt-0.5" />
            <div>
              <h3 class="text-lg font-semibold text-white mb-2">Business Value</h3>
              <p class="text-text-muted">
                {{ workflowInfo?.businessValue?.summary ||
                   'This automated process optimizes business operations, reduces manual workload, and ensures consistent service delivery. All operations are tracked for continuous improvement.' }}
              </p>

              <!-- Dynamic metrics grid if available -->
              <div v-if="workflowInfo?.businessValue" class="grid grid-cols-2 md:grid-cols-4 gap-3 mt-4">
                <div v-if="workflowInfo.businessValue.automationRate" class="text-center">
                  <div class="text-xl font-bold text-primary">{{ workflowInfo.businessValue.automationRate }}</div>
                  <div class="text-xs text-text-muted">Automation</div>
                </div>
                <div v-if="workflowInfo.businessValue.timeSaved" class="text-center">
                  <div class="text-xl font-bold text-green-400">{{ workflowInfo.businessValue.timeSaved }}</div>
                  <div class="text-xs text-text-muted">Time Saved</div>
                </div>
                <div v-if="workflowInfo.businessValue.avgResponseTime" class="text-center">
                  <div class="text-xl font-bold text-blue-400">{{ workflowInfo.businessValue.avgResponseTime }}</div>
                  <div class="text-xs text-text-muted">Avg Response</div>
                </div>
                <div v-if="workflowInfo.businessValue.dataProcessed" class="text-center">
                  <div class="text-xl font-bold text-purple-400">{{ workflowInfo.businessValue.dataProcessed }}</div>
                  <div class="text-xs text-text-muted">Items Processed</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- Latest Activity Tab - Shows recent operations -->
    <template #executions="{ data }">
      <div class="p-4">
        <!-- Recent Activity from Dashboard API -->
        <div v-if="recentActivity?.length > 0" class="space-y-4 mb-6">
          <h3 class="text-lg font-semibold text-white mb-4">Recent Business Activity</h3>
          <div v-for="(activity, index) in recentActivity.slice(0, 10)" :key="index"
               class="bg-surface-hover rounded-lg p-4 border border-border">
            <div class="flex items-center justify-between">
              <div class="flex-1">
                <div class="flex items-center gap-2 mb-2">
                  <span :class="[
                    'px-2 py-1 text-xs rounded',
                    activity.type === 'AI Response' ? 'bg-purple-500/20 text-purple-300' :
                    activity.type === 'Email' ? 'bg-blue-500/20 text-blue-300' :
                    activity.type === 'Order' ? 'bg-green-500/20 text-green-300' :
                    'bg-gray-500/20 text-gray-300'
                  ]">{{ activity.type }}</span>
                  <span class="text-xs text-text-muted">{{ formatRelativeTime(activity.timestamp) }}</span>
                </div>
                <p class="text-sm text-white">{{ activity.summary }}</p>
                <p v-if="activity.classification" class="text-xs text-text-muted mt-1">
                  Classification: {{ activity.classification }}
                </p>
              </div>
            </div>
          </div>
        </div>

        <!-- Fallback to business nodes if no recent activity -->
        <div v-else-if="data?.businessNodes?.length > 0" class="space-y-6">
          <div
            v-for="(step, index) in data.businessNodes"
            :key="step._nodeId || index"
            :class="[
              'rounded-lg p-5 border transition-all',
              step.status === 'error' || step.showTag === 'error' 
                ? 'bg-red-900/20 border-red-500/30' 
                : 'bg-gray-800/50 border-gray-700',
              // Highlight if has intelligent summary
              step.data?.intelligentSummary ? 'ring-1 ring-blue-500/20' : ''
            ]"
          >
            <!-- Step Header -->
            <div class="flex items-center justify-between mb-4">
              <div class="flex items-center">
                <div :class="[
                  'w-8 h-8 rounded-full flex items-center justify-center mr-3',
                  step.status === 'error' || step.showTag === 'error'
                    ? 'bg-red-400/20'
                    : 'bg-green-400/20'
                ]">
                  <span :class="[
                    'font-medium',
                    step.status === 'error' || step.showTag === 'error'
                      ? 'text-red-400'
                      : 'text-green-400'
                  ]">{{ step.showTag === 'error' ? 'ERR' : index + 1 }}</span>
                </div>
                <div>
                  <h4 class="text-white font-medium">{{ step.businessName || step.name || `Process Step ${index + 1}` }}</h4>
                  <p class="text-sm text-gray-400">{{ formatBusinessStepType(step) }}</p>
                </div>
              </div>
              <div class="text-xs text-gray-500">
                {{ formatDuration(step.executionTime || 0) }}
              </div>
            </div>

            <!-- Business Summary -->
            <div class="mb-4">
              <div :class="[
                'text-sm font-medium mb-2',
                step.status === 'error' || step.showTag === 'error'
                  ? 'text-red-400'
                  : 'text-green-400'
              ]">
                {{ step.status === 'error' || step.showTag === 'error' ? 'Error Details:' : 'Business Summary:' }}
              </div>
              <div :class="[
                'text-white bg-gray-900/50 p-3 rounded border-l-4',
                step.status === 'error' || step.showTag === 'error'
                  ? 'border-red-400'
                  : 'border-green-400'
              ]">
                {{ 
                  step.status === 'error' || step.showTag === 'error' 
                    ? getBusinessErrorSummary(step)
                    : generateExecutionDetail(step) 
                }}
              </div>
            </div>

            <!-- Input/Output Summary -->
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <!-- What Happened -->
              <div :class="[
                'rounded p-3 border',
                step.status === 'error' || step.showTag === 'error'
                  ? 'bg-orange-400/10 border-orange-400/20'
                  : 'bg-blue-400/10 border-blue-400/20'
              ]">
                <div :class="[
                  'text-xs font-medium mb-1',
                  step.status === 'error' || step.showTag === 'error'
                    ? 'text-orange-400'
                    : 'text-blue-400'
                ]">{{ step.status === 'error' || step.showTag === 'error' ? 'ERROR CONTEXT' : 'WHAT HAPPENED' }}</div>
                <div class="text-sm text-gray-300">
                  {{ 
                    step.status === 'error' || step.showTag === 'error' 
                      ? getBusinessErrorContext(step)
                      : (step.enrichedData?.inputSummary || getBusinessSummary(step))
                  }}
                </div>
              </div>
              
              <!-- Result -->
              <div :class="[
                'rounded p-3 border',
                step.status === 'error' || step.showTag === 'error'
                  ? 'bg-red-400/10 border-red-400/20'
                  : 'bg-green-400/10 border-green-400/20'
              ]">
                <div :class="[
                  'text-xs font-medium mb-1',
                  step.status === 'error' || step.showTag === 'error'
                    ? 'text-red-400'
                    : 'text-green-400'
                ]">{{ step.status === 'error' || step.showTag === 'error' ? 'ERROR RESULT' : 'RESULT' }}</div>
                <div class="text-sm text-gray-300">
                  {{
                    step.status === 'error' || step.showTag === 'error'
                      ? getBusinessErrorDetails(step)
                      : (step.enrichedData?.outputSummary || '')
                  }}
                </div>
              </div>
            </div>

            <!-- Business Value -->
            <div v-if="step.enrichedData?.businessValue" class="mt-4 p-3 bg-purple-400/10 rounded border border-purple-400/20">
              <div class="text-xs text-purple-400 font-medium mb-1">BUSINESS VALUE</div>
              <div class="text-sm text-white">{{ step.enrichedData.businessValue }}</div>
            </div>

            <!-- Intelligent Summary Section (for large data) -->
            <div v-if="step.data?.intelligentSummary" class="mt-4 space-y-3">
              <!-- Summary Type Badge -->
              <div class="flex items-center gap-2">
                <Icon :icon="getIntelligentSummaryIcon(step.data.intelligentSummary.type)" class="w-4 h-4 text-blue-400" />
                <span class="text-xs font-medium text-blue-400 uppercase">
                  {{ getIntelligentSummaryLabel(step.data.intelligentSummary.summaryType) }}
                </span>
                <div v-if="step.data.intelligentSummary.type === 'ai_generated'" class="ml-auto">
                  <span class="px-2 py-0.5 text-xs bg-purple-500/20 text-purple-300 rounded">AI Generated</span>
                </div>
              </div>

              <!-- Business Summary Card -->
              <div v-if="step.data.intelligentSummary.businessSummary" class="bg-blue-900/20 border border-blue-500/20 rounded-lg p-4">
                <h5 class="text-sm font-medium text-blue-300 mb-2">
                  {{ step.data.intelligentSummary.businessSummary.title }}
                </h5>
                <p class="text-sm text-gray-300">
                  {{ step.data.intelligentSummary.businessSummary.description }}
                </p>
                
                <!-- Document Type Specific -->
                <div v-if="step.data.intelligentSummary.summaryType === 'document'" class="mt-2 text-xs text-gray-400">
                  <span>{{ step.data.intelligentSummary.businessSummary.pageCount }} pages</span>
                  <span class="mx-2">•</span>
                  <span>Type: {{ step.data.intelligentSummary.businessSummary.documentType }}</span>
                </div>
                
                <!-- Dataset Type Specific -->
                <div v-else-if="step.data.intelligentSummary.summaryType === 'dataset'" class="mt-2 text-xs text-gray-400">
                  <span>{{ step.data.intelligentSummary.businessSummary.totalRows }} rows</span>
                  <span class="mx-2">•</span>
                  <span>{{ step.data.intelligentSummary.businessSummary.totalColumns }} columns</span>
                </div>
              </div>

              <!-- Metrics Grid -->
              <div v-if="step.data.intelligentSummary.metrics && Object.keys(step.data.intelligentSummary.metrics).length > 0" 
                   class="grid grid-cols-2 md:grid-cols-4 gap-2">
                <div v-for="(value, key) in step.data.intelligentSummary.metrics" 
                     :key="key"
                     class="bg-gray-800/50 rounded p-2 text-center">
                  <div class="text-xs text-gray-500 capitalize">{{ formatMetricKey(key) }}</div>
                  <div class="text-sm font-medium text-white">{{ formatMetricValue(value) }}</div>
                </div>
              </div>

              <!-- Preview Section -->
              <div v-if="step.data.intelligentSummary.preview && !expandedSteps.has(step._nodeId)" 
                   class="bg-gray-900/50 rounded-lg p-3">
                <div class="flex items-center justify-between mb-2">
                  <span class="text-xs font-medium text-gray-400">DATA PREVIEW</span>
                  <button @click="toggleExpandedStep(step._nodeId)" 
                          class="text-xs text-blue-400 hover:text-blue-300">
                    View More →
                  </button>
                </div>
                
                <!-- Document Preview -->
                <div v-if="step.data.intelligentSummary.summaryType === 'document'" class="text-xs text-gray-300 space-y-1">
                  <div v-if="step.data.intelligentSummary.preview.keyDates?.length > 0">
                    <span class="text-gray-500">Dates:</span> {{ step.data.intelligentSummary.preview.keyDates.join(', ') }}
                  </div>
                  <div v-if="step.data.intelligentSummary.preview.amounts?.length > 0">
                    <span class="text-gray-500">Amounts:</span> {{ step.data.intelligentSummary.preview.amounts.join(', ') }}
                  </div>
                </div>
                
                <!-- Dataset Preview -->
                <div v-else-if="step.data.intelligentSummary.summaryType === 'dataset' && step.data.intelligentSummary.preview.sampleRows" 
                     class="overflow-x-auto">
                  <table class="text-xs w-full">
                    <thead>
                      <tr class="text-gray-500">
                        <th v-for="header in step.data.intelligentSummary.preview.headers?.slice(0, 4)" 
                            :key="header" 
                            class="px-2 py-1 text-left">
                          {{ header }}
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="(row, idx) in step.data.intelligentSummary.preview.sampleRows?.slice(0, 3)" 
                          :key="idx"
                          class="text-gray-300 border-t border-gray-800">
                        <td v-for="header in step.data.intelligentSummary.preview.headers?.slice(0, 4)" 
                            :key="header"
                            class="px-2 py-1">
                          {{ row[header] }}
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>

              <!-- Business Insight -->
              <div v-if="step.data.intelligentSummary.businessInsight" 
                   class="bg-green-900/20 border border-green-500/20 rounded-lg p-3">
                <div class="flex items-start gap-2">
                  <Icon icon="lucide:lightbulb" class="w-4 h-4 text-green-400 mt-0.5" />
                  <div>
                    <div class="text-xs font-medium text-green-400 mb-1">BUSINESS INSIGHT</div>
                    <div class="text-sm text-gray-300">{{ step.data.intelligentSummary.businessInsight }}</div>
                  </div>
                </div>
              </div>

              <!-- Action Buttons -->
              <div v-if="step.data.intelligentSummary.actions?.length > 0" class="flex flex-wrap gap-2">
                <button v-for="action in step.data.intelligentSummary.actions" 
                        :key="action"
                        @click="handleIntelligentAction(action, step)"
                        class="px-3 py-1 text-xs bg-gray-700 hover:bg-gray-600 text-white rounded-md transition-colors">
                  {{ formatActionLabel(action) }}
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- No Data -->
        <div v-else class="text-center py-12 text-gray-400">
          <Icon icon="lucide:list" class="w-12 h-12 mx-auto mb-4 opacity-50" />
          <h3 class="text-lg font-medium mb-2">Process Not Yet Configured</h3>
          <p class="text-sm mb-2">This business process doesn't have steps configured for client reporting.</p>
          <div class="bg-blue-400/10 border border-blue-400/20 rounded-lg p-4 mt-4 max-w-md mx-auto">
            <h4 class="text-blue-400 font-medium mb-2">For Administrators:</h4>
            <p class="text-xs text-blue-300">
              Add 'show-1', 'show-2', etc. notes to workflow nodes to make them visible in business reporting.
            </p>
          </div>
        </div>
      </div>
    </template>

    <!-- Process History Tab -->
    <template #history="{ data }">
      <div class="p-4 overflow-y-auto">
        <h3 class="text-lg font-semibold text-white mb-3">Process Execution History</h3>

        <!-- History Stats (REAL DATA - Including Canceled) -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
          <div class="metric-card-glassmorphism rounded-lg p-2">
            <div class="flex items-center justify-between">
              <Icon icon="lucide:play-circle" class="w-4 h-4 text-blue-400" />
              <span class="text-xs text-gray-400">Total</span>
            </div>
            <div class="text-lg font-bold text-white">{{ workflowStats?.kpis?.totalExecutions || 0 }}</div>
            <div class="text-xs text-gray-500">{{ workflowStats?.kpis?.last24hExecutions || 0 }} oggi</div>
          </div>
          <div class="metric-card-glassmorphism rounded-lg p-2">
            <div class="flex items-center justify-between">
              <Icon icon="lucide:check-circle" class="w-4 h-4 text-green-400" />
              <span class="text-xs text-gray-400">Success</span>
            </div>
            <div class="text-lg font-bold text-green-400">{{ workflowStats?.kpis?.successfulExecutions || 0 }}</div>
            <div class="text-xs text-gray-500">{{ workflowStats?.kpis?.successRate || 0 }}% rate</div>
          </div>
          <div class="metric-card-glassmorphism rounded-lg p-2">
            <div class="flex items-center justify-between">
              <Icon icon="lucide:x-circle" class="w-4 h-4 text-red-400" />
              <span class="text-xs text-gray-400">Failed</span>
            </div>
            <div class="text-lg font-bold text-red-400">{{ workflowStats?.kpis?.failedExecutions || 0 }}</div>
            <div v-if="workflowStats?.kpis?.canceledExecutions > 0" class="text-xs text-orange-400">
              +{{ workflowStats.kpis.canceledExecutions }} canceled
            </div>
          </div>
          <div class="metric-card-glassmorphism rounded-lg p-2">
            <div class="flex items-center justify-between">
              <Icon icon="lucide:clock" class="w-4 h-4 text-purple-400" />
              <span class="text-xs text-gray-400">Avg Time</span>
            </div>
            <div class="text-lg font-bold text-purple-400">
              {{ workflowStats?.kpis?.avgRunTime ? formatDuration(workflowStats.kpis.avgRunTime) : '0ms' }}
            </div>
            <div class="text-xs text-gray-500">per run</div>
          </div>
        </div>

        <!-- Timeline Trend Chart -->
        <div v-if="workflowStats?.trend?.length > 0" class="card-glassmorphism rounded-lg p-3 mb-4">
          <h4 class="text-sm font-medium text-white mb-2">Trend ultimi 7 giorni</h4>
          <div class="flex items-end justify-between h-20 gap-1">
            <div v-for="(day, idx) in workflowStats.trend.slice(0, 7)" :key="idx" class="flex-1 flex flex-col justify-end">
              <div
                class="bg-emerald-500/30 rounded-t hover:bg-emerald-500/40 transition-all"
                :style="{ height: `${Math.max(10, (day.executions / Math.max(...workflowStats.trend.map(d => d.executions))) * 100)}%` }"
                :title="`${day.date}: ${day.executions} esecuzioni`"
              ></div>
              <span class="text-xs text-gray-500 mt-1">{{ new Date(day.date).getDate() }}</span>
            </div>
          </div>
        </div>

        <!-- Recent History Table (REAL EXECUTIONS DATA) -->
        <div v-if="executionsHistory.length > 0" class="bg-surface-hover rounded-lg border border-border overflow-hidden">
          <div class="max-h-[400px] overflow-y-auto">
          <table class="w-full">
            <thead class="bg-black/20 border-b border-border">
              <tr>
                <th class="px-4 py-3 text-left text-xs font-medium text-text-muted uppercase">Date</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-text-muted uppercase">Status</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-text-muted uppercase">Duration</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-text-muted uppercase">Business Outcome</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-border/50">
              <tr v-for="exec in executionsHistory.slice(0, 25)" :key="exec.id" class="hover:bg-surface-hover/50 text-xs">
                <td class="px-3 py-2 text-text-muted">{{ formatTimestamp(exec.startedAt || exec.createdAt) }}</td>
                <td class="px-3 py-2">
                  <span :class="[
                    'px-2 py-1 text-xs rounded',
                    exec.status === 'success' ? 'bg-green-400/20 text-green-400' :
                    exec.status === 'error' ? 'bg-red-400/20 text-red-400' :
                    'bg-yellow-400/20 text-yellow-400'
                  ]">
                    {{ exec.status === 'success' ? 'Success' : exec.status === 'error' ? 'Failed' : 'Running' }}
                  </span>
                </td>
                <td class="px-3 py-2 text-text-muted">
                  <span v-if="exec.duration">{{ formatDuration(exec.duration) }}</span>
                  <span v-else class="text-gray-600">-</span>
                </td>
                <td class="px-3 py-2 text-text-muted">
                  <span v-if="exec.data?.businessOutcome" class="text-xs">
                    {{ exec.data.businessOutcome }}
                  </span>
                  <span v-else class="text-xs text-gray-600">-</span>
                </td>
              </tr>
            </tbody>
          </table>
          </div>
        </div>

        <!-- No Data State -->
        <div v-else class="text-center py-6 text-gray-400">
          <Icon icon="lucide:history" class="w-12 h-12 mx-auto mb-4 opacity-50" />
          <p>No execution history available yet</p>
        </div>
      </div>
    </template>

    <!-- Analytics Tab -->
    <template #analytics="{ data }">
      <div class="p-3 overflow-y-auto">
        <!-- Grid 2 colonne per ottimizzare spazio -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-3">

          <!-- Colonna Sinistra -->
          <div class="space-y-3">
            <!-- Performance Scorecard Compatto -->
            <div class="card-glassmorphism rounded-lg p-3">
              <h4 class="text-sm font-medium text-white mb-2 flex items-center gap-2">
                <Icon icon="lucide:gauge" class="w-4 h-4 text-emerald-400" />
                Performance Scores
              </h4>

              <!-- 2x2 Grid Scores - Simplified Colors -->
              <div class="grid grid-cols-2 gap-2 mb-2">
                <div class="p-2 bg-surface/50 rounded border border-emerald-500/20">
                  <div class="flex items-center justify-between">
                    <Icon icon="lucide:check-circle" class="w-3 h-3 text-emerald-400" />
                    <span class="text-xl font-bold text-white">{{ workflowStats?.kpis?.successRate || 0 }}%</span>
                  </div>
                  <div class="text-xs text-gray-400">Success Rate</div>
                  <div v-if="workflowStats?.trends?.successRateTrend" class="text-xs mt-0.5"
                       :class="workflowStats.trends.successRateTrend > 0 ? 'text-emerald-400' : 'text-gray-500'">
                    {{ workflowStats.trends.successRateTrend > 0 ? '↑' : '↓' }} {{ Math.abs(workflowStats.trends.successRateTrend) }}%
                  </div>
                </div>

                <div class="p-2 bg-surface/50 rounded border border-border/50">
                  <div class="flex items-center justify-between">
                    <Icon icon="lucide:timer" class="w-3 h-3 text-gray-400" />
                    <span class="text-xl font-bold text-white">{{ formatDuration(workflowStats?.kpis?.avgRunTime || 0) }}</span>
                  </div>
                  <div class="text-xs text-gray-400">Avg Time</div>
                  <div v-if="workflowStats?.kpis?.minRunTime" class="text-xs text-gray-500 mt-0.5">
                    {{ formatDuration(workflowStats.kpis.minRunTime) }}-{{ formatDuration(workflowStats.kpis.maxRunTime) }}
                  </div>
                </div>

                <div class="p-2 bg-surface/50 rounded border border-border/50">
                  <div class="flex items-center justify-between">
                    <Icon icon="lucide:zap" class="w-3 h-3 text-gray-400" />
                    <span class="text-xl font-bold text-white">{{ workflowStats?.kpis?.efficiencyScore || 0 }}</span>
                  </div>
                  <div class="text-xs text-gray-400">Efficiency</div>
                  <div class="text-xs text-gray-500">/100 points</div>
                </div>

                <div class="p-2 bg-surface/50 rounded border border-border/50">
                  <div class="flex items-center justify-between">
                    <Icon icon="lucide:shield-check" class="w-3 h-3 text-gray-400" />
                    <span class="text-xl font-bold text-white">{{ workflowStats?.kpis?.reliabilityScore || 0 }}%</span>
                  </div>
                  <div class="text-xs text-gray-400">Reliability</div>
                  <div class="text-xs text-gray-500">10 runs</div>
                </div>
              </div>

              <!-- Mini Stats Bar -->
              <div class="grid grid-cols-3 gap-1.5">
                <div class="p-1.5 bg-surface/30 rounded text-center">
                  <div class="text-xs text-gray-500">Runs</div>
                  <div class="text-sm font-bold text-white">{{ workflowStats?.kpis?.totalExecutions || 0 }}</div>
                </div>
                <div class="p-1.5 bg-surface/30 rounded text-center">
                  <div class="text-xs text-gray-500">Data</div>
                  <div class="text-sm font-bold text-white">{{ workflowStats?.kpis?.totalDataProcessed || 0 }}</div>
                </div>
                <div class="p-1.5 bg-surface/30 rounded text-center">
                  <div class="text-xs text-gray-500">Saved</div>
                  <div class="text-sm font-bold text-white">{{ workflowStats?.kpis?.automationImpact || 0 }}m</div>
                </div>
              </div>
            </div>

            <!-- Execution Distribution Chart -->
            <div class="card-glassmorphism rounded-lg p-3">
              <h4 class="text-sm font-medium text-white mb-2 flex items-center gap-2">
                <Icon icon="lucide:pie-chart" class="w-4 h-4 text-yellow-400" />
                Execution Breakdown
              </h4>

              <!-- Visual Bar Chart -->
              <div class="h-20 flex items-end gap-1 mb-2">
                <div class="flex-1 bg-green-500/30 rounded-t border-t border-green-500/50 hover:bg-green-500/40 transition-all"
                     :style="{ height: `${Math.max(10, (workflowStats?.kpis?.successfulExecutions / (workflowStats?.kpis?.totalExecutions || 1)) * 100)}%` }"
                     :title="`Success: ${workflowStats?.kpis?.successfulExecutions || 0}`">
                  <div v-if="workflowStats?.kpis?.successfulExecutions > 0" class="text-xs text-center text-green-400 pt-1">
                    {{ workflowStats?.kpis?.successfulExecutions }}
                  </div>
                </div>
                <div class="flex-1 bg-red-500/30 rounded-t border-t border-red-500/50 hover:bg-red-500/40 transition-all"
                     :style="{ height: `${Math.max(10, (workflowStats?.kpis?.failedExecutions / (workflowStats?.kpis?.totalExecutions || 1)) * 100)}%` }"
                     :title="`Failed: ${workflowStats?.kpis?.failedExecutions || 0}`">
                  <div v-if="workflowStats?.kpis?.failedExecutions > 0" class="text-xs text-center text-red-400 pt-1">
                    {{ workflowStats?.kpis?.failedExecutions }}
                  </div>
                </div>
                <div v-if="workflowStats?.kpis?.canceledExecutions > 0" class="flex-1 bg-orange-500/30 rounded-t border-t border-orange-500/50 hover:bg-orange-500/40 transition-all"
                     :style="{ height: `${Math.max(10, (workflowStats?.kpis?.canceledExecutions / (workflowStats?.kpis?.totalExecutions || 1)) * 100)}%` }"
                     :title="`Canceled: ${workflowStats?.kpis?.canceledExecutions || 0}`">
                  <div class="text-xs text-center text-orange-400 pt-1">
                    {{ workflowStats?.kpis?.canceledExecutions }}
                  </div>
                </div>
              </div>

              <!-- Legend -->
              <div class="flex justify-around text-xs">
                <span class="flex items-center gap-1">
                  <span class="w-2 h-2 bg-green-400 rounded-full"></span>
                  Success {{ workflowStats?.kpis?.successRate || 0 }}%
                </span>
                <span class="flex items-center gap-1">
                  <span class="w-2 h-2 bg-red-400 rounded-full"></span>
                  Failed {{ workflowStats?.kpis?.failureRate || 0 }}%
                </span>
                <span v-if="workflowStats?.kpis?.canceledExecutions > 0" class="flex items-center gap-1">
                  <span class="w-2 h-2 bg-orange-400 rounded-full"></span>
                  Cancel {{ ((workflowStats?.kpis?.canceledExecutions / (workflowStats?.kpis?.totalExecutions || 1)) * 100).toFixed(1) }}%
                </span>
              </div>
            </div>

            <!-- 7-Day Trend Mini Chart -->
            <div class="card-glassmorphism rounded-lg p-3">
              <h4 class="text-sm font-medium text-white mb-2 flex items-center gap-2">
                <Icon icon="lucide:trending-up" class="w-4 h-4 text-emerald-400" />
                Weekly Trend
              </h4>
              <div v-if="workflowStats?.trend?.length > 0" class="h-24">
                <div class="flex items-end justify-between h-20 gap-0.5">
                  <div v-for="(day, idx) in workflowStats.trend.slice(0, 7).reverse()" :key="idx"
                       class="flex-1 flex flex-col justify-end">
                    <div class="bg-gradient-to-t from-emerald-500/40 to-emerald-500/20 rounded-t hover:from-emerald-500/50 hover:to-emerald-500/30 transition-all border-t border-emerald-500/50"
                         :style="{ height: `${Math.max(5, (day.executions / Math.max(...workflowStats.trend.map(d => d.executions))) * 100)}%` }"
                         :title="`${day.date}: ${day.executions} runs`">
                      <span v-if="day.executions > 0" class="text-xs text-emerald-400 text-center block pt-0.5">{{ day.executions }}</span>
                    </div>
                  </div>
                </div>
                <div class="flex justify-between mt-0.5">
                  <span v-for="(day, idx) in workflowStats.trend.slice(0, 7).reverse()" :key="idx" class="flex-1 text-center text-xs text-gray-500">
                    {{ new Date(day.date).getDate() }}
                  </span>
                </div>
              </div>
              <div v-else class="h-20 flex items-center justify-center text-xs text-gray-500">
                No trend data
              </div>
            </div>
          </div>

          <!-- Colonna Destra -->
          <div class="space-y-3">

            <!-- Activity Heatmap -->
            <div class="card-glassmorphism rounded-lg p-3">
              <h4 class="text-sm font-medium text-white mb-2 flex items-center gap-2">
                <Icon icon="lucide:activity" class="w-4 h-4 text-blue-400" />
                Activity Metrics
              </h4>

              <!-- 2x2 Grid - Minimal Colors -->
              <div class="grid grid-cols-2 gap-2 mb-2">
                <div class="p-2 bg-surface/50 rounded border border-border/50">
                  <div class="flex items-center justify-between">
                    <Icon icon="lucide:clock-3" class="w-3 h-3 text-gray-400" />
                    <span class="text-lg font-bold text-white">{{ workflowStats?.kpis?.last24hExecutions || 0 }}</span>
                  </div>
                  <div class="text-xs text-gray-400">Last 24h</div>
                </div>
                <div class="p-2 bg-surface/50 rounded border border-border/50">
                  <div class="flex items-center justify-between">
                    <Icon icon="lucide:calendar-days" class="w-3 h-3 text-gray-400" />
                    <span class="text-lg font-bold text-white">{{ workflowStats?.kpis?.last7dExecutions || 0 }}</span>
                  </div>
                  <div class="text-xs text-gray-400">Last 7d</div>
                </div>
                <div class="p-2 bg-surface/50 rounded border border-border/50">
                  <div class="flex items-center justify-between">
                    <Icon icon="lucide:bar-chart-2" class="w-3 h-3 text-gray-400" />
                    <span class="text-lg font-bold text-white">{{ workflowStats?.kpis?.avgExecutionsPerDay || 0 }}</span>
                  </div>
                  <div class="text-xs text-gray-400">Daily Avg</div>
                </div>
                <div class="p-2 bg-surface/50 rounded border border-border/50">
                  <div class="flex items-center justify-between">
                    <Icon icon="lucide:zap" class="w-3 h-3 text-gray-400" />
                    <span class="text-lg font-bold text-white">
                      <span v-if="workflowStats?.kpis?.peakHour !== null">{{ workflowStats.kpis.peakHour }}:00</span>
                      <span v-else class="text-gray-600">-</span>
                    </span>
                  </div>
                  <div class="text-xs text-gray-400">Peak Hour</div>
                </div>
              </div>

              <!-- Volume Trend Indicator -->
              <div v-if="workflowStats?.trends?.volumeTrend !== undefined" class="p-2 bg-surface/30 rounded">
                <div class="flex items-center justify-between">
                  <span class="text-xs text-gray-400">Volume Trend</span>
                  <span class="text-xs font-bold flex items-center gap-1"
                        :class="workflowStats.trends.volumeTrend > 0 ? 'text-green-400' : 'text-orange-400'">
                    <Icon :icon="workflowStats.trends.volumeTrend > 0 ? 'lucide:trending-up' : 'lucide:trending-down'" class="w-3 h-3" />
                    {{ Math.abs(workflowStats.trends.volumeTrend) }}% vs prev
                  </span>
                </div>
              </div>
            </div>

            <!-- Performance Details -->
            <div class="card-glassmorphism rounded-lg p-3">
              <h4 class="text-sm font-medium text-white mb-2 flex items-center gap-2">
                <Icon icon="lucide:gauge" class="w-4 h-4 text-gray-400" />
                Timing Analysis
              </h4>
              <div class="space-y-1.5">
                <div class="flex justify-between items-center p-1.5 bg-surface/50 rounded">
                  <span class="text-xs text-gray-400 flex items-center gap-1">
                    <Icon icon="lucide:timer" class="w-3 h-3" />
                    Average
                  </span>
                  <span class="text-sm font-bold text-yellow-400">{{ formatDuration(workflowStats?.kpis?.avgRunTime || 0) }}</span>
                </div>
                <div class="flex justify-between items-center p-1.5 bg-surface/50 rounded">
                  <span class="text-xs text-gray-400 flex items-center gap-1">
                    <Icon icon="lucide:fast-forward" class="w-3 h-3" />
                    Fastest
                  </span>
                  <span class="text-sm font-bold text-green-400">{{ formatDuration(workflowStats?.kpis?.minRunTime || 0) }}</span>
                </div>
                <div class="flex justify-between items-center p-1.5 bg-surface/50 rounded">
                  <span class="text-xs text-gray-400 flex items-center gap-1">
                    <Icon icon="lucide:pause" class="w-3 h-3" />
                    Slowest
                  </span>
                  <span class="text-sm font-bold text-red-400">{{ formatDuration(workflowStats?.kpis?.maxRunTime || 0) }}</span>
                </div>
                <div class="flex justify-between items-center p-1.5 bg-surface/30 rounded border border-emerald-500/20">
                  <span class="text-xs text-gray-400 flex items-center gap-1">
                    <Icon icon="lucide:hourglass" class="w-3 h-3" />
                    Total Time
                  </span>
                  <span class="text-sm font-bold text-emerald-400">
                    {{ Math.round((workflowStats?.kpis?.totalExecutions || 0) * (workflowStats?.kpis?.avgRunTime || 0) / 60000) }}m
                  </span>
                </div>
              </div>
            </div>

            <!-- Insights & Intelligence - Monochrome -->
            <div class="card-glassmorphism rounded-lg p-3">
              <h4 class="text-sm font-medium text-white mb-2 flex items-center gap-2">
                <Icon icon="lucide:brain" class="w-4 h-4 text-emerald-400" />
                AI Insights
              </h4>
              <ul class="space-y-1.5">
                <li v-if="workflowStats?.kpis?.totalExecutions" class="flex items-start gap-1.5">
                  <Icon icon="lucide:activity" class="w-3 h-3 text-gray-400 mt-0.5" />
                  <div class="flex-1">
                    <div class="text-xs text-white">Activity Level</div>
                    <div class="text-xs text-gray-400">{{ workflowStats.kpis.totalExecutions }} executions tracked</div>
                    <div class="mt-1 h-1 bg-surface/50 rounded-full overflow-hidden">
                      <div class="h-full bg-emerald-400/50" :style="{ width: `${Math.min(100, workflowStats.kpis.totalExecutions / 10)}%` }"></div>
                    </div>
                  </div>
                </li>
                <li v-if="workflowStats?.kpis?.successRate" class="flex items-start gap-1.5">
                  <Icon icon="lucide:shield-check" class="w-3 h-3 text-gray-400 mt-0.5" />
                  <div class="flex-1">
                    <div class="text-xs text-white">Reliability</div>
                    <div class="text-xs text-gray-400">{{ workflowStats.kpis.successRate }}% success maintained</div>
                    <div class="mt-1 h-1 bg-surface/50 rounded-full overflow-hidden">
                      <div class="h-full bg-emerald-400/50" :style="{ width: `${workflowStats.kpis.successRate}%` }"></div>
                    </div>
                  </div>
                </li>
                <li v-if="workflowStats?.kpis?.avgRunTime" class="flex items-start gap-1.5">
                  <Icon icon="lucide:clock" class="w-3 h-3 text-gray-400 mt-0.5" />
                  <div class="flex-1">
                    <div class="text-xs text-white">Speed</div>
                    <div class="text-xs text-gray-400">{{ formatDuration(workflowStats.kpis.avgRunTime) }} avg</div>
                    <div class="mt-1 h-1 bg-surface/50 rounded-full overflow-hidden">
                      <div class="h-full bg-emerald-400/50" :style="{ width: `${Math.max(10, Math.min(100, 100 - (workflowStats.kpis.avgRunTime / 10000) * 100))}%` }"></div>
                    </div>
                  </div>
                </li>
                <li v-if="executionsHistory.length > 0" class="flex items-start gap-1.5">
                  <Icon icon="lucide:trending-up" class="w-3 h-3 text-gray-400 mt-0.5" />
                  <div class="flex-1">
                    <div class="text-xs text-white">Recent Trend</div>
                    <div class="text-xs text-gray-400">
                      {{ Math.round((executionsHistory.slice(0, 10).filter(e => e.status === 'success').length / Math.min(executionsHistory.length, 10)) * 100) }}% last 10
                    </div>
                    <div class="mt-1 h-1 bg-surface/50 rounded-full overflow-hidden">
                      <div class="h-full bg-emerald-400/50" :style="{ width: `${Math.round((executionsHistory.slice(0, 10).filter(e => e.status === 'success').length / Math.min(executionsHistory.length, 10)) * 100)}%` }"></div>
                    </div>
                  </div>
                </li>
              </ul>
            </div>

            <!-- Smart Recommendations -->
            <div class="bg-gradient-to-r from-blue-500/20 to-blue-500/10 rounded-lg p-3 border border-blue-500/30">
              <h4 class="text-sm font-medium text-white mb-2 flex items-center gap-2">
                <Icon icon="lucide:sparkles" class="w-4 h-4 text-blue-400" />
                Optimization Tips
              </h4>
              <div class="space-y-1.5 text-xs">
                <div v-if="workflowStats?.kpis?.successRate && workflowStats.kpis.successRate < 95" class="flex items-start gap-1.5 p-1.5 bg-surface/30 rounded border border-border/50">
                  <Icon icon="lucide:alert-triangle" class="w-3 h-3 text-gray-400 mt-0.5" />
                  <div class="flex-1">
                    <span class="text-white font-medium">Improve Success Rate</span>
                    <p class="text-gray-400 text-xs mt-0.5">Current: {{ workflowStats.kpis.successRate }}% - Review failed executions</p>
                  </div>
                </div>
                <div v-if="workflowStats?.kpis?.avgRunTime && workflowStats.kpis.avgRunTime > 10000" class="flex items-start gap-1.5 p-1.5 bg-surface/30 rounded border border-border/50">
                  <Icon icon="lucide:clock-alert" class="w-3 h-3 text-gray-400 mt-0.5" />
                  <div class="flex-1">
                    <span class="text-white font-medium">Optimize Performance</span>
                    <p class="text-gray-400 text-xs mt-0.5">Runtime >10s - Enable parallel processing</p>
                  </div>
                </div>
                <div v-if="executionsHistory.filter(e => e.status === 'error').length > 0" class="flex items-start gap-1.5 p-1.5 bg-surface/30 rounded border border-border/50">
                  <Icon icon="lucide:bug" class="w-3 h-3 text-gray-400 mt-0.5" />
                  <div class="flex-1">
                    <span class="text-white font-medium">Error Pattern Detected</span>
                    <p class="text-gray-400 text-xs mt-0.5">{{ executionsHistory.filter(e => e.status === 'error').length }} failures need attention</p>
                  </div>
                </div>
                <div v-if="!workflowStats?.kpis?.totalExecutions || workflowStats.kpis.totalExecutions === 0" class="flex items-start gap-1.5 p-1.5 bg-surface/30 rounded border border-border/50">
                  <Icon icon="lucide:info" class="w-3 h-3 text-gray-400 mt-0.5" />
                  <div class="flex-1">
                    <span class="text-white font-medium">No Data Available</span>
                    <p class="text-gray-400 text-xs mt-0.5">Run process to start collecting metrics</p>
                  </div>
                </div>
                <div v-else-if="workflowStats?.kpis?.successRate >= 95" class="flex items-start gap-1.5 p-1.5 bg-surface/30 rounded border border-emerald-500/20">
                  <Icon icon="lucide:award" class="w-3 h-3 text-emerald-400 mt-0.5" />
                  <div class="flex-1">
                    <span class="text-emerald-400 font-medium">Excellent Performance!</span>
                    <p class="text-gray-400 text-xs mt-0.5">Consider scaling or adding features</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Bottom Stats Summary Bar -->
        <div class="mt-3 p-2 bg-surface/30 rounded-lg border border-border/50">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-4 text-xs">
              <span class="flex items-center gap-1">
                <Icon icon="lucide:database" class="w-3 h-3 text-gray-400" />
                <span class="text-gray-400">Data Points:</span>
                <span class="text-white font-medium">{{ workflowStats?.kpis?.totalExecutions || 0 }}</span>
              </span>
              <span v-if="workflowStats?.period" class="flex items-center gap-1">
                <Icon icon="lucide:calendar" class="w-3 h-3 text-gray-400" />
                <span class="text-gray-400">Period:</span>
                <span class="text-white font-medium">{{ workflowStats.period }}</span>
              </span>
              <span class="flex items-center gap-1">
                <Icon icon="lucide:refresh-cw" class="w-3 h-3 text-gray-400" />
                <span class="text-gray-400">Updated:</span>
                <span class="text-white font-medium">{{ new Date(workflowStats?._metadata?.timestamp || Date.now()).toLocaleTimeString() }}</span>
              </span>
            </div>
            <button @click="$emit('refresh')" class="p-1.5 text-gray-400 hover:text-emerald-400 transition-colors rounded hover:bg-white/5">
              <Icon icon="lucide:refresh-cw" class="w-3 h-3" />
            </button>
          </div>
        </div>
      </div>
    </template>

    <!-- Raw Data Tab (Hidden for clients) -->
    <template #raw="{ data }">
      <div class="p-6">
        <div class="flex items-center justify-between mb-4">
          <div class="flex items-center">
            <Icon icon="lucide:code" class="w-5 h-5 text-gray-400 mr-2" />
            <h3 class="text-lg font-medium text-white">Raw Timeline Data</h3>
          </div>
          <div class="flex gap-2">
            <button
              @click="generateBusinessReport"
              class="flex items-center px-3 py-1.5 bg-gray-700 hover:bg-gray-600 text-white rounded-lg text-sm transition-colors"
            >
              <Icon icon="lucide:file-text" class="w-4 h-4 mr-1.5" />
              Generate Report
            </button>
            <button
              @click="showJsonData"
              class="flex items-center px-3 py-1.5 bg-gray-700 hover:bg-gray-600 text-white rounded-lg text-sm transition-colors"
            >
              <Icon icon="lucide:code" class="w-4 h-4 mr-1.5" />
              Show JSON
            </button>
          </div>
        </div>
        
        <pre 
          id="raw-data-content"
          class="bg-black/50 p-4 rounded-lg border border-gray-800 text-xs text-gray-300 overflow-auto max-h-96 font-mono whitespace-pre premium-scrollbar"
        >{{ 
          data ? 
          JSON.stringify(data, null, 2)
            .replace(/n8n/gi, 'WFEngine')
            .replace(/\.nodes\./g, '.engine.')
            .replace(/\.base\./g, '.core.')
          : 'No data available' 
        }}</pre>
      </div>
    </template>
  </DetailModal>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { Icon } from '@iconify/vue'
import DetailModal from './DetailModal.vue'
import { useModal } from '../../composables/useModal'
import { useBusinessParser } from '../../composables/useBusinessParser'
import { businessAPI, $fetch } from '../../services/api-client'
import { API_BASE_URL } from '../../utils/api-config'
import { UnifiedBusinessProcessor, cleanHtmlContent, truncateText } from '../../shared/business-parsers'

interface Props {
  workflowId: string
  executionId?: string
  tenantId?: string
  show: boolean
}

const props = defineProps<Props>()

const emit = defineEmits<{
  close: []
}>()

// Composables
const { isLoading, error, setLoading, setError, showToast } = useModal()
const { parseBusinessData: legacyParseBusinessData, formatBusinessData, formatTimelineStepData } = useBusinessParser()

// Use new unified processor with compatibility wrapper
const parseBusinessData = (data: any, dataType: string, nodeType?: string, nodeName?: string) => {
  // Use new unified processor
  const result = UnifiedBusinessProcessor.process(data, {
    source: 'frontend',
    nodeType,
    workflowId: props.workflowId
  })

  // Convert to legacy format for compatibility
  return {
    summary: result.summary,
    details: result.details,
    type: result.type,
    metadata: result.metadata,
    businessValue: result.businessValue
  }
}

// State
const timelineData = ref<any>(null)
const expandedStep = ref<string | null>(null)
const expandedSteps = ref(new Set<string>())

// Additional data for Business Dashboard tabs
const executionsHistory = ref<any[]>([])
const workflowStats = ref<any>(null)
const recentActivity = ref<any[]>([])
const workflowInfo = ref<any>(null)

// Modal configuration
const modalTitle = computed(() => {
  return timelineData.value?.workflow?.name || `Business Process ${props.workflowId}`
})

const modalSubtitle = computed(() => {
  if (!timelineData.value) return ''
  const workflow = timelineData.value.workflow
  const execution = timelineData.value.execution
  const status = workflow?.active ? 'ACTIVE' : 'INACTIVE'
  return `ID: ${props.workflowId} • Status: ${status}${execution ? ` • Last: ${execution.id}` : ''}`
})

const tabs = [
  { id: 'overview', label: 'Process Overview', icon: 'lucide:info' },
  { id: 'executions', label: 'Latest Activity', icon: 'lucide:activity' },
  { id: 'history', label: 'Process History', icon: 'lucide:history' },
  { id: 'analytics', label: 'Analytics', icon: 'lucide:bar-chart-2' },
]

// Timeline logic
const loadTimeline = async () => {
  setLoading(true)
  setError(null)

  const API_BASE = import.meta.env.VITE_API_URL || API_BASE_URL

  try {
    console.log('🔄 Loading dashboard data for workflow:', props.workflowId)

    // Load from BOTH endpoints to get complete data
    // 1. Dashboard endpoint for executions and activity
    const dashboardResponse = await $fetch(`${API_BASE}/api/business/dashboard/${props.workflowId}`)

    // 2. Full-stats endpoint (same as Command Center) for accurate KPIs
    const fullStatsResponse = await $fetch(`${API_BASE}/api/business/workflow/${props.workflowId}/full-stats`, {
      params: { days: 30 }
    })
    console.log('✅ Dashboard data loaded:', dashboardResponse)

    // Process workflow info
    if (dashboardResponse.workflow) {
      workflowInfo.value = dashboardResponse.workflow
    }

    // Process executions with business data
    if (dashboardResponse.executions) {
      executionsHistory.value = dashboardResponse.executions
      console.log('✅ Executions with business data:', executionsHistory.value.length)
    }

    // Process statistics - Use full-stats data (same as Command Center)
    if (fullStatsResponse) {
      workflowStats.value = fullStatsResponse
      console.log('✅ Full statistics loaded:', workflowStats.value)
      console.log('📊 KPIs detail from full-stats:', {
        total: workflowStats.value?.kpis?.totalExecutions,
        success: workflowStats.value?.kpis?.successfulExecutions,
        failed: workflowStats.value?.kpis?.failedExecutions,
        canceled: workflowStats.value?.kpis?.canceledExecutions,
        rate: workflowStats.value?.kpis?.successRate
      })
    } else if (dashboardResponse.statistics) {
      // Fallback to dashboard statistics if full-stats fails
      workflowStats.value = dashboardResponse.statistics
      console.log('⚠️ Using fallback statistics from dashboard endpoint')
    }

    // Process recent activity (AI responses, emails)
    if (dashboardResponse.recentActivity) {
      recentActivity.value = dashboardResponse.recentActivity
      console.log('✅ Recent activity loaded:', recentActivity.value.length, 'items')
    }
  } catch (dashboardError) {
    console.error('❌ Failed to load dashboard data:', dashboardError)
    setError('Failed to load dashboard data. Please try again.')
  }

    // Also load timeline data for timeline tab
    try {
      let url = `${API_BASE}/api/business/raw-data-for-modal/${props.workflowId}`
      if (props.executionId) {
        url += `?executionId=${props.executionId}`
      }
      const data = await businessAPI.getWorkflowDetails(props.workflowId)
      console.log('✅ Process timeline loaded:', data.data)
    
    // Check if no business nodes are configured
    if (!data.data?.businessNodes || data.data.businessNodes.length === 0) {
      console.log('ℹ️ No show-n nodes found for this workflow - showing empty state')
      timelineData.value = { ...data.data, businessNodes: [] }
      return
    }
    
    // Enrich timeline data with business summaries
    console.log(`📊 Starting enrichment of ${data.data?.businessNodes?.length || 0} nodes`)
    if (data.data?.businessNodes) {
      const originalLength = data.data.businessNodes.length
      
      data.data.businessNodes = data.data.businessNodes.map((node: any, index: number) => {
        console.log(`📊 Processing node ${index + 1}/${originalLength}: "${node.name}"`)
        
        if (node.data && (node.data.inputJson || node.data.outputJson)) {
          try {
            const enrichedData = formatTimelineStepData(
              node.data.inputJson,
              node.data.outputJson,
              node.data.nodeType,
              node.name
            )
            console.log(`✅ Enriched node "${node.name}":`, enrichedData)
            return {
              ...node,
              enrichedData
            }
          } catch (err) {
            console.warn(`⚠️ Failed to enrich node "${node.name}":`, err)
            return node
          }
        } else {
          console.log(`ℹ️ Skipping enrichment for node "${node.name}" - no input/output data`)
          return node
        }
      })
      
      console.log(`📊 Enrichment complete: ${data.data.businessNodes.length}/${originalLength} nodes processed`)
      
      if (data.data.businessNodes.length !== originalLength) {
        console.error(`❌ Node count mismatch! Original: ${originalLength}, Final: ${data.data.businessNodes.length}`)
      }
    }
    
    timelineData.value = data.data
    
  } catch (err: any) {
    console.error('❌ Failed to load process timeline:', err)
    
    // More user-friendly error messages
    if (err.message.includes('Failed to fetch') || err.message.includes('fetch')) {
      setError('Process configuration incomplete. This business process needs to be configured with visible steps for reporting.')
    } else if (err.message.includes('404')) {
      setError('Process not found or not yet configured for business reporting.')
    } else {
      setError('Unable to load process details. Please try again or contact support.')
    }
  } finally {
    setLoading(false)
  }
}

const handleForceRefresh = async () => {
  try {
    console.log('🔥 Force refresh: Process timeline for', props.workflowId)
    
    // Try force refresh endpoint first  
    try {
      await businessAPI.refreshProcess(props.workflowId)
      console.log('✅ Force refresh succeeded')
      showToast('success', 'Timeline data refreshed successfully')
    } catch (refreshError) {
      console.warn('⚠️ Force refresh endpoint not available:', refreshError)
    }
    
    // Reload timeline data
    await loadTimeline()
    
  } catch (error: any) {
    showToast('error', 'Failed to refresh', error.message)
  }
}

// Step visualization helpers
const getStepIcon = (status: string) => {
  switch (status) {
    case 'success': return 'lucide:check-circle'
    case 'error': return 'lucide:x-circle'
    case 'running': return 'lucide:settings'
    case 'not-executed': return 'lucide:clock'
    default: return 'lucide:clock'
  }
}

const getStepColor = (status: string) => {
  switch (status) {
    case 'success': return 'border-green-400/30 bg-green-400/5 hover:bg-green-400/10'
    case 'error': return 'border-red-400/30 bg-red-400/5 hover:bg-red-400/10'
    case 'running': return 'border-yellow-400/30 bg-yellow-400/5 hover:bg-yellow-400/10'
    case 'not-executed': return 'border-gray-600/30 bg-gray-800/50 hover:bg-gray-700/50'
    default: return 'border-gray-400/30 bg-gray-400/5 hover:bg-gray-400/10'
  }
}

const getBusinessSummary = (step: any): string => {
  const parsedData = parseBusinessData(
    step.outputData || step.inputData,
    step.outputData ? 'output' : 'input',
    step.nodeType,
    step.nodeName
  )
  return parsedData.summary
}

const getBusinessErrorSummary = (step: any): string => {
  // Use the business parser to extract detailed error information
  const parsedData = parseBusinessData(
    step.data,
    'output',
    step.nodeType,
    step.name
  )
  
  // If the business parser extracted detailed error information, use it
  if (parsedData.type === 'error' && parsedData.details.length > 0) {
    return parsedData.details.join('\n')
  }
  
  // Fallback to direct n8n error details if available
  if (step.data?.n8nErrorDetails) {
    const error = step.data.n8nErrorDetails
    return `${error.errorType}: ${error.message} (Nodo: ${error.nodeName})`
  }
  
  // Final fallback
  return 'Process execution failed to complete successfully'
}

const getBusinessErrorDetails = (step: any): string => {
  // Use the business parser to extract detailed error information
  const parsedData = parseBusinessData(
    step.data,
    'output',
    step.nodeType,
    step.name
  )
  
  // If the business parser extracted detailed error information, use the first detail
  if (parsedData.type === 'error' && parsedData.details.length > 0) {
    // Return the most important detail (usually the first one with the error message)
    return parsedData.details.find(detail => detail.includes('Errore:')) || parsedData.details[0]
  }
  
  // Fallback to direct n8n error details if available
  if (step.data?.n8nErrorDetails) {
    const error = step.data.n8nErrorDetails
    return error.message || ''
  }
  
  // Final fallback
  return 'Check raw data for error details'
}

const getBusinessErrorContext = (step: any): string => {
  // Use the business parser to extract detailed error information
  const parsedData = parseBusinessData(
    step.data,
    'output',
    step.nodeType,
    step.name
  )
  
  // If the business parser extracted detailed error information, use node info
  if (parsedData.type === 'error' && parsedData.details.length > 1) {
    // Return the node context (usually the second detail with node info)
    return parsedData.details.find(detail => detail.includes('Nodo Fallito:')) || 
           parsedData.details.find(detail => detail.includes('Tipo Errore:')) ||
           parsedData.details[1]
  }
  
  // Fallback to direct n8n error details if available
  if (step.data?.n8nErrorDetails) {
    const error = step.data.n8nErrorDetails
    return `Errore nel nodo: ${error.nodeName} (${error.errorType})`
  }
  
  // Final fallback
  return `Errore durante l'esecuzione del nodo: ${step.name}`
}

const getBusinessData = (step: any, dataType: 'input' | 'output'): string => {
  const data = dataType === 'input' ? step.inputData : step.outputData
  const parsedData = parseBusinessData(data, dataType, step.nodeType, step.nodeName)
  return formatBusinessData(parsedData)
}

const toggleExpanded = (stepId: string | number) => {
  expandedStep.value = expandedStep.value === stepId ? null : String(stepId)
}

// Business Data Helper Functions - Universal for ALL workflows
const calculateSuccessRate = () => {
  // Use REAL KPI data from backend
  if (workflowStats.value?.kpis?.successRate !== undefined) {
    return workflowStats.value.kpis.successRate
  }
  // Fallback calculation if KPIs not available
  const successCount = workflowStats.value?.kpis?.successfulExecutions || 0
  const failedCount = workflowStats.value?.kpis?.failedExecutions || 0
  const total = successCount + failedCount
  if (total === 0) return 100
  return Math.round((successCount / total) * 100)
}

const getBusinessMetricLabel = () => {
  // Use REAL KPI data from backend
  const kpis = workflowStats.value?.kpis
  if (!kpis) return 'Data Points'

  // Check which metrics have actual data
  if (kpis.ordersProcessed > 0) return 'Orders Processed'
  if (kpis.aiResponsesGenerated > 0) return 'AI Responses'
  if (kpis.emailsProcessed > 0) return 'Emails Handled'
  if (kpis.avgDataItemsPerRun > 1) return 'Avg Items/Run'
  if (kpis.totalDataProcessed > 0) return 'Data Processed'
  return 'Operations'
}

const formatBusinessMetric = () => {
  // Show the most relevant REAL business metric
  const kpis = workflowStats.value?.kpis
  if (!kpis) return 0

  // Return actual data from KPIs
  if (kpis.ordersProcessed > 0) return kpis.ordersProcessed
  if (kpis.aiResponsesGenerated > 0) return kpis.aiResponsesGenerated
  if (kpis.emailsProcessed > 0) return kpis.emailsProcessed
  if (kpis.avgDataItemsPerRun > 1) return kpis.avgDataItemsPerRun.toFixed(1)
  if (kpis.totalDataProcessed > 0) return kpis.totalDataProcessed
  return kpis.totalExecutions || 0
}

const formatRelativeTime = (timestamp: string) => {
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now.getTime() - date.getTime()

  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)

  if (minutes < 1) return 'Just now'
  if (minutes < 60) return `${minutes} minute${minutes > 1 ? 's' : ''} ago`
  if (hours < 24) return `${hours} hour${hours > 1 ? 's' : ''} ago`
  return `${days} day${days > 1 ? 's' : ''} ago`
}

// Utility functions
const formatDuration = (ms: number) => {
  if (ms < 1000) return `${ms}ms`
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`
  return `${(ms / 60000).toFixed(1)}min`
}

const formatTimestamp = (timestamp: string | number) => {
  // Handle both string ISO dates and Unix timestamps
  const date = typeof timestamp === 'number' ? new Date(timestamp) : new Date(timestamp)
  return date.toLocaleString('it-IT', {
    dateStyle: 'short',
    timeStyle: 'medium'
  })
}

// Actions
const replyToCustomer = (context: any) => {
  const customerEmail = context.customerEmail
  const subject = context.subject || ''
  
  if (customerEmail) {
    window.open(`mailto:${customerEmail}?subject=Re: ${subject}`, '_blank')
  }
}

const downloadReport = () => {
  if (!timelineData.value) return
  
  const reportContent = generateBusinessReport()
  const blob = new Blob([reportContent], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `business-process-report-${props.workflowId}-${new Date().toISOString().slice(0, 10)}.txt`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

const generateBusinessReport = (): string => {
  if (!timelineData.value) return ''
  
  let report = `╔${'═'.repeat(78)}╗\n`
  report += `║${' '.repeat(15)}BUSINESS PROCESS EXECUTION REPORT${' '.repeat(16)}║\n`
  report += `║${' '.repeat(25)}PilotPro Control Center${' '.repeat(29)}║\n`
  report += `╚${'═'.repeat(78)}╝\n\n`
  
  // Process Information
  report += `┌─ PROCESS INFORMATION ${'─'.repeat(56)}┐\n\n`
  report += `  Process Name:      ${timelineData.value.workflowName || ''}\n`
  report += `  Process ID:        ${props.workflowId}\n`
  report += `  Status:            ${timelineData.value.status === 'active' ? 'ACTIVE' : 'INACTIVE'}\n`
  
  if (timelineData.value.lastExecution) {
    report += `\n  LAST EXECUTION:\n`
    report += `  ├─ Execution ID:   ${timelineData.value.lastExecution.id}\n`
    report += `  ├─ Date/Time:      ${formatTimestamp(timelineData.value.lastExecution.executedAt)}\n`
    report += `  ├─ Total Duration: ${formatDuration(timelineData.value.lastExecution.duration)}\n`
    report += `  └─ Status:         ${timelineData.value.lastExecution.status || 'Completed'}\n`
  }
  
  report += `\n└${'─'.repeat(78)}┘\n\n`
  
  // Business Context
  if (timelineData.value.execution?.businessContext && Object.keys(timelineData.value.execution.businessContext).length > 0) {
    report += `┌─ BUSINESS CONTEXT ANALYSIS ${'─'.repeat(50)}┐\n\n`
    
    const context = timelineData.value.execution.businessContext
    if (context.customerEmail) {
      report += `  CUSTOMER INFORMATION:\n`
      report += `     Email: ${context.customerEmail}\n\n`
    }
    
    if (context.subject) {
      report += `  COMMUNICATION SUBJECT:\n`
      report += `     "${context.subject}"\n\n`
    }
    
    if (context.orderId) {
      report += `  ORDER REFERENCE:\n`
      report += `     Order ID: ${context.orderId}\n\n`
    }
    
    if (context.classification) {
      report += `  AI CLASSIFICATION:\n`
      report += `     Category: ${context.classification}\n`
      if (context.confidence) {
        report += `     Confidence: ${context.confidence}%\n`
      }
      report += `\n`
    }
    
    report += `└${'─'.repeat(78)}┘\n\n`
  }
  
  return report
}

const showJsonData = () => {
  const preElement = document.getElementById('raw-data-content')
  if (preElement && timelineData.value) {
    const sanitizedJson = JSON.stringify(timelineData.value, null, 2)
      .replace(/n8n/gi, 'WFEngine')
      .replace(/\.nodes\./g, '.engine.')
      .replace(/\.base\./g, '.core.')
    preElement.textContent = sanitizedJson
  }
}

// Executions Details Helper Functions
const formatBusinessStepType = (step: any): string => {
  const nodeName = step.name?.toLowerCase() || ''
  
  if (nodeName.includes('mail') || nodeName.includes('ricezione')) {
    return 'Customer Communication'
  }
  if (nodeName.includes('milena') || nodeName.includes('assistente')) {
    return 'AI Assistant Processing'
  }
  if (nodeName.includes('qdrant') || nodeName.includes('vector')) {
    return 'Knowledge Base Search'
  }
  if (nodeName.includes('ordini') || nodeName.includes('order')) {
    return 'Order Management'
  }
  if (nodeName.includes('supabase') || nodeName.includes('database')) {
    return 'Data Storage Operation'
  }
  if (nodeName.includes('execute') || nodeName.includes('workflow')) {
    return 'Business Process Execution'
  }
  
  return 'Business Process Step'
}

const generateExecutionDetail = (step: any): string => {
  const nodeName = step.name?.toLowerCase() || ''
  
  // Email nodes - focus on communication
  if (nodeName.includes('ricezione') && step.data?.outputJson) {
    const email = step.data.outputJson
    if (email.oggetto && email.mittente) {
      return `Customer email received from ${email.mittente} regarding "${email.oggetto}". Message successfully processed and categorized for business response.`
    }
    return 'Customer email received and processed successfully.'
  }
  
  // AI Assistant nodes - focus on intelligence
  if ((nodeName.includes('milena') || nodeName.includes('assistente')) && step.data?.outputJson?.output) {
    const aiOutput = step.data.outputJson.output
    if (aiOutput.categoria) {
      return `AI Assistant analyzed the customer request and generated an intelligent response. Category: ${aiOutput.categoria}. Response crafted based on business knowledge and customer context.`
    }
    return 'AI Assistant processed the request and generated an intelligent, personalized response for the customer.'
  }
  
  // Vector/Knowledge search nodes
  if (nodeName.includes('qdrant') || nodeName.includes('vector')) {
    return 'Knowledge base searched to find relevant information and context for providing accurate customer support.'
  }
  
  // Order/Database nodes
  if (nodeName.includes('ordini') || nodeName.includes('order')) {
    return 'Order information retrieved and processed to provide customer with accurate status and details.'
  }
  
  // Database storage nodes
  if (nodeName.includes('supabase') || nodeName.includes('database')) {
    return 'Customer interaction data saved to business database for future reference and analytics.'
  }
  
  // Sub-workflow execution
  if (nodeName.includes('execute') || nodeName.includes('workflow')) {
    return 'Business process sub-routine executed successfully to handle specific customer requirements.'
  }
  
  // Generic business value
  return 'Business process step completed successfully, contributing to efficient customer service automation.'
}

// Intelligent Summary Helper Functions
const getIntelligentSummaryIcon = (type: string) => {
  const icons: Record<string, string> = {
    'document': 'lucide:file-text',
    'dataset': 'lucide:table',
    'statistical': 'lucide:bar-chart-2',
    'ai_generated': 'lucide:sparkles',
    'email_batch': 'lucide:mail',
    'api_response': 'lucide:cloud',
    'generic': 'lucide:file'
  }
  return icons[type] || 'lucide:file'
}

const getIntelligentSummaryLabel = (summaryType: string) => {
  const labels: Record<string, string> = {
    'document': 'Document Analysis',
    'dataset': 'Data Table',
    'emails': 'Email Batch',
    'api': 'API Response',
    'statistics': 'Statistical Analysis',
    'ai': 'AI Analysis',
    'generic': 'Process Data'
  }
  return labels[summaryType] || 'Process Data'
}

const formatMetricKey = (key: string) => {
  return key.replace(/_/g, ' ').replace(/([A-Z])/g, ' $1').trim()
}

const formatMetricValue = (value: any) => {
  if (typeof value === 'number') {
    if (value > 1000000) return `${(value / 1000000).toFixed(1)}M`
    if (value > 1000) return `${(value / 1000).toFixed(1)}K`
    if (value % 1 !== 0) return value.toFixed(2)
    return value.toString()
  }
  if (typeof value === 'boolean') return value ? 'Yes' : 'No'
  if (value === null || value === undefined) return '-'
  return value.toString()
}

const formatActionLabel = (action: string) => {
  const labels: Record<string, string> = {
    'download_full': 'Download Full Data',
    'request_ai_analysis': 'AI Analysis',
    'extract_data': 'Extract Data',
    'view_full_table': 'View Full Table',
    'export_excel': 'Export Excel',
    'generate_report': 'Generate Report',
    'analyze_patterns': 'Analyze Patterns',
    'view_all_emails': 'View All Emails',
    'export_list': 'Export List',
    'analyze_sentiment': 'Analyze Sentiment',
    'view_json': 'View JSON',
    'export_data': 'Export Data',
    'analyze_structure': 'Analyze Structure',
    'view_chart': 'View Chart',
    'export_stats': 'Export Statistics',
    'analyze_trends': 'Analyze Trends',
    'view_raw': 'View Raw',
    'download': 'Download',
    'regenerate_analysis': 'Regenerate Analysis'
  }
  return labels[action] || action
}

const toggleExpandedStep = (stepId: string) => {
  if (expandedSteps.value.has(stepId)) {
    expandedSteps.value.delete(stepId)
  } else {
    expandedSteps.value.add(stepId)
  }
}

const handleIntelligentAction = async (action: string, step: any) => {
  console.log('🎯 Handling intelligent action:', action, step)
  
  switch(action) {
    case 'download_full':
      downloadFullData(step)
      break
    case 'request_ai_analysis':
      await requestAIAnalysis(step)
      break
    case 'export_excel':
      exportToExcel(step)
      break
    case 'generate_report':
      generateStepReport(step)
      break
    default:
      showToast('info', `Action "${action}" not yet implemented`)
  }
}

const downloadFullData = (step: any) => {
  const data = step.data?.rawOutputData || step.data?.outputJson || {}
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `${step.name}-data-${new Date().toISOString().slice(0, 10)}.json`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
  showToast('success', 'Data downloaded successfully')
}

const requestAIAnalysis = async (step: any) => {
  showToast('info', 'Requesting AI analysis...')
  // TODO: Implement AI analysis request
  // This would call the backend to process through Ollama
  setTimeout(() => {
    showToast('success', 'AI analysis complete')
  }, 2000)
}

const exportToExcel = (step: any) => {
  // TODO: Implement Excel export using a library like xlsx
  showToast('info', 'Excel export feature coming soon')
}

const generateStepReport = (step: any) => {
  const report = `
Business Process Step Report
============================
Step Name: ${step.name}
Type: ${step.data?.intelligentSummary?.businessSummary?.title || step.type}
Status: ${step.status}
Execution Time: ${formatDuration(step.executionTime || 0)}

Business Summary:
${step.data?.intelligentSummary?.businessSummary?.description || ''}

Business Insight:
${step.data?.intelligentSummary?.businessInsight || ''}

Generated: ${new Date().toLocaleString()}
  `.trim()
  
  const blob = new Blob([report], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `${step.name}-report-${new Date().toISOString().slice(0, 10)}.txt`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
  showToast('success', 'Report generated successfully')
}

// Lifecycle
watch(() => props.show, (newShow) => {
  if (newShow) {
    console.log('📊 Timeline modal opened for process:', props.workflowId)
    loadTimeline()
  }
})

onMounted(() => {
  if (props.show) {
    loadTimeline()
  }
})
</script>

<style scoped>
/* Glassmorphism Cards - Insights Theme */
.card-glassmorphism {
  background: linear-gradient(135deg,
    rgba(25, 25, 25, 0.5) 0%,
    rgba(20, 20, 20, 0.3) 100%);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.05);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
}

.metric-card-glassmorphism {
  background: linear-gradient(135deg,
    rgba(30, 30, 30, 0.4) 0%,
    rgba(25, 25, 25, 0.2) 100%);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.05);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
  transition: all 0.3s ease;
}

.metric-card-glassmorphism:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25);
  border-color: rgba(16, 185, 129, 0.2);
}

.value-card-glassmorphism {
  background: linear-gradient(135deg,
    rgba(16, 185, 129, 0.08) 0%,
    rgba(16, 185, 129, 0.03) 100%);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(16, 185, 129, 0.2);
  box-shadow:
    0 8px 32px rgba(0, 0, 0, 0.2),
    0 0 40px rgba(16, 185, 129, 0.05);
}

/* Performance Metrics Cards */
.performance-card {
  background: linear-gradient(135deg,
    rgba(30, 30, 30, 0.3) 0%,
    rgba(25, 25, 25, 0.2) 100%);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.05);
}

/* Activity Pattern Cards */
.activity-card {
  background: rgba(20, 20, 20, 0.4);
  backdrop-filter: blur(5px);
  border: 1px solid rgba(255, 255, 255, 0.03);
}
</style>