/**
 * N8nFieldMapper - Cross-Version Field Mapping
 * 
 * Mappa automaticamente i nomi dei campi tra diverse versioni n8n
 * per mantenere compatibilità del backend con tutti gli upgrade.
 */

/**
 * Mapping completo dei campi per versioni n8n
 */
const N8N_FIELD_MAPPINGS = {
  // n8n 1.107.3+ (Current)
  '1.107.3': {
    execution_entity: {
      workflowId: 'workflowId',
      startedAt: 'startedAt', 
      stoppedAt: 'stoppedAt',
      createdAt: 'createdAt',
      updatedAt: 'updatedAt',
      deletedAt: 'deletedAt'
    },
    workflow_entity: {
      createdAt: 'createdAt',
      updatedAt: 'updatedAt',
      isArchived: 'isArchived'
    },
    credentials_entity: {
      createdAt: 'createdAt',
      updatedAt: 'updatedAt'
    }
  },
  
  // n8n 1.106.x (Previous format)
  '1.106.0': {
    execution_entity: {
      workflowId: 'workflow_id',
      startedAt: 'started_at',
      stoppedAt: 'stopped_at', 
      createdAt: 'created_at',
      updatedAt: 'updated_at',
      deletedAt: 'deleted_at'
    },
    workflow_entity: {
      createdAt: 'created_at',
      updatedAt: 'updated_at',
      isArchived: 'is_archived'
    },
    credentials_entity: {
      createdAt: 'created_at',
      updatedAt: 'updated_at'
    }
  },
  
  // n8n 1.100.x (Legacy format)
  '1.100.0': {
    execution_entity: {
      workflowId: 'workflow_id',
      startedAt: 'started_at',
      stoppedAt: 'stopped_at',
      createdAt: 'created_at', 
      updatedAt: 'updated_at',
      deletedAt: 'deleted_at'
    },
    workflow_entity: {
      createdAt: 'created_at',
      updatedAt: 'updated_at',
      isArchived: 'archived' // Diverso field name
    },
    credentials_entity: {
      createdAt: 'created_at',
      updatedAt: 'updated_at'
    }
  }
};

/**
 * Business Logic Mappings - Termini business che rimangono costanti
 */
const BUSINESS_FIELD_MAPPINGS = {
  // Termini business indipendenti dalla versione n8n
  processId: 'id',
  processName: 'name', 
  isActive: 'active',
  processCreated: 'createdAt',
  lastModified: 'updatedAt',
  
  // Execution mappings
  executionId: 'id',
  executionStatus: 'status',
  executionStarted: 'startedAt',
  executionFinished: 'stoppedAt',
  executionDuration: 'duration_calculated'
};

class N8nFieldMapper {
  constructor(version = '1.107.3') {
    this.version = version;
    this.mappings = N8N_FIELD_MAPPINGS[version] || N8N_FIELD_MAPPINGS['1.107.3'];
  }

  /**
   * Aggiorna la versione e i mappings
   */
  updateVersion(newVersion) {
    this.version = newVersion;
    this.mappings = N8N_FIELD_MAPPINGS[newVersion] || N8N_FIELD_MAPPINGS['1.107.3'];
    console.log(`🔄 Field mapper updated to n8n ${newVersion}`);
  }

  /**
   * Mappa un singolo campo per una tabella
   */
  mapField(table, logicalField) {
    const tableMapping = this.mappings[table];
    if (!tableMapping) {
      console.warn(`⚠️ No field mapping for table: ${table}`);
      return logicalField;
    }

    const actualField = tableMapping[logicalField];
    if (!actualField) {
      console.warn(`⚠️ No mapping for field: ${table}.${logicalField}`);
      return logicalField;
    }

    return actualField;
  }

  /**
   * Mappa multipli campi per una tabella
   */
  mapFields(table, logicalFields) {
    const result = {};
    
    for (const [alias, logicalField] of Object.entries(logicalFields)) {
      result[alias] = this.mapField(table, logicalField);
    }
    
    return result;
  }

  /**
   * Genera query SQL con field mapping automatico
   */
  generateQuery(template, table, fieldMappings) {
    let query = template;
    
    // Sostituisce i placeholder con i field names corretti
    for (const [placeholder, logicalField] of Object.entries(fieldMappings)) {
      const actualField = this.mapField(table, logicalField);
      const regex = new RegExp(`{{${placeholder}}}`, 'g');
      query = query.replace(regex, `"${actualField}"`);
    }
    
    return query;
  }

