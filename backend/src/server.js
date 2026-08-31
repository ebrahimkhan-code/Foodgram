const express = require('express');
const cors = require('cors');
const dotenv = require('dotenv');
const { Pool } = require('pg');
const routes = require('./src/routes/index');
const gameRoutes = require('./src/routes/game');
const recommendationRoutes = require('./src/routes/recommendations');
const tasteRoutes = require('./src/routes/taste');


// Load environment variables
dotenv.config();

const app = express();
const PORT = process.env.PORT || 5000;

// Middleware
app.use(cors());
app.use(express.json());
app.use('/api', gameRoutes);
app.use('/api', recommendationRoutes);
app.use('/api', tasteRoutes);

// Database connection
const pool = new Pool({
    user: process.env.DB_USER || 'postgres',
    host: process.env.DB_HOST || 'localhost',
    database: process.env.DB_NAME || 'foodgram',
    password: process.env.DB_PASSWORD,
    port: parseInt(process.env.DB_PORT) || 5432,
});

// Health check
app.get('/api/health', async (req, res) => {
    try {
        const result = await pool.query('SELECT NOW()');
        const foodCount = await pool.query('SELECT COUNT(*) FROM foods');
        const userCount = await pool.query('SELECT COUNT(*) FROM users');
        const orderCount = await pool.query('SELECT COUNT(*) FROM orders');
        
        res.json({
            status: 'OK',
            timestamp: result.rows[0].now,
            database: 'Connected',
            stats: {
                foods: parseInt(foodCount.rows[0].count),
                users: parseInt(userCount.rows[0].count),
                orders: parseInt(orderCount.rows[0].count)
            }
        });
    } catch (error) {
        res.status(500).json({
            status: 'Error',
            message: error.message
        });
    }
});

// Get all foods (public)
app.get('/api/foods', async (req, res) => {
    try {
        const result = await pool.query('SELECT * FROM foods WHERE is_available = TRUE ORDER BY name');
        res.json({
            success: true,
            count: result.rows.length,
            foods: result.rows
        });
    } catch (error) {
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Get single food (public)
app.get('/api/foods/:id', async (req, res) => {
    try {
        const { id } = req.params;
        const result = await pool.query('SELECT * FROM foods WHERE id = $1', [id]);
        
        if (result.rows.length === 0) {
            return res.status(404).json({
                success: false,
                error: 'Food not found'
            });
        }
        
        res.json({
            success: true,
            food: result.rows[0]
        });
    } catch (error) {
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Game routes (public)
app.get('/api/game/questions', (req, res) => {
    // ... (keep your existing game questions)
    const questions = [
        {
            id: 'q1',
            type: 'food-vs-food',
            text: 'Which sounds more appealing?',
            options: [
                { id: 'opt1', text: 'Spicy Chicken Pasta', food_id: 'food-1' },
                { id: 'opt2', text: 'Truffle Mushroom Risotto', food_id: 'food-2' },
                { id: 'skip', text: 'Skip' }
            ]
        },
        // ... add all other questions
    ];
    res.json({ success: true, questions });
});

app.post('/api/game/responses', async (req, res) => {
    // ... (keep your existing game response handler)
    const { sessionId, responses } = req.body;
    
    // Generate taste DNA
    const tasteDNA = {
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
    
    // Save to session
    await pool.query(
        'UPDATE sessions SET taste_dna = $1, game_responses = $2 WHERE session_id = $3',
        [JSON.stringify(tasteDNA), JSON.stringify(responses), sessionId]
    );
    
    // Get recommendations
    const foods = await pool.query('SELECT * FROM foods WHERE is_available = TRUE LIMIT 8');
    const exploitation = foods.rows.slice(0, 4).map(f => ({
        food_id: f.id,
        name: f.name,
        description: f.description,
        cuisine: f.cuisine,
        price: f.price,
        image_url: f.image_url,
        score: 0.8 + Math.random() * 0.15,
        confidence: 'high',
        reason: `Based on your ${tasteDNA.spicy > 0.5 ? 'spicy' : 'savory'} preferences`
    }));
    
    const exploration = foods.rows.slice(4, 8).map(f => ({
        food_id: f.id,
        name: f.name,
        description: f.description,
        cuisine: f.cuisine,
        price: f.price,
        image_url: f.image_url,
        score: 0.6 + Math.random() * 0.2,
        confidence: 'medium',
        reason: 'Try something new!'
    }));
    
    res.json({
        success: true,
        session_id: sessionId,
        taste_dna: tasteDNA,
        recommendations: { exploitation, exploration },
        is_guest: true,
        message: 'Guest profile created! Login to save and order.'
    });
});

// Use all routes
app.use('/api', routes);

// Start server
app.listen(PORT, () => {
    console.log(`\n🚀 Server running on http://localhost:${PORT}`);
    console.log(`📊 Database: ${process.env.DB_NAME || 'foodgram'}`);
    console.log(`📡 Environment: ${process.env.NODE_ENV || 'development'}`);
    console.log(`\n📋 Available endpoints:`);
    console.log(`   GET  /api/health`);
    console.log(`   GET  /api/foods`);
    console.log(`   GET  /api/foods/:id`);
    console.log(`   GET  /api/game/questions`);
    console.log(`   POST /api/game/responses`);
    console.log(`   POST /api/auth/signup`);
    console.log(`   POST /api/auth/login`);
    console.log(`   GET  /api/auth/profile`);
    console.log(`   PUT  /api/auth/profile`);
    console.log(`   POST /api/orders`);
    console.log(`   GET  /api/orders`);
    console.log(`   GET  /api/orders/:orderId`);
    console.log(`   PUT  /api/orders/:orderId/status`);
    console.log(`   PUT  /api/orders/:orderId/cancel`);
    console.log(`   GET  /api/favorites`);
    console.log(`   POST /api/favorites/:foodId`);
    console.log(`   DELETE /api/favorites/:foodId`);
    console.log(`\n✅ Server ready!`);
});

module.exports = app;