const { Pool } = require('pg');
const member1Service = require('../services/member1Service');

const pool = new Pool({
    user: process.env.DB_USER || 'postgres',
    host: process.env.DB_HOST || 'localhost',
    database: process.env.DB_NAME || 'foodgram',
    password: process.env.DB_PASSWORD,
    port: parseInt(process.env.DB_PORT) || 5432,
});

// ==================== GET RECOMMENDATIONS ====================
exports.getRecommendations = async (req, res) => {
    try {
        const { sessionId, limit = 10 } = req.query;

        // Get session data
        const session = await pool.query(
            'SELECT taste_dna, user_id FROM sessions WHERE session_id = $1',
            [sessionId]
        );

        if (!session.rows.length) {
            return res.status(404).json({
                success: false,
                message: 'Session not found'
            });
        }

        const tasteDNA = session.rows[0].taste_dna || {};
        const userId = session.rows[0].user_id;

        // Get interaction history
        const history = await pool.query(
            `SELECT food_id, type, rating, created_at
             FROM interactions
             WHERE session_id = $1
             ORDER BY created_at DESC
             LIMIT 50`,
            [sessionId]
        );

        // Get context (time-based)
        const now = new Date();
        const context = {
            hour: now.getHours(),
            day_of_week: now.getDay(),
            timestamp: now.toISOString()
        };

        // Call Member1 for recommendations
        const result = await member1Service.getRecommendations(
            tasteDNA,
            history.rows,
            context,
            parseInt(limit)
        );

        if (!result.success) {
            throw new Error(result.error || 'Failed to get recommendations');
        }

        // Save recommendations to cache
        for (const rec of result.recommendations || []) {
            await pool.query(
                `INSERT INTO recommendations (session_id, user_id, food_id, score, confidence_class, reason, type)
                 VALUES ($1, $2, $3, $4, $5, $6, $7)
                 ON CONFLICT (session_id, food_id) DO UPDATE SET
                     score = EXCLUDED.score,
                     confidence_class = EXCLUDED.confidence_class,
                     reason = EXCLUDED.reason,
                     created_at = CURRENT_TIMESTAMP`,
                [
                    sessionId,
                    userId || null,
                    rec.foodId || rec.food_id,
                    rec.score || 0,
                    rec.confidence || 'medium',
                    rec.reason || 'Recommended for you',
                    'exploitation'
                ]
            );
        }

        res.json({
            success: true,
            recommendations: result.recommendations || [],
            count: result.count || 0,
            session_id: sessionId
        });

    } catch (error) {
        console.error('Get recommendations error:', error);
        res.status(500).json({
            success: false,
            message: 'Failed to get recommendations',
            error: error.message
        });
    }
};

// ==================== GET EXPLORATION RECOMMENDATIONS ====================
exports.getExplorationRecommendations = async (req, res) => {
    try {
        const { sessionId, limit = 8 } = req.query;

        // Get session data
        const session = await pool.query(
            'SELECT taste_dna, user_id FROM sessions WHERE session_id = $1',
            [sessionId]
        );

        if (!session.rows.length) {
            return res.status(404).json({
                success: false,
                message: 'Session not found'
            });
        }

        const tasteDNA = session.rows[0].taste_dna || {};

        // Get interaction history (exclude foods already seen)
        const history = await pool.query(
            `SELECT food_id, type, created_at
             FROM interactions
             WHERE session_id = $1
             ORDER BY created_at DESC
             LIMIT 30`,
            [sessionId]
        );

        // Call Member1 for exploration recommendations
        const result = await member1Service.getExplorationRecommendations(
            tasteDNA,
            history.rows,
            parseInt(limit)
        );

        if (!result.success) {
            throw new Error(result.error || 'Failed to get exploration recommendations');
        }

        res.json({
            success: true,
            recommendations: result.recommendations || [],
            count: result.count || 0,
            session_id: sessionId
        });

    } catch (error) {
        console.error('Get exploration recommendations error:', error);
        res.status(500).json({
            success: false,
            message: 'Failed to get exploration recommendations',
            error: error.message
        });
    }
};