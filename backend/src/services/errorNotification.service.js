/**
 * Error Notification Service
 * Automatic error reporting system for PilotProOS
 */

import nodemailer from 'nodemailer';

class ErrorNotificationService {
  constructor() {
    this.emailTransporter = null;
    this.initEmailTransporter();
    
    // Throttling to avoid spam
    this.errorCache = new Map();
    this.throttleWindow = 30 * 60 * 1000; // 30 minutes
  }

  async initEmailTransporter() {
    try {
      // Configure email transporter (usando stesso sistema di GommeGo)
      this.emailTransporter = nodemailer.createTransporter({
        host: 'smtp.gmail.com',
        port: 587,
        secure: false,
        auth: {
          user: process.env.SUPPORT_EMAIL_USER || 'support@pilotpros.com',
          pass: process.env.SUPPORT_EMAIL_PASS || 'app_password_here'
        }
      });
      
      console.log('📧 Error notification email transporter initialized');
    } catch (error) {
      console.error('❌ Failed to initialize email transporter:', error);
    }
  }

  /**
   * Report execution error to support team
   */
  async reportExecutionError(errorData) {
    try {
      const {
        executionId,
        workflowId,
        workflowName,
        errorMessage,
        timestamp,
        clientInfo = {},
        stackTrace,
        // New detailed fields
        nodeName,
        nodeType,
        errorType = 'EXECUTION_ERROR',
        nodePosition,
        connectionInfo
      } = errorData;

      // Check throttling to avoid spam
      const errorKey = `execution_${workflowId}_${errorMessage?.slice(0, 50)}`;
      if (this.isThrottled(errorKey)) {
        console.log(`⏳ Error notification throttled for: ${errorKey}`);
        return;
      }

      // Create detailed error report
      const errorReport = {
        id: `ERR_${Date.now()}`,
        type: errorType,
        severity: this.classifyErrorSeverity(errorType, nodeType),
        timestamp: new Date().toISOString(),
        details: {
          executionId,
          workflowId,
          workflowName,
          errorMessage,
          originalTimestamp: timestamp,
          stackTrace,
          // Enhanced node details
          nodeName,
          nodeType,
          nodePosition,
          connectionInfo,
          errorCategory: this.categorizeError(errorMessage, nodeType)
        },
        client: {
          company: clientInfo.company || 'Unknown Client',
          domain: clientInfo.domain || 'localhost',
          environment: process.env.NODE_ENV || 'development'
        },
        system: {
          version: '1.5.1',
          component: 'Business Process Engine',
          server: process.env.SERVER_ID || 'dev-server'
        }
      };

      // Send notifications in parallel
      await Promise.allSettled([
        this.sendEmailNotification(errorReport),
        this.sendWebhookNotification(errorReport),
        this.logToDatabase(errorReport)
      ]);

      // Update throttle cache
      this.errorCache.set(errorKey, Date.now());

      console.log(`📧 Error notification sent: ${errorReport.id}`);
      return errorReport.id;

    } catch (error) {
      console.error('❌ Failed to report error:', error);
    }
  }

  /**
   * Send email notification to support team
   */
  async sendEmailNotification(errorReport) {
    if (!this.emailTransporter) {
      console.warn('⚠️ Email transporter not available');
      return;
    }

    const emailHtml = this.generateErrorEmailHtml(errorReport);
    
    const mailOptions = {
      from: process.env.SUPPORT_EMAIL_USER || 'pilotpros-system@company.com',
      to: process.env.SUPPORT_EMAIL_TO || 'support@pilotpros.com,dev@pilotpros.com',
      subject: `🚨 [PilotProOS] Execution Error - ${errorReport.details.workflowName}`,
      html: emailHtml,
      priority: 'high'
    };

    try {
      await this.emailTransporter.sendMail(mailOptions);
      console.log(`📧 Error email sent: ${errorReport.id}`);
    } catch (error) {
      console.error('❌ Failed to send error email:', error);
    }
  }

