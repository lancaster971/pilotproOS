/**
 * Express Server
 * 
 * Server REST API per controllo multi-tenant scheduler
 */

import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import rateLimit from 'express-rate-limit';
import schedulerController from '../api/scheduler-controller.js';
import authController from '../api/auth-controller.js';
import healthController from '../api/health-controller.js';
import backupController from '../api/backup-controller.js';
import tenantStatsRouter from '../api/tenant-stats.js';
import securityRoutes from '../api/security-routes.js';
import aiAgentsController from '../api/ai-agents-controller.js';
import executionImportRoutes from '../api/execution-import-routes.js';
import executionEnrichmentRoutes from '../api/execution-enrichment-routes.js';
import { DatabaseConnection } from '../database/connection.js';
import { setupSwagger } from '../api/swagger-config.js';
import { EnvConfig } from '../config/environment.js';

export interface ServerConfig {
  port: number;
  host: string;
  corsOrigins: string[];
  rateLimitWindowMs: number;
  rateLimitMaxRequests: number;
  enableHelmet: boolean;
}

export const defaultServerConfig: ServerConfig = {
  port: parseInt(process.env.API_PORT || '3001'),
  host: process.env.API_HOST || '0.0.0.0',
  corsOrigins: process.env.CORS_ORIGINS?.split(',') || ['http://localhost:3000'],
  rateLimitWindowMs: 15 * 60 * 1000, // 15 minuti
  rateLimitMaxRequests: 100, // max 100 richieste per finestra
  enableHelmet: process.env.NODE_ENV === 'production'
};

/**
 * Server Express per API REST
 */
export class ExpressServer {
  private app: express.Application;
  private config: ServerConfig;
  private server: any = null;
  private db: DatabaseConnection;

  constructor(config?: Partial<ServerConfig>) {
    this.config = { ...defaultServerConfig, ...config };
    this.app = express();
    this.db = DatabaseConnection.getInstance();
    
    this.setupMiddleware();
    this.setupRoutes();
    this.setupErrorHandlers();
  }

  /**
   * Configura middleware
   */
  private setupMiddleware(): void {
    // Security headers
    if (this.config.enableHelmet) {
      this.app.use(helmet());
    }

    // CORS - PERMETTI TUTTO IN DEVELOPMENT
    this.app.use(cors({
      origin: process.env.NODE_ENV === 'production' 
        ? this.config.corsOrigins 
        : true,  // Accetta TUTTO in development
      credentials: true
    }));

    // Rate limiting - DISABILITATO IN DEVELOPMENT
    if (process.env.NODE_ENV === 'production') {
      const limiter = rateLimit({
        windowMs: this.config.rateLimitWindowMs,
        max: this.config.rateLimitMaxRequests,
        message: {
          error: 'Too many requests',
          message: 'Rate limit exceeded, try again later'
        }
      });
      this.app.use('/api/', limiter);
    }

    // Body parsing
    this.app.use(express.json({ limit: '10mb' }));
    this.app.use(express.urlencoded({ extended: true }));

    // Request logging
    this.app.use((req, res, next) => {
      console.log(`${new Date().toISOString()} ${req.method} ${req.path}`);
      next();
    });
  }

  /**
   * Configura routes
   */
  private setupRoutes(): void {
    // Health check
    this.app.get('/health', (req, res) => {
      res.json({
        status: 'healthy',
        timestamp: new Date().toISOString(),
        uptime: process.uptime(),
        version: process.env.npm_package_version || '1.0.0'
      });
    });

    // API routes
    this.app.use('/api', schedulerController);
    this.app.use('/api', backupController);
    this.app.use('/api', tenantStatsRouter);  // Route per tenant-specific stats
    this.app.use('/api', securityRoutes);     // 🚀 PREMIUM: Security routes
    this.app.use('/api', aiAgentsController); // 🤖 KILLER FEATURE: AI Agents Transparency
    this.app.use('/api', executionImportRoutes); // 🔄 Import execution data completi (n8n API)
    this.app.use('/api', executionEnrichmentRoutes); // ✨ Enrich execution data dal database
    this.app.use('/auth', authController);
    this.app.use('/health', healthController);

    // Swagger Documentation
    setupSwagger(this.app);

    // Root endpoint
    this.app.get('/', (req, res) => {
      res.json({
        name: 'PilotPro Multi-Tenant Control API',
        version: process.env.npm_package_version || '1.0.0',
        timestamp: new Date().toISOString(),
        endpoints: {
          health: '/health',
          auth: '/auth/*',
          scheduler: '/api/scheduler/*',
          tenants: '/api/tenants/*',
          logs: '/api/logs',
          stats: '/api/stats',
          documentation: '/api-docs'
        }
      });
    });

    // 404 handler
    this.app.use('*', (req, res) => {
      res.status(404).json({
        error: 'Not Found',
        message: `Route ${req.method} ${req.path} not found`,
        timestamp: new Date().toISOString()
      });
    });
  }

