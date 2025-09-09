/**
 * Security Controller - Premium Security & Compliance Features
 * 
 * Questo controller gestisce tutte le funzionalità Premium di sicurezza:
 * - Security audit completi usando n8n API
 * - Risk scoring avanzato 
 * - Compliance reporting (GDPR, SOC2)
 * - Security metrics e monitoring
 */

import { Request, Response } from 'express';
import { N8nApiService } from './n8n-client.js';
import { DatabaseConnection } from '../database/connection.js';

/**
 * Interface per Security Audit Report
 */
interface SecurityAuditReport {
  overview: {
    securityScore: number;
    riskLevel: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
    lastAuditDate: string;
    nextAuditDue: string;
    totalIssues: number;
    criticalIssues: number;
  };
  categories: {
    credentials: SecurityCategory;
    database: SecurityCategory;
    nodes: SecurityCategory;
    filesystem: SecurityCategory;
    instance: SecurityCategory;
    access: SecurityCategory;
  };
  recommendations: SecurityRecommendation[];
  complianceStatus: ComplianceStatus;
}

interface SecurityCategory {
  risk: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  score: number;
  issues: SecurityIssue[];
  summary: string;
}

interface SecurityIssue {
  title: string;
  description: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  recommendation: string;
  location?: {
    type: 'workflow' | 'credential' | 'node' | 'user' | 'system';
    id?: string;
    name?: string;
  };
  affectedItems: number;
}

interface SecurityRecommendation {
  priority: 'HIGH' | 'MEDIUM' | 'LOW';
  category: string;
  title: string;
  description: string;
  effort: 'LOW' | 'MEDIUM' | 'HIGH';
  impact: 'LOW' | 'MEDIUM' | 'HIGH';
}

interface ComplianceStatus {
  gdpr: {
    compliant: boolean;
    score: number;
    issues: string[];
  };
  soc2: {
    compliant: boolean;
    score: number;
    issues: string[];
  };
  iso27001: {
    compliant: boolean;
    score: number;
    issues: string[];
  };
}

/**
 * Security Controller Class
 */
export class SecurityController {
  constructor(
    private n8nService: N8nApiService,
    private db: DatabaseConnection
  ) {}

  /**
   * Generate comprehensive security audit
   * GET /api/tenant/:tenantId/security/audit
   */
  async generateSecurityAudit(req: Request, res: Response): Promise<void> {
    try {
      const { tenantId } = req.params;
      const { categories, daysAbandonedWorkflow = 30 } = req.query;

      console.log(`🔍 Generando security audit per tenant: ${tenantId}`);

      // 1. Chiama n8n audit API
      const validCategories: ('credentials' | 'database' | 'nodes' | 'filesystem' | 'instance')[] = ['credentials', 'database', 'nodes', 'filesystem', 'instance'];
      const auditCategories = categories 
        ? (categories as string).split(',').filter(cat => validCategories.includes(cat as any)) as ('credentials' | 'database' | 'nodes' | 'filesystem' | 'instance')[]
        : validCategories;

      // 1. Recupera dati reali dal database locale
      console.log(`📊 Analizzando dati reali per tenant: ${tenantId}`);
      
      const [workflowsResult, executionsResult, usersResult] = await Promise.all([
        this.db.query(`
          SELECT id, name, active, raw_data, node_count, has_webhook, created_at, updated_at 
          FROM tenant_workflows 
          WHERE tenant_id = $1 AND is_archived = false
          ORDER BY created_at DESC
          LIMIT 100
        `, [tenantId]),
        
        this.db.query(`
          SELECT id, workflow_id, status, mode, 
                 started_at, stopped_at, duration_ms, has_error, raw_data
          FROM tenant_executions 
          WHERE tenant_id = $1 
          ORDER BY started_at DESC 
          LIMIT 500
        `, [tenantId]),
        
        this.db.query(`
          SELECT id, email, role, tenant_id, created_at
          FROM auth_users 
          WHERE tenant_id = $1 OR tenant_id IS NULL
        `, [tenantId])
      ]);

      const workflows = workflowsResult.rows;
      const executions = executionsResult.rows;  
      const users = usersResult.rows;

      // 2. Analizza e genera Security Report dai dati reali
      const securityReport = this.buildSecurityReportFromRealData({
        workflows,
        executions, 
        users,
        tenantId,
        categories: auditCategories
      });

      // 4. Salva audit nel database per storico
      await this.saveAuditToDatabase(tenantId, securityReport);

      res.json({
        success: true,
        data: securityReport,
        timestamp: new Date().toISOString()
      });
      return;

    } catch (error) {
      console.error('❌ Errore durante security audit:', error);
      res.status(500).json({
        success: false,
        error: 'Failed to generate security audit',
        details: error instanceof Error ? error.message : 'Unknown error'
      });
    }
  }

  /**
   * Get security score history
   * GET /api/tenant/:tenantId/security/score-history
   */
  async getSecurityScoreHistory(req: Request, res: Response): Promise<void> {
    try {
      const { tenantId } = req.params;
      const { days = 30 } = req.query;

      const result = await this.db.query(`
        SELECT 
          DATE_TRUNC('day', created_at) as date,
          AVG(security_score) as avg_score,
          MAX(security_score) as max_score,
          MIN(security_score) as min_score,
          COUNT(*) as audit_count
        FROM security_audits 
        WHERE tenant_id = $1 
          AND created_at >= NOW() - INTERVAL '${Number(days)} days'
        GROUP BY DATE_TRUNC('day', created_at)
        ORDER BY date DESC
        LIMIT 100
      `, [tenantId]);

      res.json({
        success: true,
        data: {
          history: result.rows,
          period: `${days} days`,
          totalAudits: result.rows.reduce((sum, row) => sum + row.audit_count, 0)
        }
      });

    } catch (error) {
      console.error('❌ Errore durante recupero score history:', error);
      res.status(500).json({
        success: false,
        error: 'Failed to get security score history'
      });
    }
  }

