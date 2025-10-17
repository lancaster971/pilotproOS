import express from 'express';
import axios from 'axios';
import multer from 'multer';
import FormData from 'form-data';
import businessLogger from '../utils/businessLogger.js';

const router = express.Router();

// Intelligence Engine URL (Docker internal network)
const INTELLIGENCE_ENGINE_URL = process.env.INTELLIGENCE_ENGINE_URL ||
  'http://pilotpros-intelligence-engine-dev:8000';

const TIMEOUT = 30000; // 30 seconds

// Multer configuration for file uploads (memory storage)
const upload = multer({
  storage: multer.memoryStorage(),
  limits: {
    fileSize: 50 * 1024 * 1024, // 50MB max file size
    files: 10 // Max 10 files per request
  },
  fileFilter: (req, file, cb) => {
    // Accept only specific file types
    const allowedTypes = ['.pdf', '.docx', '.txt', '.md', '.html'];
    const ext = file.originalname.toLowerCase().substring(file.originalname.lastIndexOf('.'));

    if (allowedTypes.includes(ext)) {
      cb(null, true);
    } else {
      cb(new Error(`Unsupported file type: ${ext}. Allowed: ${allowedTypes.join(', ')}`));
    }
  }
});

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
    // DEBUG: Log what we receive
    console.log('🔍 RAG SEARCH REQUEST BODY:', JSON.stringify(req.body, null, 2));

    const { query, top_k } = req.body;

    if (!query) {
      console.log('❌ QUERY MISSING! Body was:', req.body);
      return res.status(400).json({
        error: 'Missing required field: query',
        received: req.body  // DEBUG: Show what we got
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
 * @route   POST /api/rag/documents
 * @desc    Upload documents to knowledge base (FIXED multipart/form-data)
 * @access  Public
 * @note    Aligned with Intelligence Engine endpoint naming
 */
router.post('/documents', upload.array('files'), async (req, res) => {
  try {
    if (!req.files || req.files.length === 0) {
      return res.status(400).json({
        error: 'No files uploaded',
        message: 'Please select at least one file to upload'
      });
    }

    businessLogger.log('RAG document upload', {
      files_count: req.files.length,
      total_size: req.files.reduce((sum, f) => sum + f.size, 0)
    });

    // Create FormData with files
    const formData = new FormData();

    // Append each file to FormData
    req.files.forEach((file) => {
      formData.append('files', file.buffer, {
        filename: file.originalname,
        contentType: file.mimetype
      });
    });

    // Append optional metadata from request body
    if (req.body.category) {
      formData.append('category', req.body.category);
    }
    if (req.body.tags) {
      formData.append('tags', req.body.tags);
    }
    if (req.body.auto_category !== undefined) {
      formData.append('auto_category', req.body.auto_category);
    }
    if (req.body.extract_metadata !== undefined) {
      formData.append('extract_metadata', req.body.extract_metadata);
    }

    // Forward to Intelligence Engine with proper headers
    const intelligenceResponse = await axios.post(
      `${INTELLIGENCE_ENGINE_URL}/api/rag/documents`,
      formData,
      {
        timeout: 300000, // 5 minutes for large uploads
        headers: {
          ...formData.getHeaders()
        },
        maxContentLength: Infinity,
        maxBodyLength: Infinity
      }
    );

    businessLogger.log('RAG upload success', {
      files_processed: req.files.length
    });

    res.json(intelligenceResponse.data);

  } catch (error) {
    businessLogger.error('RAG upload error:', {
      message: error.message,
      status: error.response?.status,
      detail: error.response?.data
    });

    // Handle specific errors
    if (error.code === 'LIMIT_FILE_SIZE') {
      return res.status(413).json({
        error: 'File too large',
        message: 'Maximum file size is 50MB'
      });
    }

    if (error.code === 'LIMIT_FILE_COUNT') {
      return res.status(413).json({
        error: 'Too many files',
        message: 'Maximum 10 files per upload'
      });
    }

    res.status(error.response?.status || 500).json({
      error: 'Upload failed',
      message: error.response?.data?.detail || error.message
    });
  }
});

/**
 * @route   GET /api/rag/documents/:id
 * @desc    Get single document by ID
 * @access  Public
 */
router.get('/documents/:id', async (req, res) => {
  try {
    const { id } = req.params;

    businessLogger.log('RAG document get', { document_id: id });

    const intelligenceResponse = await axios.get(
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
    businessLogger.error('RAG get document error:', {
      message: error.message,
      status: error.response?.status
    });

    res.status(error.response?.status || 500).json({
      error: 'Failed to get document',
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
