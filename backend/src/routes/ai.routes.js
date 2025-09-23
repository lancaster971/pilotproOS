import express from 'express';
import agentEngineService from '../services/agent-engine.service.js';
import { authenticate as authenticateJWT } from '../middleware/auth.middleware.js';
import businessLogger from '../utils/businessLogger.js';

const router = express.Router();

/**
 * @route   GET /api/ai/health
 * @desc    Check AI service health
 * @access  Public
 */
router.get('/health', async (req, res) => {
  try {
    const health = await agentEngineService.healthCheck();
    res.json(health);
  } catch (error) {
    businessLogger.error('AI health check error:', error);
    res.status(503).json({
      status: 'unhealthy',
      error: error.message
    });
  }
});

/**
 * @route   GET /api/ai/models
 * @desc    Get available LLM models
 * @access  Private
 */
router.get('/models', authenticateJWT, async (req, res) => {
  try {
    const models = await agentEngineService.getLLMHealth();
    res.json(models);
  } catch (error) {
    businessLogger.error('Get models error:', error);
    res.status(500).json({
      error: 'Failed to get models',
      message: error.message
    });
  }
});

/**
 * @route   POST /api/ai/assistant
 * @desc    Ask PilotPro Assistant a question
 * @access  Private
 */
router.post('/assistant', authenticateJWT, async (req, res) => {
  try {
    const { question, context } = req.body;

    if (!question) {
      return res.status(400).json({
        error: 'Question is required'
      });
    }

    const jwtToken = req.headers.authorization?.split(' ')[1];
    const result = await agentEngineService.askAssistant(
      question,
      jwtToken,
      context
    );

    res.json(result);
  } catch (error) {
    businessLogger.error('Assistant error:', error);
    res.status(500).json({
      error: 'Assistant error',
      message: error.message
    });
  }
});

/**
 * @route   POST /api/ai/analyze
 * @desc    Submit analysis job
 * @access  Private
 */
router.post('/analyze', authenticateJWT, async (req, res) => {
  try {
    const { type, data, priority } = req.body;

    if (!type || !data) {
      return res.status(400).json({
        error: 'Type and data are required'
      });
    }

    const result = await agentEngineService.submitAnalysis(
      type,
      data,
      priority
    );

    res.json(result);
  } catch (error) {
    businessLogger.error('Analysis submission error:', error);
    res.status(500).json({
      error: 'Analysis submission failed',
      message: error.message
    });
  }
});

/**
 * @route   POST /api/ai/analyze/process
 * @desc    Analyze business process
 * @access  Private
 */
router.post('/analyze/process', authenticateJWT, async (req, res) => {
  try {
    const { processData } = req.body;

    if (!processData) {
      return res.status(400).json({
        error: 'Process data is required'
      });
    }

    const jwtToken = req.headers.authorization?.split(' ')[1];
    const result = await agentEngineService.analyzeProcess(
      processData,
      jwtToken
    );

    res.json(result);
  } catch (error) {
    businessLogger.error('Process analysis error:', error);
    res.status(500).json({
      error: 'Process analysis failed',
      message: error.message
    });
  }
});

/**
 * @route   GET /api/ai/jobs/:jobId
 * @desc    Get job status
 * @access  Private
 */
router.get('/jobs/:jobId', authenticateJWT, async (req, res) => {
  try {
    const { jobId } = req.params;
    const status = await agentEngineService.getJobStatus(jobId);
    res.json(status);
  } catch (error) {
    businessLogger.error('Get job status error:', error);
    res.status(404).json({
      error: 'Job not found',
      message: error.message
    });
  }
});

/**
 * @route   GET /api/ai/jobs/:jobId/result
 * @desc    Get job result
 * @access  Private
 */
router.get('/jobs/:jobId/result', authenticateJWT, async (req, res) => {
  try {
    const { jobId } = req.params;
    const result = await agentEngineService.getJobResult(jobId);
    res.json(result);
  } catch (error) {
    businessLogger.error('Get job result error:', error);
    res.status(404).json({
      error: 'Result not found',
      message: error.message
    });
  }
});

/**
 * @route   POST /api/ai/webhook/n8n
 * @desc    Webhook per ricevere dati da n8n workflows
 * @access  Public (con secret validation)
 */
router.post('/webhook/n8n', async (req, res) => {
  try {
    const { secret, workflowId, data, action } = req.body;

    // Valida il secret per sicurezza
    const expectedSecret = process.env.N8N_WEBHOOK_SECRET || 'pilotpros_n8n_secret_2025';
    if (secret !== expectedSecret) {
      return res.status(401).json({ error: 'Invalid secret' });
    }

    businessLogger.info('N8n webhook received', {
      workflowId,
      action,
      dataSize: JSON.stringify(data).length
    });

    // Processa l'azione richiesta
    switch (action) {
      case 'analyze':
        // n8n vuole che l'AI analizzi dei dati
        const analysisResult = await agentEngineService.submitAnalysis(
          'workflow_analysis',
          {
            workflowId,
            data,
            source: 'n8n'
          },
          'high' // Alta priorità per workflow
        );
        res.json(analysisResult);
        break;

      case 'assistant':
        // n8n vuole una risposta dall'assistente
        const assistantResult = await agentEngineService.askAssistant(
          data.question || 'Analizza questi dati dal workflow',
          null, // No JWT per webhook
          { workflowId, data }
        );
        res.json(assistantResult);
        break;

      case 'trigger_workflow':
        // L'AI vuole triggerare un workflow n8n
        const n8nWebhookUrl = `http://n8n-dev:5678/webhook/${data.webhookPath}`;
        const axios = (await import('axios')).default;
        const n8nResponse = await axios.post(n8nWebhookUrl, data.payload);
        res.json({
          success: true,
          workflowTriggered: true,
          response: n8nResponse.data
        });
        break;

      default:
        res.json({
          success: true,
          message: 'Webhook received',
          action: action || 'none'
        });
    }
  } catch (error) {
    businessLogger.error('N8n webhook error:', error);
    res.status(500).json({
      error: 'Webhook processing failed',
      message: error.message
    });
  }
});

/**
 * @route   POST /api/ai/trigger/workflow
 * @desc    Triggera un workflow n8n dall'AI
 * @access  Private
 */
router.post('/trigger/workflow', authenticateJWT, async (req, res) => {
  try {
    const { workflowId, webhookPath, data } = req.body;

    if (!webhookPath) {
      return res.status(400).json({
        error: 'Webhook path is required'
      });
    }

    // Chiama il webhook di n8n
    const n8nWebhookUrl = `http://n8n-dev:5678/webhook/${webhookPath}`;
    const axios = (await import('axios')).default;

    const n8nResponse = await axios.post(n8nWebhookUrl, {
      ...data,
      triggeredBy: 'ai-agent',
      timestamp: new Date().toISOString(),
      userId: req.user?.id
    });

    res.json({
      success: true,
      workflowId,
      webhookPath,
      response: n8nResponse.data
    });
  } catch (error) {
    businessLogger.error('Workflow trigger error:', error);
    res.status(500).json({
      error: 'Failed to trigger workflow',
      message: error.message
    });
  }
});

export default router;