  /**
   * Template query per workflows compatibile cross-version
   */
  getWorkflowsQuery() {
    const template = `
      SELECT 
        w.id as process_id,
        w.name as process_name,
        w.active as is_active,
        w.{{createdAt}} as created_date,
        w.{{updatedAt}} as last_modified,
        
        -- Executions count today
        (
          SELECT COUNT(*) 
          FROM n8n.execution_entity e 
          WHERE e.{{workflowId}} = w.id 
          AND e.{{startedAt}} >= CURRENT_DATE
        ) as executions_today
        
      FROM n8n.workflow_entity w
      WHERE w.active = true
      ORDER BY w.{{updatedAt}} DESC
    `;

    return this.generateQuery(template, 'execution_entity', {
      workflowId: 'workflowId',
      startedAt: 'startedAt'
    }).replace(/w\.{{(\w+)}}/g, (match, field) => {
      const actualField = this.mapField('workflow_entity', field);
      return `w."${actualField}"`;
    });
  }

  /**
   * Template query per analytics compatibile cross-version
   */
  getAnalyticsQuery() {
    const template = `
      SELECT 
        COUNT(DISTINCT w.id) as total_processes,
        COUNT(DISTINCT CASE WHEN w.active = true THEN w.id END) as active_processes,
        COUNT(e.id) as total_executions,
        COUNT(CASE WHEN e.status = 'success' THEN 1 END) as successful_executions,
        AVG(EXTRACT(EPOCH FROM (e.{{stoppedAt}} - e.{{startedAt}})) * 1000) as avg_duration_ms
      FROM n8n.workflow_entity w
      LEFT JOIN n8n.execution_entity e ON w.id = e.{{workflowId}}
        AND e.{{startedAt}} >= NOW() - INTERVAL '7 days'
    `;

    return this.generateQuery(template, 'execution_entity', {
      workflowId: 'workflowId',
      startedAt: 'startedAt',
      stoppedAt: 'stoppedAt'
    });
  }

  /**
   * Verifica compatibilità con il database corrente
   */
  async testCompatibility(dbPool) {
    const tests = [
      {
        name: 'workflow_entity fields',
        query: `SELECT column_name FROM information_schema.columns 
                WHERE table_schema = 'n8n' AND table_name = 'workflow_entity'`
      },
      {
        name: 'execution_entity fields', 
        query: `SELECT column_name FROM information_schema.columns
                WHERE table_schema = 'n8n' AND table_name = 'execution_entity'`
      }
    ];

    const results = {};
    
    for (const test of tests) {
      try {
        const result = await dbPool.query(test.query);
        results[test.name] = {
          success: true,
          fields: result.rows.map(r => r.column_name)
        };
      } catch (error) {
        results[test.name] = {
          success: false,
          error: error.message
        };
      }
    }
    
    return results;
  }

  /**
   * Genera report di compatibilità dettagliato
   */
  generateCompatibilityReport(testResults) {
    const report = {
      version: this.version,
      timestamp: new Date().toISOString(),
      compatibility: 'unknown',
      issues: [],
      recommendations: []
    };

    // Analizza i risultati dei test
    const executionFields = testResults['execution_entity fields']?.fields || [];
    const workflowFields = testResults['workflow_entity fields']?.fields || [];

    // Controlla field names critici
    const hasNewWorkflowId = executionFields.includes('workflowId');
    const hasOldWorkflowId = executionFields.includes('workflow_id');
    const hasNewTimestamps = executionFields.includes('startedAt');
    const hasOldTimestamps = executionFields.includes('started_at');

    if (hasNewWorkflowId && hasNewTimestamps) {
      report.compatibility = 'modern';
      report.recommendations.push('Using modern field format (v1.107+)');
    } else if (hasOldWorkflowId && hasOldTimestamps) {
      report.compatibility = 'legacy';
      report.recommendations.push('Using legacy field format (v1.106-)');
      report.issues.push('Consider upgrading to latest n8n version');
    } else {
      report.compatibility = 'mixed';
      report.issues.push('Mixed field formats detected - potential migration issue');
      report.recommendations.push('Verify n8n migration completed successfully');
    }

    return report;
  }
}

export { 
  N8nFieldMapper,
  N8N_FIELD_MAPPINGS,
  BUSINESS_FIELD_MAPPINGS
};