/**
 * Business Logger Utility
 * Logs business events without technical details
 */

class BusinessLogger {
  constructor() {
    this.logs = [];
  }

  log(message, data = {}) {
    const entry = {
      timestamp: new Date().toISOString(),
      message,
      data,
      level: 'info'
    };

    this.logs.push(entry);
    console.log(`[BUSINESS] ${message}`, data);

    return entry;
  }

  error(message, error = {}) {
    const entry = {
      timestamp: new Date().toISOString(),
      message,
      error: error.message || error,
      level: 'error'
    };

    this.logs.push(entry);
    console.error(`[BUSINESS ERROR] ${message}`, error);

    return entry;
  }

  success(message, data = {}) {
    const entry = {
      timestamp: new Date().toISOString(),
      message,
      data,
      level: 'success'
    };

    this.logs.push(entry);
    console.log(`[BUSINESS SUCCESS] ${message}`, data);

    return entry;
  }

  getRecentLogs(limit = 100) {
    return this.logs.slice(-limit);
  }

  clearLogs() {
    this.logs = [];
  }
}

// Singleton instance
const businessLogger = new BusinessLogger();

export default businessLogger;