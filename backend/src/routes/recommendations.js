const express = require('express');
const router = express.Router();
const recommendationController = require('../controllers/recommendationController');

// Get personalized recommendations
router.get('/recommendations', recommendationController.getRecommendations);

// Get exploration recommendations
router.get('/recommendations/explore', recommendationController.getExplorationRecommendations);

module.exports = router;