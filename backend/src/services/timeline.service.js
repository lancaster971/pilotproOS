/**
 * Timeline Service - Critical Business Intelligence Feature
 * Replaces complex raw SQL logic in server.js /api/business/raw-data-for-modal
 * Uses repository pattern while maintaining all existing business logic
 */

import { BusinessRepository } from '../repositories/business.repository.js';
import { WorkflowRepository } from '../repositories/workflow.repository.js';
import { ExecutionRepository } from '../repositories/execution.repository.js';
import businessIntelligenceService from './business-intelligence.service.js';
import { humanizeStepData } from '../utils/business-step-parser.js';
// Temporarily disabled - path issue in Docker container
// import { UnifiedBusinessProcessor } from '../../../frontend/src/shared/business-parsers/unified-processor.js';

export class TimelineService {
  constructor(dbPool) {
    this.businessRepo = new BusinessRepository();
    this.workflowRepo = new WorkflowRepository();
    this.executionRepo = new ExecutionRepository();
    this.dbPool = dbPool; // Keep dbPool for complex legacy queries during transition
  }

  /**
   * Get Timeline Data for Modal
   * Replaces the massive raw SQL query logic in server.js
   * Maintains all existing business logic and Business Intelligence processing
   */
  async getTimelineData(workflowId, executionId = null) {
    console.log(`🎯 Timeline Service: Loading data for workflow ${workflowId}, execution: ${executionId || 'latest'}`);
    
    try {
      // Step 1: Try to load saved business data first (preserve existing logic)
      console.log('📊 Attempting to load data from business_execution_data table...');
      const savedBusinessData = await this.loadBusinessDataFromDatabase(workflowId, executionId);
      
      // FOR NOW: Use fallback logic (preserve all existing Timeline functionality)
      // This maintains 100% compatibility while transitioning to repositories
      console.log('🔧 Using repository-enhanced fallback to preserve all Timeline functionality');
      
      // Get timeline data using repository (replaces the main raw SQL)
      const timelineData = await this.businessRepo.getTimelineData(workflowId, executionId);
      
      if (!timelineData) {
        return {
          success: false,
          data: {
            processName: 'Unknown Process',
            status: 'no_executions',
            message: 'No executions found for this process',
            timeline: []
          }
        };
      }

      console.log(`✅ Found execution: ${timelineData.executionId}`);
      
      // Step 3: Parse execution data to extract timeline (preserve existing logic)
      const timeline = await this.parseExecutionDataToTimeline(timelineData);
      
      // Step 4: Process through Business Intelligence Service (existing logic)
      const enrichedTimeline = await this.enrichTimelineWithBusinessIntelligence(timeline);
      
      // Step 5: Build final response (preserve existing response format)
      return {
        success: true,
        data: {
          workflow: {
            id: timelineData.workflowId,
            name: timelineData.workflowName,
            active: timelineData.status !== 'error',
            isActive: timelineData.status !== 'error',
            source: 'repository'
          },
          businessNodes: enrichedTimeline,
          execution: {
            id: timelineData.executionId,
            status: this.mapExecutionStatus(timelineData),
            startedAt: timelineData.startedAt,
            stoppedAt: timelineData.stoppedAt,
            duration: timelineData.duration,
            source: 'repository'
          },
          stats: {
            totalShowNodes: enrichedTimeline.length,
            executedNodes: enrichedTimeline.filter(node => node.executed).length,
            successNodes: enrichedTimeline.filter(node => node.status === 'success').length,
            source: 'repository'
          },
          _metadata: {
            system: 'Business Process Operating System',
            endpoint: 'timeline-service',
            source: 'drizzle_repository_layer',
            timestamp: new Date().toISOString(),
            dataProcessingMethod: 'business_intelligence_enhanced'
          }
        }
      };

    } catch (error) {
      console.error('❌ Timeline Service failed:', error);
      throw error;
    }
  }

  /**
   * Parse Execution Data to Timeline
   * Preserves all existing parsing logic from server.js
   */
  async parseExecutionDataToTimeline(timelineData) {
    const timeline = [];
    
    // Parse execution data (preserve existing logic)
    let executionData;
    try {
      // Handle both string and object formats
      if (typeof timelineData.executionData === 'string') {
        executionData = JSON.parse(timelineData.executionData);
      } else {
        executionData = timelineData.executionData;
      }
    } catch (parseError) {
      console.error('❌ Failed to parse execution data:', parseError);
      executionData = null;
    }

    // Handle n8n compressed format (preserve existing logic)
    let runData = null;
    
    if (Array.isArray(executionData)) {
      console.log('📊 Processing compressed n8n execution data format');
      
      for (const dataItem of executionData) {
        if (dataItem && typeof dataItem === 'object' && dataItem.resultData) {
          if (dataItem.resultData.runData) {
            runData = dataItem.resultData.runData;
            break;
          }
        }
      }
    } else if (executionData && executionData.resultData && executionData.resultData.runData) {
      runData = executionData.resultData.runData;
    }

    if (!runData) {
      console.log('⚠️ No runData found in execution - returning empty timeline');
      return [];
    }

    // Parse workflow nodes (preserve existing logic)
    const nodes = timelineData.nodes || [];
    const showNodes = nodes.filter(node => node.name && node.name.startsWith('show-'));
    
    console.log(`🔍 Found ${showNodes.length} show nodes to process`);

    // Process each show node (preserve existing logic)
    for (let index = 0; index < showNodes.length; index++) {
      const node = showNodes[index];
      const nodeRunData = runData[node.name];

      if (nodeRunData && nodeRunData.length > 0) {
        const nodeData = nodeRunData[0];

        // Extract input/output data (preserve existing logic)
        const inputData = nodeData.data?.main?.[0]?.json || null;
        const outputData = nodeData.data?.main?.[0]?.json || null;

        // Create timeline entry (preserve existing structure)
        const timelineEntry = {
          showTag: node.name,
          name: node.parameters?.nodeName || node.name,
          businessName: this.generateBusinessStepName(node, index), // ADD business-friendly name
          type: node.type,
          nodeType: this.categorizeNodeType(node.type),
          executed: true,
          status: nodeData.error ? 'error' : 'success',
          data: {
            nodeType: node.type,
            nodeName: node.parameters?.nodeName || node.name,
            executedAt: new Date().toISOString(),
            hasInputData: !!inputData,
            hasOutputData: !!outputData,
            rawInputData: inputData,
            rawOutputData: outputData,
            inputJson: inputData || {},
            outputJson: outputData || {},
            nodeCategory: this.categorizeNodeType(node.type),
            totalDataSize: this.calculateDataSize(inputData, outputData)
          },
          _nodeId: node.id
        };

        timeline.push(timelineEntry);
      }
    }

    return timeline;
  }

