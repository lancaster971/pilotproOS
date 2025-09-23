/**
 * Database Connection Module
 * 
 * Gestisce la connessione al database PostgreSQL/MySQL per il sistema di analytics n8n.
 * Fornisce un pool di connessioni ottimizzato e funzioni helper per query.
 */

import { Pool } from 'pg';


/**
 * Classe singleton per gestire la connessione al database
 */
export class DatabaseConnection {
  static instance = null;
  pool = null;
  config = null;
  isConnected = false;

  /**
   * Costruttore privato per pattern singleton
   */
  constructor() {
    // Config caricata in connect() per assicurare che dotenv sia già stato inizializzato
  }

  /**
   * Ottiene l'istanza singleton della connessione database
   * 
   * @returns Istanza della connessione database
   */
  static getInstance() {
    if (!DatabaseConnection.instance) {
      DatabaseConnection.instance = new DatabaseConnection();
    }
    return DatabaseConnection.instance;
  }

  /**
   * Carica la configurazione del database dalle variabili d'ambiente
   * 
   * @returns Configurazione database completa
   */
  loadDatabaseConfig() {
    const env = process.env;
    
    // Se DATABASE_URL è presente, parsalo
    if (env.DATABASE_URL) {
      const url = new URL(env.DATABASE_URL);
      return {
        type: 'postgres',
        host: url.hostname,
        port: parseInt(url.port || '5432'),
        database: url.pathname.slice(1), // Rimuove lo slash iniziale
        user: url.username,
        password: url.password || '',
        ssl: env.DB_SSL === 'true',
        max: parseInt(env.DB_POOL_SIZE || '20'),
        idleTimeoutMillis: parseInt(env.DB_IDLE_TIMEOUT || '30000'),
        connectionTimeoutMillis: parseInt(env.DB_CONNECTION_TIMEOUT || '5000')
      };
    }
    
    // Altrimenti usa variabili separate
    return {
      type: env.DB_TYPE || 'postgres',
      host: env.DB_HOST || 'localhost',
      port: parseInt(env.DB_PORT || '5432'),
      database: env.DB_NAME || 'n8n_mcp',
      user: env.DB_USER || 'postgres',
      password: env.DB_PASSWORD || '',
      ssl: env.DB_SSL === 'true',
      max: parseInt(env.DB_POOL_SIZE || '20'),
      idleTimeoutMillis: parseInt(env.DB_IDLE_TIMEOUT || '30000'),
      connectionTimeoutMillis: parseInt(env.DB_CONNECTION_TIMEOUT || '5000')
    };
  }

  /**
   * Inizializza la connessione al database
   * 
   * @returns Promise che si risolve quando la connessione è stabilita
   */
  async connect() {
    if (this.isConnected && this.pool) {
      console.log('Database già connesso');
      return;
    }

    // Carica config qui, dopo che dotenv è stato inizializzato
    if (!this.config) {
      this.config = this.loadDatabaseConfig();
      console.log('Config database caricata:', { 
        host: this.config.host, 
        database: this.config.database, 
        user: this.config.user 
      });
    }

    try {
      // Configurazione pool per PostgreSQL
      const poolConfig = {
        host: this.config.host,
        port: this.config.port,
        database: this.config.database,
        user: this.config.user,
        password: this.config.password,
        max: this.config.max,
        idleTimeoutMillis: this.config.idleTimeoutMillis,
        connectionTimeoutMillis: this.config.connectionTimeoutMillis,
      };

      // Aggiungi SSL se configurato
      if (this.config.ssl) {
        poolConfig.ssl = {
          rejectUnauthorized: false
        };
      }

      // Use shared pool instead of creating new one
      this.pool = dbPool;

      // Gestione eventi del pool
      this.pool.on('error', (err) => {
        console.error('Errore inaspettato nel pool del database:', err);
      });

      this.pool.on('connect', () => {
        console.log('Nuova connessione aggiunta al pool');
      });

      // Test della connessione
      await this.testConnection();
      
      this.isConnected = true;
      console.log(`✅ Connesso al database ${this.config.database} su ${this.config.host}:${this.config.port}`);
    } catch (error) {
      console.error('❌ Errore nella connessione al database:', error);
      throw error;
    }
  }

  /**
   * Testa la connessione al database
   * 
   * @returns Promise che si risolve se la connessione è valida
   */
  async testConnection() {
    if (!this.pool) {
      throw new Error('Pool non inizializzato');
    }

    const result = await this.pool.query('SELECT NOW() as current_time');
    console.log('Test connessione riuscito:', result.rows[0].current_time);
  }

  /**
   * Esegue una query sul database
   * 
   * @param text - Testo della query SQL
   * @param params - Parametri per la query parametrizzata
   * @returns Promise con il risultato della query
   */
  async query(text, params) {
    if (!this.pool) {
      throw new Error('Database non connesso. Chiamare connect() prima di eseguire query.');
    }

    const start = Date.now();
    
    try {
      const result = await this.pool.query(text, params);
      
      // Log query in modalità debug
      if (process.env.LOG_LEVEL === 'debug') {
        const duration = Date.now() - start;
        console.log('Query eseguita:', {
          text: text.substring(0, 100),
          duration: `${duration}ms`,
          rows: result.rowCount
        });
      }
      
      return result;
    } catch (error) {
      console.error('Errore nell\'esecuzione della query:', error);
      throw error;
    }
  }