  /**
   * Send webhook notification (Slack, Discord, etc.)
   */
  async sendWebhookNotification(errorReport) {
    const webhookUrl = process.env.ERROR_WEBHOOK_URL;
    if (!webhookUrl) return;

    const payload = {
      text: `🚨 PilotProOS Execution Error`,
      attachments: [
        {
          color: 'danger',
          title: `Error in workflow: ${errorReport.details.workflowName}`,
          fields: [
            {
              title: 'Execution ID',
              value: errorReport.details.executionId,
              short: true
            },
            {
              title: 'Timestamp',
              value: errorReport.timestamp,
              short: true
            },
            {
              title: 'Client',
              value: errorReport.client.company,
              short: true
            },
            {
              title: 'Environment',
              value: errorReport.client.environment,
              short: true
            },
            {
              title: 'Error Message',
              value: errorReport.details.errorMessage || 'Execution failed to complete',
              short: false
            }
          ]
        }
      ]
    };

    try {
      const response = await fetch(webhookUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      
      if (response.ok) {
        console.log(`📱 Webhook notification sent: ${errorReport.id}`);
      }
    } catch (error) {
      console.error('❌ Failed to send webhook notification:', error);
    }
  }

  /**
   * Log error to database for tracking
   */
  async logToDatabase(errorReport) {
    try {
      // Dynamic import to avoid circular dependency  
      const { default: dbPool } = await import('../database.js');
      
      await dbPool.query(`
        INSERT INTO pilotpros.error_reports (
          error_id, 
          error_type, 
          severity,
          execution_id,
          workflow_id, 
          workflow_name,
          error_message,
          client_info,
          system_info,
          created_at,
          reported_at
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
      `, [
        errorReport.id,
        errorReport.type,
        errorReport.severity,
        errorReport.details.executionId,
        errorReport.details.workflowId,
        errorReport.details.workflowName,
        errorReport.details.errorMessage,
        JSON.stringify(errorReport.client),
        JSON.stringify(errorReport.system),
        errorReport.details.originalTimestamp,
        errorReport.timestamp
      ]);

      console.log(`💾 Error logged to database: ${errorReport.id}`);
    } catch (error) {
      console.error('❌ Failed to log error to database:', error);
      // Create table if it doesn't exist
      await this.createErrorReportsTable();
    }
  }

  /**
   * Create error reports table if it doesn't exist
   */
  async createErrorReportsTable() {
    try {
      // Dynamic import to avoid circular dependency  
      const { default: dbPool } = await import('../database.js');
      
      await dbPool.query(`
        CREATE TABLE IF NOT EXISTS pilotpros.error_reports (
          id SERIAL PRIMARY KEY,
          error_id VARCHAR(50) UNIQUE NOT NULL,
          error_type VARCHAR(50) NOT NULL,
          severity VARCHAR(20) NOT NULL,
          execution_id INTEGER,
          workflow_id VARCHAR(50),
          workflow_name VARCHAR(200),
          error_message TEXT,
          client_info JSONB,
          system_info JSONB,
          created_at TIMESTAMP WITH TIME ZONE,
          reported_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
          resolved BOOLEAN DEFAULT FALSE,
          resolution_notes TEXT
        )
      `);
      
      console.log('✅ Error reports table created');
    } catch (error) {
      console.error('❌ Failed to create error reports table:', error);
    }
  }

  /**
   * Generate HTML email for error notification
   */
  generateErrorEmailHtml(errorReport) {
    return `
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
            .container { max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .header { background: #dc3545; color: white; padding: 20px; text-align: center; }
            .content { padding: 30px; }
            .field { margin-bottom: 15px; }
            .label { font-weight: bold; color: #333; }
            .value { background: #f8f9fa; padding: 8px 12px; border-radius: 4px; margin-top: 5px; }
            .error-message { background: #ffebee; border-left: 4px solid #f44336; padding: 15px; margin: 20px 0; }
            .footer { background: #f8f9fa; padding: 20px; text-align: center; color: #666; font-size: 14px; }
            .btn { display: inline-block; background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; margin: 10px 5px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚨 PilotProOS - Execution Error Alert</h1>
                <p>Automatic error detection system</p>
            </div>
            
            <div class="content">
                <div class="field">
                    <div class="label">Error ID:</div>
                    <div class="value">${errorReport.id}</div>
                </div>
                
                <div class="field">
                    <div class="label">Workflow Name:</div>
                    <div class="value">${errorReport.details.workflowName || 'Unknown'}</div>
                </div>
                
                <div class="field">
                    <div class="label">Execution ID:</div>
                    <div class="value">${errorReport.details.executionId}</div>
                </div>
                
                ${errorReport.details.nodeName ? `
                <div class="field">
                    <div class="label">Failed Node:</div>
                    <div class="value">${errorReport.details.nodeName}</div>
                </div>
                ` : ''}
                
                ${errorReport.details.nodeType ? `
                <div class="field">
                    <div class="label">Node Type:</div>
                    <div class="value">${errorReport.details.nodeType}</div>
                </div>
                ` : ''}
                
                <div class="field">
                    <div class="label">Error Type:</div>
                    <div class="value">${errorReport.type} (${errorReport.details.errorCategory})</div>
                </div>
                
                <div class="field">
                    <div class="label">Severity:</div>
                    <div class="value" style="color: ${errorReport.severity === 'CRITICAL' ? '#d32f2f' : errorReport.severity === 'HIGH' ? '#f57c00' : '#1976d2'}">${errorReport.severity}</div>
                </div>
                
                <div class="field">
                    <div class="label">Timestamp:</div>
                    <div class="value">${errorReport.timestamp}</div>
                </div>
                
                <div class="field">
                    <div class="label">Client:</div>
                    <div class="value">${errorReport.client.company} (${errorReport.client.domain})</div>
                </div>
                
                <div class="field">
                    <div class="label">Environment:</div>
                    <div class="value">${errorReport.client.environment}</div>
                </div>
                
                ${errorReport.details.errorMessage ? `
                <div class="error-message">
                    <strong>Error Details:</strong><br>
                    ${errorReport.details.errorMessage}
                </div>
                ` : ''}
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="http://${errorReport.client.domain}/executions" class="btn">View Executions</a>
                    <a href="http://${errorReport.client.domain}/workflows" class="btn">View Workflows</a>
                </div>
            </div>
            
            <div class="footer">
                <p>PilotProOS Business Process Operating System</p>
                <p>Automatic Error Monitoring System</p>
                <p>Generated at ${new Date().toLocaleString('it-IT')}</p>
            </div>
        </div>
    </body>
    </html>
    `;
  }

  /**
   * Classify error severity based on type and node
   */
  classifyErrorSeverity(errorType, nodeType) {
    // Critical nodes that affect business operations
    const criticalNodes = [
      'microsoftOutlookTrigger',
      'agent', 
      'emailSend',
      'databaseInsert',
      'databaseUpdate'
    ];
    
    const isCriticalNode = criticalNodes.some(critical => 
      nodeType?.toLowerCase().includes(critical.toLowerCase())
    );
    
    if (errorType === 'NODE_ERROR' && isCriticalNode) return 'CRITICAL';
    if (errorType === 'EXECUTION_ERROR') return 'HIGH';
    if (errorType === 'NODE_ERROR') return 'MEDIUM';
    
    return 'LOW';
  }

  /**
   * Categorize error for better debugging
   */
  categorizeError(errorMessage, nodeType) {
    const message = errorMessage?.toLowerCase() || '';
    const type = nodeType?.toLowerCase() || '';
    
    // Network/Connection errors
    if (message.includes('connection') || message.includes('timeout') || 
        message.includes('network') || message.includes('enotfound')) {
      return 'NETWORK_ERROR';
    }
    
    // Authentication errors
    if (message.includes('auth') || message.includes('permission') || 
        message.includes('unauthorized') || message.includes('forbidden')) {
      return 'AUTH_ERROR';
    }
    
    // Email-specific errors
    if (type.includes('outlook') || type.includes('email') || type.includes('mail')) {
      if (message.includes('quota') || message.includes('limit')) return 'EMAIL_QUOTA_ERROR';
      if (message.includes('invalid') && message.includes('address')) return 'EMAIL_ADDRESS_ERROR';
      return 'EMAIL_ERROR';
    }
    
    // AI/LangChain errors  
    if (type.includes('agent') || type.includes('langchain')) {
      if (message.includes('token') || message.includes('limit')) return 'AI_TOKEN_ERROR';
      if (message.includes('api') || message.includes('key')) return 'AI_API_ERROR';
      return 'AI_ERROR';
    }
    
    // Database errors
    if (type.includes('database') || type.includes('sql') || message.includes('postgres')) {
      return 'DATABASE_ERROR';
    }
    
    // Vector store errors
    if (type.includes('vector') || type.includes('qdrant')) {
      return 'VECTOR_STORE_ERROR';
    }
    
    // Configuration errors
    if (message.includes('config') || message.includes('missing') || 
        message.includes('required') || message.includes('undefined')) {
      return 'CONFIG_ERROR';
    }
    
    return 'UNKNOWN_ERROR';
  }

  /**
   * Check if error is throttled (to avoid spam)
   */
  isThrottled(errorKey) {
    const lastSent = this.errorCache.get(errorKey);
    if (!lastSent) return false;
    
    return (Date.now() - lastSent) < this.throttleWindow;
  }

  /**
   * Clean up old throttle entries
   */
  cleanupThrottleCache() {
    const now = Date.now();
    for (const [key, timestamp] of this.errorCache.entries()) {
      if (now - timestamp > this.throttleWindow) {
        this.errorCache.delete(key);
      }
    }
  }
}

// Singleton instance
let errorNotificationService = null;

function getErrorNotificationService() {
  if (!errorNotificationService) {
    errorNotificationService = new ErrorNotificationService();
    
    // Cleanup throttle cache every 10 minutes
    setInterval(() => {
      errorNotificationService.cleanupThrottleCache();
    }, 10 * 60 * 1000);
  }
  
  return errorNotificationService;
}

export {
  ErrorNotificationService,
  getErrorNotificationService
};