  /**
   * Get compliance report
   * GET /api/tenant/:tenantId/security/compliance
   */
  async getComplianceReport(req: Request, res: Response): Promise<void> {
    try {
      const { tenantId } = req.params;
      const { standard = 'all' } = req.query;

      // Recupera ultimo audit per compliance analysis
      const latestAudit = await this.getLatestAudit(tenantId);
      
      if (!latestAudit) {
        res.status(404).json({
          success: false,
          error: 'No security audit found. Please run an audit first.'
        });
        return;
      }

      const complianceReport = this.generateComplianceReport(latestAudit, standard as string);

      res.json({
        success: true,
        data: complianceReport,
        auditDate: latestAudit.created_at
      });

    } catch (error) {
      console.error('❌ Errore durante compliance report:', error);
      res.status(500).json({
        success: false,
        error: 'Failed to generate compliance report'
      });
    }
  }

  /**
   * Costruisce Security Report dai dati reali del database
   */
  private buildSecurityReportFromRealData(data: {
    workflows: any[];
    executions: any[];
    users: any[];
    tenantId: string;
    categories: string[];
  }): SecurityAuditReport {
    const { workflows, executions, users } = data;

    console.log(`🔍 Analizzando dati reali: ${workflows.length} workflows, ${executions.length} executions, ${users.length} users`);

    // Calcola security score basato sui dati reali
    const securityScore = this.calculateSecurityScoreFromRealData(workflows, executions, users);
    const riskLevel = this.getRiskLevel(securityScore);

    // Analizza solo le categorie richieste dai dati reali
    const categories: any = {};
    
    if (data.categories.includes('credentials')) {
      categories.credentials = this.analyzeCredentialsFromReal(workflows, users);
    }
    if (data.categories.includes('database')) {
      categories.database = this.analyzeDatabaseFromReal(workflows, executions);
    }
    if (data.categories.includes('nodes')) {
      categories.nodes = this.analyzeNodesFromReal(workflows);
    }
    if (data.categories.includes('filesystem')) {
      categories.filesystem = this.analyzeFilesystemFromReal(workflows);
    }
    if (data.categories.includes('instance')) {
      categories.instance = this.analyzeInstanceFromReal(executions, users);
    }
    if (data.categories.includes('access')) {
      categories.access = this.analyzeAccessFromReal(users, workflows);
    }

    console.log(`🎯 Categorie analizzate: ${Object.keys(categories).join(', ')} (richieste: ${data.categories.join(', ')})`);

    // Genera raccomandazioni dai dati reali
    const recommendations = this.generateSecurityRecommendationsFromReal(categories);

    // Valuta compliance dai dati reali
    const complianceStatus = this.evaluateComplianceFromReal(categories, workflows, users);

    return {
      overview: {
        securityScore,
        riskLevel,
        lastAuditDate: new Date().toISOString(),
        nextAuditDue: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
        totalIssues: this.countTotalIssues(categories),
        criticalIssues: this.countCriticalIssues(categories)
      },
      categories,
      recommendations,
      complianceStatus
    };
  }

  /**
   * OLD METHOD - mantenuto per retrocompatibilità
   * Costruisce Security Report avanzato dai dati n8n
   */
  private buildSecurityReport(data: {
    n8nAudit: any;
    workflows: any[];
    executions: any[];
    credentials: any[];
    users: any[];
    variables: any[];
    tenantId: string;
  }): SecurityAuditReport {
    const { n8nAudit, workflows, executions, credentials, users, variables } = data;

    // Calcola security score complessivo
    const securityScore = this.calculateSecurityScore(n8nAudit);
    const riskLevel = this.getRiskLevel(securityScore);

    // Analizza ogni categoria
    const categories = {
      credentials: this.analyzeCredentialsSecurity(n8nAudit['Credentials Risk Report'], credentials),
      database: this.analyzeDatabaseSecurity(n8nAudit['Database Risk Report']),
      nodes: this.analyzeNodesSecurity(n8nAudit['Nodes Risk Report']),
      filesystem: this.analyzeFilesystemSecurity(n8nAudit['Filesystem Risk Report']),
      instance: this.analyzeInstanceSecurity(n8nAudit['Instance Risk Report']),
      access: this.analyzeAccessSecurity(users, workflows)
    };

    // Genera raccomandazioni prioritarie
    const recommendations = this.generateSecurityRecommendations(categories);

    // Valuta compliance status
    const complianceStatus = this.evaluateCompliance(categories, workflows, users);

    return {
      overview: {
        securityScore,
        riskLevel,
        lastAuditDate: new Date().toISOString(),
        nextAuditDue: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(), // 7 giorni
        totalIssues: this.countTotalIssues(categories),
        criticalIssues: this.countCriticalIssues(categories)
      },
      categories,
      recommendations,
      complianceStatus
    };
  }

  /**
   * Calcola security score (0-100)
   */
  private calculateSecurityScore(n8nAudit: any): number {
    let score = 100;
    let totalPenalties = 0;

    // Analizza ogni categoria e applica penalità
    Object.keys(n8nAudit).forEach(categoryKey => {
      const category = n8nAudit[categoryKey];
      if (category && category.sections) {
        category.sections.forEach((section: any) => {
          const issueCount = section.location ? section.location.length : 0;
          const penalty = Math.min(issueCount * 5, 20); // Max 20 punti per categoria
          totalPenalties += penalty;
        });
      }
    });

    score = Math.max(0, score - totalPenalties);
    return Math.round(score);
  }

