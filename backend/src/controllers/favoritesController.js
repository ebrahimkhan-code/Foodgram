const { Pool } = require('pg');
require('dotenv').config();

const pool = new Pool({
    user: process.env.DB_USER || 'postgres',
    host: process.env.DB_HOST || 'localhost',
    database: process.env.DB_NAME || 'foodgram',
    password: process.env.DB_PASSWORD,
    port: parseInt(process.env.DB_PORT) || 5432,
});

// ==================== ADD TO FAVORITES ====================
exports.addFavorite = async (req, res) => {
    try {
        const userId = req.user.id;
        const { foodId } = req.params;

        // Check if food exists
        const foodCheck = await pool.query(
            'SELECT id, name FROM foods WHERE id = $1',
            [foodId]
        );

        if (foodCheck.rows.length === 0) {
            return res.status(404).json({
                success: false,
                message: 'Food not found'
            });
        }

        // Add to favorites
        await pool.query(
            `INSERT INTO favorites (user_id, food_id)
             VALUES ($1, $2)
             ON CONFLICT (user_id, food_id) DO NOTHING`,
            [userId, foodId]
        );

        // Log interaction
        await pool.query(
            `INSERT INTO interactions (user_id, food_id, type)
             VALUES ($1, $2, $3)`,
            [userId, foodId, 'favorite_added']
        );

        res.json({
            success: true,
            message: 'Added to favorites',
            food: foodCheck.rows[0]
        });

    } catch (error) {
        console.error('Add favorite error:', error);
        res.status(500).json({
            success: false,
            message: 'Failed to add favorite',
            error: error.message
        });
    }
};

// ==================== REMOVE FROM FAVORITES ====================
exports.removeFavorite = async (req, res) => {
    try {
        const userId = req.user.id;
        const { foodId } = req.params;

        await pool.query(
            'DELETE FROM favorites WHERE user_id = $1 AND food_id = $2',
            [userId, foodId]
        );

        await pool.query(
            `INSERT INTO interactions (user_id, food_id, type)
             VALUES ($1, $2, $3)`,
            [userId, foodId, 'favorite_removed']
        );

        res.json({
            success: true,
            message: 'Removed from favorites'
        });

    } catch (error) {
        console.error('Remove favorite error:', error);
        res.status(500).json({
            success: false,
            message: 'Failed to remove favorite',
            error: error.message
        });
    }
};

// ==================== GET USER FAVORITES ====================
exports.getFavorites = async (req, res) => {
    try {
        const userId = req.user.id;

        const result = await pool.query(
            `SELECT f.*, 
                    fd.name, fd.description, fd.cuisine, fd.meal_type, fd.price, fd.image_url,
                    f.created_at as favorited_at
             FROM favorites f
             JOIN foods fd ON fd.id = f.food_id
             WHERE f.user_id = $1
             ORDER BY f.created_at DESC`,
            [userId]
        );

        res.json({
            success: true,
            count: result.rows.length,
            favorites: result.rows
        });

    } catch (error) {
        console.error('Get favorites error:', error);
        res.status(500).json({
            success: false,
            message: 'Failed to get favorites',
            error: error.message
        });
    }
};

// ==================== CHECK IF FAVORITE ====================
exports.checkFavorite = async (req, res) => {
    try {
        const userId = req.user.id;
        const { foodId } = req.params;

        const result = await pool.query(
            'SELECT id FROM favorites WHERE user_id = $1 AND food_id = $2',
            [userId, foodId]
        );

        res.json({
            success: true,
            is_favorite: result.rows.length > 0
        });

    } catch (error) {
        console.error('Check favorite error:', error);
        res.status(500).json({
            success: false,
            message: 'Failed to check favorite',
            error: error.message
        });
    }
};