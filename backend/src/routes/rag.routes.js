import express from 'express';
import axios from 'axios';
import businessLogger from '../utils/businessLogger.js';

const router = express.Router();

// Intelligence Engine URL (Docker internal network)
const INTELLIGENCE_ENGINE_URL = process.env.INTELLIGENCE_ENGINE_URL ||
  'http://pilotpros-intelligence-engine-dev:8000';

const TIMEOUT = 30000; // 30 seconds

/**
 * @route   GET /api/rag/stats
 * @desc    Get RAG knowledge base statistics
 * @access  Public
 */
router.get('/stats', async (req, res) => {
  try {
    businessLogger.log('RAG stats requested');

    const intelligenceResponse = await axios.get(
      `${INTELLIGENCE_ENGINE_URL}/api/rag/stats`,
      {
        timeout: TIMEOUT,
        headers: {
          'Content-Type': 'application/json'
        }
      }
    );

    res.json(intelligenceResponse.data);

  } catch (error) {
    businessLogger.error('RAG stats error:', {
      message: error.message,
      status: error.response?.status
    });

    res.status(error.response?.status || 500).json({
      error: 'Failed to get RAG statistics',
      message: error.response?.data?.detail || error.message
    });
  }
});

/**
 * @route   GET /api/rag/documents
 * @desc    Get all documents in knowledge base
 * @access  Public
 */
router.get('/documents', async (req, res) => {
  try {
    businessLogger.log('RAG documents list requested');

    const intelligenceResponse = await axios.get(
      `${INTELLIGENCE_ENGINE_URL}/api/rag/documents`,
      {
        timeout: TIMEOUT,
        headers: {
          'Content-Type': 'application/json'
        }
      }
    );

    res.json(intelligenceResponse.data);

  } catch (error) {
    businessLogger.error('RAG documents error:', {
      message: error.message,
      status: error.response?.status
    });

    res.status(error.response?.status || 500).json({
      error: 'Failed to get documents',
      message: error.response?.data?.detail || error.message
    });
  }
});

/**
 * @route   POST /api/rag/search
 * @desc    Semantic search in knowledge base
 * @access  Public
 */
router.post('/search', async (req, res) => {
  try {
    const { query, top_k } = req.body;

    if (!query) {
      return res.status(400).json({
        error: 'Missing required field: query'
      });
    }

    businessLogger.log('RAG semantic search', { query, top_k });

    const intelligenceResponse = await axios.post(
      `${INTELLIGENCE_ENGINE_URL}/api/rag/search`,
      { query, top_k: top_k || 10 },
      {
        timeout: TIMEOUT,
        headers: {
          'Content-Type': 'application/json'
        }
      }
    );

    res.json(intelligenceResponse.data);

  } catch (error) {
    businessLogger.error('RAG search error:', {
      message: error.message,
      status: error.response?.status
    });

    res.status(error.response?.status || 500).json({
      error: 'Search failed',
      message: error.response?.data?.detail || error.message
    });
  }
});

/**
 * @route   POST /api/rag/upload
 * @desc    Upload documents to knowledge base
 * @access  Public
 */
router.post('/upload', async (req, res) => {
  try {
    businessLogger.log('RAG document upload');

    // Forward the multipart/form-data directly to intelligence engine
    const intelligenceResponse = await axios.post(
      `${INTELLIGENCE_ENGINE_URL}/api/rag/upload`,
      req.body,
      {
        timeout: TIMEOUT,
        headers: {
          ...req.headers,
          'host': undefined // Remove host header
        }
      }
    );

    res.json(intelligenceResponse.data);

  } catch (error) {
    businessLogger.error('RAG upload error:', {
      message: error.message,
      status: error.response?.status
    });

    res.status(error.response?.status || 500).json({
      error: 'Upload failed',
      message: error.response?.data?.detail || error.message
    });
  }
});

/**
 * @route   DELETE /api/rag/documents/:id
 * @desc    Delete document from knowledge base
 * @access  Public
 */
router.delete('/documents/:id', async (req, res) => {
  try {
    const { id } = req.params;

    businessLogger.log('RAG document delete', { document_id: id });

    const intelligenceResponse = await axios.delete(
      `${INTELLIGENCE_ENGINE_URL}/api/rag/documents/${id}`,
      {
        timeout: TIMEOUT,
        headers: {
          'Content-Type': 'application/json'
        }
      }
    );

    res.json(intelligenceResponse.data);

  } catch (error) {
    businessLogger.error('RAG delete error:', {
      message: error.message,
      status: error.response?.status
    });

    res.status(error.response?.status || 500).json({
      error: 'Failed to delete document',
      message: error.response?.data?.detail || error.message
    });
  }
});

export default router;
