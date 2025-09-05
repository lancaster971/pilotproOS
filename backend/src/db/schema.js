/**
 * Drizzle ORM Schema - PilotProOS Database
 * Maps existing PostgreSQL dual-schema (n8n + pilotpros) to type-safe ORM
 */

import { sql } from 'drizzle-orm'
import { 
  pgTable, 
  pgSchema, 
  text, 
  integer, 
  boolean, 
  timestamp, 
  json, 
  serial,
  varchar,
  jsonb
} from 'drizzle-orm/pg-core'

// N8N Schema - Read-only access to workflow data
export const n8nSchema = pgSchema('n8n')

export const workflowEntity = n8nSchema.table('workflow_entity', {
  id: serial('id').primaryKey(),
  name: varchar('name', { length: 128 }).notNull(),
  active: boolean('active').default(false).notNull(),
  nodes: jsonb('nodes').default(sql`'[]'`).notNull(),
  connections: jsonb('connections').default(sql`'{}'`).notNull(),
  settings: jsonb('settings').default(sql`'{}'`).notNull(),
  staticData: jsonb('staticData').default(sql`'{}'`).notNull(),
  createdAt: timestamp('createdAt').defaultNow().notNull(),
  updatedAt: timestamp('updatedAt').defaultNow().notNull(),
  versionId: varchar('versionId', { length: 36 }),
  isArchived: boolean('isArchived').default(false).notNull(),
})

export const executionEntity = n8nSchema.table('execution_entity', {
  id: serial('id').primaryKey(),
  finished: boolean('finished').default(false).notNull(),
  mode: varchar('mode', { length: 255 }).notNull(),
  retryOf: varchar('retryOf', { length: 255 }),
  retrySuccessId: varchar('retrySuccessId', { length: 255 }),
  status: varchar('status', { length: 255 }),
  startedAt: timestamp('startedAt').notNull(),
  stoppedAt: timestamp('stoppedAt'),
  workflowData: jsonb('workflowData').notNull(),
  workflowId: varchar('workflowId', { length: 255 }),
  waitTill: timestamp('waitTill'),
  executionData: jsonb('executionData'),
  customData: jsonb('customData'),
  deletedAt: timestamp('deletedAt'),
  metadata: jsonb('metadata'),
})

export const credentialsEntity = n8nSchema.table('credentials_entity', {
  id: serial('id').primaryKey(),
  name: varchar('name', { length: 128 }).notNull(),
  data: text('data').notNull(),
  type: varchar('type', { length: 32 }).notNull(),
  nodesAccess: jsonb('nodesAccess').default(sql`'[]'`).notNull(),
  createdAt: timestamp('createdAt').defaultNow().notNull(),
  updatedAt: timestamp('updatedAt').defaultNow().notNull(),
})

// PilotProS Schema - Business application data
export const pilotprosSchema = pgSchema('pilotpros')

export const users = pilotprosSchema.table('users', {
  id: serial('id').primaryKey(),
  username: varchar('username', { length: 50 }).unique().notNull(),
  email: varchar('email', { length: 100 }).unique().notNull(),
  password: varchar('password', { length: 255 }).notNull(),
  role: varchar('role', { length: 20 }).default('user').notNull(),
  isActive: boolean('is_active').default(true).notNull(),
  createdAt: timestamp('created_at').defaultNow().notNull(),
  updatedAt: timestamp('updated_at').defaultNow().notNull(),
  lastLogin: timestamp('last_login'),
  settings: jsonb('settings').default(sql`'{}'`),
})

export const businessExecutionData = pilotprosSchema.table('business_execution_data', {
  id: serial('id').primaryKey(),
  executionId: varchar('execution_id', { length: 255 }).notNull(),
  workflowId: varchar('workflow_id', { length: 255 }).notNull(),
  nodeId: varchar('node_id', { length: 255 }).notNull(),
  nodeName: varchar('node_name', { length: 255 }).notNull(),
  nodeType: varchar('node_type', { length: 255 }).notNull(),
  businessCategory: varchar('business_category', { length: 50 }).notNull(),
  businessData: jsonb('business_data').notNull(),
  executedAt: timestamp('executed_at').defaultNow().notNull(),
  isActive: boolean('is_active').default(true).notNull(),
})

export const businessAnalytics = pilotprosSchema.table('business_analytics', {
  id: serial('id').primaryKey(),
  workflowId: varchar('workflow_id', { length: 255 }).notNull(),
  executionCount: integer('execution_count').default(0).notNull(),
  successCount: integer('success_count').default(0).notNull(),
  failureCount: integer('failure_count').default(0).notNull(),
  avgExecutionTime: integer('avg_execution_time').default(0),
  lastExecution: timestamp('last_execution'),
  createdAt: timestamp('created_at').defaultNow().notNull(),
  updatedAt: timestamp('updated_at').defaultNow().notNull(),
})

export const processTemplates = pilotprosSchema.table('process_templates', {
  id: serial('id').primaryKey(),
  name: varchar('name', { length: 128 }).notNull(),
  description: text('description'),
  category: varchar('category', { length: 50 }).notNull(),
  template: jsonb('template').notNull(),
  isPublic: boolean('is_public').default(false).notNull(),
  createdBy: integer('created_by').notNull(),
  createdAt: timestamp('created_at').defaultNow().notNull(),
  updatedAt: timestamp('updated_at').defaultNow().notNull(),
})

export const auditLogs = pilotprosSchema.table('audit_logs', {
  id: serial('id').primaryKey(),
  userId: integer('user_id'),
  action: varchar('action', { length: 100 }).notNull(),
  entityType: varchar('entity_type', { length: 50 }),
  entityId: varchar('entity_id', { length: 255 }),
  details: jsonb('details'),
  ipAddress: varchar('ip_address', { length: 45 }),
  userAgent: text('user_agent'),
  createdAt: timestamp('created_at').defaultNow().notNull(),
})

export const systemSettings = pilotprosSchema.table('system_settings', {
  id: serial('id').primaryKey(),
  key: varchar('key', { length: 100 }).unique().notNull(),
  value: jsonb('value'),
  description: text('description'),
  isPublic: boolean('is_public').default(false).notNull(),
  createdAt: timestamp('created_at').defaultNow().notNull(),
  updatedAt: timestamp('updated_at').defaultNow().notNull(),
})

export const userSessions = pilotprosSchema.table('user_sessions', {
  id: serial('id').primaryKey(),
  userId: integer('user_id').notNull(),
  sessionToken: varchar('session_token', { length: 255 }).unique().notNull(),
  expiresAt: timestamp('expires_at').notNull(),
  ipAddress: varchar('ip_address', { length: 45 }),
  userAgent: text('user_agent'),
  isActive: boolean('is_active').default(true).notNull(),
  createdAt: timestamp('created_at').defaultNow().notNull(),
})