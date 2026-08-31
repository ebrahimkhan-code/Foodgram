const express = require('express');
const router = express.Router();
const tasteController = require('../controllers/tasteController');

// Generate Taste DNA from game answers
router.post('/taste/generate', tasteController.generateTasteDNA);

// Update Taste DNA based on interaction
router.post('/taste/update', tasteController.updateTasteDNA);

// Get current Taste DNA
router.get('/taste/:sessionId', tasteController.getTasteDNA);

// Get taste history
router.get('/taste/:sessionId/history', tasteController.getTasteHistory);

module.exports = router;    