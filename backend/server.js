const express = require('express');
const cors = require('cors');
const dotenv = require('dotenv');
const { Pool } = require('pg');
const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');

// Load environment variables
dotenv.config();

const app = express();
const PORT = process.env.PORT || 5000;

// Middleware
app.use(cors());
app.use(express.json());

// Request logging middleware
app.use((req, res, next) => {
    console.log(`📝 ${req.method} ${req.path}`);
    if (req.path.includes('/auth/')) {
        console.log(`   Body:`, { ...req.body, password: '***HIDDEN***' });
    }
    next();
});

// Database connection
const pool = new Pool({
    user: process.env.DB_USER || 'postgres',
    host: process.env.DB_HOST || 'localhost',
    database: process.env.DB_NAME || 'foodgram',
    password: process.env.DB_PASSWORD,
    port: parseInt(process.env.DB_PORT) || 5432,
});

// Test database connection
pool.connect((err, client, release) => {
    if (err) {
        console.error('❌ Database connection error:', err.message);
    } else {
        console.log('✅ Database connected successfully');
        release();
    }
});

// ==================== HELPER FUNCTIONS ====================

// Generate JWT Token
const generateToken = (userId, email) => {
    return jwt.sign(
        { id: userId, email },
        process.env.JWT_SECRET || 'your-secret-key-change-this',
        { expiresIn: '7d' }
    );
};

// Hash password
const hashPassword = async (password) => {
    const salt = await bcrypt.genSalt(10);
    return await bcrypt.hash(password, salt);
};

// ==================== HEALTH CHECK ====================
app.get('/api/health', async (req, res) => {
    try {
        const result = await pool.query('SELECT NOW()');
        const foodCount = await pool.query('SELECT COUNT(*) FROM foods');
        const userCount = await pool.query('SELECT COUNT(*) FROM users');
        res.json({
            status: 'OK',
            timestamp: result.rows[0].now,
            database: 'Connected',
            stats: {
                foods: parseInt(foodCount.rows[0].count),
                users: parseInt(userCount.rows[0].count)
            }
        });
    } catch (error) {
        res.status(500).json({
            status: 'Error',
            message: error.message
        });
    }
});

// ==================== SESSION STATUS ====================
app.get('/api/auth/session-status', async (req, res) => {
    try {
        const { sessionId } = req.query;

        console.log(`🔍 Session status check for: ${sessionId}`);

        if (!sessionId) {
            return res.json({
                is_guest: true,
                is_converted: false,
                user_id: null
            });
        }

        // Check if session exists
        const result = await pool.query(
            'SELECT user_id, is_converted FROM sessions WHERE session_id = $1',
            [sessionId]
        );

        if (result.rows.length === 0) {
            // Create session if it doesn't exist
            await pool.query(
                'INSERT INTO sessions (session_id, is_converted) VALUES ($1, $2)',
                [sessionId, false]
            );
            
            return res.json({
                is_guest: true,
                is_converted: false,
                user_id: null
            });
        }

        const session = result.rows[0];

        res.json({
            is_guest: !session.user_id,
            is_converted: session.is_converted || false,
            user_id: session.user_id || null
        });

    } catch (error) {
        console.error('Session status error:', error);
        res.status(500).json({
            success: false,
            message: 'Failed to check session status',
            error: error.message
        });
    }
});

// ==================== AUTH ROUTES - REAL DATABASE ====================

