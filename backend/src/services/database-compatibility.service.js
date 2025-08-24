/**
 * DatabaseCompatibilityService - n8n Schema Compatibility Layer
 * 
 * Gestisce automaticamente i breaking changes tra versioni n8n
 * mantenendo il backend sempre compatibile con qualsiasi versione.
 */

class DatabaseCompatibilityService {
  constructor(dbPool) {
    this.db = dbPool;
    this.detectedVersion = null;
    this.fieldMappings = null;
    this.isReady = false;
  }

  /**
   * Inizializza il servizio rilevando la versione n8n corrente
   */
  async initialize() {
    try {
      this.detectedVersion = await this.detectN8nVersion();
      this.fieldMappings = this.getFieldMappings(this.detectedVersion);
      this.isReady = true;
      
      console.log(`✅ Database compatibility initialized for n8n ${this.detectedVersion}`);
      return true;
    } catch (error) {
      console.error('❌ Failed to initialize database compatibility:', error);
      this.isReady = false;
      return false;
    }
  }

  /**
   * Rileva la versione n8n dal database analizzando le migrazioni
   */
  async detectN8nVersion() {
    try {
      // Rileva versione dalle migrazioni più recenti
      const latestMigrations = await this.db.query(`
        SELECT name, timestamp 
        FROM n8n.migrations 
        ORDER BY timestamp DESC 
        LIMIT 10
      `);

      const migrations = latestMigrations.rows;
      
      // Analizza le migrazioni per determinare la versione
      if (migrations.some(m => m.name.includes('AddInputsOutputsToTestCaseExecution'))) {
        return '1.107.3'; // Latest detected features
      } else if (migrations.some(m => m.name.includes('AddLastActiveAtColumnToUser'))) {
        return '1.106.0';
      } else if (migrations.some(m => m.name.includes('AddWorkflowArchivedColumn'))) {
        return '1.105.0';
      } else if (migrations.some(m => m.name.includes('RenameAnalyticsToInsights'))) {
        return '1.100.0';
      } else {
        return '1.0.0'; // Fallback version
      }
      
    } catch (error) {
      console.warn('⚠️ Could not detect n8n version, using fallback');
      return '1.0.0';
    }
  }

  /**
   * Ottiene i mapping dei campi per la versione rilevata
   */
  getFieldMappings(version) {
    const mappings = {
      '1.107.3': {
        execution_entity: {
          workflowId: 'workflowId',      // Nuovo formato
          startedAt: 'startedAt',
          stoppedAt: 'stoppedAt',
          createdAt: 'createdAt',
          updatedAt: 'updatedAt'
        },
        workflow_entity: {
          createdAt: 'createdAt',
          updatedAt: 'updatedAt',
          isArchived: 'isArchived'
        }
      },
      '1.106.0': {
        execution_entity: {
          workflowId: 'workflow_id',     // Vecchio formato
          startedAt: 'started_at',
          stoppedAt: 'stopped_at',
          createdAt: 'created_at',
          updatedAt: 'updated_at'
        },
        workflow_entity: {
          createdAt: 'created_at',
          updatedAt: 'updated_at',
          isArchived: 'is_archived'
        }
      },
      'fallback': {
        execution_entity: {
          workflowId: 'workflow_id',
          startedAt: 'started_at',
          stoppedAt: 'stopped_at',
          createdAt: 'created_at',
          updatedAt: 'updated_at'
        },
        workflow_entity: {
          createdAt: 'created_at',
          updatedAt: 'updated_at',
          isArchived: 'is_archived'
        }
      }
    };

    return mappings[version] || mappings['fallback'];
  }

  /**
   * Mappa i nomi dei campi per la versione corrente
   */
  mapFieldName(table, logicalField) {
    if (!this.isReady || !this.fieldMappings) {
      console.warn('⚠️ Compatibility service not ready, using fallback');
      return logicalField;
    }

    const mapping = this.fieldMappings[table];
    if (!mapping) {
      console.warn(`⚠️ No mapping found for table: ${table}`);
      return logicalField;
    }

    return mapping[logicalField] || logicalField;
  }

  /**
   * Genera query SQL compatibile con la versione corrente
   */
  buildCompatibleQuery(baseQuery, table, fields) {
    if (!this.isReady) {
      return baseQuery; // Return original if not ready
    }

    let compatibleQuery = baseQuery;

    // Sostituisce i field names con quelli compatibili
    for (const logicalField of fields) {
      const actualField = this.mapFieldName(table, logicalField);
      const regex = new RegExp(`e\\.${logicalField}`, 'g');
      compatibleQuery = compatibleQuery.replace(regex, `e."${actualField}"`);
    }

    return compatibleQuery;
  }

