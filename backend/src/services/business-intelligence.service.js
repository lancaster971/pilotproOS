/**
 * Business Intelligence Service
 * 
 * Intelligently processes large data outputs from n8n workflows
 * to generate business-friendly summaries for the Timeline feature.
 * 
 * Features:
 * - Pattern-based summarization (no AI cost)
 * - Statistical analysis for structured data
 * - Smart caching for performance
 * - Optional AI enhancement via Ollama
 */

class BusinessIntelligenceService {
  constructor() {
    // In-memory cache for summaries
    this.summaryCache = new Map();
    this.aiSummaryCache = new Map();
    this.CACHE_TTL = 3600000; // 1 hour
    
    // Size thresholds for processing strategy
    this.DIRECT_THRESHOLD = 5000;      // < 5KB: direct passthrough
    this.PATTERN_THRESHOLD = 50000;    // < 50KB: pattern matching
    this.STATISTICAL_THRESHOLD = 500000; // < 500KB: statistical analysis
    // > 500KB: AI-assisted (with caching)
  }

  /**
   * Main entry point - processes node output data
   * @param {any} nodeData - Raw node output data
   * @param {string} nodeType - Type of n8n node
   * @param {string} nodeName - Name of the node
   * @returns {Object} Processed summary for Timeline
   */
  async processNodeOutput(nodeData, nodeType, nodeName) {
    try {
      // Check if already summarized (by Business Summarizer Node)
      if (nodeData?.businessSummary) {
        return {
          type: 'pre-processed',
          summary: nodeData.businessSummary,
          metrics: nodeData.metrics,
          preview: nodeData.preview,
          fullDataAvailable: true
        };
      }

      const dataSize = JSON.stringify(nodeData).length;
      const cacheKey = this.generateCacheKey(nodeData, nodeType, nodeName);
      
      // Check cache
      const cached = this.getCachedSummary(cacheKey);
      if (cached) {
        return cached;
      }

      // Determine processing strategy
      const strategy = this.determineStrategy(dataSize, nodeType, nodeName);
      
      let result;
      switch(strategy) {
        case 'DIRECT':
          result = this.directPassthrough(nodeData);
          break;
        case 'PATTERN':
          result = await this.patternBasedSummary(nodeData, nodeType, nodeName);
          break;
        case 'STATISTICAL':
          result = this.statisticalSummary(nodeData, nodeType, nodeName);
          break;
        case 'AI_REQUIRED':
          result = await this.aiAssistedSummary(nodeData, nodeType, nodeName);
          break;
        default:
          result = this.genericSummary(nodeData);
      }

      // Cache the result
      this.cacheSummary(cacheKey, result);
      
      return result;
    } catch (error) {
      console.error('❌ BI Service Error:', {
        error: error.message,
        nodeType,
        nodeName,
        dataSize: JSON.stringify(nodeData).length
      });
      
      // Return graceful fallback on error
      return {
        type: 'error_fallback',
        summaryType: 'error',
        businessSummary: {
          title: nodeName || 'Process Data',
          description: 'Data processing encountered an error but data is preserved',
          error: error.message
        },
        metrics: {
          size: JSON.stringify(nodeData).length,
          error: true
        },
        preview: {
          errorMessage: error.message,
          dataAvailable: true
        },
        fullDataAvailable: true,
        actions: ['view_raw', 'retry_processing']
      };
    }
  }

  /**
   * Determines the best processing strategy based on data characteristics
   */
  determineStrategy(dataSize, nodeType, nodeName) {
    // Small data - pass through directly
    if (dataSize < this.DIRECT_THRESHOLD) {
      return 'DIRECT';
    }
    
    // Check if we have a known pattern for this node type
    if (dataSize < this.PATTERN_THRESHOLD && this.hasKnownPattern(nodeType, nodeName)) {
      return 'PATTERN';
    }
    
    // Structured data suitable for statistical analysis
    if (dataSize < this.STATISTICAL_THRESHOLD && this.isStructuredData(nodeType)) {
      return 'STATISTICAL';
    }
    
    // Large data requires AI assistance
    if (dataSize > this.STATISTICAL_THRESHOLD) {
      return 'AI_REQUIRED';
    }
    
    return 'PATTERN'; // Default to pattern matching
  }

  /**
   * Direct passthrough for small data
   */
  directPassthrough(nodeData) {
    return {
      type: 'direct',
      data: nodeData,
      summaryType: 'direct',
      businessSummary: null,
      metrics: null
    };
  }