// SIGNUP - Real Database
app.post('/api/auth/signup', async (req, res) => {
    const { email, password, name, sessionId } = req.body;
    
    try {
        console.log(`📝 Signup attempt for: ${email}`);

        // Validate input
        if (!email || !password) {
            return res.status(400).json({
                success: false,
                message: 'Email and password are required'
            });
        }

        if (password.length < 6) {
            return res.status(400).json({
                success: false,
                message: 'Password must be at least 6 characters'
            });
        }

        // Check if user exists in database
        const userCheck = await pool.query(
            'SELECT id, email FROM users WHERE email = $1',
            [email.toLowerCase()]
        );

        if (userCheck.rows.length > 0) {
            console.log(`❌ User already exists: ${email}`);
            return res.status(400).json({
                success: false,
                message: 'User already exists with this email'
            });
        }

        // Hash password
        const hashedPassword = await hashPassword(password);

        // Create user in database
        const result = await pool.query(
            `INSERT INTO users (email, password_hash, name, session_id, created_at, last_login)
             VALUES ($1, $2, $3, $4, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
             RETURNING id, email, name, session_id, taste_dna, created_at`,
            [email.toLowerCase(), hashedPassword, name || email.split('@')[0], sessionId || null]
        );

        const user = result.rows[0];
        console.log(`✅ User created: ${user.email}`);

        // Link session to user if session exists
        if (sessionId) {
            await pool.query(
                'UPDATE sessions SET user_id = $1, is_converted = TRUE WHERE session_id = $2',
                [user.id, sessionId]
            );

            // Copy taste DNA from session to user
            const session = await pool.query(
                'SELECT taste_dna FROM sessions WHERE session_id = $1',
                [sessionId]
            );

            if (session.rows.length && session.rows[0].taste_dna) {
                await pool.query(
                    'UPDATE users SET taste_dna = $1 WHERE id = $2',
                    [session.rows[0].taste_dna, user.id]
                );
                user.taste_dna = session.rows[0].taste_dna;
            }
        }

        // Generate token
        const token = generateToken(user.id, user.email);

        res.status(201).json({
            success: true,
            message: 'Account created successfully!',
            token,
            user: {
                id: user.id,
                email: user.email,
                name: user.name,
                taste_dna: user.taste_dna || {},
                created_at: user.created_at
            },
            session_linked: !!sessionId
        });

    } catch (error) {
        console.error('Signup error:', error);
        res.status(500).json({
            success: false,
            message: 'Failed to create account',
            error: error.message
        });
    }
});

// LOGIN - Real Database Validation
app.post('/api/auth/login', async (req, res) => {
    const { email, password, sessionId } = req.body;

    try {
        console.log(`🔍 Login attempt for: ${email}`);

        // Validate input
        if (!email || !password) {
            return res.status(400).json({
                success: false,
                message: 'Email and password are required'
            });
        }

        // FIND USER IN DATABASE
        const result = await pool.query(
            'SELECT * FROM users WHERE email = $1',
            [email.toLowerCase()]
        );

        // If user doesn't exist in database
        if (result.rows.length === 0) {
            console.log(`❌ User not found: ${email}`);
            return res.status(401).json({
                success: false,
                message: 'Invalid email or password'
            });
        }

        const user = result.rows[0];
        console.log(`✅ User found: ${user.email}`);

        // COMPARE PASSWORD WITH HASHED PASSWORD IN DATABASE
        const validPassword = await bcrypt.compare(password, user.password_hash);
        
        if (!validPassword) {
            console.log(`❌ Invalid password for: ${email}`);
            return res.status(401).json({
                success: false,
                message: 'Invalid email or password'
            });
        }

        console.log(`✅ Password valid for: ${email}`);

        // Update last login
        await pool.query(
            'UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = $1',
            [user.id]
        );

        // Link session to user if provided
        if (sessionId) {
            await pool.query(
                'UPDATE sessions SET user_id = $1, is_converted = TRUE WHERE session_id = $2',
                [user.id, sessionId]
            );

            // Copy taste DNA from session if user doesn't have it
            if (!user.taste_dna || Object.keys(user.taste_dna).length === 0) {
                const session = await pool.query(
                    'SELECT taste_dna FROM sessions WHERE session_id = $1',
                    [sessionId]
                );
                if (session.rows.length && session.rows[0].taste_dna) {
                    await pool.query(
                        'UPDATE users SET taste_dna = $1 WHERE id = $2',
                        [session.rows[0].taste_dna, user.id]
                    );
                    user.taste_dna = session.rows[0].taste_dna;
                }
            }
        }

        // Generate token
        const token = generateToken(user.id, user.email);

        // Log successful login
        await pool.query(
            `INSERT INTO interactions (user_id, type, metadata)
             VALUES ($1, $2, $3)`,
            [user.id, 'login', JSON.stringify({ 
                timestamp: new Date().toISOString(),
                sessionId: sessionId || null 
            })]
        );

        console.log(`✅ Login successful for: ${email}`);

        res.json({
            success: true,
            message: 'Login successful!',
            token,
            user: {
                id: user.id,
                email: user.email,
                name: user.name || user.email.split('@')[0],
                taste_dna: user.taste_dna || {},
                created_at: user.created_at,
                last_login: user.last_login
            },
            session_linked: !!sessionId
        });

    } catch (error) {
        console.error('Login error:', error);
        res.status(500).json({
            success: false,
            message: 'Login failed',
            error: error.message
        });
    }
});

// ==================== FOODS ROUTES ====================

// Get all foods
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

// Get single food by ID
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

