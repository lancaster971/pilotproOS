/**
 * Analytics Tools Module
 * 
 * Esporta tutti gli analytics tools e le loro definizioni
 * per l'integrazione con il server MCP.
 */

import { Tool } from '@modelcontextprotocol/sdk/types.js';

// Importa handlers
export { DashboardOverviewHandler } from './dashboard-overview.js';
export { WorkflowAnalyticsHandler } from './workflow-analytics.js';
export { ErrorAnalyticsHandler } from './error-analytics.js';
export { ExecutionHeatmapHandler } from './execution-heatmap.js';

// Importa definizioni tools
import { dashboardOverviewTool } from './dashboard-overview.js';
import { workflowAnalyticsTool } from './workflow-analytics.js';
import { errorAnalyticsTool } from './error-analytics.js';
import { executionHeatmapTool } from './execution-heatmap.js';

/**
 * Configura e restituisce tutti gli analytics tools disponibili
 * 
 * @returns Array di definizioni Tool per analytics
 */
export async function setupAnalyticsTools(): Promise<Tool[]> {
  return [
    dashboardOverviewTool,
    workflowAnalyticsTool,
    errorAnalyticsTool,
    executionHeatmapTool
  ];
}