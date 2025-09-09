/**
 * Base Repository
 * 
 * Classe base astratta per tutti i repository.
 * Fornisce funzionalità comuni per CRUD e query.
 */

import { DatabaseConnection, db } from '../connection.js';
import { QueryResult, QueryResultRow } from 'pg';
import {
  PaginatedResult,
  QueryFilters,
  BatchOperationResult,
  createPaginatedResult,
  validatePaginationParams,
  buildWhereClause
} from '../models/index.js';

/**
 * Classe base astratta per i repository
 * @template T - Tipo del modello gestito dal repository
 */
export abstract class BaseRepository<T extends QueryResultRow> {
  protected db: DatabaseConnection;
  protected tableName: string;

  /**
   * Costruttore del repository base
   * 
   * @param tableName - Nome della tabella nel database
   */
  constructor(tableName: string) {
    this.db = DatabaseConnection.getInstance();
    this.tableName = tableName;
  }

  /**
   * Trova un record per ID
   * 
   * @param id - ID del record da cercare
   * @returns Record trovato o null
   */
  async findById(id: string | number): Promise<T | null> {
    const query = `SELECT * FROM ${this.tableName} WHERE id = $1`;
    return await this.db.getOne<T>(query, [id]);
  }

  /**
   * Trova tutti i record
   * 
   * @param filters - Filtri opzionali per la query
   * @returns Array di record
   */
  async findAll(filters?: QueryFilters): Promise<T[]> {
    let query = `SELECT * FROM ${this.tableName}`;
    const params: any[] = [];
    
    // Applica ordinamento se specificato
    if (filters?.orderBy) {
      query += ` ORDER BY ${filters.orderBy} ${filters.orderDir || 'ASC'}`;
    }
    
    // Applica limite e offset
    if (filters?.limit) {
      query += ` LIMIT ${filters.limit}`;
      if (filters.offset) {
        query += ` OFFSET ${filters.offset}`;
      }
    }
    
    return await this.db.getMany<T>(query, params);
  }

  /**
   * Trova record con paginazione
   * 
   * @param page - Numero di pagina (1-based)
   * @param pageSize - Dimensione della pagina
   * @param filters - Filtri aggiuntivi
   * @returns Risultato paginato
   */
  async findPaginated(
    page: number = 1,
    pageSize: number = 20,
    filters?: QueryFilters
  ): Promise<PaginatedResult<T>> {
    const { page: validPage, pageSize: validPageSize, offset } = validatePaginationParams(page, pageSize);
    
    // Query per i dati
    let dataQuery = `SELECT * FROM ${this.tableName}`;
    
    // Aggiungi ordinamento
    if (filters?.orderBy) {
      dataQuery += ` ORDER BY ${filters.orderBy} ${filters.orderDir || 'ASC'}`;
    }
    
    dataQuery += ` LIMIT $1 OFFSET $2`;
    
    // Query per il conteggio totale
    const countQuery = `SELECT COUNT(*) as total FROM ${this.tableName}`;
    
    // Esegui entrambe le query in parallelo
    const [data, countResult] = await Promise.all([
      this.db.getMany<T>(dataQuery, [validPageSize, offset]),
      this.db.getOne<{ total: string }>(countQuery)
    ]);
    
    const total = parseInt(countResult?.total || '0');
    
    return createPaginatedResult(data, total, validPage, validPageSize);
  }

  /**
   * Crea un nuovo record
   * 
   * @param data - Dati del record da creare
   * @returns Record creato
   */
  async create(data: Partial<T>): Promise<T> {
    const fields = Object.keys(data);
    const values = Object.values(data);
    const placeholders = fields.map((_, index) => `$${index + 1}`).join(', ');
    
    const query = `
      INSERT INTO ${this.tableName} (${fields.join(', ')})
      VALUES (${placeholders})
      RETURNING *
    `;
    
    return await this.db.insert<T>(query, values);
  }