  /**
   * Esegue una transazione sul database
   * 
   * @param callback - Funzione che contiene le operazioni da eseguire in transazione
   * @returns Promise con il risultato della transazione
   */
  async transaction(callback) {
    if (!this.pool) {
      throw new Error('Database non connesso');
    }

    const client = await this.pool.connect();
    
    try {
      await client.query('BEGIN');
      const result = await callback(client);
      await client.query('COMMIT');
      return result;
    } catch (error) {
      await client.query('ROLLBACK');
      throw error;
    } finally {
      client.release();
    }
  }

  /**
   * Ottiene una singola riga dal risultato della query
   * 
   * @param text - Testo della query SQL
   * @param params - Parametri per la query
   * @returns Promise con la prima riga o null
   */
  async getOne(text, params) {
    const result = await this.query<T>(text, params);
    return result.rows[0] || null;
  }

  /**
   * Ottiene tutte le righe dal risultato della query
   * 
   * @param text - Testo della query SQL
   * @param params - Parametri per la query
   * @returns Promise con array di righe
   */
  async getMany(text, params) {
    const result = await this.query<T>(text, params);
    return result.rows;
  }

  /**
   * Esegue una query di INSERT e restituisce l'ID generato
   * 
   * @param text - Testo della query INSERT
   * @param params - Parametri per la query
   * @returns Promise con l'ID della riga inserita
   */
  async insert(text, params) {
    const queryText = text.includes('RETURNING') ? text : `${text} RETURNING *`;
    const result = await this.query<T>(queryText, params);
    return result.rows[0];
  }

  /**
   * Esegue una query di UPDATE
   * 
   * @param text - Testo della query UPDATE
   * @param params - Parametri per la query
   * @returns Promise con il numero di righe modificate
   */
  async update(text, params) {
    const result = await this.query(text, params);
    return result.rowCount || 0;
  }

  /**
   * Esegue una query di DELETE
   * 
   * @param text - Testo della query DELETE
   * @param params - Parametri per la query
   * @returns Promise con il numero di righe eliminate
   */
  async delete(text, params) {
    const result = await this.query(text, params);
    return result.rowCount || 0;
  }

  /**
   * Verifica se una tabella esiste nel database
   * 
   * @param tableName - Nome della tabella da verificare
   * @returns Promise con booleano che indica se la tabella esiste
   */
  async tableExists(tableName) {
    const query = `
      SELECT EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name = $1
      ) as exists
    `;
    
    const result = await this.getOne(query, [tableName]);
    return result && result.exists || false;
  }

  /**
   * Inizializza lo schema del database eseguendo il file SQL di migrazione
   * 
   * @returns Promise che si risolve quando lo schema è creato
   */
  async initializeSchema() {
    try {
      console.log('Inizializzazione schema database...');
      
      // Leggi il file SQL di migrazione
      const fs = await import('fs/promises');
      const path = await import('path');
      const { fileURLToPath } = await import('url');
      
      const __filename = fileURLToPath(import.meta.url);
      const __dirname = path.dirname(__filename);
      
      const sqlPath = path.join(__dirname, 'migrations', '001_initial_schema.sql');
      const sqlContent = await fs.readFile(sqlPath, 'utf-8');
      
      // Esegui lo script SQL
      await this.query(sqlContent);
      
      console.log('✅ Schema database inizializzato con successo');
    } catch (error) {
      console.error('❌ Errore nell\'inizializzazione dello schema:', error);
      throw error;
    }
  }

  /**
   * Ottieni la configurazione del database
   * 
   * @returns Configurazione del database
   */
  getConfig() {
    if (!this.config) {
      throw new Error('Database configuration not initialized');
    }
    return { ...this.config };
  }

  /**
   * Chiude la connessione al database
   * 
   * @returns Promise che si risolve quando la connessione è chiusa
   */
  async disconnect() {
    if (this.pool) {
      await this.pool.end();
      this.pool = null;
      this.isConnected = false;
      console.log('Disconnesso dal database');
    }
  }

  /**
   * Ottiene statistiche sul pool di connessioni
   * 
   * @returns Oggetto con statistiche del pool
   */
  getPoolStats() {
    if (!this.pool) {
      return null;
    }

    return {
      totalCount: this.pool.totalCount,
      idleCount: this.pool.idleCount,
      waitingCount: this.pool.waitingCount
    };
  }
}

/**
 * Istanza singleton esportata per uso globale
 */
export const db = DatabaseConnection.getInstance();

/**
 * Helper function per inizializzare il database
 * 
 * @returns Promise che si risolve quando il database è pronto
 */
export async function initializeDatabase() {
  const database = DatabaseConnection.getInstance();
  await database.connect();
  
  // Verifica se le tabelle esistono, altrimenti inizializza lo schema
  const workflowsExists = await database.tableExists('workflows');
  if (!workflowsExists) {
    console.log('Tabelle non trovate, inizializzazione schema...');
    await database.initializeSchema();
  } else {
    console.log('Schema database già presente');
  }
}

/**
 * Helper per eseguire query con retry in caso di errore
 * 
 * @param queryFn - Funzione che esegue la query
 * @param maxRetries - Numero massimo di tentativi
 * @param retryDelay - Delay tra i tentativi in ms
 * @returns Promise con il risultato della query
 */
export async function queryWithRetry(
  queryFn,
  maxRetries = 3,
  retryDelay = 1000
) {
  let lastError = null;
  
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await queryFn();
    } catch (error) {
      lastError = error;
      console.warn(`Tentativo ${i + 1} fallito:`, error);
      
      if (i < maxRetries - 1) {
        await new Promise(resolve => setTimeout(resolve, retryDelay));
      }
    }
  }
  
  throw lastError || new Error('Query fallita dopo tutti i tentativi');
}