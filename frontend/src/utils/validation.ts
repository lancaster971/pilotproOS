import Ajv, { JSONSchemaType } from 'ajv'
import addFormats from 'ajv-formats'

// Initialize AJV with formats support
const ajv = new Ajv({ allErrors: true, removeAdditional: true })
addFormats(ajv)

// Business Execution Schema
interface BusinessExecution {
  workflowId: string
  executionId: string
  status: 'running' | 'success' | 'error'
  startedAt: string
  finishedAt?: string
  nodeData: Array<{
    nodeId: string
    nodeType: string
    nodeName: string
    data: any
    businessContent?: string
    businessSummary?: string
  }>
}

const businessExecutionSchema: JSONSchemaType<BusinessExecution> = {
  type: 'object',
  properties: {
    workflowId: { type: 'string', minLength: 1 },
    executionId: { type: 'string', minLength: 1 },
    status: { type: 'string', enum: ['running', 'success', 'error'] },
    startedAt: { type: 'string', format: 'date-time' },
    finishedAt: { type: 'string', format: 'date-time', nullable: true },
    nodeData: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          nodeId: { type: 'string', minLength: 1 },
          nodeType: { type: 'string', minLength: 1 },
          nodeName: { type: 'string', minLength: 1 },
          data: {},
          businessContent: { type: 'string', nullable: true },
          businessSummary: { type: 'string', nullable: true }
        },
        required: ['nodeId', 'nodeType', 'nodeName', 'data'],
        additionalProperties: false
      }
    }
  },
  required: ['workflowId', 'executionId', 'status', 'startedAt', 'nodeData'],
  additionalProperties: false
}

// Workflow Schema
interface Workflow {
  id: string
  name: string
  active: boolean
  description?: string
  tags: string[]
  createdAt: string
  updatedAt: string
  nodes: Array<{
    id: string
    name: string
    type: string
    parameters: any
  }>
  connections: any
}

const workflowSchema: JSONSchemaType<Workflow> = {
  type: 'object',
  properties: {
    id: { type: 'string', minLength: 1 },
    name: { type: 'string', minLength: 1, maxLength: 255 },
    active: { type: 'boolean' },
    description: { type: 'string', nullable: true },
    tags: {
      type: 'array',
      items: { type: 'string' }
    },
    createdAt: { type: 'string', format: 'date-time' },
    updatedAt: { type: 'string', format: 'date-time' },
    nodes: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          id: { type: 'string', minLength: 1 },
          name: { type: 'string', minLength: 1 },
          type: { type: 'string', minLength: 1 },
          parameters: {}
        },
        required: ['id', 'name', 'type', 'parameters'],
        additionalProperties: false
      }
    },
    connections: {}
  },
  required: ['id', 'name', 'active', 'tags', 'createdAt', 'updatedAt', 'nodes', 'connections'],
  additionalProperties: false
}

// User Input Schema
interface UserInput {
  email: string
  password: string
  name?: string
}

const userInputSchema: JSONSchemaType<UserInput> = {
  type: 'object',
  properties: {
    email: { type: 'string', format: 'email', minLength: 5, maxLength: 255 },
    password: { type: 'string', minLength: 8, maxLength: 128 },
    name: { type: 'string', minLength: 1, maxLength: 255, nullable: true }
  },
  required: ['email', 'password'],
  additionalProperties: false
}

// API Response Schema
interface ApiResponse<T> {
  success: boolean
  data?: T
  error?: string
  timestamp: string
}

const createApiResponseSchema = <T>(dataSchema: JSONSchemaType<T>): JSONSchemaType<ApiResponse<T>> => ({
  type: 'object',
  properties: {
    success: { type: 'boolean' },
    data: { ...dataSchema, nullable: true },
    error: { type: 'string', nullable: true },
    timestamp: { type: 'string', format: 'date-time' }
  },
  required: ['success', 'timestamp'],
  additionalProperties: false
})

// Compile validators
export const validateBusinessExecution = ajv.compile(businessExecutionSchema)
export const validateWorkflow = ajv.compile(workflowSchema)
export const validateUserInput = ajv.compile(userInputSchema)
export const validateApiResponse = <T>(schema: JSONSchemaType<T>) => 
  ajv.compile(createApiResponseSchema(schema))

// Business Data Parser
export class BusinessDataParser {
  /**
   * Parse and validate business execution data
   */
  static parseExecution(rawData: any): BusinessExecution | null {
    try {
      // Clean and transform raw data
      const cleaned = this.cleanExecutionData(rawData)
      
      // Validate with schema
      if (validateBusinessExecution(cleaned)) {
        return cleaned
      }
      
      console.warn('Business execution validation failed:', validateBusinessExecution.errors)
      return null
    } catch (error) {
      console.error('Error parsing business execution:', error)
      return null
    }
  }

  /**
   * Parse workflow definition
   */
  static parseWorkflow(rawData: any): Workflow | null {
    try {
      const cleaned = this.cleanWorkflowData(rawData)
      
      if (validateWorkflow(cleaned)) {
        return cleaned
      }
      
      console.warn('Workflow validation failed:', validateWorkflow.errors)
      return null
    } catch (error) {
      console.error('Error parsing workflow:', error)
      return null
    }
  }

