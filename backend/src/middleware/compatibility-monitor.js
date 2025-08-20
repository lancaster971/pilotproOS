/**
 * Compatibility Monitor Middleware
 * 
 * Monitora in runtime la compatibilità con n8n e gestisce
 * automaticamente i breaking changes tra versioni.
 */

class CompatibilityMonitor {
  constructor(compatibilityService, fieldMapper) {
    this.compatibilityService = compatibilityService;
    this.fieldMapper = fieldMapper;
    this.lastCheck = null;
    this.checkInterval = 5 * 60 * 1000; // 5 minuti
    this.issues = [];
  }

  /**
   * Middleware per monitoring automatico
   */
  middleware() {
    return async (req, res, next) => {
      // Controlla compatibility periodicamente
      if (this.shouldCheckCompatibility()) {
        await this.performCompatibilityCheck();
      }

      // Aggiungi compatibility info alle response
      const originalJson = res.json.bind(res);
      res.json = (data) => {
        if (data && typeof data === 'object') {
          data._compatibility = {
            n8nVersion: this.compatibilityService.detectedVersion,
            status: this.compatibilityService.isReady ? 'compatible' : 'checking',
            lastCheck: this.lastCheck,
            issuesCount: this.issues.length
          };
        }
        return originalJson(data);
      };

      next();
    };
  }

  /**
   * Determina se è necessario un check di compatibilità
   */
  shouldCheckCompatibility() {
    if (!this.lastCheck) return true;
    return (Date.now() - this.lastCheck) > this.checkInterval;
  }

  /**
   * Esegue check di compatibilità completo
   */
  async performCompatibilityCheck() {
    try {
      this.lastCheck = Date.now();
      this.issues = [];

      // Check 1: Verifica versione n8n
      const currentVersion = await this.compatibilityService.detectN8nVersion();
      if (currentVersion !== this.compatibilityService.detectedVersion) {
        this.issues.push({
          type: 'version_change',
          message: `n8n version changed from ${this.compatibilityService.detectedVersion} to ${currentVersion}`,
          severity: 'warning',
          action: 'restart_recommended'
        });
      }

      // Check 2: Test query compatibility
      const testResults = await this.fieldMapper.testCompatibility(
        this.compatibilityService.db
      );

      // Analizza risultati test
      const compatibilityReport = this.fieldMapper.generateCompatibilityReport(testResults);
      
      if (compatibilityReport.issues.length > 0) {
        this.issues.push({
          type: 'schema_compatibility',
          message: 'Database schema compatibility issues detected',
          details: compatibilityReport.issues,
          severity: 'error',
          action: 'check_migrations'
        });
      }

      // Check 3: Performance monitoring
      await this.checkPerformance();

      console.log(`🔍 Compatibility check completed: ${this.issues.length} issues found`);

    } catch (error) {
      console.error('❌ Compatibility check failed:', error);
      this.issues.push({
        type: 'check_failure',
        message: 'Unable to perform compatibility check',
        error: error.message,
        severity: 'error'
      });
    }
  }

  /**
   * Monitora performance delle query
   */
  async checkPerformance() {
    const startTime = Date.now();
    
    try {
      // Test query semplice
      await this.compatibilityService.db.query('SELECT COUNT(*) FROM n8n.workflow_entity');
      
      const duration = Date.now() - startTime;
      
      if (duration > 5000) { // > 5 secondi
        this.issues.push({
          type: 'performance',
          message: `Query performance degraded: ${duration}ms`,
          severity: 'warning',
          action: 'optimize_queries'
        });
      }
      
    } catch (error) {
      this.issues.push({
        type: 'database_error',
        message: 'Database query failed',
        error: error.message,
        severity: 'error'
      });
    }
  }

  /**
   * Endpoint per compatibility status
   */
  getCompatibilityEndpoint() {
    return async (req, res) => {
      try {
        // Force fresh compatibility check
        await this.performCompatibilityCheck();
        
        const status = await this.compatibilityService.getHealthStatus();
        const testResults = await this.fieldMapper.testCompatibility(
          this.compatibilityService.db
        );
        
        res.json({
          compatibility: {
            status: status.compatibility,
            version: status.detectedVersion,
            isReady: status.isReady,
            lastCheck: new Date(this.lastCheck).toISOString()
          },
          
          issues: this.issues,
          
          schemaInfo: testResults,
          
          recommendations: this.generateRecommendations(),
          
          supportedVersions: status.supportedVersions,
          
          _metadata: {
            system: 'Business Process Operating System',
            endpoint: '/api/system/compatibility',
            timestamp: new Date().toISOString()
          }
        });
        
      } catch (error) {
        res.status(500).json({
          error: 'Compatibility check failed',
          message: error.message,
          timestamp: new Date().toISOString()
        });
      }
    };
  }

  /**
   * Genera raccomandazioni based on issues
   */
  generateRecommendations() {
    const recommendations = [];
    
    if (this.issues.length === 0) {
      recommendations.push('✅ System is fully compatible with current n8n version');
    }

    for (const issue of this.issues) {
      switch (issue.type) {
        case 'version_change':
          recommendations.push('🔄 Restart backend to apply new n8n version compatibility');
          break;
        case 'schema_compatibility':
          recommendations.push('🔧 Check n8n database migrations and update field mappings');
          break;
        case 'performance':
          recommendations.push('⚡ Optimize database queries and consider indexing');
          break;
        case 'database_error':
          recommendations.push('🗄️ Check database connectivity and permissions');
          break;
      }
    }

    if (recommendations.length === 0) {
      recommendations.push('📊 Monitor system regularly for optimal performance');
    }

    return recommendations;
  }

  /**
   * Alert system per critical issues
   */
  checkCriticalIssues() {
    const criticalIssues = this.issues.filter(issue => issue.severity === 'error');
    
    if (criticalIssues.length > 0) {
      console.error('🚨 CRITICAL COMPATIBILITY ISSUES:', criticalIssues);
      
      // Log to audit for alerting
      // In production: send alerts, notifications, etc.
      return true;
    }
    
    return false;
  }
}

export { CompatibilityMonitor };