  /**
   * Esegue query con fallback automatico per compatibility
   */
  async executeWithFallback(queries) {
    const queryVersions = Array.isArray(queries) ? queries : [queries];
    
    for (let i = 0; i < queryVersions.length; i++) {
      try {
        const result = await this.db.query(queryVersions[i]);
        
        if (i > 0) {
          console.log(`✅ Query succeeded with fallback strategy ${i + 1}`);
        }
        
        return result;
      } catch (error) {
        console.warn(`⚠️ Query attempt ${i + 1} failed:`, error.message);
        
        if (i === queryVersions.length - 1) {
          throw new Error(`All query strategies failed. Last error: ${error.message}`);
        }
      }
    }
  }

  /**
   * Ottieni workflows con compatibility automatica
   */
  async getWorkflowsCompatible() {
    const workflowIdField = this.mapFieldName('execution_entity', 'workflowId');
    const startedAtField = this.mapFieldName('execution_entity', 'startedAt');
    const createdAtField = this.mapFieldName('workflow_entity', 'createdAt');
    const updatedAtField = this.mapFieldName('workflow_entity', 'updatedAt');

    const queries = [
      // Modern query (v1.107+)
      `SELECT 
        w.id as process_id,
        w.name as process_name,
        w.active as is_active,
        w."${createdAtField}" as created_date,
        w."${updatedAtField}" as last_modified,
        (
          SELECT COUNT(*) 
          FROM n8n.execution_entity e 
          WHERE e."${workflowIdField}" = w.id 
          AND e."${startedAtField}" >= CURRENT_DATE
        ) as executions_today
      FROM n8n.workflow_entity w
      WHERE w."isArchived" = false
      ORDER BY w.active DESC, w."${updatedAtField}" DESC`,
      
      // Legacy query (v1.106-)
      `SELECT 
        w.id as process_id,
        w.name as process_name,
        w.active as is_active,
        w.created_at as created_date,
        w.updated_at as last_modified,
        (
          SELECT COUNT(*) 
          FROM n8n.execution_entity e 
          WHERE e.workflow_id = w.id 
          AND e.started_at >= CURRENT_DATE
        ) as executions_today
      FROM n8n.workflow_entity w
      WHERE w."isArchived" = false
      ORDER BY w.active DESC, w.updated_at DESC`,
      
      // Ultimate fallback (basic) - SHOW ALL WORKFLOWS
      `SELECT 
        w.id as process_id,
        w.name as process_name,
        w.active as is_active,
        0 as executions_today
      FROM n8n.workflow_entity w
      WHERE w."isArchived" = false
      ORDER BY w.active DESC, w.name ASC`
    ];

    return await this.executeWithFallback(queries);
  }

  /**
   * Ottieni analytics con compatibility automatica
   */
  async getAnalyticsCompatible() {
    const workflowIdField = this.mapFieldName('execution_entity', 'workflowId');
    const startedAtField = this.mapFieldName('execution_entity', 'startedAt');
    const stoppedAtField = this.mapFieldName('execution_entity', 'stoppedAt');

    const queries = [
      // Modern query (v1.107+)
      `SELECT 
        COUNT(DISTINCT w.id) as total_processes,
        COUNT(DISTINCT CASE WHEN w.active = true THEN w.id END) as active_processes,
        COUNT(e.id) as total_executions,
        COUNT(CASE WHEN e.status = 'success' THEN 1 END) as successful_executions,
        AVG(EXTRACT(EPOCH FROM (e."${stoppedAtField}" - e."${startedAtField}")) * 1000) as avg_duration_ms
      FROM n8n.workflow_entity w
      LEFT JOIN n8n.execution_entity e ON w.id = e."${workflowIdField}"
        AND e."${startedAtField}" >= NOW() - INTERVAL '7 days'`,
      
      // Legacy query (v1.106-)
      `SELECT 
        COUNT(DISTINCT w.id) as total_processes,
        COUNT(DISTINCT CASE WHEN w.active = true THEN w.id END) as active_processes,
        COUNT(e.id) as total_executions,
        COUNT(CASE WHEN e.status = 'success' THEN 1 END) as successful_executions,
        AVG(EXTRACT(EPOCH FROM (e.stopped_at - e.started_at)) * 1000) as avg_duration_ms
      FROM n8n.workflow_entity w
      LEFT JOIN n8n.execution_entity e ON w.id = e.workflow_id
        AND e.started_at >= NOW() - INTERVAL '7 days'`,
      
      // Ultimate fallback
      `SELECT 
        COUNT(*) as total_processes,
        0 as active_processes,
        0 as total_executions,
        0 as successful_executions,
        0 as avg_duration_ms
      FROM n8n.workflow_entity w`
    ];

    return await this.executeWithFallback(queries);
  }

  /**
   * Health check per compatibility
   */
  async getHealthStatus() {
    return {
      isReady: this.isReady,
      detectedVersion: this.detectedVersion,
      supportedVersions: ['1.107.3', '1.106.0', '1.105.0', '1.100.0'],
      lastCheck: new Date().toISOString(),
      compatibility: this.isReady ? 'compatible' : 'unknown'
    };
  }
}

export { DatabaseCompatibilityService };