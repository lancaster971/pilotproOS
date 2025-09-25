/**
 * Business Logger - Centralizes business event logging
 */

import winston from 'winston';

const businessLogger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  defaultMeta: { service: 'pilotpros-business' },
  transports: [
    new winston.transports.Console({
      format: winston.format.simple()
    })
  ]
});

// Business event types
export const BusinessEvents = {
  WORKFLOW_CREATED: 'workflow.created',
  WORKFLOW_UPDATED: 'workflow.updated',
  WORKFLOW_DELETED: 'workflow.deleted',
  EXECUTION_STARTED: 'execution.started',
  EXECUTION_COMPLETED: 'execution.completed',
  EXECUTION_FAILED: 'execution.failed',
  USER_LOGIN: 'user.login',
  USER_LOGOUT: 'user.logout',
  AI_QUERY: 'ai.query',
  AI_RESPONSE: 'ai.response'
};

// Log business event
export function logBusinessEvent(event, data = {}) {
  businessLogger.info({
    event,
    ...data,
    timestamp: new Date().toISOString()
  });
}

export default businessLogger;