  /**
   * Crea multipli record in batch
   * 
   * @param items - Array di record da creare
   * @returns Risultato dell'operazione batch
   */
  async createBatch(items: Partial<T>[]): Promise<BatchOperationResult> {
    const startTime = Date.now();
    let successful = 0;
    let failed = 0;
    const errors: Array<{ id: string | number; error: string }> = [];
    
    // Usa transazione per operazione atomica
    await this.db.transaction(async (client) => {
      for (let i = 0; i < items.length; i++) {
        try {
          await this.create(items[i]);
          successful++;
        } catch (error) {
          failed++;
          errors.push({
            id: i,
            error: error instanceof Error ? error.message : 'Errore sconosciuto'
          });
        }
      }
    });
    
    return {
      successful,
      failed,
      errors,
      duration_ms: Date.now() - startTime
    };
  }

  /**
   * Aggiorna un record per ID
   * 
   * @param id - ID del record da aggiornare
   * @param data - Dati da aggiornare
   * @returns Numero di record aggiornati
   */
  async update(id: string | number, data: Partial<T>): Promise<number> {
    // Rimuovi updated_at se presente nei dati, verrà impostato automaticamente
    const dataWithoutUpdatedAt = { ...data };
    delete (dataWithoutUpdatedAt as any).updated_at;
    
    // Aggiungi sempre updated_at con CURRENT_TIMESTAMP
    const fieldsToUpdate = { ...dataWithoutUpdatedAt };
    
    const fields = Object.keys(fieldsToUpdate);
    const values = Object.values(fieldsToUpdate);
    
    const setClause = fields
      .map((field, index) => `${field} = $${index + 2}`)
      .join(', ');
    
    // Aggiungi updated_at solo se ci sono altri campi da aggiornare
    const updateClause = setClause 
      ? `${setClause}, updated_at = CURRENT_TIMESTAMP`
      : 'updated_at = CURRENT_TIMESTAMP';
    
    const query = `
      UPDATE ${this.tableName}
      SET ${updateClause}
      WHERE id = $1
    `;
    
    return await this.db.update(query, [id, ...values]);
  }

  /**
   * Aggiorna multipli record che soddisfano una condizione
   * 
   * @param condition - Condizione WHERE
   * @param data - Dati da aggiornare
   * @returns Numero di record aggiornati
   */
  async updateWhere(condition: Record<string, any>, data: Partial<T>): Promise<number> {
    const { clause: whereClause, params: whereParams } = buildWhereClause(condition);
    
    const fields = Object.keys(data);
    const values = Object.values(data);
    
    const setClause = fields
      .map((field, index) => `${field} = $${whereParams.length + index + 1}`)
      .join(', ');
    
    const query = `
      UPDATE ${this.tableName}
      SET ${setClause}, updated_at = CURRENT_TIMESTAMP
      ${whereClause}
    `;
    
    return await this.db.update(query, [...whereParams, ...values]);
  }

  /**
   * Elimina un record per ID
   * 
   * @param id - ID del record da eliminare
   * @returns Numero di record eliminati
   */
  async delete(id: string | number): Promise<number> {
    const query = `DELETE FROM ${this.tableName} WHERE id = $1`;
    return await this.db.delete(query, [id]);
  }

  /**
   * Elimina multipli record che soddisfano una condizione
   * 
   * @param condition - Condizione WHERE
   * @returns Numero di record eliminati
   */
  async deleteWhere(condition: Record<string, any>): Promise<number> {
    const { clause: whereClause, params } = buildWhereClause(condition);
    
    if (!whereClause) {
      throw new Error('Condizione WHERE richiesta per deleteWhere');
    }
    
    const query = `DELETE FROM ${this.tableName} ${whereClause}`;
    return await this.db.delete(query, params);
  }

