/**
 * Swagger/OpenAPI Documentation Configuration
 * Complete API documentation for PilotProOS
 * Resolves DOC-001 technical debt
 */

import swaggerJsdoc from 'swagger-jsdoc';
import config from '../config/index.js';

const swaggerDefinition = {
  openapi: '3.0.0',
  info: {
    title: 'PilotProOS API Documentation',
    version: '1.0.0',
    description: 'Business Process Operating System - Complete API Reference',
    contact: {
      name: 'PilotProOS Support',
      email: config.notifications.email.user || 'support@pilotproos.com',
    },
    license: {
      name: 'MIT',
      url: 'https://opensource.org/licenses/MIT',
    },
  },
  servers: [
    {
      url: `http://${config.server.host}:${config.server.port}`,
      description: 'Development server',
    },
    {
      url: `https://${config.branding.domain}`,
      description: 'Production server',
    },
  ],
  components: {
    securitySchemes: {
      bearerAuth: {
        type: 'http',
        scheme: 'bearer',
        bearerFormat: 'JWT',
      },
      cookieAuth: {
        type: 'apiKey',
        in: 'cookie',
        name: 'token',
      },
    },
    schemas: {
      Error: {
        type: 'object',
        properties: {
          error: {
            type: 'string',
            description: 'Error message',
          },
          code: {
            type: 'string',
            description: 'Error code',
          },
          details: {
            type: 'object',
            description: 'Additional error details',
          },
        },
      },
      User: {
        type: 'object',
        properties: {
          id: {
            type: 'integer',
            description: 'User ID',
          },
          email: {
            type: 'string',
            format: 'email',
            description: 'User email address',
          },
          fullName: {
            type: 'string',
            description: 'User full name',
          },
          role: {
            type: 'string',
            enum: ['admin', 'user', 'viewer'],
            description: 'User role',
          },
          createdAt: {
            type: 'string',
            format: 'date-time',
            description: 'Account creation date',
          },
        },
      },
      BusinessProcess: {
        type: 'object',
        properties: {
          id: {
            type: 'string',
            description: 'Process ID',
          },
          name: {
            type: 'string',
            description: 'Process name',
          },
          description: {
            type: 'string',
            description: 'Process description',
          },
          category: {
            type: 'string',
            description: 'Process category',
          },
          status: {
            type: 'string',
            enum: ['active', 'inactive', 'error'],
            description: 'Process status',
          },
          executionCount: {
            type: 'integer',
            description: 'Number of executions',
          },
          successRate: {
            type: 'number',
            format: 'float',
            description: 'Success rate percentage',
          },
          lastExecuted: {
            type: 'string',
            format: 'date-time',
            description: 'Last execution time',
          },
        },
      },
      ProcessExecution: {
        type: 'object',
        properties: {
          id: {
            type: 'string',
            description: 'Execution ID',
          },
          processId: {
            type: 'string',
            description: 'Process ID',
          },
          status: {
            type: 'string',
            enum: ['success', 'error', 'running', 'waiting'],
            description: 'Execution status',
          },
          startedAt: {
            type: 'string',
            format: 'date-time',
            description: 'Execution start time',
          },
          finishedAt: {
            type: 'string',
            format: 'date-time',
            description: 'Execution end time',
          },
          duration: {
            type: 'integer',
            description: 'Execution duration in milliseconds',
          },
          error: {
            type: 'string',
            description: 'Error message if failed',
          },
        },
      },
      PerformanceMetrics: {
        type: 'object',
        properties: {
          totalProcesses: {
            type: 'integer',
            description: 'Total number of processes',
          },
          activeProcesses: {
            type: 'integer',
            description: 'Number of active processes',
          },
          totalExecutions: {
            type: 'integer',
            description: 'Total number of executions',
          },
          successRate: {
            type: 'number',
            format: 'float',
            description: 'Overall success rate',
          },
          avgDuration: {
            type: 'integer',
            description: 'Average execution duration in ms',
          },
          peakConcurrent: {
            type: 'integer',
            description: 'Peak concurrent executions',
          },
          systemLoad: {
            type: 'number',
            format: 'float',
            description: 'System load percentage',
          },
        },
      },
    },
  },
  tags: [
    {
      name: 'Authentication',
      description: 'User authentication and authorization',
    },
    {
      name: 'Business Processes',
      description: 'Business process management',
    },
    {
      name: 'Executions',
      description: 'Process execution management',
    },
    {
      name: 'Performance',
      description: 'Performance metrics and monitoring',
    },
    {
      name: 'Timeline',
      description: 'Business intelligence timeline',
    },
    {
      name: 'Health',
      description: 'System health and status',
    },
  ],
};

const options = {
  definition: swaggerDefinition,
  apis: [
    './src/controllers/*.js',
    './src/routes/*.js',
    './src/server.js',
  ],
};

const swaggerSpec = swaggerJsdoc(options);

export default swaggerSpec;