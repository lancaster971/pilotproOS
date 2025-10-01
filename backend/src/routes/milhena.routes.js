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
      `${INTELLIGENCE_ENGINE_URL}/api/milhena/stats`,
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

export default router;
