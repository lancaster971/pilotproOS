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
  id: varchar('id', { length: 36 }).primaryKey(),
  name: varchar('name', { length: 128 }).notNull(),
  active: boolean('active').default(false).notNull(),
  nodes: json('nodes').default(sql`'[]'`).notNull(),
  connections: json('connections').default(sql`'{}'`).notNull(),
  settings: json('settings'),
  staticData: json('staticData'),
  pinData: json('pinData'),
  createdAt: timestamp('createdAt', { withTimezone: true, precision: 3 }).defaultNow().notNull(),
  updatedAt: timestamp('updatedAt', { withTimezone: true, precision: 3 }).defaultNow().notNull(),
  versionId: varchar('versionId', { length: 36 }),
  triggerCount: integer('triggerCount').default(0).notNull(),
  meta: json('meta'),
  parentFolderId: varchar('parentFolderId', { length: 36 }),
  isArchived: boolean('isArchived').default(false).notNull(),
})

export const executionEntity = n8nSchema.table('execution_entity', {
  id: serial('id').primaryKey(),
  finished: boolean('finished').notNull(),
  mode: varchar('mode').notNull(),
  retryOf: varchar('retryOf'),
  retrySuccessId: varchar('retrySuccessId'),
  status: varchar('status').notNull(),
  startedAt: timestamp('startedAt', { withTimezone: true, precision: 3 }),
  stoppedAt: timestamp('stoppedAt', { withTimezone: true, precision: 3 }),
  workflowId: varchar('workflowId', { length: 36 }).notNull(),
  waitTill: timestamp('waitTill', { withTimezone: true, precision: 3 }),
  deletedAt: timestamp('deletedAt', { withTimezone: true, precision: 3 }),
  createdAt: timestamp('createdAt', { withTimezone: true, precision: 3 }).defaultNow().notNull(),
})

export const credentialsEntity = n8nSchema.table('credentials_entity', {
  id: varchar('id', { length: 36 }).primaryKey(),
  name: varchar('name', { length: 128 }).notNull(),
  data: text('data').notNull(),
  type: varchar('type', { length: 128 }).notNull(),
  createdAt: timestamp('createdAt', { withTimezone: true, precision: 3 }).defaultNow().notNull(),
  updatedAt: timestamp('updatedAt', { withTimezone: true, precision: 3 }).defaultNow().notNull(),
  isManaged: boolean('isManaged').default(false).notNull(),
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

// Additional tables for authentication and monitoring
export const authConfig = pilotprosSchema.table('auth_config', {
  id: integer('id').primaryKey().default(1),
  authMethod: varchar('auth_method', { length: 20 }).default('local').notNull(),
  ldapConfig: jsonb('ldap_config'),
  mfaConfig: jsonb('mfa_config'),
  createdAt: timestamp('created_at').defaultNow(),
  updatedAt: timestamp('updated_at').defaultNow(),
})

export const ldapConfig = pilotprosSchema.table('ldap_config', {
  id: serial('id').primaryKey(),
  name: varchar('name', { length: 100 }).notNull(),
  serverUrl: varchar('server_url', { length: 255 }).notNull(),
  bindDn: varchar('bind_dn', { length: 255 }),
  bindPassword: text('bind_password'),
  userSearchBase: varchar('user_search_base', { length: 255 }).notNull(),
  userFilter: varchar('user_filter', { length: 255 }).default('(&(objectClass=person)(mail={email}))'),
  groupSearchBase: varchar('group_search_base', { length: 255 }),
  groupFilter: varchar('group_filter', { length: 255 }).default('(objectClass=group)'),
  enabled: boolean('enabled').default(true),
  sslEnabled: boolean('ssl_enabled').default(true),
  createdAt: timestamp('created_at').defaultNow(),
  updatedAt: timestamp('updated_at').defaultNow(),
})

export const userAuthMethods = pilotprosSchema.table('user_auth_methods', {
  id: serial('id').primaryKey(),
  userId: integer('user_id').notNull(),
  authMethod: varchar('auth_method', { length: 20 }).notNull(),
  authIdentifier: varchar('auth_identifier', { length: 255 }),
  isEnabled: boolean('is_enabled').default(true).notNull(),
  lastUsedAt: timestamp('last_used_at'),
  createdAt: timestamp('created_at').defaultNow().notNull(),
})

export const userMfa = pilotprosSchema.table('user_mfa', {
  id: serial('id').primaryKey(),
  userId: integer('user_id').notNull(),
  mfaType: varchar('mfa_type', { length: 20 }).notNull(),
  secret: text('secret'),
  backupCodes: jsonb('backup_codes'),
  isEnabled: boolean('is_enabled').default(false).notNull(),
  verifiedAt: timestamp('verified_at'),
  createdAt: timestamp('created_at').defaultNow().notNull(),
  updatedAt: timestamp('updated_at').defaultNow().notNull(),
})

export const activeSessions = pilotprosSchema.table('active_sessions', {
  id: serial('id').primaryKey(),
  sessionId: varchar('session_id', { length: 255 }).unique().notNull(),
  userId: integer('user_id').notNull(),
  ipAddress: varchar('ip_address', { length: 45 }),
  userAgent: text('user_agent'),
  lastActivity: timestamp('last_activity').defaultNow().notNull(),
  expiresAt: timestamp('expires_at').notNull(),
  createdAt: timestamp('created_at').defaultNow().notNull(),
})

export const failedLoginAttempts = pilotprosSchema.table('failed_login_attempts', {
  id: serial('id').primaryKey(),
  email: varchar('email', { length: 100 }).notNull(),
  ipAddress: varchar('ip_address', { length: 45 }),
  attemptTime: timestamp('attempt_time').defaultNow().notNull(),
  reason: varchar('reason', { length: 255 }),
})