  /**
   * Enrich Timeline with Business Intelligence
   * Applies Business Intelligence Service to each timeline entry
   * Preserves existing Business Intelligence logic
   */
  async enrichTimelineWithBusinessIntelligence(timeline) {
    console.log(`🧠 Processing ${timeline.length} timeline entries through Business Intelligence`);
    
    const enrichedTimeline = [];
    
    for (const entry of timeline) {
      const dataToProcess = entry.data.rawOutputData || entry.data.rawInputData;
      
      if (dataToProcess) {
        const dataSize = JSON.stringify(dataToProcess).length;
        
        // Apply Business Intelligence for large data (preserve existing logic)
        if (dataSize > 5000) {
          console.log(`🧠 Processing large data (${dataSize} bytes) through Business Intelligence Service for ${entry.name}`);
          
          const intelligentSummary = await businessIntelligenceService.processNodeOutput(
            dataToProcess,
            entry.type,
            entry.name
          );
          
          entry.data.intelligentSummary = intelligentSummary;
          console.log(`✅ Business Intelligence processing complete: type=${intelligentSummary.type}`);
        }
      }
      
      enrichedTimeline.push(entry);
    }
    
    return enrichedTimeline;
  }

  /**
   * Generate Business Step Name for Client Display
   * Converts technical node names to business-friendly descriptions
   * Hides technical implementation details from client view
   */
  generateBusinessStepName(node, stepIndex) {
    const nodeName = (node.parameters?.nodeName || node.name || '').toLowerCase();

    // Email/Communication nodes
    if (nodeName.includes('mail') || nodeName.includes('ricezione') || nodeName.includes('email')) {
      return 'Customer Request Processing';
    }

    // AI Assistant nodes
    if (nodeName.includes('milena') || nodeName.includes('assistant') || nodeName.includes('ai') || nodeName.includes('gpt')) {
      return 'Intelligent Response Generation';
    }

    // Database/Search nodes
    if (nodeName.includes('ordini') || nodeName.includes('order') || nodeName.includes('database') ||
        nodeName.includes('search') || nodeName.includes('query') || nodeName.includes('qdrant')) {
      return 'Information Retrieval';
    }

    // Sending/Communication output
    if (nodeName.includes('send') || nodeName.includes('invio') || nodeName.includes('reply') ||
        nodeName.includes('response')) {
      return 'Customer Communication';
    }

    // Document processing
    if (nodeName.includes('pdf') || nodeName.includes('document') || nodeName.includes('file')) {
      return 'Document Processing';
    }

    // Data processing
    if (nodeName.includes('csv') || nodeName.includes('excel') || nodeName.includes('spreadsheet') ||
        nodeName.includes('data')) {
      return 'Data Processing';
    }

    // Webhook/Integration
    if (nodeName.includes('webhook') || nodeName.includes('http') || nodeName.includes('api')) {
      return 'System Integration';
    }

    // Generic business step with meaningful name
    return `Business Task ${stepIndex + 1}`;
  }

  /**
   * Helper Methods (preserve existing business logic)
   */
  categorizeNodeType(nodeType) {
    if (nodeType.includes('email') || nodeType.includes('mail')) return 'communication';
    if (nodeType.includes('webhook') || nodeType.includes('http')) return 'integration';
    if (nodeType.includes('schedule') || nodeType.includes('trigger')) return 'automation';
    if (nodeType.includes('spreadsheet') || nodeType.includes('csv')) return 'data-processing';
    return 'business';
  }

  calculateDataSize(inputData, outputData) {
    let size = 0;
    if (inputData) size += JSON.stringify(inputData).length;
    if (outputData) size += JSON.stringify(outputData).length;
    return size;
  }

  mapExecutionStatus(timelineData) {
    if (timelineData.status === 'error') return 'error';
    if (timelineData.finished) return 'success';
    if (timelineData.stoppedAt) return 'completed';
    return 'running';
  }

  /**
   * Load Business Data from Database (preserve existing logic)
   * Uses raw SQL temporarily during transition to preserve functionality
   */
  async loadBusinessDataFromDatabase(workflowId) {
    try {
      // Use existing BusinessRepository method
      return await this.businessRepo.searchBusinessData({
        workflowId,
        limit: 100
      });
    } catch (error) {
      console.error('⚠️ Failed to load business data from database:', error);
      return [];
    }
  }
}