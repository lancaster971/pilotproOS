import express from 'express';
import { authenticateToken } from '../middleware/auth.js';
import agentEngineService from '../services/agent-engine.service.js';
import businessLogger from '../utils/businessLogger.js';

const router = express.Router();

/**
 * Agent Engine health check
 */
router.get('/health', async (req, res) => {
  try {
    const health = await agentEngineService.healthCheck();
    res.json(health);
  } catch (error) {
    businessLogger.error('Agent Engine health check error:', error);
    res.status(503).json({
      status: 'unhealthy',
      error: error.message
    });
  }
});

/**
 * LLM health and available models
 */
router.get('/llm-health', authenticateToken, async (req, res) => {
  try {
    const llmHealth = await agentEngineService.getLLMHealth();
    res.json(llmHealth);
  } catch (error) {
    businessLogger.error('LLM health check error:', error);
    res.status(503).json({
      status: 'unhealthy',
      error: error.message
    });
  }
});

/**
 * Ask PilotPro Assistant
 */
router.post('/assistant', authenticateToken, async (req, res) => {
  try {
    const { question, context } = req.body;

    if (!question) {
      return res.status(400).json({
        success: false,
        error: 'Question is required'
      });
    }

    // Get JWT from authorization header
    const jwt = req.headers.authorization?.replace('Bearer ', '');

    const response = await agentEngineService.askAssistant(
      question,
      jwt,
      context
    );

    res.json(response);

  } catch (error) {
    businessLogger.error('Assistant error:', error);
    res.status(500).json({
      success: false,
      error: error.message,
      answer: 'Mi dispiace, non sono riuscito a elaborare la tua domanda.'
    });
  }
});

/**
 * Analyze business process
 */
router.post('/analyze-process', authenticateToken, async (req, res) => {
  try {
    const { processData } = req.body;

    if (!processData) {
      return res.status(400).json({
        success: false,
        error: 'Process data is required'
      });
    }

    // Get JWT from authorization header
    const jwt = req.headers.authorization?.replace('Bearer ', '');

    const result = await agentEngineService.analyzeProcess(processData, jwt);

    res.json(result);

  } catch (error) {
    businessLogger.error('Process analysis error:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

/**
 * Submit generic analysis job
 */
router.post('/analyze', authenticateToken, async (req, res) => {
  try {
    const { type, data, priority } = req.body;

    if (!type || !data) {
      return res.status(400).json({
        success: false,
        error: 'Type and data are required'
      });
    }

    const result = await agentEngineService.submitAnalysis(
      type,
      data,
      priority || 'normal'
    );

    res.json(result);

  } catch (error) {
    businessLogger.error('Analysis submission error:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

/**
 * Get job status
 */
router.get('/jobs/:jobId/status', authenticateToken, async (req, res) => {
  try {
    const { jobId } = req.params;
    const status = await agentEngineService.getJobStatus(jobId);
    res.json(status);
  } catch (error) {
    businessLogger.error(`Job status error for ${req.params.jobId}:`, error);
    res.status(404).json({
      success: false,
      error: error.message
    });
  }
});

/**
 * Get job result
 */
router.get('/jobs/:jobId/result', authenticateToken, async (req, res) => {
  try {
    const { jobId } = req.params;
    const result = await agentEngineService.getJobResult(jobId);
    res.json(result);
  } catch (error) {
    businessLogger.error(`Job result error for ${req.params.jobId}:`, error);

    if (error.message.includes('not found')) {
      res.status(404).json({
        success: false,
        error: error.message
      });
    } else if (error.message.includes('not completed')) {
      res.status(400).json({
        success: false,
        error: error.message
      });
    } else {
      res.status(500).json({
        success: false,
        error: error.message
      });
    }
  }
});

/**
 * Quick insight from Assistant (with short timeout)
 */
router.post('/quick-insight', authenticateToken, async (req, res) => {
  try {
    const { question, context } = req.body;

    if (!question) {
      return res.status(400).json({
        success: false,
        error: 'Question is required'
      });
    }

    // Get JWT from authorization header
    const jwt = req.headers.authorization?.replace('Bearer ', '');

    // Use shorter timeout for quick insights
    const timeoutPromise = new Promise((_, reject) =>
      setTimeout(() => reject(new Error('Timeout')), 5000)
    );

    const assistantPromise = agentEngineService.askAssistant(
      question,
      jwt,
      context
    );

    try {
      const response = await Promise.race([assistantPromise, timeoutPromise]);
      res.json(response);
    } catch (timeoutError) {
      // Return partial response on timeout
      res.json({
        success: false,
        answer: 'Il sistema sta elaborando... Riprova tra qualche secondo.',
        confidence: 0,
        timeout: true
      });
    }

  } catch (error) {
    businessLogger.error('Quick insight error:', error);
    res.status(500).json({
      success: false,
      error: error.message,
      answer: 'Errore nell\'elaborazione rapida.'
    });
  }
});

export default router;