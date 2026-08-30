// routes/game.js
const router = require('express').Router();
const { v4: uuidv4 } = require('uuid');

// Get game questions (5-7 rounds)
router.get('/game/questions', (req, res) => {
    // Return demo questions
    const questions = [
        {
            id: 'q1',
            type: 'food-vs-food',
            text: 'Which sounds more appealing?',
            options: [
                { id: 'opt1', text: 'Spicy Chicken Pasta', food_id: 'food-1' },
                { id: 'opt2', text: 'Truffle Risotto', food_id: 'food-2' },
                { id: 'skip', text: 'Skip' }
            ]
        },
        {
            id: 'q2',
            type: 'flavor-vs-flavor',
            text: 'Which flavor do you prefer?',
            options: [
                { id: 'opt1', text: 'Spicy 🌶️' },
                { id: 'opt2', text: 'Savory 🧂' },
                { id: 'opt3', text: 'Sweet 🍯' },
                { id: 'skip', text: 'Skip' }
            ]
        },
        {
            id: 'q3',
            type: 'mood-context',
            text: 'What are you in the mood for?',
            options: [
                { id: 'opt1', text: 'Comfort food' },
                { id: 'opt2', text: 'Adventurous dish' },
                { id: 'opt3', text: 'Healthy option' },
                { id: 'skip', text: 'Skip' }
            ]
        },
        {
            id: 'q4',
            type: 'food-vs-food',
            text: 'Pick your favorite cuisine vibe:',
            options: [
                { id: 'opt1', text: 'Italian 🍝', food_id: 'food-2' },
                { id: 'opt2', text: 'Mexican 🌮', food_id: 'food-3' },
                { id: 'opt3', text: 'Asian 🥡', food_id: 'food-4' },
                { id: 'skip', text: 'Skip' }
            ]
        },
        {
            id: 'q5',
            type: 'flavor-vs-flavor',
            text: 'Choose your protein preference:',
            options: [
                { id: 'opt1', text: 'Chicken' },
                { id: 'opt2', text: 'Beef' },
                { id: 'opt3', text: 'Fish' },
                { id: 'opt4', text: 'Vegetarian' },
                { id: 'skip', text: 'Skip' }
            ]
        },
        {
            id: 'q6',
            type: 'food-vs-food',
            text: 'Which dish catches your eye?',
            options: [
                { id: 'opt1', text: 'Korean BBQ Tacos', food_id: 'food-3' },
                { id: 'opt2', text: 'Mediterranean Bowl', food_id: 'food-5' },
                { id: 'skip', text: 'Skip' }
            ]
        },
        {
            id: 'q7',
            type: 'mood-context',
            text: 'How hungry are you?',
            options: [
                { id: 'opt1', text: 'Just a snack' },
                { id: 'opt2', text: 'Full meal' },
                { id: 'opt3', text: 'Something light' },
                { id: 'skip', text: 'Skip' }
            ]
        }
    ];
    
    res.json({ questions: questions.slice(0, 7) }); // 7 rounds max
});

// Submit game responses - Guest Mode (NO AUTH)
router.post('/game/responses', async (req, res) => {
    const { sessionId, responses } = req.body;
    
    // Validate session exists or create new
    let session = await db.query(
        'SELECT * FROM sessions WHERE session_id = $1',
        [sessionId]
    );
    
    if (!session.rows.length) {
        await db.query(
            'INSERT INTO sessions (session_id, game_responses) VALUES ($1, $2)',
            [sessionId, JSON.stringify(responses)]
        );
    } else {
        await db.query(
            'UPDATE sessions SET game_responses = $1 WHERE session_id = $2',
            [JSON.stringify(responses), sessionId]
        );
    }
    
    // Generate Taste DNA based on responses (MOCK)
    const tasteDNA = generateTasteDNA(responses);
    
    // Update session with taste DNA
    await db.query(
        'UPDATE sessions SET taste_dna = $1 WHERE session_id = $2',
        [JSON.stringify(tasteDNA), sessionId]
    );
    
    // Get recommendations based on taste DNA
    const recommendations = await getRecommendations(tasteDNA, sessionId);
    
    res.json({
        taste_dna: tasteDNA,
        recommendations: recommendations,
        session_id: sessionId,
        is_guest: true,
        message: 'Guest profile created! Login to save and order.'
    });
});

// Generate Taste DNA (MOCK - Member 1 integration)
function generateTasteDNA(responses) {
    // Simple mock - in reality, this would use Member 1's algorithm
    const dna = {
        spicy: 0.6,
        savory: 0.7,
        sweet: 0.4,
        comfort: 0.5,
        adventurous: 0.6,
        healthy: 0.3,
        cuisines: { Italian: 0.6, Mexican: 0.4, Asian: 0.5 },
        proteins: { chicken: 0.7, beef: 0.4, fish: 0.3, vegetarian: 0.2 },
        meal_types: { dinner: 0.7, lunch: 0.5, snack: 0.3 },
        created_at: new Date().toISOString()
    };
    
    // Adjust based on responses
    responses.forEach(r => {
        if (r.optionId === 'opt1' && r.questionId === 'q1') dna.spicy += 0.2;
        if (r.optionId === 'opt2' && r.questionId === 'q2') dna.savory += 0.2;
        // ... more logic
    });
    
    return dna;
}

// Get recommendations (MOCK - Member 1 integration)
async function getRecommendations(tasteDNA, sessionId) {
    // Demo recommendations based on taste DNA
    const foods = await db.query('SELECT * FROM foods LIMIT 10');
    
    // Simple scoring - in reality, use Member 1's algorithm
    const exploitation = foods.rows.slice(0, 4).map(f => ({
        food_id: f.id,
        score: 0.8 + Math.random() * 0.15,
        confidence: 'high',
        reason: `Based on your ${tasteDNA.spicy > 0.5 ? 'spicy' : 'savory'} preferences`
    }));
    
    const exploration = foods.rows.slice(4, 8).map(f => ({
        food_id: f.id,
        score: 0.6 + Math.random() * 0.2,
        confidence: 'medium',
        reason: 'Try something new!'
    }));
    
    // Store in recommendations table
    const allRecs = [...exploitation, ...exploration];
    for (const rec of allRecs) {
        await db.query(
            `INSERT INTO recommendations (session_id, food_id, score, confidence_class, reason, type) 
             VALUES ($1, $2, $3, $4, $5, $6)`,
            [sessionId, rec.food_id, rec.score, rec.confidence, rec.reason, 
             allRecs.indexOf(rec) < 4 ? 'exploitation' : 'exploration']
        );
    }
    
    return { exploitation, exploration };
}

module.exports = router;