  /**
   * Conta i record che soddisfano una condizione
   * 
   * @param condition - Condizione WHERE opzionale
   * @returns Numero di record
   */
  async count(condition?: Record<string, any>): Promise<number> {
    let query = `SELECT COUNT(*) as total FROM ${this.tableName}`;
    let params: any[] = [];
    
    if (condition) {
      const { clause: whereClause, params: whereParams } = buildWhereClause(condition);
      query += ` ${whereClause}`;
      params = whereParams;
    }
    
    const result = await this.db.getOne<{ total: string }>(query, params);
    return parseInt(result?.total || '0');
  }

  /**
   * Verifica se esiste un record con l'ID specificato
   * 
   * @param id - ID da verificare
   * @returns true se esiste, false altrimenti
   */
  async exists(id: string | number): Promise<boolean> {
    const query = `
      SELECT EXISTS(
        SELECT 1 FROM ${this.tableName} WHERE id = $1
      ) as exists
    `;
    
    const result = await this.db.getOne<{ exists: boolean }>(query, [id]);
    return result?.exists || false;
  }

  /**
   * Esegue una query SQL personalizzata
   * 
   * @param query - Query SQL da eseguire
   * @param params - Parametri per la query
   * @returns Risultato della query
   */
  async executeQuery<R extends QueryResultRow = T>(query: string, params?: any[]): Promise<R[]> {
    return await this.db.getMany<R>(query, params);
  }

  /**
   * Esegue una query che restituisce un singolo valore
   * 
   * @param query - Query SQL da eseguire
   * @param params - Parametri per la query
   * @returns Singolo valore o null
   */
  async executeScalar<R extends QueryResultRow = any>(query: string, params?: any[]): Promise<R | null> {
    return await this.db.getOne<R>(query, params);
  }

  /**
   * Inizia una transazione
   * 
   * @param callback - Funzione da eseguire nella transazione
   * @returns Risultato della transazione
   */
  async transaction<R>(callback: (client: any) => Promise<R>): Promise<R> {
    return await this.db.transaction(callback);
  }

  /**
   * Ottiene informazioni sulla tabella
   * 
   * @returns Informazioni schema tabella
   */
  async getTableInfo(): Promise<any> {
    const query = `
      SELECT 
        column_name,
        data_type,
        is_nullable,
        column_default
      FROM information_schema.columns
      WHERE table_name = $1
      ORDER BY ordinal_position
    `;
    
    return await this.db.getMany(query, [this.tableName]);
  }

  /**
   * Ottiene statistiche sulla tabella
   * 
   * @returns Statistiche tabella
   */
  async getTableStats(): Promise<{
    rowCount: number;
    diskSize: string;
    lastVacuum: Date | null;
    lastAnalyze: Date | null;
  }> {
    const statsQuery = `
      SELECT 
        n_live_tup as row_count,
        pg_size_pretty(pg_total_relation_size($1::regclass)) as disk_size,
        last_vacuum,
        last_analyze
      FROM pg_stat_user_tables
      WHERE schemaname = 'public' AND tablename = $1
    `;
    
    const result = await this.db.getOne<any>(statsQuery, [this.tableName]);
    
    return {
      rowCount: result?.row_count || 0,
      diskSize: result?.disk_size || '0 bytes',
      lastVacuum: result?.last_vacuum ? new Date(result.last_vacuum) : null,
      lastAnalyze: result?.last_analyze ? new Date(result.last_analyze) : null
    };
  }

  /**
   * Pulisce vecchi record in base a un campo data
   * 
   * @param dateField - Nome del campo data
   * @param daysToKeep - Giorni da mantenere
   * @returns Numero di record eliminati
   */
  async cleanOldRecords(dateField: string, daysToKeep: number): Promise<number> {
    const query = `
      DELETE FROM ${this.tableName}
      WHERE ${dateField} < NOW() - INTERVAL '${daysToKeep} days'
    `;
    
    return await this.db.delete(query);
  }
}