  /**
   * Pattern-based summarization without AI
   */
  async patternBasedSummary(nodeData, nodeType, nodeName) {
    try {
      const nodeNameLower = nodeName?.toLowerCase() || '';
      
      // PDF/Document processing
      if (this.isPDFData(nodeData, nodeType, nodeName)) {
        return this.summarizePDF(nodeData);
      }
      
      // CSV/Table processing
      if (this.isCSVData(nodeData, nodeType, nodeName)) {
        return this.summarizeCSV(nodeData);
      }
      
      // Email batch processing
      if (this.isEmailData(nodeData, nodeType, nodeName)) {
        return this.summarizeEmails(nodeData);
      }
      
      // API response processing
      if (this.isAPIData(nodeData, nodeType, nodeName)) {
        return this.summarizeAPI(nodeData);
      }
      
      // Database query results
      if (this.isDatabaseData(nodeData, nodeType, nodeName)) {
        return this.summarizeDatabase(nodeData);
      }
      
      // Default generic summary
      return this.genericSummary(nodeData);
    } catch (error) {
      console.error('❌ Pattern-based summary error:', {
        error: error.message,
        nodeType,
        nodeName,
        stack: error.stack
      });
      
      // Return safe fallback
      return {
        type: 'error',
        summaryType: 'fallback',
        businessSummary: {
          title: 'Processing Error',
          description: 'Unable to process data due to an error'
        },
        error: error.message,
        fullDataAvailable: false
      };
    }
  }

  /**
   * PDF Document Summarization
   */
  summarizePDF(data) {
    try {
      const text = data.extractedText || data.text || data.content || '';
      const pageCount = data.pageCount || this.estimatePages(text);
    
    // Extract key information using patterns
    const title = this.extractTitle(text);
    const documentType = this.identifyDocumentType(text);
    const keyDates = this.extractDates(text);
    const amounts = this.extractAmounts(text);
    const entities = this.extractEntities(text);
    
    // Generate business-friendly summary
    const businessSummary = this.generatePDFBusinessSummary(title, documentType, keyDates, amounts, entities);
    
    return {
      type: 'document',
      summaryType: 'document',
      businessSummary: {
        title: title || 'Document',
        description: businessSummary,
        documentType,
        pageCount
      },
      metrics: {
        pages: pageCount,
        dates: keyDates.length,
        amounts: amounts.length,
        entities: entities.length
      },
      preview: {
        firstPage: text.substring(0, 500),
        keyDates: keyDates.slice(0, 3),
        amounts: amounts.slice(0, 3),
        entities: entities.slice(0, 5)
      },
      businessInsight: this.generatePDFInsight(documentType, amounts, entities),
      fullDataAvailable: true,
      actions: ['download_full', 'request_ai_analysis', 'extract_data']
    };
    } catch (error) {
      console.error('❌ PDF summarization error:', error.message);
      return this.genericSummary(data);
    }
  }

  /**
   * CSV/Table Data Summarization
   */
  summarizeCSV(data) {
    try {
      const rows = Array.isArray(data) ? data : (data.rows || data.data || []);
      const columns = this.extractColumns(rows);
      const rowCount = rows.length;
    
    // Calculate statistics
    const statistics = this.calculateTableStatistics(rows, columns);
    const dataQuality = this.assessDataQuality(rows, columns);
    const distribution = this.calculateDistribution(rows, columns);
    
    // Generate business summary
    const businessSummary = this.generateCSVBusinessSummary(rowCount, columns, statistics, dataQuality);
    
    return {
      type: 'dataset',
      summaryType: 'dataset',
      businessSummary: {
        title: `Dataset (${rowCount} rows)`,
        description: businessSummary,
        totalRows: rowCount,
        totalColumns: columns.length
      },
      metrics: {
        rows: rowCount,
        columns: columns.length,
        completeness: dataQuality.completeness,
        uniqueValues: statistics.uniqueValues
      },
      preview: {
        headers: columns,
        sampleRows: rows.slice(0, 5),
        dataTypes: this.inferDataTypes(rows.slice(0, 100), columns),
        distribution
      },
      statistics,
      dataQuality,
      businessInsight: this.generateCSVInsight(rowCount, dataQuality, statistics),
      fullDataAvailable: true,
      actions: ['view_full_table', 'export_excel', 'generate_report', 'analyze_patterns']
    };
    } catch (error) {
      console.error('❌ CSV summarization error:', error.message);
      return this.genericSummary(data);
    }
  }

