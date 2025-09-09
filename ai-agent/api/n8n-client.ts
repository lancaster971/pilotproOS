/**
 * n8n API Client Interface
 * 
 * This module defines interfaces and types for the n8n API client.
 */

import { N8nApiClient } from './client.js';
import { EnvConfig } from '../config/environment.js';
import { Workflow, Execution } from '../types/index.js';

/**
 * n8n API service - provides functions for interacting with n8n API
 */
export class N8nApiService {
  private client: N8nApiClient;

  /**
   * Create a new n8n API service
   * 
   * @param config Environment configuration
   */
  constructor(config: EnvConfig) {
    this.client = new N8nApiClient(config);
  }

  /**
   * Check connectivity to the n8n API
   */
  async checkConnectivity(): Promise<void> {
    return this.client.checkConnectivity();
  }

  /**
   * Get all workflows from n8n
   * 
   * @returns Array of workflow objects
   */
  async getWorkflows(): Promise<Workflow[]> {
    return this.client.getWorkflows();
  }

  /**
   * Get a specific workflow by ID
   * 
   * @param id Workflow ID
   * @returns Workflow object
   */
  async getWorkflow(id: string): Promise<Workflow> {
    return this.client.getWorkflow(id);
  }

  /**
   * Execute a workflow by ID
   * 
   * @param id Workflow ID
   * @param data Optional data to pass to the workflow
   * @returns Execution result
   */
  async executeWorkflow(id: string, data?: Record<string, any>): Promise<any> {
    return this.client.executeWorkflow(id, data);
  }

  /**
   * Create a new workflow
   * 
   * @param workflow Workflow object to create
   * @returns Created workflow
   */
  async createWorkflow(workflow: Record<string, any>): Promise<Workflow> {
    return this.client.createWorkflow(workflow);
  }

  /**
   * Update an existing workflow
   * 
   * @param id Workflow ID
   * @param workflow Updated workflow object
   * @returns Updated workflow
   */
  async updateWorkflow(id: string, workflow: Record<string, any>): Promise<Workflow> {
    return this.client.updateWorkflow(id, workflow);
  }

  /**
   * Delete a workflow
   * 
   * @param id Workflow ID
   * @returns Deleted workflow or success message
   */
  async deleteWorkflow(id: string): Promise<any> {
    return this.client.deleteWorkflow(id);
  }

  /**
   * Activate a workflow
   * 
   * @param id Workflow ID
   * @returns Activated workflow
   */
  async activateWorkflow(id: string): Promise<Workflow> {
    return this.client.activateWorkflow(id);
  }

  /**
   * Deactivate a workflow
   * 
   * @param id Workflow ID
   * @returns Deactivated workflow
   */
  async deactivateWorkflow(id: string): Promise<Workflow> {
    return this.client.deactivateWorkflow(id);
  }

  /**
   * Get all workflow executions
   * 
   * @param options Query options
   * @returns Array of execution objects
   */
  async getExecutions(options?: {
    includeData?: boolean;
    status?: 'error' | 'success' | 'waiting';
    workflowId?: string;
    limit?: number;
  }): Promise<Execution[]> {
    return this.client.getExecutions(options);
  }

  /**
   * Alias per getWorkflows per compatibilità
   */
  async listWorkflows(): Promise<Workflow[]> {
    return this.getWorkflows();
  }

  /**
   * Lista esecuzioni con filtri opzionali
   * 
   * @param options - Opzioni per filtrare le esecuzioni
   * @returns Array di esecuzioni
   */
  async listExecutions(options?: { workflowId?: string; limit?: number }): Promise<Execution[]> {
    // Per ora restituisce tutte le esecuzioni
    // In futuro potremmo implementare filtri lato client o API
    const allExecutions = await this.getExecutions();
    
    let filtered = allExecutions;
    
    if (options?.workflowId) {
      filtered = filtered.filter((e: any) => e.workflowId === options.workflowId);
    }
    
    if (options?.limit) {
      filtered = filtered.slice(0, options.limit);
    }
    
    return filtered;
  }

  /**
   * Get a specific execution by ID
   * 
   * @param id Execution ID
   * @param includeData Whether to include detailed execution data
   * @returns Execution object
   */
  async getExecution(id: string, includeData = false): Promise<Execution> {
    return this.client.getExecution(id, includeData);
  }
  
  /**
   * Delete an execution
   * 
   * @param id Execution ID
   * @returns Deleted execution or success message
   */
  async deleteExecution(id: string): Promise<any> {
    return this.client.deleteExecution(id);
  }

  /**
   * Generate security audit for n8n instance
   * 
   * @param options Audit configuration options
   * @returns Security audit report with risk analysis
   */
  async generateSecurityAudit(options?: {
    daysAbandonedWorkflow?: number;
    categories?: ('credentials' | 'database' | 'nodes' | 'filesystem' | 'instance')[];
  }): Promise<any> {
    return this.client.generateSecurityAudit(options);
  }

  /**
   * Get all credentials for security analysis
   * 
   * @returns Array of credential objects
   */
  async getCredentials(): Promise<any[]> {
    return this.client.getCredentials();
  }

  /**
   * Get all users for access control analysis
   * 
   * @param includeRole Whether to include user roles
   * @returns Array of user objects
   */
  async getUsers(includeRole: boolean = true): Promise<any[]> {
    return this.client.getUsers(includeRole);
  }

  /**
   * Get all tags for organization analysis
   * 
   * @returns Array of tag objects
   */
  async getTags(): Promise<any[]> {
    return this.client.getTags();
  }

  /**
   * Get all variables for configuration security analysis
   * 
   * @returns Array of variable objects
   */
  async getVariables(): Promise<any[]> {
    return this.client.getVariables();
  }
}

/**
 * Create a new n8n API service
 * 
 * @param config Environment configuration
 * @returns n8n API service
 */
export function createApiService(config: EnvConfig): N8nApiService {
  return new N8nApiService(config);
}
