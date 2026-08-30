const { Pool } = require('pg');
const { v4: uuidv4 } = require('uuid');
require('dotenv').config();

const pool = new Pool({
    user: process.env.DB_USER || 'postgres',
    host: process.env.DB_HOST || 'localhost',
    database: process.env.DB_NAME || 'foodgram',
    password: process.env.DB_PASSWORD,
    port: parseInt(process.env.DB_PORT) || 5432,
});

// Generate order number
const generateOrderNumber = () => {
    const timestamp = Date.now().toString(36).toUpperCase();
    const random = Math.random().toString(36).substring(2, 6).toUpperCase();
    return `FOOD-${timestamp}-${random}`;
};

// ==================== CREATE ORDER ====================
exports.createOrder = async (req, res) => {
    try {
        const userId = req.user.id;
        const { 
            foodItems, 
            deliveryAddress, 
            specialInstructions,
            paymentMethod,
            sessionId 
        } = req.body;

        if (!foodItems || foodItems.length === 0) {
            return res.status(400).json({
                success: false,
                message: 'No items in order'
            });
        }

        // Calculate totals
        let subtotal = 0;
        const orderItems = [];

        for (const item of foodItems) {
            // Get food details from database
            const foodResult = await pool.query(
                'SELECT id, name, price FROM foods WHERE id = $1',
                [item.food_id]
            );

            if (foodResult.rows.length === 0) {
                return res.status(400).json({
                    success: false,
                    message: `Food item not found: ${item.food_id}`
                });
            }

            const food = foodResult.rows[0];
            const quantity = item.quantity || 1;
            const unitPrice = parseFloat(food.price) || 14.99;
            const totalPrice = unitPrice * quantity;

            subtotal += totalPrice;

            orderItems.push({
                food_id: food.id,
                food_name: food.name,
                quantity,
                unit_price: unitPrice,
                total_price: totalPrice,
                special_instructions: item.special_instructions || null
            });
        }

        const tax = subtotal * 0.08; // 8% tax
        const deliveryFee = subtotal > 30 ? 0 : 4.99;
        const totalAmount = subtotal + tax + deliveryFee;

        // Generate order number
        const orderNumber = generateOrderNumber();

        // Create order
        const orderResult = await pool.query(
            `INSERT INTO orders (
                order_number, user_id, session_id, status, 
                total_amount, subtotal, tax, delivery_fee,
                delivery_address, payment_method, special_instructions,
                created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            RETURNING *`,
            [
                orderNumber,
                userId,
                sessionId || null,
                'pending',
                totalAmount,
                subtotal,
                tax,
                deliveryFee,
                deliveryAddress || null,
                paymentMethod || 'card',
                specialInstructions || null
            ]
        );

        const order = orderResult.rows[0];

        // Create order items
        for (const item of orderItems) {
            await pool.query(
                `INSERT INTO order_items (
                    order_id, food_id, food_name, quantity,
                    unit_price, total_price, special_instructions
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)`,
                [
                    order.id,
                    item.food_id,
                    item.food_name,
                    item.quantity,
                    item.unit_price,
                    item.total_price,
                    item.special_instructions
                ]
            );
        }

        // Log interaction
        await pool.query(
            `INSERT INTO interactions (user_id, type, metadata)
             VALUES ($1, $2, $3)`,
            [userId, 'order_placed', JSON.stringify({ 
                order_id: order.id,
                order_number: order.order_number,
                total: totalAmount,
                items_count: orderItems.length
            })]
        );

        res.status(201).json({
            success: true,
            message: 'Order placed successfully!',
            order: {
                id: order.id,
                order_number: order.order_number,
                status: order.status,
                total_amount: parseFloat(order.total_amount),
                created_at: order.created_at,
                items: orderItems
            }
        });

    } catch (error) {
        console.error('Create order error:', error);
        res.status(500).json({
            success: false,
            message: 'Failed to create order',
            error: error.message
        });
    }
};

// ==================== GET USER ORDERS ====================
exports.getUserOrders = async (req, res) => {
    try {
        const userId = req.user.id;
        const { limit = 20, offset = 0, status } = req.query;

        let query = `
            SELECT o.*, 
                   COUNT(oi.id) as item_count,
                   json_agg(
                       json_build_object(
                           'id', oi.id,
                           'food_id', oi.food_id,
                           'food_name', oi.food_name,
                           'quantity', oi.quantity,
                           'unit_price', oi.unit_price,
                           'total_price', oi.total_price
                       )
                   ) as items
            FROM orders o
            LEFT JOIN order_items oi ON oi.order_id = o.id
            WHERE o.user_id = $1
        `;

        const values = [userId];
        let paramCount = 2;

        if (status) {
            query += ` AND o.status = $${paramCount}`;
            values.push(status);
            paramCount++;
        }

        query += `
            GROUP BY o.id
            ORDER BY o.created_at DESC
            LIMIT $${paramCount} OFFSET $${paramCount + 1}
        `;
        values.push(parseInt(limit), parseInt(offset));

        const result = await pool.query(query, values);

        // Get total count
        const countQuery = await pool.query(
            'SELECT COUNT(*) FROM orders WHERE user_id = $1',
            [userId]
        );

        res.json({
            success: true,
            orders: result.rows,
            total: parseInt(countQuery.rows[0].count),
            limit: parseInt(limit),
            offset: parseInt(offset)
        });

    } catch (error) {
        console.error('Get orders error:', error);
        res.status(500).json({
            success: false,
            message: 'Failed to get orders',
            error: error.message
        });
    }
};