  /**
   * Determina risk level da score
   */
  private getRiskLevel(score: number): 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL' {
    if (score >= 90) return 'LOW';
    if (score >= 70) return 'MEDIUM';
    if (score >= 50) return 'HIGH';
    return 'CRITICAL';
  }

  /**
   * Analizza sicurezza credenziali
   */
  private analyzeCredentialsSecurity(credentialsAudit: any, credentials: any[]): SecurityCategory {
    const issues: SecurityIssue[] = [];
    let score = 100;

    if (credentialsAudit?.sections) {
      credentialsAudit.sections.forEach((section: any) => {
        const affectedCount = section.location ? section.location.length : 0;
        issues.push({
          title: section.title,
          description: section.description,
          severity: this.getSeverityFromTitle(section.title),
          recommendation: section.recommendation,
          affectedItems: affectedCount
        });
        score -= Math.min(affectedCount * 2, 15);
      });
    }

    // Analisi aggiuntive credentials
    const unusedCredentials = credentials.filter(cred => 
      // Logic per identificare credenziali inutilizzate
      !cred.name || cred.name.includes('test') || cred.name.includes('demo')
    );

    if (unusedCredentials.length > 0) {
      issues.push({
        title: 'Potentially unused credentials detected',
        description: `Found ${unusedCredentials.length} credentials that may not be in active use`,
        severity: 'MEDIUM',
        recommendation: 'Review and remove unused credentials to reduce attack surface',
        affectedItems: unusedCredentials.length
      });
    }

    return {
      risk: this.getRiskLevel(Math.max(0, score)),
      score: Math.max(0, score),
      issues,
      summary: `${issues.length} security issues found in credentials management`
    };
  }

  /**
   * Analizza sicurezza database
   */
  private analyzeDatabaseSecurity(databaseAudit: any): SecurityCategory {
    const issues: SecurityIssue[] = [];
    let score = 100;

    if (databaseAudit?.sections) {
      databaseAudit.sections.forEach((section: any) => {
        const affectedCount = section.location ? section.location.length : 0;
        issues.push({
          title: section.title,
          description: section.description,
          severity: 'HIGH', // Database security issues are generally high severity
          recommendation: section.recommendation,
          affectedItems: affectedCount
        });
        score -= Math.min(affectedCount * 5, 25);
      });
    }

    return {
      risk: this.getRiskLevel(Math.max(0, score)),
      score: Math.max(0, score),
      issues,
      summary: `${issues.length} database security issues identified`
    };
  }

  /**
   * Analizza sicurezza nodi
   */
  private analyzeNodesSecurity(nodesAudit: any): SecurityCategory {
    const issues: SecurityIssue[] = [];
    let score = 100;

    if (nodesAudit?.sections) {
      nodesAudit.sections.forEach((section: any) => {
        const affectedCount = section.location ? section.location.length : 0;
        issues.push({
          title: section.title,
          description: section.description,
          severity: section.title.includes('Community') ? 'HIGH' : 'MEDIUM',
          recommendation: section.recommendation,
          affectedItems: affectedCount
        });
        score -= Math.min(affectedCount * 3, 20);
      });
    }

    return {
      risk: this.getRiskLevel(Math.max(0, score)),
      score: Math.max(0, score),
      issues,
      summary: `${issues.length} node security concerns found`
    };
  }

  /**
   * Analizza sicurezza filesystem
   */
  private analyzeFilesystemSecurity(filesystemAudit: any): SecurityCategory {
    const issues: SecurityIssue[] = [];
    let score = 100;

    if (filesystemAudit?.sections) {
      filesystemAudit.sections.forEach((section: any) => {
        const affectedCount = section.location ? section.location.length : 0;
        issues.push({
          title: section.title,
          description: section.description,
          severity: 'HIGH', // Filesystem access is high risk
          recommendation: section.recommendation,
          affectedItems: affectedCount
        });
        score -= Math.min(affectedCount * 4, 25);
      });
    }

    return {
      risk: this.getRiskLevel(Math.max(0, score)),
      score: Math.max(0, score),
      issues,
      summary: `${issues.length} filesystem security issues detected`
    };
  }

  /**
   * Analizza sicurezza istanza
   */
  private analyzeInstanceSecurity(instanceAudit: any): SecurityCategory {
    const issues: SecurityIssue[] = [];
    let score = 100;

    if (instanceAudit?.sections) {
      instanceAudit.sections.forEach((section: any) => {
        const affectedCount = section.location ? section.location.length : 0;
        issues.push({
          title: section.title,
          description: section.description,
          severity: section.title.includes('webhook') ? 'CRITICAL' : 'HIGH',
          recommendation: section.recommendation,
          affectedItems: affectedCount
        });
        score -= Math.min(affectedCount * 6, 30);
      });
    }

    return {
      risk: this.getRiskLevel(Math.max(0, score)),
      score: Math.max(0, score),
      issues,
      summary: `${issues.length} instance-level security issues found`
    };
  }

  /**
   * Analizza sicurezza accessi
   */
  private analyzeAccessSecurity(users: any[], workflows: any[]): SecurityCategory {
    const issues: SecurityIssue[] = [];
    let score = 100;

    // Analisi utenti
    const adminUsers = users.filter(user => user.role === 'owner' || user.role === 'admin');
    if (adminUsers.length > 3) {
      issues.push({
        title: 'Excessive admin privileges',
        description: `${adminUsers.length} users have admin/owner privileges`,
        severity: 'MEDIUM',
        recommendation: 'Review admin privileges and apply principle of least privilege',
        affectedItems: adminUsers.length
      });
      score -= 10;
    }

    // Analisi workflow pubblici
    const publicWorkflows = workflows.filter(wf => wf.active && !wf.settings?.saveManualExecutions);
    if (publicWorkflows.length > workflows.length * 0.5) {
      issues.push({
        title: 'Many workflows lack execution logging',
        description: `${publicWorkflows.length} workflows don't save execution data`,
        severity: 'LOW',
        recommendation: 'Enable execution logging for audit trail purposes',
        affectedItems: publicWorkflows.length
      });
      score -= 5;
    }

    return {
      risk: this.getRiskLevel(Math.max(0, score)),
      score: Math.max(0, score),
      issues,
      summary: `${issues.length} access control issues identified`
    };
  }

  /**
   * Genera raccomandazioni di sicurezza
   */
  private generateSecurityRecommendations(categories: any): SecurityRecommendation[] {
    const recommendations: SecurityRecommendation[] = [];

    // Raccomandazioni basate sui issues più critici
    Object.entries(categories).forEach(([categoryName, category]: [string, any]) => {
      const criticalIssues = category.issues.filter((issue: SecurityIssue) => 
        issue.severity === 'CRITICAL' || issue.severity === 'HIGH'
      );

      if (criticalIssues.length > 0) {
        recommendations.push({
          priority: 'HIGH',
          category: categoryName,
          title: `Address ${categoryName} security issues`,
          description: `Fix ${criticalIssues.length} high-priority ${categoryName} security issues`,
          effort: criticalIssues.length > 3 ? 'HIGH' : 'MEDIUM',
          impact: 'HIGH'
        });
      }
    });

    // Raccomandazioni generali
    recommendations.push({
      priority: 'MEDIUM',
      category: 'monitoring',
      title: 'Implement continuous security monitoring',
      description: 'Set up automated security scanning and alerting for ongoing protection',
      effort: 'MEDIUM',
      impact: 'HIGH'
    });

    return recommendations.slice(0, 10); // Top 10 raccomandazioni
  }

  /**
   * Valuta compliance status
   */
  private evaluateCompliance(categories: any, workflows: any[], users: any[]): ComplianceStatus {
    // GDPR Compliance Check
    const gdprIssues: string[] = [];
    let gdprScore = 100;

    if (!workflows.some(wf => wf.name.toLowerCase().includes('data') && wf.name.toLowerCase().includes('delete'))) {
      gdprIssues.push('No data deletion workflow found');
      gdprScore -= 20;
    }

    // SOC2 Compliance Check  
    const soc2Issues: string[] = [];
    let soc2Score = 100;

    const hasAuditLogging = workflows.some(wf => wf.settings?.saveManualExecutions);
    if (!hasAuditLogging) {
      soc2Issues.push('Insufficient audit logging enabled');
      soc2Score -= 15;
    }

    // ISO27001 Compliance Check
    const isoIssues: string[] = [];
    let isoScore = 100;

    const criticalIssuesCount = this.countCriticalIssues(categories);
    if (criticalIssuesCount > 0) {
      isoIssues.push(`${criticalIssuesCount} critical security issues need addressing`);
      isoScore -= criticalIssuesCount * 10;
    }

    return {
      gdpr: {
        compliant: gdprScore >= 80,
        score: Math.max(0, gdprScore),
        issues: gdprIssues
      },
      soc2: {
        compliant: soc2Score >= 85,
        score: Math.max(0, soc2Score),
        issues: soc2Issues
      },
      iso27001: {
        compliant: isoScore >= 90,
        score: Math.max(0, isoScore),
        issues: isoIssues
      }
    };
  }

  /**
   * NUOVI METODI per analisi dati reali
   */
  private calculateSecurityScoreFromRealData(workflows: any[], executions: any[], users: any[]): number {
    let score = 100;
    
    // Penalità per workflow inattivi
    const inactiveWorkflows = workflows.filter(w => !w.active).length;
    score -= Math.min(inactiveWorkflows * 2, 20);
    
    // Penalità per esecuzioni fallite
    const failedExecutions = executions.filter(e => e.status === 'failed' || e.status === 'error').length;
    const failureRate = executions.length > 0 ? failedExecutions / executions.length : 0;
    score -= Math.min(failureRate * 30, 25);
    
    // Penalità per troppi admin users  
    const adminUsers = users.filter(u => u.role === 'admin' || u.role === 'owner').length;
    if (adminUsers > 2) {
      score -= (adminUsers - 2) * 5;
    }
    
    // Bonus per workflow attivi e stabili
    const recentSuccessfulExecutions = executions.filter(e => 
      e.status === 'success' && 
      new Date(e.started_at) > new Date(Date.now() - 7 * 24 * 60 * 60 * 1000)
    ).length;
    
    if (recentSuccessfulExecutions > 10) {
      score += 5;
    }

    console.log(`📊 Security score calcolato: ${Math.max(0, Math.round(score))} (workflows attivi: ${workflows.filter(w => w.active).length}/${workflows.length})`);
    
    return Math.max(0, Math.round(score));
  }

  private analyzeCredentialsFromReal(workflows: any[], users: any[]): SecurityCategory {
    const issues: SecurityIssue[] = [];
    let score = 100;

    // Analisi dettagliata credenziali hardcoded
    const credentialFindings: Array<{workflow: string, node: string, type: 'password' | 'apikey' | 'token' | 'connection', value: string}> = [];

    workflows.forEach(workflow => {
      if (workflow.raw_data && workflow.raw_data.nodes) {
        const nodes = workflow.raw_data.nodes;
        Object.keys(nodes).forEach(nodeId => {
          const node = nodes[nodeId];
          const nodeName = node.name || nodeId;
          const params = JSON.stringify(node.parameters || {}).toLowerCase();

          // Pattern specifici per diversi tipi di credenziali
          if (params.includes('"password":') && !params.includes('{{') && !params.includes('$node')) {
            const match = params.match(/"password":\s*"([^"]{1,50})/);
            if (match && match[1] && match[1] !== '' && !match[1].includes('{{')) {
              credentialFindings.push({
                workflow: workflow.name || workflow.id,
                node: nodeName,
                type: 'password',
                value: '***' + match[1].slice(-3)
              });
            }
          }

          if (params.includes('apikey') || params.includes('api_key')) {
            const match = params.match(/"(?:apikey|api_key)":\s*"([^"]{10,100})/);
            if (match && match[1] && !match[1].includes('{{')) {
              credentialFindings.push({
                workflow: workflow.name || workflow.id,
                node: nodeName,
                type: 'apikey',
                value: match[1].substring(0, 8) + '***'
              });
            }
          }

          if (params.includes('token') && !params.includes('{{')) {
            const match = params.match(/"token":\s*"([^"]{20,200})/);
            if (match && match[1] && !match[1].includes('{{')) {
              credentialFindings.push({
                workflow: workflow.name || workflow.id,
                node: nodeName,
                type: 'token',
                value: match[1].substring(0, 12) + '***'
              });
            }
          }

          // Database connection strings
          if (params.includes('connectionstring') || params.includes('connection_string')) {
            const match = params.match(/"(?:connectionstring|connection_string)":\s*"([^"]+)/);
            if (match && match[1] && (match[1].includes('password=') || match[1].includes('pwd='))) {
              credentialFindings.push({
                workflow: workflow.name || workflow.id,
                node: nodeName,
                type: 'connection',
                value: 'Database connection with embedded password'
              });
            }
          }
        });
      }
    });

    // Genera issue specifico per credenziali hardcoded
    if (credentialFindings.length > 0) {
      const criticalFindings = credentialFindings.slice(0, 5); // Top 5 più critici
      issues.push({
        title: 'CRITICAL: Hardcoded credentials detected',
        description: `${credentialFindings.length} hardcoded credentials found in workflow parameters`,
        severity: 'CRITICAL',
        recommendation: `IMMEDIATE ACTION: Replace hardcoded secrets in these locations: ${criticalFindings.map(f => `${f.type.toUpperCase()} in node "${f.node}" of workflow "${f.workflow}" (value: ${f.value})`).join(' | ')}. Use n8n credential store instead.`,
        location: {
          type: 'workflow',
          name: criticalFindings.map(f => f.workflow).join(', ')
        },
        affectedItems: credentialFindings.length
      });
      score -= credentialFindings.length * 15; // Penalità alta per credenziali hardcoded
    }

    // Analisi utenti admin specifici
    const adminUsers = users.filter(u => u.role === 'admin' || u.role === 'owner');
    if (adminUsers.length > 2) {
      issues.push({
        title: 'Excessive admin privileges detected',
        description: `${adminUsers.length} users have administrative access`,
        severity: 'MEDIUM',
        recommendation: `Review admin access for: ${adminUsers.map(u => u.email).join(', ')}. Consider reducing privileges following principle of least access.`,
        location: {
          type: 'user',
          name: adminUsers.map(u => u.email).join(', ')
        },
        affectedItems: adminUsers.length
      });
      score -= (adminUsers.length - 2) * 5;
    }

    // Credenziali non utilizzate (placeholder per future implementazioni)
    const unusedCredentials = workflows.filter(w => 
      w.raw_data && JSON.stringify(w.raw_data).includes('"credentials":') && !w.active
    );
    
    if (unusedCredentials.length > 0) {
      issues.push({
        title: 'Inactive workflows with stored credentials',
        description: `${unusedCredentials.length} inactive workflows still reference credentials`,
        severity: 'LOW',
        recommendation: `Clean up credentials in inactive workflows: ${unusedCredentials.slice(0, 3).map(w => w.name || w.id).join(', ')}${unusedCredentials.length > 3 ? ` and ${unusedCredentials.length - 3} others` : ''}`,
        location: {
          type: 'workflow',
          name: unusedCredentials.slice(0, 3).map(w => w.name || w.id).join(', ')
        },
        affectedItems: unusedCredentials.length
      });
      score -= unusedCredentials.length * 2;
    }

    return {
      risk: this.getRiskLevel(Math.max(0, score)),
      score: Math.max(0, score),
      issues,
      summary: `${issues.length} credential security issues: ${credentialFindings.length} hardcoded secrets, ${adminUsers.length} admin users`
    };
  }

  private analyzeDatabaseFromReal(workflows: any[], executions: any[]): SecurityCategory {
    const issues: SecurityIssue[] = [];
    let score = 100;

    // Analisi connessioni database non sicure
    const workflowsWithDbConnections = workflows.filter(w => {
      const rawDataStr = JSON.stringify(w.raw_data || {}).toLowerCase();
      return rawDataStr.includes('mysql') || rawDataStr.includes('postgres') || rawDataStr.includes('database');
    });

    if (workflowsWithDbConnections.length > 0) {
      issues.push({
        title: 'Database connections in workflows require security review',
        description: `${workflowsWithDbConnections.length} workflows connect to databases`,
        severity: 'MEDIUM',
        recommendation: 'Ensure database connections use encrypted connections and least privilege access',
        affectedItems: workflowsWithDbConnections.length
      });
      score -= workflowsWithDbConnections.length * 3;
    }

    // Analisi execution errors che potrebbero indicare problemi DB
    const dbErrors = executions.filter(e => {
      if (!e.has_error || !e.raw_data) return false;
      const errorStr = JSON.stringify(e.raw_data).toLowerCase();
      return errorStr.includes('connection') || errorStr.includes('database') || errorStr.includes('timeout');
    }).length;

    if (dbErrors > 0) {
      issues.push({
        title: 'Database connection errors detected',
        description: `${dbErrors} executions failed with database-related errors`,
        severity: 'MEDIUM',
        recommendation: 'Review database connection stability and error handling',
        affectedItems: dbErrors
      });
      score -= Math.min(dbErrors * 2, 15);
    }

    return {
      risk: this.getRiskLevel(Math.max(0, score)),
      score: Math.max(0, score),
      issues,
      summary: `${issues.length} database security concerns found`
    };
  }

  private analyzeNodesFromReal(workflows: any[]): SecurityCategory {
    const issues: SecurityIssue[] = [];
    let score = 100;

    // Analisi dettagliata per ogni workflow
    let totalNodes = 0;
    let httpNodes = 0;
    const riskyCodeNodes: Array<{workflow: string, node: string, type: string, code?: string, url?: string}> = [];
    const insecureHttpNodes: Array<{workflow: string, node: string, url: string, method: string}> = [];

    workflows.forEach(workflow => {
      if (workflow.raw_data && workflow.raw_data.nodes) {
        const nodes = workflow.raw_data.nodes;
        Object.keys(nodes).forEach(nodeId => {
          totalNodes++;
          const node = nodes[nodeId];
          const nodeType = node.type || '';
          const nodeName = node.name || nodeId;

          // Analisi HTTP nodes con URL specifici
          if (nodeType.includes('http')) {
            httpNodes++;
            const url = node.parameters?.url || '';
            const method = node.parameters?.requestMethod || 'GET';
            
            // Identifica URL potenzialmente insicuri
            if (url && (url.startsWith('http://') || url.includes('localhost') || url.includes('127.0.0.1'))) {
              insecureHttpNodes.push({
                workflow: workflow.name || workflow.id,
                node: nodeName,
                url: url.substring(0, 100), // Tronca URL lunghi
                method
              });
            }
          }

          // Analisi dettagliata Code nodes
          if (nodeType.includes('code') || nodeType.includes('function')) {
            const codeContent = node.parameters?.jsCode || node.parameters?.code || '';
            let riskLevel = 'MEDIUM';
            let riskReasons: string[] = [];

            // Analisi pattern rischiosi nel codice
            if (codeContent) {
              if (codeContent.includes('eval(') || codeContent.includes('Function(')) {
                riskLevel = 'CRITICAL';
                riskReasons.push('Dynamic code execution (eval/Function)');
              }
              if (codeContent.includes('require(') && !codeContent.includes('require("crypto")')) {
                riskLevel = 'HIGH';
                riskReasons.push('Dynamic module loading');
              }
              if (codeContent.includes('fs.') || codeContent.includes('filesystem')) {
                riskLevel = 'HIGH';
                riskReasons.push('File system access');
              }
              if (codeContent.includes('process.') || codeContent.includes('child_process')) {
                riskLevel = 'CRITICAL';
                riskReasons.push('Process manipulation');
              }
              if (codeContent.includes('password') || codeContent.includes('apikey') || codeContent.includes('token')) {
                riskLevel = 'HIGH';
                riskReasons.push('Hardcoded secrets detected');
              }
              if (codeContent.length > 500) {
                riskReasons.push('Complex logic (>500 chars)');
              }
            }

            riskyCodeNodes.push({
              workflow: workflow.name || workflow.id,
              node: nodeName,
              type: nodeType,
              code: riskReasons.length > 0 ? codeContent.substring(0, 200) + '...' : undefined
            });
          }
        });
      }
    });

    // Genera issues specifici per HTTP nodes insicuri
    if (insecureHttpNodes.length > 0) {
      const topInsecureUrls = insecureHttpNodes.slice(0, 5);
      issues.push({
        title: 'Insecure HTTP connections detected',
        description: `${insecureHttpNodes.length} HTTP nodes use non-HTTPS or localhost URLs`,
        severity: 'HIGH',
        recommendation: `Review these specific nodes: ${topInsecureUrls.map(n => `"${n.node}" in workflow "${n.workflow}" (${n.method} ${n.url})`).join(', ')}`,
        location: {
          type: 'node',
          name: `${topInsecureUrls.length} HTTP nodes`
        },
        affectedItems: insecureHttpNodes.length
      });
      score -= insecureHttpNodes.length * 5;
    }

    // Genera issues specifici per ogni Code node rischioso
    const criticalCodeNodes = riskyCodeNodes.filter(n => n.code);
    if (criticalCodeNodes.length > 0) {
      const topRiskyNodes = criticalCodeNodes.slice(0, 3);
      issues.push({
        title: 'High-risk custom code detected',
        description: `${criticalCodeNodes.length} code nodes contain potentially dangerous patterns`,
        severity: 'HIGH',
        recommendation: `IMMEDIATE ACTION REQUIRED - Review these nodes: ${topRiskyNodes.map(n => `"${n.node}" in workflow "${n.workflow}" (${n.type})`).join(', ')}. Check for: eval(), file system access, process manipulation, hardcoded secrets.`,
        location: {
          type: 'workflow',
          name: topRiskyNodes.map(n => n.workflow).join(', ')
        },
        affectedItems: criticalCodeNodes.length
      });
      score -= criticalCodeNodes.length * 10;
    }

    // Issues per code nodes generici (basso rischio)
    const lowRiskCodeNodes = riskyCodeNodes.filter(n => !n.code);
    if (lowRiskCodeNodes.length > 0 && lowRiskCodeNodes.length <= 10) {
      issues.push({
        title: 'Custom code nodes need review',
        description: `${lowRiskCodeNodes.length} code nodes contain custom logic`,
        severity: 'LOW',
        recommendation: `Review these specific nodes for input validation and error handling: ${lowRiskCodeNodes.slice(0, 5).map(n => `"${n.node}" in workflow "${n.workflow}"`).join(', ')}${lowRiskCodeNodes.length > 5 ? ` and ${lowRiskCodeNodes.length - 5} others` : ''}`,
        location: {
          type: 'node',
          name: `${lowRiskCodeNodes.length} code nodes`
        },
        affectedItems: lowRiskCodeNodes.length
      });
      score -= lowRiskCodeNodes.length * 1;
    }

    return {
      risk: this.getRiskLevel(Math.max(0, score)),
      score: Math.max(0, score),
      issues,
      summary: `${issues.length} node security issues found across ${totalNodes} total nodes (${httpNodes} HTTP, ${riskyCodeNodes.length} custom code)`
    };
  }

  private analyzeFilesystemFromReal(workflows: any[]): SecurityCategory {
    const issues: SecurityIssue[] = [];
    let score = 100;

    // Analisi accesso filesystem
    const workflowsWithFileAccess = workflows.filter(w => {
      const nodesStr = JSON.stringify((w.raw_data && w.raw_data.nodes) || {}).toLowerCase();
      return nodesStr.includes('file') || nodesStr.includes('csv') || nodesStr.includes('json') || nodesStr.includes('write');
    });

    if (workflowsWithFileAccess.length > 0) {
      issues.push({
        title: 'Workflows with filesystem access',
        description: `${workflowsWithFileAccess.length} workflows access files or write data`,
        severity: 'MEDIUM',
        recommendation: 'Ensure file operations use secure paths and validate file permissions',
        affectedItems: workflowsWithFileAccess.length
      });
      score -= workflowsWithFileAccess.length * 4;
    }

    return {
      risk: this.getRiskLevel(Math.max(0, score)),
      score: Math.max(0, score),
      issues,
      summary: `${issues.length} filesystem security issues detected`
    };
  }

  private analyzeInstanceFromReal(executions: any[], users: any[]): SecurityCategory {
    const issues: SecurityIssue[] = [];
    let score = 100;

    // Analisi stabilità istanza
    const recentExecutions = executions.filter(e => 
      new Date(e.started_at) > new Date(Date.now() - 24 * 60 * 60 * 1000)
    );
    
    const errorRate = recentExecutions.length > 0 ? 
      recentExecutions.filter(e => e.status === 'failed' || e.status === 'error').length / recentExecutions.length : 0;

    if (errorRate > 0.1) {
      issues.push({
        title: 'High error rate detected',
        description: `${Math.round(errorRate * 100)}% of recent executions failed`,
        severity: errorRate > 0.3 ? 'HIGH' : 'MEDIUM',
        recommendation: 'Investigate recurring errors and improve workflow reliability',
        affectedItems: Math.round(recentExecutions.length * errorRate)
      });
      score -= errorRate * 30;
    }

    // Analisi accessi admin
    const adminUsers = users.filter(u => u.role === 'admin' || u.role === 'owner').length;
    if (adminUsers > 3) {
      issues.push({
        title: 'Excessive administrative access',
        description: `${adminUsers} users have administrative privileges`,
        severity: 'MEDIUM',
        recommendation: 'Apply principle of least privilege and review admin access',
        affectedItems: adminUsers
      });
      score -= (adminUsers - 3) * 5;
    }

    return {
      risk: this.getRiskLevel(Math.max(0, score)),
      score: Math.max(0, score),
      issues,
      summary: `${issues.length} instance-level security issues found`
    };
  }

  private analyzeAccessFromReal(users: any[], workflows: any[]): SecurityCategory {
    const issues: SecurityIssue[] = [];
    let score = 100;

    // Analisi distribuzione utenti
    const totalUsers = users.length;
    const adminUsers = users.filter(u => u.role === 'admin' || u.role === 'owner').length;
    const regularUsers = totalUsers - adminUsers;

    if (adminUsers > totalUsers * 0.3) {
      issues.push({
        title: 'High percentage of admin users',
        description: `${adminUsers}/${totalUsers} users have admin access (${Math.round(adminUsers/totalUsers*100)}%)`,
        severity: 'MEDIUM',
        recommendation: 'Review and reduce administrative privileges where possible',
        affectedItems: adminUsers
      });
      score -= 10;
    }

    // Analisi workflow pubblici vs privati
    const activeWorkflows = workflows.filter(w => w.active).length;
    if (activeWorkflows > 0) {
      // Simula analisi di workflow con webhook pubblici
      const potentialPublicWorkflows = workflows.filter(w => {
        const rawDataStr = JSON.stringify(w.raw_data || {}).toLowerCase();
        return rawDataStr.includes('webhook') || rawDataStr.includes('trigger');
      }).length;

      if (potentialPublicWorkflows > 0) {
        issues.push({
          title: 'Workflows with potential public access',
          description: `${potentialPublicWorkflows} workflows may be publicly accessible`,
          severity: 'LOW',
          recommendation: 'Review webhook security and access controls',
          affectedItems: potentialPublicWorkflows
        });
        score -= potentialPublicWorkflows * 2;
      }
    }

    return {
      risk: this.getRiskLevel(Math.max(0, score)),
      score: Math.max(0, score),
      issues,
      summary: `${issues.length} access control issues identified`
    };
  }

  private generateSecurityRecommendationsFromReal(categories: any): SecurityRecommendation[] {
    const recommendations: SecurityRecommendation[] = [];

    // Raccomandazioni basate sui problemi più critici
    Object.entries(categories).forEach(([categoryName, category]: [string, any]) => {
      const criticalIssues = category.issues.filter((issue: SecurityIssue) => 
        issue.severity === 'CRITICAL' || issue.severity === 'HIGH'
      );

      if (criticalIssues.length > 0) {
        recommendations.push({
          priority: 'HIGH',
          category: categoryName,
          title: `Address ${categoryName} security issues`,
          description: `Fix ${criticalIssues.length} high-priority ${categoryName} security issues`,
          effort: criticalIssues.length > 3 ? 'HIGH' : 'MEDIUM',
          impact: 'HIGH'
        });
      }
    });

    // Raccomandazioni generali
    recommendations.push({
      priority: 'MEDIUM',
      category: 'monitoring',
      title: 'Implement continuous security monitoring',
      description: 'Set up automated security scanning and alerting for ongoing protection',
      effort: 'MEDIUM',
      impact: 'HIGH'
    });

    return recommendations.slice(0, 10); // Top 10 raccomandazioni
  }

  private evaluateComplianceFromReal(categories: any, workflows: any[], users: any[]): ComplianceStatus {
    // GDPR Compliance Check based on real data
    const gdprIssues: string[] = [];
    let gdprScore = 100;

    const hasDataProcessingWorkflows = workflows.some(w => {
      const nodesStr = JSON.stringify((w.raw_data && w.raw_data.nodes) || {}).toLowerCase();
      return nodesStr.includes('personal') || nodesStr.includes('email') || nodesStr.includes('user');
    });

    if (hasDataProcessingWorkflows && !workflows.some(w => w.name && w.name.toLowerCase().includes('delete'))) {
      gdprIssues.push('No data deletion workflows found for personal data processing');
      gdprScore -= 20;
    }

    // SOC2 Compliance Check
    const soc2Issues: string[] = [];
    let soc2Score = 100;

    const recentExecutions = workflows.some(w => {
      const settingsStr = JSON.stringify((w.raw_data && w.raw_data.settings) || {});
      return settingsStr.includes('log') || settingsStr.includes('saveManualExecutions');
    });
    if (!recentExecutions) {
      soc2Issues.push('Insufficient audit logging configuration detected');
      soc2Score -= 15;
    }

    // ISO27001 Compliance Check
    const isoIssues: string[] = [];
    let isoScore = 100;

    const criticalIssuesCount = this.countCriticalIssues(categories);
    if (criticalIssuesCount > 0) {
      isoIssues.push(`${criticalIssuesCount} critical security issues need immediate addressing`);
      isoScore -= criticalIssuesCount * 10;
    }

    return {
      gdpr: {
        compliant: gdprScore >= 80,
        score: Math.max(0, gdprScore),
        issues: gdprIssues
      },
      soc2: {
        compliant: soc2Score >= 85,
        score: Math.max(0, soc2Score),
        issues: soc2Issues
      },
      iso27001: {
        compliant: isoScore >= 90,
        score: Math.max(0, isoScore),
        issues: isoIssues
      }
    };
  }

  /**
   * Utility methods
   */
  private getSeverityFromTitle(title: string): 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL' {
    const lowerTitle = title.toLowerCase();
    if (lowerTitle.includes('critical') || lowerTitle.includes('unprotected') || lowerTitle.includes('injection')) {
      return 'CRITICAL';
    }
    if (lowerTitle.includes('high') || lowerTitle.includes('exposed') || lowerTitle.includes('unauthorized')) {
      return 'HIGH';
    }
    if (lowerTitle.includes('medium') || lowerTitle.includes('unused') || lowerTitle.includes('community')) {
      return 'MEDIUM';
    }
    return 'LOW';
  }

  private countTotalIssues(categories: any): number {
    return Object.values(categories).reduce((total: number, category: any) => 
      total + category.issues.length, 0
    );
  }

  private countCriticalIssues(categories: any): number {
    return Object.values(categories).reduce((total: number, category: any) => 
      total + category.issues.filter((issue: SecurityIssue) => issue.severity === 'CRITICAL').length, 0
    );
  }

  /**
   * Salva audit nel database
   */
  private async saveAuditToDatabase(tenantId: string, auditReport: SecurityAuditReport): Promise<void> {
    try {
      await this.db.query(`
        INSERT INTO security_audits (
          tenant_id, security_score, risk_level, 
          total_issues, critical_issues, 
          audit_data, created_at
        ) VALUES ($1, $2, $3, $4, $5, $6, NOW())
      `, [
        tenantId,
        auditReport.overview.securityScore,
        auditReport.overview.riskLevel,
        auditReport.overview.totalIssues,
        auditReport.overview.criticalIssues,
        JSON.stringify(auditReport)
      ]);

      console.log(`✅ Security audit salvato per tenant: ${tenantId}`);
    } catch (error) {
      console.error('❌ Errore salvataggio audit:', error);
      // Non bloccare il response se il salvataggio fallisce
    }
  }

  /**
   * Recupera ultimo audit dal database
   */
  private async getLatestAudit(tenantId: string): Promise<any> {
    const result = await this.db.query(`
      SELECT audit_data, created_at
      FROM security_audits 
      WHERE tenant_id = $1 
      ORDER BY created_at DESC 
      LIMIT 1
    `, [tenantId]);

    return result.rows[0]?.audit_data;
  }

  /**
   * Genera compliance report dettagliato
   */
  private generateComplianceReport(auditData: any, standard: string): any {
    const compliance = auditData.complianceStatus;
    
    if (standard === 'gdpr') return { gdpr: compliance.gdpr };
    if (standard === 'soc2') return { soc2: compliance.soc2 };
    if (standard === 'iso27001') return { iso27001: compliance.iso27001 };
    
    return compliance; // All standards
  }
}