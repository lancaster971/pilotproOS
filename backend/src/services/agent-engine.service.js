import axios from 'axios';
import businessLogger from '../utils/businessLogger.js';

class AgentEngineService {
  constructor() {
    this.apiUrl = process.env.AGENT_ENGINE_URL || 'http://agent-engine-dev:8000';
    this.timeout = 30000; // 30 seconds
  }

  /**
   * Check Agent Engine health
   */
  async healthCheck() {
    try {
      const response = await axios.get(`${this.apiUrl}/health`, {
        timeout: 5000
      });
      return response.data;
    } catch (error) {
      businessLogger.error('Agent Engine health check failed:', error.message);
      return { status: 'unhealthy', error: error.message };
    }
  }

  /**
   * Ask a question to PilotPro Assistant
   */
  async askAssistant(question, jwtToken, context = null) {
    try {
      const response = await axios.post(
        `${this.apiUrl}/api/v1/assistant`,
        {
          question,
          context,
          language: 'italian',
          jwt_token: jwtToken
        },
        {
          timeout: this.timeout,
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${jwtToken}`
          }
        }
      );

      return response.data;
    } catch (error) {
      businessLogger.error('Agent Engine assistant error:', error);
      throw new Error(`Assistant error: ${error.message}`);
    }
  }

  /**
   * Submit an analysis job
   */
  async submitAnalysis(type, data, priority = 'normal', callback_url = null) {
    try {
      const response = await axios.post(
        `${this.apiUrl}/api/v1/analyze`,
        {
          type,
          data,
          priority,
          callback_url
        },
        {
          timeout: this.timeout,
          headers: {
            'Content-Type': 'application/json'
          }
        }
      );

      return response.data;
    } catch (error) {
      businessLogger.error('Agent Engine analysis submission error:', error);
      throw new Error(`Analysis submission error: ${error.message}`);
    }
  }

  /**
   * Get job status
   */
  async getJobStatus(jobId) {
    try {
      const response = await axios.get(
        `${this.apiUrl}/api/v1/jobs/${jobId}/status`,
        {
          timeout: this.timeout
        }
      );

      return response.data;
    } catch (error) {
      businessLogger.error(`Agent Engine job status error for ${jobId}:`, error);
      throw new Error(`Job status error: ${error.message}`);
    }
  }

  /**
   * Get job result
   */
  async getJobResult(jobId) {
    try {
      const response = await axios.get(
        `${this.apiUrl}/api/v1/jobs/${jobId}/result`,
        {
          timeout: this.timeout
        }
      );

      return response.data;
    } catch (error) {
      businessLogger.error(`Agent Engine job result error for ${jobId}:`, error);
      throw new Error(`Job result error: ${error.message}`);
    }
  }

  /**
   * Get LLM health and available models
   */
  async getLLMHealth() {
    try {
      const response = await axios.get(`${this.apiUrl}/api/v1/health/llm`, {
        timeout: 5000
      });
      return response.data;
    } catch (error) {
      businessLogger.error('Agent Engine LLM health check failed:', error);
      return { status: 'unhealthy', error: error.message };
    }
  }

  /**
   * Analyze business process
   */
  async analyzeProcess(processData, jwtToken) {
    try {
      const response = await axios.post(
        `${this.apiUrl}/api/v1/analyze`,
        {
          type: 'process_analysis',
          data: processData,
          priority: 'normal'
        },
        {
          timeout: this.timeout,
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${jwtToken}`
          }
        }
      );

      // Wait for result if it's a quick job
      if (response.data.job_id) {
        let attempts = 0;
        const maxAttempts = 30; // 30 seconds total

        while (attempts < maxAttempts) {
          await new Promise(resolve => setTimeout(resolve, 1000)); // Wait 1 second

          const status = await this.getJobStatus(response.data.job_id);

          if (status.status === 'completed') {
            return await this.getJobResult(response.data.job_id);
          } else if (status.status === 'failed') {
            throw new Error('Analysis job failed');
          }

          attempts++;
        }

        // If we're here, job is still running
        return {
          success: false,
          job_id: response.data.job_id,
          status: 'processing',
          message: 'Analysis is taking longer than expected. Check back later.'
        };
      }

      return response.data;
    } catch (error) {
      businessLogger.error('Process analysis error:', error);
      throw new Error(`Process analysis error: ${error.message}`);
    }
  }
}

export default new AgentEngineService();