// ==================== GET SINGLE ORDER ====================
exports.getOrderById = async (req, res) => {
    try {
        const userId = req.user.id;
        const { orderId } = req.params;

        const result = await pool.query(
            `SELECT o.*, 
                   COUNT(oi.id) as item_count,
                   json_agg(
                       json_build_object(
                           'id', oi.id,
                           'food_id', oi.food_id,
                           'food_name', oi.food_name,
                           'quantity', oi.quantity,
                           'unit_price', oi.unit_price,
                           'total_price', oi.total_price,
                           'special_instructions', oi.special_instructions
                       )
                   ) as items
            FROM orders o
            LEFT JOIN order_items oi ON oi.order_id = o.id
            WHERE o.id = $1 AND o.user_id = $2
            GROUP BY o.id`,
            [orderId, userId]
        );

        if (result.rows.length === 0) {
            return res.status(404).json({
                success: false,
                message: 'Order not found'
            });
        }

        res.json({
            success: true,
            order: result.rows[0]
        });

    } catch (error) {
        console.error('Get order error:', error);
        res.status(500).json({
            success: false,
            message: 'Failed to get order',
            error: error.message
        });
    }
};

// ==================== UPDATE ORDER STATUS ====================
exports.updateOrderStatus = async (req, res) => {
    try {
        const userId = req.user.id;
        const { orderId } = req.params;
        const { status } = req.body;

        const validStatuses = ['pending', 'confirmed', 'preparing', 'delivered', 'cancelled'];
        if (!validStatuses.includes(status)) {
            return res.status(400).json({
                success: false,
                message: 'Invalid status'
            });
        }

        // Check if order belongs to user
        const checkResult = await pool.query(
            'SELECT id, user_id FROM orders WHERE id = $1',
            [orderId]
        );

        if (checkResult.rows.length === 0) {
            return res.status(404).json({
                success: false,
                message: 'Order not found'
            });
        }

        if (checkResult.rows[0].user_id !== userId) {
            return res.status(403).json({
                success: false,
                message: 'Unauthorized'
            });
        }

        const result = await pool.query(
            `UPDATE orders 
             SET status = $1, updated_at = CURRENT_TIMESTAMP
             WHERE id = $2
             RETURNING *`,
            [status, orderId]
        );

        // Log interaction
        await pool.query(
            `INSERT INTO interactions (user_id, type, metadata)
             VALUES ($1, $2, $3)`,
            [userId, 'order_updated', JSON.stringify({ 
                order_id: orderId,
                new_status: status
            })]
        );

        res.json({
            success: true,
            message: 'Order status updated',
            order: result.rows[0]
        });

    } catch (error) {
        console.error('Update order error:', error);
        res.status(500).json({
            success: false,
            message: 'Failed to update order',
            error: error.message
        });
    }
};

// ==================== CANCEL ORDER ====================
exports.cancelOrder = async (req, res) => {
    try {
        const userId = req.user.id;
        const { orderId } = req.params;

        // Check if order belongs to user and is cancellable
        const checkResult = await pool.query(
            'SELECT id, status FROM orders WHERE id = $1 AND user_id = $2',
            [orderId, userId]
        );

        if (checkResult.rows.length === 0) {
            return res.status(404).json({
                success: false,
                message: 'Order not found'
            });
        }

        const order = checkResult.rows[0];
        if (order.status === 'delivered' || order.status === 'cancelled') {
            return res.status(400).json({
                success: false,
                message: `Cannot cancel order with status: ${order.status}`
            });
        }

        const result = await pool.query(
            `UPDATE orders 
             SET status = 'cancelled', updated_at = CURRENT_TIMESTAMP
             WHERE id = $1
             RETURNING *`,
            [orderId]
        );

        await pool.query(
            `INSERT INTO interactions (user_id, type, metadata)
             VALUES ($1, $2, $3)`,
            [userId, 'order_cancelled', JSON.stringify({ 
                order_id: orderId
            })]
        );

        res.json({
            success: true,
            message: 'Order cancelled successfully',
            order: result.rows[0]
        });

    } catch (error) {
        console.error('Cancel order error:', error);
        res.status(500).json({
            success: false,
            message: 'Failed to cancel order',
            error: error.message
        });
    }
};