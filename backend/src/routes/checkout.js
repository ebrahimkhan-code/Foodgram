// routes/checkout.js
const router = require('express').Router();

// Protected route - requires auth
router.post('/checkout', authenticate, async (req, res) => {
    const { sessionId, foodItems } = req.body;
    const userId = req.user.id;
    
    // Create order
    const order = await db.query(
        `INSERT INTO orders (session_id, user_id, food_items, status) 
         VALUES ($1, $2, $3, 'pending') RETURNING *`,
        [sessionId, userId, JSON.stringify(foodItems)]
    );
    
    // Log interaction
    await db.query(
        `INSERT INTO interactions (session_id, user_id, food_id, type) 
         VALUES ($1, $2, $3, 'order')`,
        [sessionId, userId, foodItems[0].food_id]
    );
    
    res.json({
        order_id: order.rows[0].id,
        message: 'Order placed successfully!',
        order: order.rows[0]
    });
});

module.exports = router;