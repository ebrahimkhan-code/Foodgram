const express = require('express');
const router = express.Router();
const { authenticate, optionalAuth } = require('../middleware/auth');

// Import controllers
const authController = require('../controllers/authController');
const orderController = require('../controllers/orderController');
const favoritesController = require('../controllers/favoritesController');

// ==================== AUTH ROUTES ====================
router.post('/auth/signup', authController.signup);
router.post('/auth/login', authController.login);
router.get('/auth/session-status', authController.checkSession);
router.get('/auth/profile', authenticate, authController.getProfile);
router.put('/auth/profile', authenticate, authController.updateProfile);

// ==================== ORDER ROUTES ====================
router.post('/orders', authenticate, orderController.createOrder);
router.get('/orders', authenticate, orderController.getUserOrders);
router.get('/orders/:orderId', authenticate, orderController.getOrderById);
router.put('/orders/:orderId/status', authenticate, orderController.updateOrderStatus);
router.put('/orders/:orderId/cancel', authenticate, orderController.cancelOrder);

// ==================== FAVORITES ROUTES ====================
router.get('/favorites', authenticate, favoritesController.getFavorites);
router.post('/favorites/:foodId', authenticate, favoritesController.addFavorite);
router.delete('/favorites/:foodId', authenticate, favoritesController.removeFavorite);
router.get('/favorites/:foodId/check', authenticate, favoritesController.checkFavorite);

module.exports = router;