  /**
   * Email Batch Summarization
   */
  summarizeEmails(data) {
    try {
      const emails = Array.isArray(data) ? data : [data];
      const emailCount = emails.length;
    
    // Analyze email patterns
    const senders = this.extractEmailSenders(emails);
    const subjects = this.extractEmailSubjects(emails);
    const categories = this.categorizeEmails(emails);
    const timeRange = this.getEmailTimeRange(emails);
    
    // Generate summary
    const businessSummary = this.generateEmailBusinessSummary(emailCount, senders, categories, timeRange);
    
    return {
      type: 'email_batch',
      summaryType: 'emails',
      businessSummary: {
        title: `Email Batch (${emailCount} messages)`,
        description: businessSummary,
        totalEmails: emailCount,
        uniqueSenders: senders.length
      },
      metrics: {
        total: emailCount,
        uniqueSenders: senders.length,
        categories: Object.keys(categories).length,
        timeSpan: timeRange
      },
      preview: {
        recentEmails: emails.slice(0, 3).map(e => ({
          from: e.mittente || e.sender || 'Unknown',
          subject: e.oggetto || e.subject || 'No subject',
          date: e.date || e.timestamp
        })),
        topSenders: this.getTopSenders(senders),
        categories
      },
      businessInsight: this.generateEmailInsight(categories, senders),
      fullDataAvailable: true,
      actions: ['view_all_emails', 'export_list', 'analyze_sentiment']
    };
    } catch (error) {
      console.error('❌ Email summarization error:', error.message);
      return this.genericSummary(data);
    }
  }

  /**
   * API Response Summarization
   */
  summarizeAPI(data) {
    try {
      const isArray = Array.isArray(data);
      const itemCount = isArray ? data.length : 1;
      const dataStructure = this.analyzeDataStructure(data);
      const keyFields = this.identifyKeyFields(data);
    
    // Generate summary based on structure
    const businessSummary = this.generateAPIBusinessSummary(itemCount, dataStructure, keyFields);
    
    return {
      type: 'api_response',
      summaryType: 'api',
      businessSummary: {
        title: 'API Response',
        description: businessSummary,
        itemCount,
        structure: dataStructure
      },
      metrics: {
        items: itemCount,
        fields: keyFields.length,
        depth: dataStructure.depth,
        dataTypes: dataStructure.types
      },
      preview: {
        sample: isArray ? data.slice(0, 3) : data,
        keyFields,
        structure: dataStructure
      },
      businessInsight: this.generateAPIInsight(itemCount, dataStructure),
      fullDataAvailable: true,
      actions: ['view_json', 'export_data', 'analyze_structure']
    };
    } catch (error) {
      console.error('❌ API summarization error:', error.message);
      return this.genericSummary(data);
    }
  }

  /**
   * Statistical Summary for numerical data
   */
  statisticalSummary(data, nodeType, nodeName) {
    const numbers = this.extractNumericalData(data);
    
    if (numbers.length === 0) {
      return this.genericSummary(data);
    }
    
    const stats = {
      count: numbers.length,
      min: Math.min(...numbers),
      max: Math.max(...numbers),
      mean: numbers.reduce((a, b) => a + b, 0) / numbers.length,
      median: this.calculateMedian(numbers),
      stdDev: this.calculateStdDev(numbers),
      quartiles: this.calculateQuartiles(numbers)
    };
    
    const outliers = this.detectOutliers(numbers);
    const trends = this.identifyTrends(numbers);
    
    return {
      type: 'statistical',
      summaryType: 'statistics',
      businessSummary: {
        title: 'Statistical Analysis',
        description: `Analysis of ${stats.count} data points`,
        dataPoints: stats.count
      },
      metrics: stats,
      preview: {
        distribution: this.createDistribution(numbers),
        outliers: outliers.slice(0, 10),
        trends
      },
      businessInsight: this.generateStatisticalInsight(stats, outliers, trends),
      visualization: {
        chartType: 'histogram',
        data: this.prepareChartData(numbers)
      },
      fullDataAvailable: true,
      actions: ['view_chart', 'export_stats', 'analyze_trends']
    };
  }

