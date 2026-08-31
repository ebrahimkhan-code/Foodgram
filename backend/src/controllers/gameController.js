const { Pool } = require('pg');
const member1Service = require('../services/member1Service');

const pool = new Pool({
    user: process.env.DB_USER || 'postgres',
    host: process.env.DB_HOST || 'localhost',
    database: process.env.DB_NAME || 'foodgram',
    password: process.env.DB_PASSWORD,
    port: parseInt(process.env.DB_PORT) || 5432,
});

// ==================== GET GAME QUESTIONS ====================
exports.getQuestions = async (req, res) => {
    try {
        // Try to get questions from Member1
        const result = await member1Service.getGameQuestions();

        if (result.success) {
            return res.json({
                success: true,
                questions: result.questions,
                total: result.total || result.questions?.length || 0
            });
        }

        // Fallback questions
        const fallbackQuestions = [
            {
                id: 'q1',
                type: 'cuisine',
                text: 'Which cuisine do you prefer?',
                options: [
                    { id: 'cuisine_italian', text: 'Italian 🍝', value: 'italian' },
                    { id: 'cuisine_mexican', text: 'Mexican 🌮', value: 'mexican' },
                    { id: 'cuisine_chinese', text: 'Chinese 🥡', value: 'chinese' },
                    { id: 'cuisine_indian', text: 'Indian 🍛', value: 'indian' }
                ]
            },
            {
                id: 'q2',
                type: 'protein',
                text: 'What protein do you prefer?',
                options: [
                    { id: 'protein_chicken', text: 'Chicken 🐔', value: 'chicken' },
                    { id: 'protein_beef', text: 'Beef 🥩', value: 'beef' },
                    { id: 'protein_fish', text: 'Fish 🐟', value: 'fish' },
                    { id: 'protein_vegetarian', text: 'Vegetarian 🌱', value: 'vegetarian' }
                ]
            },
            {
                id: 'q3',
                type: 'flavor',
                text: 'Which flavor profile do you enjoy?',
                options: [
                    { id: 'flavor_savory', text: 'Savory 🧂', value: 'savory' },
                    { id: 'flavor_spicy', text: 'Spicy 🌶️', value: 'spicy' },
                    { id: 'flavor_sweet', text: 'Sweet 🍯', value: 'sweet' },
                    { id: 'flavor_smoky', text: 'Smoky 🔥', value: 'smoky' }
                ]
            },
            {
                id: 'q4',
                type: 'spice_level',
                text: 'How spicy do you like your food?',
                options: [
                    { id: 'spice_mild', text: 'Mild 🌶️', value: 'mild' },
                    { id: 'spice_medium', text: 'Medium 🌶️🌶️', value: 'medium' },
                    { id: 'spice_hot', text: 'Hot 🌶️🌶️🌶️', value: 'hot' },
                    { id: 'spice_extra_hot', text: 'Extra Hot 🔥🔥🔥', value: 'extra_hot' }
                ]
            },
            {
                id: 'q5',
                type: 'meal_type',
                text: 'What meal are you looking for?',
                options: [
                    { id: 'meal_breakfast', text: 'Breakfast 🍳', value: 'breakfast' },
                    { id: 'meal_lunch', text: 'Lunch 🥗', value: 'lunch' },
                    { id: 'meal_dinner', text: 'Dinner 🍽️', value: 'dinner' },
                    { id: 'meal_dessert', text: 'Dessert 🍰', value: 'dessert' }
                ]
            },
            {
                id: 'q6',
                type: 'food-vs-food',
                text: 'Which sounds more appealing?',
                options: [
                    { id: 'opt1', text: 'Spicy Chicken Pasta', food_id: 'food-1' },
                    { id: 'opt2', text: 'Truffle Mushroom Risotto', food_id: 'food-2' },
                    { id: 'skip', text: 'Skip' }
                ]
            },
            {
                id: 'q7',
                type: 'mood',
                text: 'What are you in the mood for?',
                options: [
                    { id: 'mood_comfort', text: 'Comfort food 🥘', value: 'comfort' },
                    { id: 'mood_adventurous', text: 'Adventurous 🧭', value: 'adventurous' },
                    { id: 'mood_healthy', text: 'Healthy 🥬', value: 'healthy' },
                    { id: 'mood_quick', text: 'Quick bite ⏱️', value: 'quick' }
                ]
            }
        ];

        res.json({
            success: true,
            questions: fallbackQuestions,
            total: fallbackQuestions.length,
            is_fallback: true
        });

    } catch (error) {
        console.error('Get questions error:', error);
        res.status(500).json({
            success: false,
            message: 'Failed to get game questions',
            error: error.message
        });
    }
};

// ==================== SUBMIT GAME RESPONSES ====================
exports.submitResponses = async (req, res) => {
    try {
        const { sessionId, responses } = req.body;

        if (!responses || responses.length === 0) {
            return res.status(400).json({
                success: false,
                message: 'No responses provided'
            });
        }

        console.log(`🎮 Processing ${responses.length} game responses for session: ${sessionId}`);

        // Convert responses to answers format for Member1
        const answers = responses.map(r => ({
            attribute: r.questionType || r.type || 'cuisine',
            value: r.optionValue || r.value || r.optionId,
            preference: r.preference || 1
        }));

        // Call Member1 to generate Taste DNA
        const result = await member1Service.generateTasteDNA(answers);

        if (!result.success) {
            throw new Error(result.error || 'Failed to generate Taste DNA');
        }

        const tasteDNA = result.taste_dna;

        // Save to database
        await pool.query(
            `INSERT INTO sessions (session_id, taste_dna, game_responses, last_active)
             VALUES ($1, $2, $3, CURRENT_TIMESTAMP)
             ON CONFLICT (session_id) 
             DO UPDATE SET 
                 taste_dna = $2, 
                 game_responses = $3,
                 last_active = CURRENT_TIMESTAMP`,
            [sessionId, JSON.stringify(tasteDNA), JSON.stringify(responses)]
        );

        // Get recommendations
        const recResult = await member1Service.getRecommendations(tasteDNA, [], {}, 8);

        const recommendations = recResult.success ? recResult.recommendations : [];

        res.json({
            success: true,
            session_id: sessionId,
            taste_dna: tasteDNA,
            recommendations: recommendations,
            answers_processed: answers.length,
            is_guest: true,
            message: 'Taste profile created! Login to save and order.'
        });

    } catch (error) {
        console.error('Submit game responses error:', error);
        res.status(500).json({
            success: false,
            message: 'Failed to process game responses',
            error: error.message
        });
    }
};