  /**
   * Configura error handlers
   */
  private setupErrorHandlers(): void {
    // Global error handler
    this.app.use((error: any, req: express.Request, res: express.Response, next: express.NextFunction) => {
      console.error('API Error:', error);

      const statusCode = error.statusCode || error.status || 500;
      
      res.status(statusCode).json({
        error: error.name || 'Internal Server Error',
        message: error.message || 'Something went wrong',
        timestamp: new Date().toISOString(),
        ...(process.env.NODE_ENV === 'development' && { stack: error.stack })
      });
    });

    // Unhandled promise rejection
    process.on('unhandledRejection', (reason, promise) => {
      console.error('Unhandled Rejection at:', promise, 'reason:', reason);
    });

    // Uncaught exception
    process.on('uncaughtException', (error) => {
      console.error('Uncaught Exception:', error);
      process.exit(1);
    });
  }

  /**
   * Avvia server
   */
  async start(): Promise<void> {
    try {
      // Inizializza database
      await this.db.connect();
      console.log('✅ Database connection established');

      // Avvia server HTTP
      this.server = this.app.listen(this.config.port, this.config.host, () => {
        console.log('🚀 EXPRESS API SERVER STARTED');
        console.log('='.repeat(40));
        console.log(`📡 Host: ${this.config.host}:${this.config.port}`);
        console.log(`🌐 CORS: ${this.config.corsOrigins.join(', ')}`);
        console.log(`🛡️ Rate Limit: ${this.config.rateLimitMaxRequests} req/${this.config.rateLimitWindowMs/1000/60}min`);
        console.log(`🔒 Security: ${this.config.enableHelmet ? 'enabled' : 'disabled'}`);
        console.log('='.repeat(40));
        console.log('Available endpoints:');
        console.log(`  GET  ${this.config.host}:${this.config.port}/health`);
        console.log(`  GET  ${this.config.host}:${this.config.port}/api/scheduler/status`);
        console.log(`  POST ${this.config.host}:${this.config.port}/api/scheduler/start`);
        console.log(`  POST ${this.config.host}:${this.config.port}/api/scheduler/stop`);
        console.log(`  POST ${this.config.host}:${this.config.port}/api/scheduler/sync`);
        console.log(`  GET  ${this.config.host}:${this.config.port}/api/tenants`);
        console.log(`  POST ${this.config.host}:${this.config.port}/api/tenants`);
        console.log(`  GET  ${this.config.host}:${this.config.port}/api/logs`);
        console.log(`  GET  ${this.config.host}:${this.config.port}/api/stats`);
        console.log(`  📚   ${this.config.host}:${this.config.port}/api-docs (Swagger UI)`);
      });

      // Gestione shutdown graceful
      process.on('SIGINT', this.handleShutdown.bind(this));
      process.on('SIGTERM', this.handleShutdown.bind(this));

    } catch (error) {
      console.error('❌ Failed to start server:', error);
      throw error;
    }
  }

  /**
   * Ferma server
   */
  async stop(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (!this.server) {
        resolve();
        return;
      }

      console.log('🛑 Stopping Express server...');
      
      this.server.close(async (error: any) => {
        if (error) {
          console.error('❌ Error stopping server:', error);
          reject(error);
          return;
        }

        try {
          await this.db.disconnect();
          console.log('✅ Express server stopped gracefully');
          resolve();
        } catch (dbError) {
          console.error('❌ Error disconnecting database:', dbError);
          reject(dbError);
        }
      });
    });
  }

  /**
   * Gestisce shutdown graceful
   */
  private async handleShutdown(signal: string): Promise<void> {
    console.log(`\n📛 Received ${signal}, starting graceful shutdown...`);
    
    try {
      await this.stop();
      process.exit(0);
    } catch (error) {
      console.error('❌ Error during shutdown:', error);
      process.exit(1);
    }
  }

  /**
   * Ottieni istanza Express app
   */
  getApp(): express.Application {
    return this.app;
  }

  /**
   * Ottieni configurazione server
   */
  getConfig(): ServerConfig {
    return { ...this.config };
  }
}

/**
 * Istanza singleton del server
 */
let serverInstance: ExpressServer | null = null;

/**
 * Ottieni istanza singleton del server
 */
export function getExpressServer(config?: Partial<ServerConfig>): ExpressServer {
  if (!serverInstance) {
    serverInstance = new ExpressServer(config);
  }
  return serverInstance;
}

/**
 * Entry point per avvio standalone del server
 */
if (import.meta.url === `file://${process.argv[1]}`) {
  console.log('🚀 Starting Express API Server in standalone mode...');
  
  const server = getExpressServer();
  
  server.start().catch(error => {
    console.error('❌ Fatal error:', error);
    process.exit(1);
  });
}