  /**
   * AI-Assisted Summarization (using local Ollama)
   */
  async aiAssistedSummary(data, nodeType, nodeName) {
    // OLLAMA PROJECT FAILED - REMOVED COMPLETELY
    // Fallback directly to pattern-based analysis
    console.log('AI analysis disabled - using pattern-based analysis');
    return this.patternBasedSummary(data, nodeType, nodeName);
  }

  /**
   * Generic summary fallback
   */
  genericSummary(data) {
    const dataStr = JSON.stringify(data);
    const dataSize = dataStr.length;
    const keys = this.extractKeys(data);
    
    return {
      type: 'generic',
      summaryType: 'generic',
      businessSummary: {
        title: 'Process Data',
        description: `Data object with ${keys.length} fields`,
        dataSize: this.formatBytes(dataSize)
      },
      metrics: {
        size: dataSize,
        fields: keys.length,
        type: typeof data
      },
      preview: {
        keys: keys.slice(0, 10),
        sample: dataSize > 1000 ? dataStr.substring(0, 1000) + '...' : dataStr
      },
      businessInsight: 'Complex data structure processed',
      fullDataAvailable: true,
      actions: ['view_raw', 'download', 'export_excel', 'request_ai_analysis']
    };
  }

  // ========== HELPER METHODS ==========

  /**
   * Check if node has a known pattern
   */
  hasKnownPattern(nodeType, nodeName) {
    const knownPatterns = [
      'pdf', 'csv', 'email', 'api', 'database', 
      'document', 'table', 'mail', 'response', 'query'
    ];
    
    const combined = `${nodeType} ${nodeName}`.toLowerCase();
    return knownPatterns.some(pattern => combined.includes(pattern));
  }

  /**
   * Check if data is structured
   */
  isStructuredData(nodeType) {
    const structuredTypes = ['csv', 'table', 'database', 'json', 'api'];
    return structuredTypes.some(type => nodeType?.toLowerCase().includes(type));
  }

  /**
   * Identify data type checks
   */
  isPDFData(data, nodeType, nodeName) {
    return (nodeType?.includes('pdf') || 
            nodeName?.toLowerCase().includes('pdf') ||
            data.extractedText || 
            data.pageCount);
  }

  isCSVData(data, nodeType, nodeName) {
    return (nodeType?.includes('csv') || 
            nodeName?.toLowerCase().includes('csv') ||
            (Array.isArray(data) && data.length > 0 && typeof data[0] === 'object') ||
            data.rows);
  }

  isEmailData(data, nodeType, nodeName) {
    const nameCheck = nodeName?.toLowerCase().includes('mail') || 
                     nodeName?.toLowerCase().includes('email');
    const dataCheck = data.mittente || data.sender || data.oggetto || data.subject;
    return nameCheck || dataCheck;
  }

  isAPIData(data, nodeType, nodeName) {
    return nodeType?.includes('http') || 
           nodeName?.toLowerCase().includes('api') ||
           nodeName?.toLowerCase().includes('webhook');
  }

  isDatabaseData(data, nodeType, nodeName) {
    return nodeType?.includes('database') || 
           nodeName?.toLowerCase().includes('query') ||
           nodeName?.toLowerCase().includes('sql');
  }

  /**
   * Extract title from text
   */
  extractTitle(text) {
    // Try to find a title pattern
    const titlePatterns = [
      /^#\s+(.+)$/m,  // Markdown title
      /^(.+)\n=+$/m,  // Underlined title
      /^Title:\s*(.+)$/mi,
      /^Subject:\s*(.+)$/mi
    ];
    
    for (const pattern of titlePatterns) {
      const match = text.match(pattern);
      if (match) return match[1].trim();
    }
    
    // Fallback to first line
    const firstLine = text.split('\n')[0];
    return firstLine.length > 100 ? firstLine.substring(0, 100) + '...' : firstLine;
  }

  /**
   * Identify document type
   */
  identifyDocumentType(text) {
    const types = {
      'contract': /contract|agreement|terms/i,
      'invoice': /invoice|bill|payment/i,
      'report': /report|analysis|summary/i,
      'email': /@|from:|to:|subject:/i,
      'legal': /legal|law|court|attorney/i,
      'financial': /financial|revenue|profit|loss/i
    };
    
    for (const [type, pattern] of Object.entries(types)) {
      if (pattern.test(text)) return type;
    }
    
    return 'document';
  }

