/**
 * MCP Server Configuration for PilotProOS AI Agent
 * 
 * Configures the MCP server with tools for workflow and execution management
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { getEnvironmentConfig } from './environment.js';

// Import tools
import { workflowTools } from '../tools/workflow/index.js';
import { executionTools } from '../tools/execution/index.js'; 
import { analyticsTools } from '../tools/analytics/index.js';

/**
 * Configure and create MCP server with all tools
 */
export async function configureServer() {
  const server = new Server(
    {
      name: 'pilotpros-mcp-server',
      version: '1.0.0'
    },
    {
      capabilities: {
        tools: {},
        resources: {}
      }
    }
  );
  
  console.error('Configuring PilotProOS MCP Server...');
  
  // Register workflow tools
  console.error('Registering workflow tools...');
  await registerWorkflowTools(server);
  
  // Register execution tools  
  console.error('Registering execution tools...');
  await registerExecutionTools(server);
  
  // Register analytics tools
  console.error('Registering analytics tools...');
  await registerAnalyticsTools(server);
  
  console.error('MCP Server configuration complete');
  return server;
}

/**
 * Register workflow management tools
 */
async function registerWorkflowTools(server) {
  // Workflow list tool
  server.setRequestHandler('tools/list', async () => {
    return {
      tools: [
        {
          name: 'workflow.list',
          description: 'List workflows with filtering options',
          inputSchema: {
            type: 'object',
            properties: {
              active: { type: 'boolean', description: 'Filter by active status' },
              limit: { type: 'number', description: 'Maximum number of workflows to return' }
            }
          }
        },
        {
          name: 'workflow.get',
          description: 'Get detailed workflow information',
          inputSchema: {
            type: 'object',
            properties: {
              workflowId: { type: 'string', description: 'Workflow ID to retrieve' }
            },
            required: ['workflowId']
          }
        },
        {
          name: 'execution.list',
          description: 'List workflow executions',
          inputSchema: {
            type: 'object',
            properties: {
              workflowId: { type: 'string', description: 'Filter by workflow ID' },
              status: { type: 'string', description: 'Filter by execution status' },
              limit: { type: 'number', description: 'Maximum number of executions to return' }
            }
          }
        },
        {
          name: 'analytics.dashboard-overview',
          description: 'Get dashboard overview analytics',
          inputSchema: {
            type: 'object',
            properties: {
              timeframe: { type: 'string', description: 'Time period for analytics (1d, 7d, 30d)' }
            }
          }
        },
        {
          name: 'analytics.workflow-analytics', 
          description: 'Get detailed workflow analytics',
          inputSchema: {
            type: 'object',
            properties: {
              workflowId: { type: 'string', description: 'Workflow ID for analytics' },
              timeframe: { type: 'string', description: 'Time period for analytics' }
            }
          }
        },
        {
          name: 'analytics.error-analytics',
          description: 'Get error analytics and troubleshooting data',
          inputSchema: {
            type: 'object',
            properties: {
              timeframe: { type: 'string', description: 'Time period for error analysis' }
            }
          }
        }
      ]
    };
  });
  
  // Workflow list implementation
  server.setRequestHandler('tools/call', async (request) => {
    const { name, arguments: args } = request.params;
    
    try {
      switch (name) {
        case 'workflow.list':
          return await handleWorkflowList(args);
          
        case 'workflow.get':
          return await handleWorkflowGet(args);
          
        case 'execution.list':
          return await handleExecutionList(args);
          
        case 'analytics.dashboard-overview':
          return await handleDashboardOverview(args);
          
        case 'analytics.workflow-analytics':
          return await handleWorkflowAnalytics(args);
          
        case 'analytics.error-analytics':
          return await handleErrorAnalytics(args);
          
        default:
          throw new Error(`Unknown tool: ${name}`);
      }
    } catch (error) {
      console.error(`Tool ${name} error:`, error);
      return {
        content: [{
          type: 'text',
          text: `Error executing ${name}: ${error.message}`
        }],
        isError: true
      };
    }
  });
}

/**
 * Placeholder tool handlers - Call backend APIs
 */
async function handleWorkflowList(args) {
  try {
    const url = new URL('http://localhost:3001/api/business/processes');
    
    const response = await fetch(url);
    const data = await response.json();
    
    return {
      content: [{
        type: 'text',
        text: JSON.stringify(data.data || [], null, 2)
      }]
    };
  } catch (error) {
    return {
      content: [{
        type: 'text', 
        text: `Failed to fetch workflows: ${error.message}`
      }],
      isError: true
    };
  }
}

async function handleWorkflowGet(args) {
  try {
    const response = await fetch(`http://localhost:3001/api/business/process-details/${args.workflowId}`);
    const data = await response.json();
    
    return {
      content: [{
        type: 'text',
        text: JSON.stringify(data.data || {}, null, 2)
      }]
    };
  } catch (error) {
    return {
      content: [{
        type: 'text',
        text: `Failed to fetch workflow details: ${error.message}`
      }],
      isError: true
    };
  }
}

async function handleExecutionList(args) {
  try {
    const url = new URL('http://localhost:3001/api/business/process-runs');
    if (args.workflowId) url.searchParams.set('processId', args.workflowId);
    if (args.status) url.searchParams.set('status', args.status);
    if (args.limit) url.searchParams.set('limit', args.limit.toString());
    
    const response = await fetch(url);
    const data = await response.json();
    
    return {
      content: [{
        type: 'text',
        text: JSON.stringify(data.data || [], null, 2)
      }]
    };
  } catch (error) {
    return {
      content: [{
        type: 'text',
        text: `Failed to fetch executions: ${error.message}`
      }],
      isError: true
    };
  }
}

async function handleDashboardOverview(args) {
  try {
    const response = await fetch('http://localhost:3001/api/business/analytics');
    const data = await response.json();
    
    return {
      content: [{
        type: 'text',
        text: JSON.stringify(data || {}, null, 2)
      }]
    };
  } catch (error) {
    return {
      content: [{
        type: 'text',
        text: `Failed to fetch dashboard data: ${error.message}`
      }],
      isError: true
    };
  }
}

async function handleWorkflowAnalytics(args) {
  try {
    const response = await fetch('http://localhost:3001/api/business/automation-insights');
    const data = await response.json();
    
    return {
      content: [{
        type: 'text',
        text: JSON.stringify(data || {}, null, 2)
      }]
    };
  } catch (error) {
    return {
      content: [{
        type: 'text',
        text: `Failed to fetch analytics: ${error.message}`
      }],
      isError: true
    };
  }
}

async function handleErrorAnalytics(args) {
  try {
    const response = await fetch('http://localhost:3001/api/business/integration-health');
    const data = await response.json();
    
    return {
      content: [{
        type: 'text',
        text: JSON.stringify(data || {}, null, 2)
      }]
    };
  } catch (error) {
    return {
      content: [{
        type: 'text',
        text: `Failed to fetch error analytics: ${error.message}`
      }],
      isError: true
    };
  }
}

async function registerExecutionTools(server) {
  // Execution tools are included in the main tool handler above
  console.error('Execution tools registered');
}

async function registerAnalyticsTools(server) {
  // Analytics tools are included in the main tool handler above  
  console.error('Analytics tools registered');
}