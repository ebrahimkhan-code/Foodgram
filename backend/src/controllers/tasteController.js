const { Pool } = require('pg');
const member1Service = require('../services/member1Service');

const pool = new Pool({
    user: process.env.DB_USER || 'postgres',
    host: process.env.DB_HOST || 'localhost',
    database: process.env.DB_NAME || 'foodgram',
    password: process.env.DB_PASSWORD,
    port: parseInt(process.env.DB_PORT) || 5432,
});

// ==================== GENERATE TASTE DNA ====================
exports.generateTasteDNA = async (req, res) => {
    try {
        const { sessionId, answers } = req.body;

        if (!answers || answers.length === 0) {
            return res.status(400).json({
                success: false,
                message: 'No answers provided'
            });
        }

        console.log(`🎮 Generating Taste DNA for session: ${sessionId}`);

        // Call Member1 service
        const result = await member1Service.generateTasteDNA(answers);

        if (!result.success) {
            throw new Error(result.error || 'Failed to generate Taste DNA');
        }

        const tasteDNA = result.taste_dna;

        // Save to database
        await pool.query(
            `UPDATE sessions 
             SET taste_dna = $1, 
                 game_responses = $2,
                 last_active = CURRENT_TIMESTAMP
             WHERE session_id = $3`,
            [JSON.stringify(tasteDNA), JSON.stringify(answers), sessionId]
        );

        // If user is logged in, also save to user
        const session = await pool.query(
            'SELECT user_id FROM sessions WHERE session_id = $1',
            [sessionId]
        );

        if (session.rows.length && session.rows[0].user_id) {
            await pool.query(
                'UPDATE users SET taste_dna = $1 WHERE id = $2',
                [JSON.stringify(tasteDNA), session.rows[0].user_id]
            );
        }

        res.json({
            success: true,
            taste_dna: tasteDNA,
            answers_processed: answers.length,
            session_id: sessionId
        });

    } catch (error) {
        console.error('Generate Taste DNA error:', error);
        res.status(500).json({
            success: false,
            message: 'Failed to generate Taste DNA',
            error: error.message
        });
    }
};

// ==================== UPDATE TASTE DNA ====================
exports.updateTasteDNA = async (req, res) => {
    try {
        const { sessionId, foodId, interactionType, rating } = req.body;

        // Get current taste DNA
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

        const currentDNA = session.rows[0].taste_dna || {};
        const userId = session.rows[0].user_id;

        // Get food attributes
        const food = await pool.query(
            'SELECT * FROM foods WHERE id = $1',
            [foodId]
        );

        if (!food.rows.length) {
            return res.status(404).json({
                success: false,
                message: 'Food not found'
            });
        }

        const foodData = food.rows[0];

        // Prepare interaction for Member1
        const interaction = {
            food_id: foodId,
            type: interactionType,
            rating: rating || null,
            food_attributes: {
                cuisine: foodData.cuisine,
                protein: foodData.protein,
                flavor: foodData.flavor,
                spice_level: foodData.spice_level,
                meal_type: foodData.meal_type
            }
        };

        // Update Taste DNA via Member1
        const result = await member1Service.updateTasteDNA(currentDNA, interaction);

        if (!result.success) {
            throw new Error(result.error || 'Failed to update Taste DNA');
        }

        const updatedDNA = result.taste_dna;

        // Save updated DNA
        await pool.query(
            'UPDATE sessions SET taste_dna = $1, last_active = CURRENT_TIMESTAMP WHERE session_id = $2',
            [JSON.stringify(updatedDNA), sessionId]
        );

        if (userId) {
            await pool.query(
                'UPDATE users SET taste_dna = $1 WHERE id = $2',
                [JSON.stringify(updatedDNA), userId]
            );
        }

        // Save interaction
        await pool.query(
            `INSERT INTO interactions (session_id, user_id, food_id, type, rating, created_at)
             VALUES ($1, $2, $3, $4, $5, CURRENT_TIMESTAMP)`,
            [sessionId, userId, foodId, interactionType, rating || null]
        );

        res.json({
            success: true,
            taste_dna: updatedDNA,
            interaction: interactionType,
            message: 'Taste DNA updated successfully'
        });

    } catch (error) {
        console.error('Update Taste DNA error:', error);
        res.status(500).json({
            success: false,
            message: 'Failed to update Taste DNA',
            error: error.message
        });
    }
};

// ==================== GET TASTE DNA ====================
exports.getTasteDNA = async (req, res) => {
    try {
        const { sessionId } = req.params;

        const session = await pool.query(
            'SELECT taste_dna FROM sessions WHERE session_id = $1',
            [sessionId]
        );

        if (!session.rows.length) {
            return res.status(404).json({
                success: false,
                message: 'Session not found'
            });
        }

        res.json({
            success: true,
            taste_dna: session.rows[0].taste_dna || {}
        });

    } catch (error) {
        console.error('Get Taste DNA error:', error);
        res.status(500).json({
            success: false,
            message: 'Failed to get Taste DNA',
            error: error.message
        });
    }
};

// ==================== GET TASTE HISTORY ====================
exports.getTasteHistory = async (req, res) => {
    try {
        const { sessionId } = req.params;

        const interactions = await pool.query(
            `SELECT i.*, f.name as food_name, f.cuisine, f.protein, f.flavor
             FROM interactions i
             JOIN foods f ON f.id = i.food_id
             WHERE i.session_id = $1
             ORDER BY i.created_at DESC
             LIMIT 50`,
            [sessionId]
        );

        res.json({
            success: true,
            history: interactions.rows
        });

    } catch (error) {
        console.error('Get taste history error:', error);
        res.status(500).json({
            success: false,
            message: 'Failed to get taste history',
            error: error.message
        });
    }
};