  /**
   * Extract dates from text
   */
  extractDates(text) {
    const datePattern = /\b(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}|\d{4}[\/\-]\d{1,2}[\/\-]\d{1,2}|[A-Z][a-z]+ \d{1,2},? \d{4})\b/g;
    const dates = text.match(datePattern) || [];
    return [...new Set(dates)]; // Remove duplicates
  }

  /**
   * Extract monetary amounts
   */
  extractAmounts(text) {
    const amountPattern = /[€$£¥]\s*\d+(?:[.,]\d{3})*(?:[.,]\d{2})?|\d+(?:[.,]\d{3})*(?:[.,]\d{2})?\s*(?:EUR|USD|GBP|euro|dollar)/gi;
    const amounts = text.match(amountPattern) || [];
    return [...new Set(amounts)];
  }

  /**
   * Extract named entities
   */
  extractEntities(text) {
    const entities = [];
    
    // Extract emails
    const emailPattern = /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g;
    const emails = text.match(emailPattern) || [];
    entities.push(...emails.map(e => ({ type: 'email', value: e })));
    
    // Extract phone numbers
    const phonePattern = /[\+]?[(]?[0-9]{3}[)]?[-\s\.]?[0-9]{3}[-\s\.]?[0-9]{4,6}/g;
    const phones = text.match(phonePattern) || [];
    entities.push(...phones.map(p => ({ type: 'phone', value: p })));
    
    // Extract capitalized words (potential names/companies)
    const namePattern = /\b[A-Z][a-z]+ [A-Z][a-z]+\b/g;
    const names = text.match(namePattern) || [];
    entities.push(...names.slice(0, 10).map(n => ({ type: 'name', value: n })));
    
    return entities;
  }

  /**
   * Extract columns from data rows
   */
  extractColumns(rows) {
    if (!rows || rows.length === 0) return [];
    const firstRow = rows[0];
    return Object.keys(firstRow);
  }

  /**
   * Calculate table statistics
   */
  calculateTableStatistics(rows, columns) {
    const stats = {
      totalRows: rows.length,
      totalColumns: columns.length,
      uniqueValues: {},
      nullCounts: {},
      dataTypes: {}
    };
    
    columns.forEach(col => {
      const values = rows.map(row => row[col]);
      stats.uniqueValues[col] = new Set(values.filter(v => v != null)).size;
      stats.nullCounts[col] = values.filter(v => v == null).length;
      stats.dataTypes[col] = this.inferColumnType(values);
    });
    
    return stats;
  }

  /**
   * Assess data quality
   */
  assessDataQuality(rows, columns) {
    const totalCells = rows.length * columns.length;
    let nullCount = 0;
    let duplicateRows = 0;
    
    const rowHashes = new Set();
    rows.forEach(row => {
      const hash = JSON.stringify(row);
      if (rowHashes.has(hash)) duplicateRows++;
      rowHashes.add(hash);
      
      columns.forEach(col => {
        if (row[col] == null || row[col] === '') nullCount++;
      });
    });
    
    return {
      completeness: ((totalCells - nullCount) / totalCells * 100).toFixed(1),
      uniqueness: ((rows.length - duplicateRows) / rows.length * 100).toFixed(1),
      nullCount,
      duplicateRows,
      totalCells
    };
  }

  /**
   * Infer column data type
   */
  inferColumnType(values) {
    const sample = values.filter(v => v != null).slice(0, 100);
    
    if (sample.every(v => typeof v === 'number')) return 'number';
    if (sample.every(v => !isNaN(Date.parse(v)))) return 'date';
    if (sample.every(v => typeof v === 'boolean')) return 'boolean';
    if (sample.every(v => /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/.test(v))) return 'email';
    
    return 'string';
  }

  /**
   * Calculate distribution
   */
  calculateDistribution(rows, columns) {
    const dist = {};
    
    columns.slice(0, 5).forEach(col => { // Limit to first 5 columns
      const values = rows.map(row => row[col]);
      const uniqueValues = [...new Set(values)];
      
      if (uniqueValues.length <= 10) {
        // Categorical distribution
        dist[col] = {};
        values.forEach(v => {
          dist[col][v] = (dist[col][v] || 0) + 1;
        });
      } else if (this.inferColumnType(values) === 'number') {
        // Numerical distribution
        const numbers = values.filter(v => !isNaN(v)).map(Number);
        dist[col] = {
          min: Math.min(...numbers),
          max: Math.max(...numbers),
          mean: numbers.reduce((a, b) => a + b, 0) / numbers.length
        };
      }
    });
    
    return dist;
  }

  /**
   * Extract email senders
   */
  extractEmailSenders(emails) {
    const senders = [];
    emails.forEach(email => {
      const sender = email.mittente || email.sender || email.from;
      if (sender) senders.push(sender);
    });
    return [...new Set(senders)];
  }

  /**
   * Extract email subjects
   */
  extractEmailSubjects(emails) {
    return emails.map(email => email.oggetto || email.subject || 'No subject');
  }

  /**
   * Categorize emails
   */
  categorizeEmails(emails) {
    const categories = {
      support: 0,
      order: 0,
      inquiry: 0,
      complaint: 0,
      other: 0
    };
    
    emails.forEach(email => {
      const text = `${email.oggetto || ''} ${email.messaggio || ''}`.toLowerCase();
      
      if (text.includes('support') || text.includes('help')) categories.support++;
      else if (text.includes('order') || text.includes('ordine')) categories.order++;
      else if (text.includes('info') || text.includes('question')) categories.inquiry++;
      else if (text.includes('problem') || text.includes('issue')) categories.complaint++;
      else categories.other++;
    });
    
    return categories;
  }

  /**
   * Get email time range
   */
  getEmailTimeRange(emails) {
    const dates = emails.map(e => new Date(e.date || e.timestamp || Date.now())).filter(d => !isNaN(d));
    if (dates.length === 0) return 'Unknown';
    
    const minDate = new Date(Math.min(...dates));
    const maxDate = new Date(Math.max(...dates));
    
    const diffDays = Math.ceil((maxDate - minDate) / (1000 * 60 * 60 * 24));
    return `${diffDays} days`;
  }

  /**
   * Statistical calculations
   */
  calculateMedian(numbers) {
    const sorted = [...numbers].sort((a, b) => a - b);
    const mid = Math.floor(sorted.length / 2);
    return sorted.length % 2 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;
  }

  calculateStdDev(numbers) {
    const mean = numbers.reduce((a, b) => a + b, 0) / numbers.length;
    const squaredDiffs = numbers.map(n => Math.pow(n - mean, 2));
    const variance = squaredDiffs.reduce((a, b) => a + b, 0) / numbers.length;
    return Math.sqrt(variance);
  }

  calculateQuartiles(numbers) {
    const sorted = [...numbers].sort((a, b) => a - b);
    const q1Index = Math.floor(sorted.length * 0.25);
    const q3Index = Math.floor(sorted.length * 0.75);
    
    return {
      q1: sorted[q1Index],
      q2: this.calculateMedian(numbers),
      q3: sorted[q3Index]
    };
  }

  detectOutliers(numbers) {
    const q = this.calculateQuartiles(numbers);
    const iqr = q.q3 - q.q1;
    const lowerBound = q.q1 - 1.5 * iqr;
    const upperBound = q.q3 + 1.5 * iqr;
    
    return numbers.filter(n => n < lowerBound || n > upperBound);
  }

  /**
   * Generate business summaries
   */
  generatePDFBusinessSummary(title, type, dates, amounts, entities) {
    let summary = `${type.charAt(0).toUpperCase() + type.slice(1)} document`;
    
    if (title) summary = `"${title}"`;
    if (dates.length > 0) summary += ` dated ${dates[0]}`;
    if (amounts.length > 0) summary += ` with amounts: ${amounts.slice(0, 2).join(', ')}`;
    if (entities.length > 0) {
      const emails = entities.filter(e => e.type === 'email').slice(0, 2);
      if (emails.length > 0) summary += ` involving ${emails.map(e => e.value).join(', ')}`;
    }
    
    return summary;
  }

  generateCSVBusinessSummary(rows, columns, stats, quality) {
    let summary = `Dataset with ${rows} records across ${columns.length} fields. `;
    summary += `Data completeness: ${quality.completeness}%. `;
    
    const numericCols = Object.entries(stats.dataTypes).filter(([, type]) => type === 'number').length;
    if (numericCols > 0) summary += `Contains ${numericCols} numeric columns for analysis. `;
    
    if (quality.duplicateRows > 0) summary += `Found ${quality.duplicateRows} duplicate records. `;
    
    return summary;
  }

  generateEmailBusinessSummary(count, senders, categories, timeRange) {
    let summary = `${count} emails from ${senders.length} unique senders over ${timeRange}. `;
    
    const topCategory = Object.entries(categories).sort((a, b) => b[1] - a[1])[0];
    if (topCategory) summary += `Most emails are ${topCategory[0]} related (${topCategory[1]} messages). `;
    
    return summary;
  }

  generateAPIBusinessSummary(count, structure, fields) {
    let summary = `API response with ${count} ${count === 1 ? 'item' : 'items'}. `;
    summary += `Data structure depth: ${structure.depth} levels. `;
    
    if (fields.length > 0) {
      summary += `Key fields: ${fields.slice(0, 3).join(', ')}`;
      if (fields.length > 3) summary += ` and ${fields.length - 3} more`;
    }
    
    return summary;
  }

  /**
   * Generate business insights
   */
  generatePDFInsight(type, amounts, entities) {
    if (type === 'contract' && amounts.length > 0) {
      return `Contract document with financial obligations of ${amounts[0]}`;
    }
    if (type === 'invoice') {
      return `Invoice requiring processing${amounts.length > 0 ? ' for ' + amounts[0] : ''}`;
    }
    if (type === 'report') {
      return 'Business report document successfully processed';
    }
    return 'Document processed and ready for review';
  }

  generateCSVInsight(rows, quality, stats) {
    if (quality.completeness < 80) {
      return `Data quality needs attention (${quality.completeness}% complete). Consider data cleaning.`;
    }
    if (rows > 10000) {
      return `Large dataset processed efficiently. Ready for analysis or export.`;
    }
    return `Data successfully imported with ${quality.completeness}% completeness`;
  }

  generateEmailInsight(categories, senders) {
    const topCategory = Object.entries(categories).sort((a, b) => b[1] - a[1])[0];
    if (topCategory && topCategory[0] === 'support') {
      return 'High volume of support requests detected. Consider automation or FAQ updates.';
    }
    if (topCategory && topCategory[0] === 'complaint') {
      return 'Multiple complaints received. Immediate attention recommended.';
    }
    return `Email batch processed. ${senders.length} unique contacts engaged.`;
  }

  generateStatisticalInsight(stats, outliers, trends) {
    if (outliers.length > stats.count * 0.1) {
      return `Significant outliers detected (${outliers.length} anomalies). Review for data quality.`;
    }
    if (trends.includes('increasing')) {
      return 'Positive trend detected in data. Growth pattern identified.';
    }
    if (trends.includes('decreasing')) {
      return 'Declining trend observed. Investigation recommended.';
    }
    return `Statistical analysis complete. Data shows normal distribution.`;
  }

  /**
   * Cache management
   */
  generateCacheKey(data, nodeType, nodeName) {
    const str = JSON.stringify({ 
      dataHash: this.generateHash(data), 
      nodeType, 
      nodeName 
    });
    return this.simpleHash(str);
  }

  generateHash(data) {
    const str = JSON.stringify(data);
    return this.simpleHash(str.substring(0, 1000)); // Hash first 1KB only for performance
  }

  simpleHash(str) {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32bit integer
    }
    return hash.toString(36);
  }

  getCachedSummary(key) {
    const cached = this.summaryCache.get(key);
    if (cached && cached.timestamp + this.CACHE_TTL > Date.now()) {
      return cached.data;
    }
    return null;
  }

  cacheSummary(key, data) {
    this.summaryCache.set(key, {
      data,
      timestamp: Date.now()
    });
    
    // Clean old cache entries
    if (this.summaryCache.size > 100) {
      const now = Date.now();
      for (const [k, v] of this.summaryCache.entries()) {
        if (v.timestamp + this.CACHE_TTL < now) {
          this.summaryCache.delete(k);
        }
      }
    }
  }

  /**
   * OLLAMA REMOVED - PROJECT FAILED
   * Kept for compatibility but not used
   */
  buildAIPrompt(data, nodeType, nodeName) {
    // This method is no longer used since Ollama was removed
    return '';
  }

  // OLLAMA REMOVED - PROJECT FAILED
  // This method is no longer used but kept as stub for compatibility
  async callLocalOllama(prompt) {
    return {
      summary: 'AI analysis temporarily unavailable',
      metrics: {},
      keyPoints: [],
      insight: 'Manual analysis required',
      recommendations: [],
      confidence: 'low'
    };
  }

  /**
   * Utility methods
   */
  formatBytes(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
    return (bytes / (1024 * 1024 * 1024)).toFixed(1) + ' GB';
  }

  extractKeys(obj) {
    if (!obj || typeof obj !== 'object') return [];
    
    const keys = [];
    const extract = (o, prefix = '') => {
      Object.keys(o).forEach(key => {
        const fullKey = prefix ? `${prefix}.${key}` : key;
        keys.push(fullKey);
        
        if (typeof o[key] === 'object' && o[key] !== null && !Array.isArray(o[key]) && keys.length < 50) {
          extract(o[key], fullKey);
        }
      });
    };
    
    extract(obj);
    return keys;
  }

  extractNumericalData(data) {
    const numbers = [];
    
    const extract = (obj) => {
      if (typeof obj === 'number') {
        numbers.push(obj);
      } else if (Array.isArray(obj)) {
        obj.forEach(extract);
      } else if (typeof obj === 'object' && obj !== null) {
        Object.values(obj).forEach(extract);
      }
    };
    
    extract(data);
    return numbers;
  }

  identifyTrends(numbers) {
    if (numbers.length < 3) return ['insufficient_data'];
    
    const trends = [];
    let increasing = 0;
    let decreasing = 0;
    
    for (let i = 1; i < numbers.length; i++) {
      if (numbers[i] > numbers[i - 1]) increasing++;
      else if (numbers[i] < numbers[i - 1]) decreasing++;
    }
    
    if (increasing > numbers.length * 0.6) trends.push('increasing');
    if (decreasing > numbers.length * 0.6) trends.push('decreasing');
    if (Math.abs(increasing - decreasing) < numbers.length * 0.2) trends.push('stable');
    
    return trends.length > 0 ? trends : ['mixed'];
  }

  analyzeDataStructure(data) {
    const structure = {
      type: Array.isArray(data) ? 'array' : typeof data,
      depth: 0,
      types: new Set()
    };
    
    const analyze = (obj, depth = 0) => {
      structure.depth = Math.max(structure.depth, depth);
      
      if (Array.isArray(obj)) {
        obj.slice(0, 10).forEach(item => analyze(item, depth + 1));
      } else if (typeof obj === 'object' && obj !== null) {
        Object.values(obj).forEach(val => {
          structure.types.add(typeof val);
          if (typeof val === 'object' && val !== null) {
            analyze(val, depth + 1);
          }
        });
      }
    };
    
    analyze(data);
    structure.types = Array.from(structure.types);
    
    return structure;
  }

  identifyKeyFields(data) {
    const fields = [];
    const sample = Array.isArray(data) ? data[0] : data;
    
    if (sample && typeof sample === 'object') {
      Object.keys(sample).forEach(key => {
        const value = sample[key];
        
        // Prioritize important fields
        if (key.match(/id|name|title|email|date|amount|status|type/i)) {
          fields.unshift(key);
        } else {
          fields.push(key);
        }
      });
    }
    
    return fields.slice(0, 10); // Limit to 10 key fields
  }

  getTopSenders(senders) {
    const counts = {};
    senders.forEach(s => counts[s] = (counts[s] || 0) + 1);
    
    return Object.entries(counts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5)
      .map(([sender, count]) => ({ sender, count }));
  }

  estimatePages(text) {
    const charsPerPage = parseInt(process.env.BI_CHARS_PER_PAGE || '3000');
    // Estimate pages based on character count
    return Math.ceil(text.length / charsPerPage);
  }

  inferDataTypes(rows, columns) {
    const types = {};
    
    columns.forEach(col => {
      const values = rows.map(row => row[col]).filter(v => v != null);
      types[col] = this.inferColumnType(values);
    });
    
    return types;
  }

  createDistribution(numbers) {
    if (numbers.length === 0) return {};
    
    const min = Math.min(...numbers);
    const max = Math.max(...numbers);
    const buckets = 10;
    const bucketSize = (max - min) / buckets;
    
    const distribution = {};
    for (let i = 0; i < buckets; i++) {
      const rangeStart = min + i * bucketSize;
      const rangeEnd = rangeStart + bucketSize;
      const count = numbers.filter(n => n >= rangeStart && n < rangeEnd).length;
      distribution[`${rangeStart.toFixed(1)}-${rangeEnd.toFixed(1)}`] = count;
    }
    
    return distribution;
  }

  prepareChartData(numbers) {
    const dist = this.createDistribution(numbers);
    
    return {
      labels: Object.keys(dist),
      datasets: [{
        label: 'Distribution',
        data: Object.values(dist)
      }]
    };
  }
}

// Export singleton instance
const businessIntelligenceService = new BusinessIntelligenceService();

export default businessIntelligenceService;
export { BusinessIntelligenceService };