  /**
   * Extract business content from node data
   */
  static extractBusinessContent(nodeType: string, nodeData: any): { content: string; summary: string } {
    switch (nodeType) {
      case 'n8n-nodes-base.emailReadImap':
      case 'n8n-nodes-base.emailSend':
        return this.parseEmailNode(nodeData)
      
      case '@n8n/n8n-nodes-langchain.agent':
      case '@n8n/n8n-nodes-langchain.toolCalculator':
        return this.parseAINode(nodeData)
      
      case 'n8n-nodes-base.httpRequest':
        return this.parseHttpNode(nodeData)
      
      case 'n8n-nodes-base.postgres':
      case 'n8n-nodes-base.mysql':
        return this.parseDatabaseNode(nodeData)
      
      default:
        return this.parseGenericNode(nodeData)
    }
  }

  private static cleanExecutionData(rawData: any): BusinessExecution {
    return {
      workflowId: String(rawData.workflowId || ''),
      executionId: String(rawData.executionId || rawData.id || ''),
      status: rawData.status === 'success' ? 'success' : 
              rawData.status === 'error' ? 'error' : 'running',
      startedAt: new Date(rawData.startedAt || rawData.createdAt || Date.now()).toISOString(),
      finishedAt: rawData.finishedAt ? new Date(rawData.finishedAt).toISOString() : undefined,
      nodeData: Array.isArray(rawData.nodeData) 
        ? rawData.nodeData.map((node: any) => this.cleanNodeData(node))
        : []
    }
  }

  private static cleanWorkflowData(rawData: any): Workflow {
    return {
      id: String(rawData.id || ''),
      name: String(rawData.name || ''),
      active: Boolean(rawData.active),
      description: rawData.description ? String(rawData.description) : undefined,
      tags: Array.isArray(rawData.tags) ? rawData.tags.map(String) : [],
      createdAt: new Date(rawData.createdAt || Date.now()).toISOString(),
      updatedAt: new Date(rawData.updatedAt || Date.now()).toISOString(),
      nodes: Array.isArray(rawData.nodes) 
        ? rawData.nodes.map((node: any) => ({
            id: String(node.id || ''),
            name: String(node.name || ''),
            type: String(node.type || ''),
            parameters: node.parameters || {}
          }))
        : [],
      connections: rawData.connections || {}
    }
  }

  private static cleanNodeData(rawNode: any) {
    const businessContent = this.extractBusinessContent(rawNode.nodeType, rawNode.data)
    
    return {
      nodeId: String(rawNode.nodeId || rawNode.id || ''),
      nodeType: String(rawNode.nodeType || rawNode.type || ''),
      nodeName: String(rawNode.nodeName || rawNode.name || ''),
      data: rawNode.data || {},
      businessContent: businessContent.content,
      businessSummary: businessContent.summary
    }
  }

  private static parseEmailNode(data: any): { content: string; summary: string } {
    const emails = Array.isArray(data) ? data : [data]
    const email = emails[0] || {}
    
    return {
      content: email.text || email.html || 'Nessun contenuto email',
      summary: `Email: ${email.subject || 'Nessun oggetto'} (${email.from || 'mittente sconosciuto'})`
    }
  }

  private static parseAINode(data: any): { content: string; summary: string } {
    const responses = Array.isArray(data) ? data : [data]
    const response = responses[0] || {}
    
    return {
      content: response.text || response.content || response.output || 'Nessuna risposta AI',
      summary: `AI Response: ${(response.text || '').substring(0, 100)}...`
    }
  }

  private static parseHttpNode(data: any): { content: string; summary: string } {
    const requests = Array.isArray(data) ? data : [data]
    const request = requests[0] || {}
    
    return {
      content: JSON.stringify(request, null, 2),
      summary: `HTTP Request: ${request.status || 'unknown'} (${Object.keys(request).length} fields)`
    }
  }

  private static parseDatabaseNode(data: any): { content: string; summary: string } {
    const results = Array.isArray(data) ? data : [data]
    
    return {
      content: JSON.stringify(results, null, 2),
      summary: `Database Query: ${results.length} record(s) affected`
    }
  }

  private static parseGenericNode(data: any): { content: string; summary: string } {
    const items = Array.isArray(data) ? data : [data]
    
    return {
      content: JSON.stringify(items, null, 2),
      summary: `Generic Node: ${items.length} item(s) processed`
    }
  }
}

// Validation utilities
export const validateAndTransform = {
  /**
   * Validate user input with sanitization
   */
  userInput: (data: any): UserInput | null => {
    if (validateUserInput(data)) {
      return {
        email: data.email.toLowerCase().trim(),
        password: data.password,
        name: data.name?.trim()
      }
    }
    return null
  },

  /**
   * Validate API response
   */
  apiResponse: <T>(data: any, dataSchema: JSONSchemaType<T>): ApiResponse<T> | null => {
    const validator = validateApiResponse(dataSchema)
    return validator(data) ? data : null
  }
}

export default {
  validateBusinessExecution,
  validateWorkflow,
  validateUserInput,
  BusinessDataParser,
  validateAndTransform
}