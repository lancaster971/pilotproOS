/**
 * n8n API Client
 * 
 * This module provides a client for interacting with the n8n API.
 */

import axios, { AxiosInstance } from 'axios';
import { EnvConfig } from '../config/environment.js';
import { handleAxiosError, N8nApiError } from '../errors/index.js';

/**
 * n8n API Client class for making requests to the n8n API
 */
export class N8nApiClient {
  private axiosInstance: AxiosInstance;
  private config: EnvConfig;

  /**
   * Create a new n8n API client
   * 
   * @param config Environment configuration
   */
  constructor(config: EnvConfig) {
    this.config = config;
    this.axiosInstance = axios.create({
      baseURL: config.n8nApiUrl,
      headers: {
        'X-N8N-API-KEY': config.n8nApiKey,
        'Accept': 'application/json',
      },
      timeout: 10000, // 10 seconds
    });

    // Add request debugging if debug mode is enabled
    if (config.debug) {
      this.axiosInstance.interceptors.request.use(request => {
        console.error(`[DEBUG] Request: ${request.method?.toUpperCase()} ${request.url}`);
        return request;
      });

      this.axiosInstance.interceptors.response.use(response => {
        console.error(`[DEBUG] Response: ${response.status} ${response.statusText}`);
        return response;
      });
    }
  }

  /**
   * Check connectivity to the n8n API
   * 
   * @returns Promise that resolves if connectivity check succeeds
   * @throws N8nApiError if connectivity check fails
   */
  async checkConnectivity(): Promise<void> {
    try {
      // Try to fetch health endpoint or workflows
      const response = await this.axiosInstance.get('/workflows');
      
      if (response.status !== 200) {
        throw new N8nApiError(
          'n8n API connectivity check failed',
          response.status
        );
      }
      
      if (this.config.debug) {
        console.error(`[DEBUG] Successfully connected to n8n API at ${this.config.n8nApiUrl}`);
        console.error(`[DEBUG] Found ${response.data.data?.length || 0} workflows`);
      }
    } catch (error) {
      throw handleAxiosError(error, 'Failed to connect to n8n API');
    }
  }

  /**
   * Get the axios instance for making custom requests
   * 
   * @returns Axios instance
   */
  getAxiosInstance(): AxiosInstance {
    return this.axiosInstance;
  }

  /**
   * Get all workflows from n8n
   * 
   * @returns Array of workflow objects
   */
  async getWorkflows(): Promise<any[]> {
    try {
      const response = await this.axiosInstance.get('/workflows');
      return response.data.data || [];
    } catch (error) {
      throw handleAxiosError(error, 'Failed to fetch workflows');
    }
  }

