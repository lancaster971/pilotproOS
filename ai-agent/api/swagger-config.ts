/**
 * Swagger/OpenAPI Configuration
 * 
 * Documentazione interattiva delle API
 */

import swaggerJsdoc from 'swagger-jsdoc';
import swaggerUi from 'swagger-ui-express';
import type { Application } from 'express';

const swaggerOptions: swaggerJsdoc.Options = {
  definition: {
    openapi: '3.0.0',
    info: {
      title: 'PilotPro Multi-Tenant Control API',
      version: '1.0.0',
      description: `
# PilotPro Multi-Tenant Control System API

Sistema completo per gestione multi-tenant di workflow con scheduler automatico, 
sincronizzazione dati e monitoring.

## Features Principali
- 🏢 **Multi-Tenant Support** - Gestione multiple istanze workflow
- ⏰ **Scheduler Automatico** - Sincronizzazione programmata
- 🔐 **JWT Authentication** - Sistema sicuro con ruoli e permessi
- 📊 **Real-time Statistics** - Metriche e monitoring
- 🔄 **Sync Management** - Controllo completo sincronizzazione
- 📝 **Audit Logging** - Tracciabilità completa operazioni

## Autenticazione
Tutte le API protette richiedono un JWT token ottenuto tramite login.
Usa il token nell'header \`Authorization: Bearer <token>\`

## Rate Limiting
- 100 richieste per 15 minuti per IP
- Header \`X-RateLimit-*\` per info sui limiti
      `,
      contact: {
        name: 'API Support',
        email: 'support@pilotpro.com'
      },
      license: {
        name: 'MIT',
        url: 'https://opensource.org/licenses/MIT'
      }
    },
    servers: [
      {
        url: 'http://localhost:3001',
        description: 'Development server'
      },
      {
        url: 'https://api.pilotpro.com',
        description: 'Production server'
      }
    ],
    components: {
      securitySchemes: {
        bearerAuth: {
          type: 'http',
          scheme: 'bearer',
          bearerFormat: 'JWT',
          description: 'JWT token ottenuto tramite /auth/login'
        },
        apiKey: {
          type: 'apiKey',
          in: 'header',
          name: 'X-API-Key',
          description: 'API Key per automazioni'
        }
      },
      schemas: {
        // Error Response
        Error: {
          type: 'object',
          properties: {
            error: { type: 'string' },
            message: { type: 'string' },
            timestamp: { type: 'string', format: 'date-time' }
          }
        },
        
        // User Schema
        User: {
          type: 'object',
          properties: {
            id: { type: 'string', format: 'uuid' },
            email: { type: 'string', format: 'email' },
            role: { 
              type: 'string',
              enum: ['admin', 'tenant', 'readonly']
            },
            tenantId: { type: 'string', nullable: true },
            permissions: {
              type: 'array',
              items: { type: 'string' }
            },
            createdAt: { type: 'string', format: 'date-time' },
            lastLoginAt: { type: 'string', format: 'date-time' }
          }
        },
        
        // Tenant Schema
        Tenant: {
          type: 'object',
          properties: {
            id: { type: 'string' },
            name: { type: 'string' },
            n8n_api_url: { type: 'string', format: 'uri' },
            n8n_version: { type: 'string' },
            sync_enabled: { type: 'boolean' },
            created_at: { type: 'string', format: 'date-time' },
            last_sync_at: { type: 'string', format: 'date-time' },
            stats: {
              type: 'object',
              properties: {
                workflows: { type: 'integer' },
                executions: { type: 'integer' }
              }
            }
          }
        },
        
        // Scheduler Status
        SchedulerStatus: {
          type: 'object',
          properties: {
            scheduler: {
              type: 'object',
              properties: {
                isRunning: { type: 'boolean' },
                scheduledTasks: {
                  type: 'array',
                  items: { type: 'string' }
                },
                config: { type: 'object' }
              }
            },
            stats: {
              type: 'object',
              properties: {
                totalSyncRuns: { type: 'integer' },
                lastSyncTime: { type: 'string', format: 'date-time' },
                activeTenants: { type: 'integer' },
                totalWorkflowsSynced: { type: 'integer' },
                totalExecutionsSynced: { type: 'integer' }
              }
            },
            health: {
              type: 'object',
              properties: {
                status: {
                  type: 'string',
                  enum: ['healthy', 'degraded', 'unhealthy']
                },
                checks: { type: 'object' }
              }
            }
          }
        },
        
        // System Stats
        SystemStats: {
          type: 'object',
          properties: {
            database: {
              type: 'object',
              properties: {
                totalTenants: { type: 'integer' },
                activeTenants: { type: 'integer' },
                totalWorkflows: { type: 'integer' },
                totalExecutions: { type: 'integer' }
              }
            },
            scheduler: { type: 'object' },
            health: { type: 'object' },
            recentActivity: { type: 'array' },
            system: {
              type: 'object',
              properties: {
                uptime: { type: 'number' },
                memory: { type: 'object' },
                nodeVersion: { type: 'string' }
              }
            }
          }
        }
      }
    },
    tags: [
      {
        name: 'Authentication',
        description: 'Login, logout e gestione autenticazione'
      },
      {
        name: 'Scheduler',
        description: 'Controllo scheduler multi-tenant'
      },
      {
        name: 'Tenants',
        description: 'Gestione tenant'
      },
      {
        name: 'Users',
        description: 'Gestione utenti'
      },
      {
        name: 'Monitoring',
        description: 'Statistiche e monitoring'
      }
    ]
  },
  apis: [
    './build/api/*.js',
    './src/api/*.ts'
  ]
};

/**
 * Setup Swagger UI in Express app
 */
export function setupSwagger(app: Application): void {
  const swaggerSpec = swaggerJsdoc(swaggerOptions);
  
  // Serve Swagger UI
  app.use('/api-docs', swaggerUi.serve, swaggerUi.setup(swaggerSpec, {
    customCss: '.swagger-ui .topbar { display: none }',
    customSiteTitle: 'PilotPro API Documentation',
    customfavIcon: '/favicon.ico'
  }));
  
  // Serve OpenAPI spec as JSON
  app.get('/api-docs.json', (req, res) => {
    res.setHeader('Content-Type', 'application/json');
    res.send(swaggerSpec);
  });
  
  console.log('📚 API Documentation available at /api-docs');
}