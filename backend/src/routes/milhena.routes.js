import express from 'express';
import axios from 'axios';
import businessLogger from '../utils/businessLogger.js';

const router = express.Router();

// Intelligence Engine URL (Docker internal network)
const INTELLIGENCE_ENGINE_URL = process.env.INTELLIGENCE_ENGINE_URL ||
  'http://pilotpros-intelligence-engine-dev:8000';

const TIMEOUT = 30000; // 30 seconds

/**
 * @route   POST /api/milhena/feedback
 * @desc    Submit user feedback to Milhena Learning System
 * @access  Public (will be protected in production)
 */
router.post('/feedback', async (req, res) => {
  try {
    const { query, response, feedback_type, intent, session_id, trace_id } = req.body;

    // Validate required fields
    if (!query || !response || !feedback_type || !session_id) {
      return res.status(400).json({
        success: false,
        error: 'Missing required fields: query, response, feedback_type, session_id'
      });
    }

    // Validate feedback_type
    if (!['positive', 'negative', 'correction'].includes(feedback_type)) {
      return res.status(400).json({
        success: false,
        error: 'Invalid feedback_type. Must be: positive, negative, or correction'
      });
    }

    businessLogger.log('Milhena feedback submission', {
      feedback_type,
      session_id,
      has_trace_id: !!trace_id
    });

    // Forward to Intelligence Engine
    const intelligenceResponse = await axios.post(
      `${INTELLIGENCE_ENGINE_URL}/api/milhena/feedback`,
      {
        query,
        response,
        feedback_type,
        intent: intent || 'GENERAL',
        session_id,
        trace_id
      },
      {
        timeout: TIMEOUT,
        headers: {
          'Content-Type': 'application/json'
        }
      }
    );

    businessLogger.success('Milhena feedback recorded successfully', {
      session_id,
      feedback_type
    });

    res.json({
      success: true,
      ...intelligenceResponse.data
    });

  } catch (error) {
    businessLogger.error('Milhena feedback error:', {
      message: error.message,
      status: error.response?.status,
      data: error.response?.data
    });

    res.status(error.response?.status || 500).json({
      success: false,
      error: 'Failed to submit feedback',
      message: error.response?.data?.detail || error.message
    });
  }
});

/**
 * @route   GET /api/milhena/performance
 * @desc    Get Milhena learning performance metrics
 * @access  Public (will be protected in production)
 */
router.get('/performance', async (req, res) => {
  try {
    businessLogger.log('Milhena performance report requested');

    // Forward to Intelligence Engine
    const intelligenceResponse = await axios.get(
      `${INTELLIGENCE_ENGINE_URL}/api/milhena/performance`,
      {
        timeout: TIMEOUT,
        headers: {
          'Content-Type': 'application/json'
        }
      }
    );

    res.json({
      success: true,
      ...intelligenceResponse.data
    });

  } catch (error) {
    businessLogger.error('Milhena performance error:', {
      message: error.message,
      status: error.response?.status
    });

    res.status(error.response?.status || 500).json({
      success: false,
      error: 'Failed to get performance report',
      message: error.response?.data?.detail || error.message
    });
  }
});

/**
 * @route   GET /api/milhena/stats
 * @desc    Get Milhena statistics
 * @access  Public (will be protected in production)
 */
router.get('/stats', async (req, res) => {
  try {
    businessLogger.log('Milhena stats requested');

    // Forward to Intelligence Engine
    const intelligenceResponse = await axios.get(
      `${INTELLIGENCE_ENGINE_URL}/api/stats`,
      {
        timeout: TIMEOUT,
        headers: {
          'Content-Type': 'application/json'
        }
      }
    );

    res.json({
      success: true,
      ...intelligenceResponse.data
    });

  } catch (error) {
    businessLogger.error('Milhena stats error:', {
      message: error.message,
      status: error.response?.status
    });

    res.status(error.response?.status || 500).json({
      success: false,
      error: 'Failed to get statistics',
      message: error.response?.data?.detail || error.message
    });
  }
});

/**
 * @route   POST /api/milhena/patterns/reload
 * @desc    Trigger hot-reload of auto-learned patterns (admin only)
 * @access  Admin (requires JWT authentication in production)
 */
router.post('/patterns/reload', async (req, res) => {
  try {
    const { pattern_id } = req.body;

    businessLogger.log('Milhena pattern hot-reload triggered', {
      pattern_id,
      source: 'admin-endpoint'
    });

    // TODO: Add JWT admin authentication check here
    // if (!req.user || !req.user.isAdmin) {
    //   return res.status(403).json({ success: false, error: 'Admin access required' });
    // }

    // Publish reload message to Redis PubSub
    const { createClient } = await import('redis');
    const redisUrl = process.env.REDIS_URL || 'redis://pilotpros-redis-dev:6379/0';
    const redisClient = createClient({ url: redisUrl });

    await redisClient.connect();

    const message = JSON.stringify({
      action: 'reload',
      pattern_id: pattern_id || null
    });

    const channel = 'pilotpros:patterns:reload';
    const subscribers = await redisClient.publish(channel, message);

    await redisClient.disconnect();

    businessLogger.success('Milhena pattern reload message published', {
      subscribers,
      pattern_id
    });

    res.json({
      success: true,
      message: 'Pattern reload triggered successfully',
      subscribers,
      pattern_id
    });

  } catch (error) {
    businessLogger.error('Milhena pattern reload error:', {
      message: error.message,
      stack: error.stack
    });

    res.status(500).json({
      success: false,
      error: 'Failed to trigger pattern reload',
      message: error.message
    });
  }
});

/**
 * @route   POST /api/milhena/chat
 * @desc    Chat with Milhena assistant
 * @access  Public (will be protected in production)
 */
router.post('/chat', async (req, res) => {
  try {
    const { message, session_id, context } = req.body;

    // Validate required fields
    if (!message) {
      return res.status(400).json({
        success: false,
        error: 'Missing required field: message'
      });
    }

    businessLogger.log('Milhena chat request', {
      session_id,
      has_context: !!context
    });

    // Forward to Intelligence Engine
    const intelligenceResponse = await axios.post(
      `${INTELLIGENCE_ENGINE_URL}/api/chat`,
      {
        message,
        user_id: session_id || 'anonymous',
        context
      },
      {
        timeout: TIMEOUT,
        headers: {
          'Content-Type': 'application/json'
        }
      }
    );

    businessLogger.success('Milhena chat response', {
      session_id,
      category: intelligenceResponse.data.metadata?.supervisor_category,
      latency: intelligenceResponse.data.metadata?.processing_time
    });

    res.json({
      success: true,
      ...intelligenceResponse.data
    });

  } catch (error) {
    businessLogger.error('Milhena chat error:', {
      message: error.message,
      status: error.response?.status,
      data: error.response?.data
    });

    res.status(error.response?.status || 500).json({
      success: false,
      error: 'Failed to process chat message',
      message: error.response?.data?.detail || error.message
    });
  }
});

export default router;