  /**
   * Get a specific workflow by ID
   * 
   * @param id Workflow ID
   * @returns Workflow object
   */
  async getWorkflow(id: string): Promise<any> {
    try {
      const response = await this.axiosInstance.get(`/workflows/${id}`);
      return response.data;
    } catch (error) {
      throw handleAxiosError(error, `Failed to fetch workflow ${id}`);
    }
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
    cursor?: string;
  }): Promise<any[]> {
    try {
      const params = new URLSearchParams();
      
      if (options?.includeData !== false) {
        params.append('includeData', 'true');
      }
      if (options?.status) {
        params.append('status', options.status);
      }
      if (options?.workflowId) {
        params.append('workflowId', options.workflowId);
      }
      if (options?.limit) {
        params.append('limit', options.limit.toString());
      }
      if (options?.cursor) {
        params.append('cursor', options.cursor);
      }
      
      const url = `/executions${params.toString() ? '?' + params.toString() : ''}`;
      const response = await this.axiosInstance.get(url);
      return response.data.data || [];
    } catch (error) {
      throw handleAxiosError(error, 'Failed to fetch executions');
    }
  }

  /**
   * Get a specific execution by ID
   * 
   * @param id Execution ID
   * @param includeData Whether to include detailed execution data
   * @returns Execution object
   */
  async getExecution(id: string, includeData = true): Promise<any> {
    try {
      const url = includeData ? `/executions/${id}?includeData=true` : `/executions/${id}`;
      const response = await this.axiosInstance.get(url);
      return response.data;
    } catch (error) {
      throw handleAxiosError(error, `Failed to fetch execution ${id}`);
    }
  }

  /**
   * Execute a workflow by ID
   * 
   * @param id Workflow ID
   * @param data Optional data to pass to the workflow
   * @returns Execution result
   */
  async executeWorkflow(id: string, data?: Record<string, any>): Promise<any> {
    try {
      const response = await this.axiosInstance.post(`/workflows/${id}/execute`, data || {});
      return response.data;
    } catch (error) {
      throw handleAxiosError(error, `Failed to execute workflow ${id}`);
    }
  }

  /**
   * Create a new workflow
   * 
   * @param workflow Workflow object to create
   * @returns Created workflow
   */
  async createWorkflow(workflow: Record<string, any>): Promise<any> {
    try {
      // Make sure settings property is present
      if (!workflow.settings) {
        workflow.settings = {
          saveExecutionProgress: true,
          saveManualExecutions: true,
          saveDataErrorExecution: "all",
          saveDataSuccessExecution: "all",
          executionTimeout: 3600,
          timezone: "UTC"
        };
      }
      
      // Remove read-only properties that cause issues
      const workflowToCreate = { ...workflow };
      delete workflowToCreate.active; // Remove active property as it's read-only
      delete workflowToCreate.id; // Remove id property if it exists
      delete workflowToCreate.createdAt; // Remove createdAt property if it exists
      delete workflowToCreate.updatedAt; // Remove updatedAt property if it exists
      delete workflowToCreate.tags; // Remove tags property as it's read-only
      
      // Log request for debugging
      console.error('[DEBUG] Creating workflow with data:', JSON.stringify(workflowToCreate, null, 2));
      
      const response = await this.axiosInstance.post('/workflows', workflowToCreate);
      return response.data;
    } catch (error) {
      console.error('[ERROR] Create workflow error:', error);
      throw handleAxiosError(error, 'Failed to create workflow');
    }
  }

  /**
   * Update an existing workflow
   * 
   * @param id Workflow ID
   * @param workflow Updated workflow object
   * @returns Updated workflow
   */
  async updateWorkflow(id: string, workflow: Record<string, any>): Promise<any> {
    try {
      // Remove read-only properties that cause issues with n8n API v1
      // According to n8n API schema, only name, nodes, connections, settings, and staticData are allowed
      const workflowToUpdate = { ...workflow };
      delete workflowToUpdate.id; // Remove id property as it's read-only
      delete workflowToUpdate.active; // Remove active property as it's read-only
      delete workflowToUpdate.createdAt; // Remove createdAt property as it's read-only
      delete workflowToUpdate.updatedAt; // Remove updatedAt property as it's read-only
      delete workflowToUpdate.tags; // Remove tags property as it's read-only

      // Log request for debugging
      if (this.config.debug) {
        console.error('[DEBUG] Updating workflow with data:', JSON.stringify(workflowToUpdate, null, 2));
      }

      const response = await this.axiosInstance.put(`/workflows/${id}`, workflowToUpdate);
      return response.data;
    } catch (error) {
      throw handleAxiosError(error, `Failed to update workflow ${id}`);
    }
  }

  /**
   * Delete a workflow
   * 
   * @param id Workflow ID
   * @returns Deleted workflow
   */
  async deleteWorkflow(id: string): Promise<any> {
    try {
      const response = await this.axiosInstance.delete(`/workflows/${id}`);
      return response.data;
    } catch (error) {
      throw handleAxiosError(error, `Failed to delete workflow ${id}`);
    }
  }

  /**
   * Activate a workflow
   * 
   * @param id Workflow ID
   * @returns Activated workflow
   */
  async activateWorkflow(id: string): Promise<any> {
    try {
      const response = await this.axiosInstance.post(`/workflows/${id}/activate`);
      return response.data;
    } catch (error) {
      throw handleAxiosError(error, `Failed to activate workflow ${id}`);
    }
  }

  /**
   * Deactivate a workflow
   * 
   * @param id Workflow ID
   * @returns Deactivated workflow
   */
  async deactivateWorkflow(id: string): Promise<any> {
    try {
      const response = await this.axiosInstance.post(`/workflows/${id}/deactivate`);
      return response.data;
    } catch (error) {
      throw handleAxiosError(error, `Failed to deactivate workflow ${id}`);
    }
  }
  
  /**
   * Delete an execution
   * 
   * @param id Execution ID
   * @returns Deleted execution or success message
   */
  async deleteExecution(id: string): Promise<any> {
    try {
      const response = await this.axiosInstance.delete(`/executions/${id}`);
      return response.data;
    } catch (error) {
      throw handleAxiosError(error, `Failed to delete execution ${id}`);
    }
  }

  /**
   * Generate security audit for n8n instance
   * 
   * @param options Audit configuration options
   * @returns Security audit report
   */
  async generateSecurityAudit(options?: {
    daysAbandonedWorkflow?: number;
    categories?: ('credentials' | 'database' | 'nodes' | 'filesystem' | 'instance')[];
  }): Promise<any> {
    try {
      const requestBody = options ? { additionalOptions: options } : {};
      const response = await this.axiosInstance.post('/audit', requestBody);
      return response.data;
    } catch (error) {
      throw handleAxiosError(error, 'Failed to generate security audit');
    }
  }

  /**
   * Get all credentials (for security analysis)
   * 
   * @returns Array of credential objects
   */
  async getCredentials(): Promise<any[]> {
    try {
      const response = await this.axiosInstance.get('/credentials');
      return response.data.data || [];
    } catch (error) {
      throw handleAxiosError(error, 'Failed to fetch credentials');
    }
  }

  /**
   * Get all users (for access analysis)
   * 
   * @param includeRole Whether to include user roles
   * @returns Array of user objects
   */
  async getUsers(includeRole: boolean = true): Promise<any[]> {
    try {
      const params = includeRole ? '?includeRole=true' : '';
      const response = await this.axiosInstance.get(`/users${params}`);
      return response.data.data || [];
    } catch (error) {
      throw handleAxiosError(error, 'Failed to fetch users');
    }
  }

  /**
   * Get all tags (for organization analysis)
   * 
   * @returns Array of tag objects
   */
  async getTags(): Promise<any[]> {
    try {
      const response = await this.axiosInstance.get('/tags');
      return response.data.data || [];
    } catch (error) {
      throw handleAxiosError(error, 'Failed to fetch tags');
    }
  }

  /**
   * Get all variables (for configuration security analysis)
   * 
   * @returns Array of variable objects
   */
  async getVariables(): Promise<any[]> {
    try {
      const response = await this.axiosInstance.get('/variables');
      return response.data.data || [];
    } catch (error) {
      throw handleAxiosError(error, 'Failed to fetch variables');
    }
  }
}

/**
 * Create and return a configured n8n API client
 * 
 * @param config Environment configuration
 * @returns n8n API client instance
 */
export function createApiClient(config: EnvConfig): N8nApiClient {
  return new N8nApiClient(config);
}