// Get foods by cuisine
app.get('/api/foods/cuisine/:cuisine', async (req, res) => {
    try {
        const { cuisine } = req.params;
        const result = await pool.query(
            'SELECT * FROM foods WHERE cuisine ILIKE $1 ORDER BY name',
            [`%${cuisine}%`]
        );
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

// Get foods by meal type
app.get('/api/foods/meal/:type', async (req, res) => {
    try {
        const { type } = req.params;
        const result = await pool.query(
            'SELECT * FROM foods WHERE meal_type ILIKE $1 ORDER BY name',
            [`%${type}%`]
        );
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

// ==================== GAME ROUTES ====================

// Get game questions
app.get('/api/game/questions', (req, res) => {
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
                { id: 'opt3', text: 'Asian 🥡', food_id: 'food-5' },
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
                { id: 'opt2', text: 'Mediterranean Bowl', food_id: 'food-4' },
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
    
    res.json({
        success: true,
        questions: questions
    });
});

// Submit game responses
app.post('/api/game/responses', async (req, res) => {
    try {
        const { sessionId, responses } = req.body;
        
        // Generate taste DNA
        const tasteDNA = {
            spicy: 0.6 + Math.random() * 0.3,
            savory: 0.5 + Math.random() * 0.4,
            sweet: 0.3 + Math.random() * 0.4,
            comfort: 0.4 + Math.random() * 0.4,
            adventurous: 0.5 + Math.random() * 0.4,
            healthy: 0.3 + Math.random() * 0.3,
            cuisines: { Italian: 0.6, Mexican: 0.4, Asian: 0.5 },
            proteins: { chicken: 0.7, beef: 0.4, fish: 0.3, vegetarian: 0.2 },
            meal_types: { dinner: 0.7, lunch: 0.5, snack: 0.3 },
            created_at: new Date().toISOString()
        };

        // Save to session
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
        const foods = await pool.query('SELECT * FROM foods WHERE is_available = TRUE LIMIT 8');
        const exploitation = foods.rows.slice(0, 4).map(f => ({
            food_id: f.id,
            name: f.name,
            description: f.description,
            cuisine: f.cuisine,
            price: f.price || 14.99,
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
            price: f.price || 14.99,
            image_url: f.image_url,
            score: 0.6 + Math.random() * 0.2,
            confidence: 'medium',
            reason: 'Try something new!'
        }));
        
        res.json({
            success: true,
            session_id: sessionId,
            taste_dna: tasteDNA,
            recommendations: {
                exploitation: exploitation,
                exploration: exploration
            },
            is_guest: true,
            message: 'Guest profile created! Login to save and order.'
        });
        
    } catch (error) {
        console.error('Game response error:', error);
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// ==================== CHECKOUT ROUTE ====================

app.post('/api/checkout', async (req, res) => {
    try {
        const { sessionId, foodItems } = req.body;
        
        // Check if user is logged in (has token)
        const authHeader = req.headers.authorization;
        let userId = null;
        
        if (authHeader) {
            try {
                const token = authHeader.split(' ')[1];
                const decoded = jwt.verify(token, process.env.JWT_SECRET || 'your-secret-key-change-this');
                userId = decoded.id;
            } catch (e) {
                // Token invalid, continue as guest
            }
        }
        
        const orderNumber = `ORD-${Date.now().toString(36).toUpperCase()}`;
        
        res.json({
            success: true,
            order_id: 'order-' + Date.now(),
            order_number: orderNumber,
            message: 'Order placed successfully!',
            order: {
                id: 'order-' + Date.now(),
                order_number: orderNumber,
                user_id: userId,
                session_id: sessionId,
                items: foodItems,
                status: 'pending',
                total: 14.99,
                created_at: new Date().toISOString()
            }
        });
    } catch (error) {
        console.error('Checkout error:', error);
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// ==================== START SERVER ====================

app.listen(PORT, () => {
    console.log(`\n🚀 Server running on http://localhost:${PORT}`);
    console.log(`📊 Database: ${process.env.DB_NAME || 'foodgram'}`);
    console.log(`📡 Environment: ${process.env.NODE_ENV || 'development'}`);
    console.log(`\n📋 Available endpoints:`);
    console.log(`   GET  /api/health`);
    console.log(`   GET  /api/auth/session-status`);
    console.log(`   POST /api/auth/signup`);
    console.log(`   POST /api/auth/login`);
    console.log(`   GET  /api/foods`);
    console.log(`   GET  /api/foods/:id`);
    console.log(`   GET  /api/foods/cuisine/:cuisine`);
    console.log(`   GET  /api/foods/meal/:type`);
    console.log(`   GET  /api/game/questions`);
    console.log(`   POST /api/game/responses`);
    console.log(`   POST /api/checkout`);
    console.log(`\n✅ Server ready!`);
});

module.exports = app;