const express = require('express');
const cors = require('cors');
const dotenv = require('dotenv');
const { Pool } = require('pg');
const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');
const member1Service = require('./src/services/member1Service');
const member2Service = require('./src/services/member2Service');
const catalogRecommender = require('./src/services/catalogRecommender');

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

// ==================== SCHEMA BOOTSTRAP ====================
// Ensure the tables/columns the app needs exist. This runs on boot and is
// idempotent (IF NOT EXISTS), so the user never has to run a manual migration
// for the new favorites / orders / profile features.
//
// NOTE: recommendations come from the enriched CSV catalog, whose food_id
// values (e.g. "x8l5__beef-gyro") are NOT rows in the Postgres `foods` table.
// So user_favorites / user_orders store the dish snapshot as JSONB instead of
// a foreign key into `foods` — favorites & orders work for any recommended
// dish regardless of whether it was ever seeded into `foods`.
const ensureSchema = async () => {
    try {
        await pool.query(`ALTER TABLE users ADD COLUMN IF NOT EXISTS first_name VARCHAR(100)`);
        await pool.query(`ALTER TABLE users ADD COLUMN IF NOT EXISTS last_name VARCHAR(100)`);

        await pool.query(`
            CREATE TABLE IF NOT EXISTS user_favorites (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID REFERENCES users(id) ON DELETE CASCADE,
                food_id VARCHAR(150) NOT NULL,
                food_data JSONB NOT NULL DEFAULT '{}'::jsonb,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, food_id)
            )`);
        await pool.query(`CREATE INDEX IF NOT EXISTS idx_user_favorites_user ON user_favorites(user_id)`);

        await pool.query(`
            CREATE TABLE IF NOT EXISTS user_orders (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                order_number VARCHAR(40) UNIQUE NOT NULL,
                user_id UUID REFERENCES users(id) ON DELETE CASCADE,
                session_id VARCHAR(100),
                status VARCHAR(50) DEFAULT 'confirmed',
                items JSONB NOT NULL DEFAULT '[]'::jsonb,
                subtotal DECIMAL(10,2) DEFAULT 0,
                delivery_fee DECIMAL(10,2) DEFAULT 0,
                tax DECIMAL(10,2) DEFAULT 0,
                total_amount DECIMAL(10,2) DEFAULT 0,
                delivery_address JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )`);
        await pool.query(`CREATE INDEX IF NOT EXISTS idx_user_orders_user ON user_orders(user_id)`);

        // Lightweight interaction log for the 👍/👎 buttons on recommendation
        // cards. Works for guests (session_id only) and logged-in users alike.
        await pool.query(`
            CREATE TABLE IF NOT EXISTS user_feedback (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                session_id VARCHAR(100),
                user_id UUID REFERENCES users(id) ON DELETE SET NULL,
                food_id VARCHAR(150),
                interaction_type VARCHAR(30),
                rating INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )`);
        await pool.query(`CREATE INDEX IF NOT EXISTS idx_user_feedback_session ON user_feedback(session_id)`);

        console.log('✅ Schema ready (users.first_name/last_name, user_favorites, user_orders, user_feedback)');
    } catch (e) {
        console.error('⚠️  ensureSchema failed (favorites/orders/profile may not work):', e.message);
    }
};

// ==================== AUTH MIDDLEWARE ====================
// Verifies the Bearer JWT and attaches { id, email } to req.user.
const requireAuth = (req, res, next) => {
    const authHeader = req.headers.authorization;
    if (!authHeader) {
        return res.status(401).json({ success: false, message: 'Authentication required' });
    }
    try {
        const token = authHeader.split(' ')[1];
        const decoded = jwt.verify(token, process.env.JWT_SECRET || 'your-secret-key-change-this');
        req.user = decoded;
        next();
    } catch (e) {
        return res.status(401).json({ success: false, message: 'Invalid or expired session. Please log in again.' });
    }
};

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

// ==================== MEMBER1 RECOMMENDER HELPERS ====================

// Convert raw game responses into the {attribute, value, preference} answer
// objects the member1 Taste DNA generator expects. Skipped / valueless
// answers are dropped.
const buildMember1Answers = (responses = []) => {
    return (responses || [])
        .filter(r =>
            r &&
            r.attribute &&
            r.value &&
            r.optionId !== 'skip' &&
            String(r.value).toLowerCase() !== 'skip'
        )
        .map(r => ({
            attribute: String(r.attribute),
            value: String(r.value),
            preference: typeof r.preference === 'number' ? r.preference : 1,
        }));
};

// Split a flat, score-ranked list from member1 into the exploitation /
// exploration buckets the frontend renders. Top matches are "For You";
// the next slice is framed as "Discover Something New".
const splitRecommendations = (recs = [], exploitCount = 12, exploreCount = 12) => {
    const list = Array.isArray(recs) ? recs : [];
    const exploitation = list.slice(0, exploitCount).map(r => ({
        ...r,
        confidence: r.confidence || 'high',
        reason: r.reason || 'High-confidence match for your taste profile',
    }));
    const exploration = list.slice(exploitCount, exploitCount + exploreCount).map(r => ({
        ...r,
        confidence: 'medium',
        reason: 'Try something new! 🚀',
    }));
    return { exploitation, exploration };
};

// Ask the member1 Flask service for Taste DNA + ranked recommendations.
// Throws if the service is unreachable so callers can fall back to the DB.
const getMember1Recommendations = async (answers, existingTasteDNA = null, limit = 24) => {
    let tasteDNA = existingTasteDNA;

    if (!tasteDNA) {
        const dnaResp = await member1Service.generateTasteDNA(answers || []);
        tasteDNA = (dnaResp && dnaResp.taste_dna) ? dnaResp.taste_dna : {};
    }

    const recResp = await member1Service.getRecommendations(tasteDNA || {}, [], {}, limit);
    const recs = (recResp && recResp.recommendations) ? recResp.recommendations : [];

    return { tasteDNA, recommendations: splitRecommendations(recs) };
};

// Fallback recommendations sourced DIRECTLY from the enriched menu catalog
// (menu_dataset_enriched_claude_FINAL.csv) — used when the member1 Flask
// service is offline. Unlike the old Postgres fallback, every dish here carries
// a real product image (image_url), price and restaurant, so the UI always
// renders proper recommendation cards with pictures.
//
// `prefs` is an {attribute: {value: weight}} map (see catalogRecommender's
// answersToPreferences / dnaToPreferences). An empty map yields top-rated
// popular picks.
const getFallbackRecommendations = (prefs = {}) => {
    const ranked = catalogRecommender.recommend(prefs, 24);
    return splitRecommendations(ranked, 12, 12);
};

// ==================== MEMBER2 (RAG/LLM) ENRICHMENT ====================
// Member 1 decides WHAT to recommend (ranking). Member 2 explains WHY, in
// grounded natural language. This turns the generic "High-confidence match"
// card text into a real sentence about the dish, sourced from Member 2's food
// knowledge base + LLM. It is strictly best-effort: if Member 2 is disabled,
// offline, slow, or missing its LLM key, the original reason is kept and the
// recommendations response is unaffected.

// Summarize the user's taste into one short phrase for Member 2's prompt
// framing. Handles both shapes we store: a fallback record with a raw
// {attribute,value} answers array, or a member1 Taste DNA weight-map object.
const buildTasteSummary = (tasteDNA = {}) => {
    try {
        if (tasteDNA && Array.isArray(tasteDNA.answers) && tasteDNA.answers.length) {
            const vals = [];
            const seen = new Set();
            for (const a of tasteDNA.answers) {
                const v = a && a.value ? String(a.value).trim() : '';
                if (v && v.toLowerCase() !== 'skip' && !seen.has(v.toLowerCase())) {
                    seen.add(v.toLowerCase());
                    vals.push(v);
                }
            }
            if (vals.length) return `You enjoy ${vals.slice(0, 6).join(', ')}`;
        }

        // member1 DNA object: { cuisine: {beef: 0.8, ...}, flavor: {...}, ... }
        if (tasteDNA && typeof tasteDNA === 'object') {
            const picks = [];
            for (const key of ['cuisine', 'protein', 'flavor', 'base', 'meal_type', 'spice_level']) {
                const bucket = tasteDNA[key];
                if (bucket && typeof bucket === 'object') {
                    const top = Object.entries(bucket)
                        .sort((a, b) => (Number(b[1]) || 0) - (Number(a[1]) || 0))[0];
                    if (top && top[0]) picks.push(String(top[0]));
                }
            }
            if (picks.length) return `You enjoy ${picks.slice(0, 6).join(', ')}`;
        }
    } catch (_) { /* fall through to default */ }
    return 'A taste profile based on your recent picks';
};

// Enrich a bucket of recommendation cards with Member 2 explanations, in
// parallel. Only the top `max` items are explained (each explanation is an LLM
// call, so we cap the count to keep latency bounded). Uses Promise.allSettled
// so one failed/timed-out call never blocks the others, and only overwrites the
// card's `reason` when Member 2 returns a grounded explanation.
const enrichBucketWithExplanations = async (items = [], tasteSummary, isExploration, max) => {
    const list = Array.isArray(items) ? items : [];
    const limit = Math.min(list.length, max);
    if (limit === 0) return list;

    const jobs = list.slice(0, limit).map((food) => {
        const foodId = food.food_id || food.id;
        if (!foodId) return Promise.resolve(null);
        const conf = isExploration ? 'low' : (food.confidence || 'high');
        return member2Service
            .explainRecommendation(foodId, food.score, tasteSummary, conf)
            .then((r) => ({ foodId, r }))
            .catch(() => null);
    });

    const settled = await Promise.allSettled(jobs);
    const byId = {};
    for (const s of settled) {
        if (s.status === 'fulfilled' && s.value && s.value.r) {
            byId[s.value.foodId] = s.value.r;
        }
    }

    return list.map((food) => {
        const foodId = food.food_id || food.id;
        const r = byId[foodId];
        const explanation = r && typeof r.explanation === 'string' ? r.explanation.trim() : '';
        // Skip the LLM's honest "no info" fallbacks — keep the friendly default.
        const usable = explanation &&
            !/^no information available/i.test(explanation) &&
            !/don't have detailed information/i.test(explanation);
        if (usable) {
            return { ...food, reason: explanation, explained: true, grounded: r.grounded !== false };
        }
        return food;
    });
};

// Add Member 2 explanations to a { exploitation, exploration } payload.
// Best-effort and time-bounded; returns the input unchanged on any problem.
const enrichRecommendations = async (recommendations, tasteDNA) => {
    if (!recommendations || !member2Service.isEnabled()) return recommendations;
    try {
        const tasteSummary = buildTasteSummary(tasteDNA || {});
        const exploitCap = parseInt(process.env.MEMBER2_EXPLAIN_MAX) || 6;
        const exploreCap = parseInt(process.env.MEMBER2_EXPLAIN_EXPLORE_MAX) || 3;

        const [exploitation, exploration] = await Promise.all([
            enrichBucketWithExplanations(recommendations.exploitation, tasteSummary, false, exploitCap),
            enrichBucketWithExplanations(recommendations.exploration, tasteSummary, true, exploreCap),
        ]);

        return { ...recommendations, exploitation, exploration };
    } catch (err) {
        console.error('⚠️  member2 enrichment skipped:', err.message);
        return recommendations;
    }
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
    const { email, password, name, firstName, lastName, sessionId } = req.body;

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

        // Build a display name from first/last name when provided.
        const fullName = (name && name.trim())
            || [firstName, lastName].filter(Boolean).join(' ').trim()
            || email.split('@')[0];

        // Create user in database
        const result = await pool.query(
            `INSERT INTO users (email, password_hash, name, first_name, last_name, session_id, created_at, last_login)
             VALUES ($1, $2, $3, $4, $5, $6, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
             RETURNING id, email, name, first_name, last_name, session_id, taste_dna, avatar_url, created_at`,
            [email.toLowerCase(), hashedPassword, fullName, firstName || null, lastName || null, sessionId || null]
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
                first_name: user.first_name,
                last_name: user.last_name,
                avatar_url: user.avatar_url || null,
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
                first_name: user.first_name || null,
                last_name: user.last_name || null,
                avatar_url: user.avatar_url || null,
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
// NOTE: `type` is the Taste DNA attribute and each option carries a `value`.
// The frontend sends {attribute: question.type, value: option.value} back so
// the member1 model can personalize. Values are lower-cased to match the
// recommender's food catalog fields.
app.get('/api/game/questions', (req, res) => {
    const questions = [
        {
            id: 'q1',
            type: 'cuisine',
            text: 'Which cuisine are you craving?',
            options: [
                { id: 'cuisine_pakistani', text: 'Pakistani 🍛', value: 'pakistani' },
                { id: 'cuisine_chinese', text: 'Chinese 🥡', value: 'chinese' },
                { id: 'cuisine_italian', text: 'Italian 🍝', value: 'italian' },
                { id: 'cuisine_fastfood', text: 'Fast Food 🍔', value: 'fast food' },
                { id: 'skip', text: 'Skip' }
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
                { id: 'protein_vegetarian', text: 'Vegetarian 🌱', value: 'vegetarian' },
                { id: 'skip', text: 'Skip' }
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
                { id: 'flavor_smoky', text: 'Smoky 🔥', value: 'smoky' },
                { id: 'skip', text: 'Skip' }
            ]
        },
        {
            id: 'q4',
            type: 'spice_level',
            text: 'How spicy do you like it?',
            options: [
                { id: 'spice_mild', text: 'Mild', value: 'mild' },
                { id: 'spice_medium', text: 'Medium 🌶️', value: 'medium' },
                { id: 'spice_hot', text: 'Hot 🌶️🌶️', value: 'hot' },
                { id: 'skip', text: 'Skip' }
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
                { id: 'meal_dessert', text: 'Dessert 🍰', value: 'dessert' },
                { id: 'skip', text: 'Skip' }
            ]
        },
        {
            id: 'q6',
            type: 'base',
            text: 'Pick your base:',
            options: [
                { id: 'base_rice', text: 'Rice 🍚', value: 'rice' },
                { id: 'base_bread', text: 'Bread / Naan 🫓', value: 'bread' },
                { id: 'base_noodles', text: 'Noodles / Pasta 🍜', value: 'noodles' },
                { id: 'base_wrap', text: 'Wrap / Roll 🌯', value: 'wrap' },
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
                { id: 'mood_quick', text: 'Quick bite ⏱️', value: 'quick' },
                { id: 'skip', text: 'Skip' }
            ]
        }
    ];

    res.json({
        success: true,
        questions: questions
    });
});

// Photo "this or that" rounds — each round is a pair of real dishes (with
// images) pulled from the enriched CSV catalog. The frontend shows both and the
// user taps the tastier-looking one; the chosen dish's attributes
// (cuisine/protein/flavor/spice_level/meal_type/base) build the Taste DNA.
app.get('/api/game/photo-rounds', (req, res) => {
    try {
        const rounds = Math.min(Math.max(parseInt(req.query.rounds) || 8, 3), 15);
        const pairs = catalogRecommender.getPhotoRounds(rounds);
        res.json({ success: true, count: pairs.length, rounds: pairs });
    } catch (error) {
        console.error('Photo rounds error:', error);
        res.status(500).json({ success: false, error: error.message });
    }
});

// Record a 👍/👎/save interaction on a recommendation card. Optional auth:
// logged-in users are linked by id, guests by session_id. Never fails the UI.
app.post('/api/feedback', async (req, res) => {
    try {
        const { sessionId, foodId, interactionType, rating } = req.body || {};
        let userId = null;
        const authHeader = req.headers.authorization;
        if (authHeader) {
            try {
                const decoded = jwt.verify(authHeader.split(' ')[1], process.env.JWT_SECRET || 'your-secret-key-change-this');
                userId = decoded.id;
            } catch (_) { /* treat as guest */ }
        }
        await pool.query(
            `INSERT INTO user_feedback (session_id, user_id, food_id, interaction_type, rating)
             VALUES ($1, $2, $3, $4, $5)`,
            [sessionId || null, userId, foodId || null, interactionType || null,
             Number.isFinite(parseInt(rating)) ? parseInt(rating) : null]
        );
        res.json({ success: true });
    } catch (error) {
        console.error('Feedback error:', error);
        // Non-critical: acknowledge so the UI never surfaces an error.
        res.json({ success: false });
    }
});
// ==================== USER PROFILE ROUTE ====================

// Get user by ID
app.get('/api/users/:userId', async (req, res, next) => {
    try {
        const { userId } = req.params;
        // "/api/users/me" is its own route defined below. Without this guard the
        // param route captures it first and runs `WHERE id = 'me'`, which 500s on
        // the UUID cast. Fall through to the dedicated /me handler instead.
        if (userId === 'me') return next();

        const result = await pool.query(
            `SELECT id, email, name, first_name, last_name, taste_dna, preferences, avatar_url, created_at, last_login
             FROM users WHERE id = $1`,
            [userId]
        );

        if (result.rows.length === 0) {
            return res.status(404).json({
                success: false,
                message: 'User not found'
            });
        }

        res.json({
            success: true,
            user: result.rows[0]
        });

    } catch (error) {
        console.error('Get user error:', error);
        res.status(500).json({
            success: false,
            message: 'Failed to get user',
            error: error.message
        });
    }
});

// Get user profile (authenticated)
app.get('/api/users/me', async (req, res) => {
    try {
        // Get user from session or token
        const authHeader = req.headers.authorization;
        if (!authHeader) {
            return res.status(401).json({
                success: false,
                message: 'Authentication required'
            });
        }

        const token = authHeader.split(' ')[1];
        let decoded;
        try {
            decoded = jwt.verify(token, process.env.JWT_SECRET || 'your-secret-key-change-this');
        } catch (e) {
            // Stale / expired / malformed token → this is an auth failure, not a
            // server error. Return 401 so the client can fall back to guest mode
            // instead of surfacing a noisy 500.
            return res.status(401).json({ success: false, message: 'Invalid or expired token' });
        }

        const result = await pool.query(
            `SELECT id, email, name, first_name, last_name, taste_dna, preferences, avatar_url, created_at, last_login
             FROM users WHERE id = $1`,
            [decoded.id]
        );

        if (result.rows.length === 0) {
            return res.status(404).json({
                success: false,
                message: 'User not found'
            });
        }

        res.json({
            success: true,
            user: result.rows[0]
        });

    } catch (error) {
        console.error('Get user error:', error);
        res.status(500).json({
            success: false,
            message: 'Failed to get user',
            error: error.message
        });
    }
});

// Update the authenticated user's profile (name, first/last name, avatar).
app.put('/api/users/me', requireAuth, async (req, res) => {
    try {
        const { name, firstName, lastName, avatarUrl, preferences } = req.body;

        // Compose a display name: explicit name wins, else first+last, else keep existing.
        const composedName = (name && name.trim())
            || [firstName, lastName].filter(Boolean).join(' ').trim()
            || null;

        const result = await pool.query(
            `UPDATE users SET
                name       = COALESCE($1, name),
                first_name = COALESCE($2, first_name),
                last_name  = COALESCE($3, last_name),
                avatar_url = COALESCE($4, avatar_url),
                preferences = COALESCE($5, preferences)
             WHERE id = $6
             RETURNING id, email, name, first_name, last_name, taste_dna, preferences, avatar_url, created_at, last_login`,
            [
                composedName,
                firstName || null,
                lastName || null,
                avatarUrl || null,
                preferences ? JSON.stringify(preferences) : null,
                req.user.id
            ]
        );

        if (result.rows.length === 0) {
            return res.status(404).json({ success: false, message: 'User not found' });
        }

        res.json({
            success: true,
            message: 'Profile updated',
            user: result.rows[0]
        });
    } catch (error) {
        console.error('Update profile error:', error);
        res.status(500).json({ success: false, message: 'Failed to update profile', error: error.message });
    }
});

// ==================== FAVORITES ROUTES ====================
// Favorites store a denormalized dish snapshot (food_data) so any recommended
// dish — including CSV catalog items not present in the `foods` table — can be
// favorited and rendered later with its image, price and restaurant.

// List the authenticated user's favorites (newest first).
app.get('/api/favorites', requireAuth, async (req, res) => {
    try {
        const result = await pool.query(
            `SELECT food_id, food_data, created_at
             FROM user_favorites WHERE user_id = $1 ORDER BY created_at DESC`,
            [req.user.id]
        );
        const favorites = result.rows.map(r => ({
            ...(r.food_data || {}),
            food_id: r.food_id,
            favorited_at: r.created_at
        }));
        res.json({ success: true, count: favorites.length, favorites });
    } catch (error) {
        console.error('Get favorites error:', error);
        res.status(500).json({ success: false, message: 'Failed to get favorites', error: error.message });
    }
});

// Add (or update) a favorite. Body: { food: { food_id, name, image_url, ... } }.
app.post('/api/favorites', requireAuth, async (req, res) => {
    try {
        const { food } = req.body;
        const foodId = food && (food.food_id || food.id);
        if (!food || !foodId) {
            return res.status(400).json({ success: false, message: 'A food with a food_id is required' });
        }
        await pool.query(
            `INSERT INTO user_favorites (user_id, food_id, food_data)
             VALUES ($1, $2, $3)
             ON CONFLICT (user_id, food_id)
             DO UPDATE SET food_data = $3, created_at = CURRENT_TIMESTAMP`,
            [req.user.id, String(foodId), JSON.stringify(food)]
        );
        res.json({ success: true, message: 'Added to favorites', food_id: String(foodId) });
    } catch (error) {
        console.error('Add favorite error:', error);
        res.status(500).json({ success: false, message: 'Failed to add favorite', error: error.message });
    }
});

// Remove a favorite by food_id.
app.delete('/api/favorites/:foodId', requireAuth, async (req, res) => {
    try {
        const { foodId } = req.params;
        await pool.query(
            'DELETE FROM user_favorites WHERE user_id = $1 AND food_id = $2',
            [req.user.id, String(foodId)]
        );
        res.json({ success: true, message: 'Removed from favorites', food_id: String(foodId) });
    } catch (error) {
        console.error('Remove favorite error:', error);
        res.status(500).json({ success: false, message: 'Failed to remove favorite', error: error.message });
    }
});

// ==================== ORDERS ROUTES ====================

const generateOrderNumber = () => {
    const ts = Date.now().toString(36).toUpperCase();
    const rand = Math.random().toString(36).substring(2, 6).toUpperCase();
    return `FOOD-${ts}-${rand}`;
};

// List the authenticated user's orders (newest first). Empty array when none —
// the frontend renders a "No previous orders" empty state.
app.get('/api/orders', requireAuth, async (req, res) => {
    try {
        const result = await pool.query(
            `SELECT id, order_number, status, items, subtotal, delivery_fee, tax,
                    total_amount, delivery_address, created_at
             FROM user_orders WHERE user_id = $1 ORDER BY created_at DESC`,
            [req.user.id]
        );
        res.json({ success: true, count: result.rows.length, orders: result.rows });
    } catch (error) {
        console.error('Get orders error:', error);
        res.status(500).json({ success: false, message: 'Failed to get orders', error: error.message });
    }
});

// Create an order from a list of dish snapshots.
// Body: { items: [{ food_id, name, price, quantity, image_url, ... }], deliveryAddress?, sessionId? }
app.post('/api/orders', requireAuth, async (req, res) => {
    try {
        const { items, deliveryAddress, sessionId } = req.body;
        if (!Array.isArray(items) || items.length === 0) {
            return res.status(400).json({ success: false, message: 'No items in order' });
        }

        // Normalize items + compute totals (prices are in PKR from the catalog).
        const lineItems = items.map(it => {
            const price = Number(it.price) || 0;
            const quantity = Math.max(1, parseInt(it.quantity) || 1);
            return {
                food_id: it.food_id || it.id || null,
                name: it.name || it.food_name || 'Dish',
                image_url: it.image_url || '',
                restaurant: it.restaurant || '',
                cuisine: it.cuisine || '',
                unit_price: price,
                quantity,
                total_price: Math.round(price * quantity * 100) / 100,
                currency: it.currency || 'PKR'
            };
        });

        const subtotal = lineItems.reduce((s, it) => s + it.total_price, 0);
        const deliveryFee = subtotal > 2000 || subtotal === 0 ? 0 : 149;
        const tax = Math.round(subtotal * 0.05 * 100) / 100; // 5%
        const totalAmount = Math.round((subtotal + deliveryFee + tax) * 100) / 100;
        const orderNumber = generateOrderNumber();

        const result = await pool.query(
            `INSERT INTO user_orders
                (order_number, user_id, session_id, status, items, subtotal, delivery_fee, tax, total_amount, delivery_address)
             VALUES ($1, $2, $3, 'confirmed', $4, $5, $6, $7, $8, $9)
             RETURNING id, order_number, status, items, subtotal, delivery_fee, tax, total_amount, delivery_address, created_at`,
            [
                orderNumber,
                req.user.id,
                sessionId || null,
                JSON.stringify(lineItems),
                subtotal,
                deliveryFee,
                tax,
                totalAmount,
                deliveryAddress ? JSON.stringify(deliveryAddress) : null
            ]
        );

        res.status(201).json({ success: true, message: 'Order placed successfully!', order: result.rows[0] });
    } catch (error) {
        console.error('Create order error:', error);
        res.status(500).json({ success: false, message: 'Failed to create order', error: error.message });
    }
});
// Submit game responses
app.post('/api/game/responses', async (req, res) => {
    try {
        const { sessionId, responses } = req.body;

        // Turn the raw game answers into member1 {attribute, value, preference}.
        const answers = buildMember1Answers(responses);

        let tasteDNA = null;
        let recommendations = null;
        let source = 'member1';

        // 1) Primary path: real member1 model (Taste DNA + ranked catalog).
        try {
            const result = await getMember1Recommendations(answers, null, 24);
            tasteDNA = result.tasteDNA;
            recommendations = result.recommendations;
        } catch (err) {
            console.error('⚠️  member1 service unavailable, using DB fallback:', err.message);
            source = 'fallback';
        }

        // 2) Fallback: if member1 was down or returned nothing, use DB foods so
        //    the UI still renders recommendations.
        const isEmpty = !recommendations ||
            ((recommendations.exploitation || []).length === 0 &&
             (recommendations.exploration || []).length === 0);

        if (isEmpty) {
            // Personalize the CSV fallback with the answers the user just gave.
            recommendations = getFallbackRecommendations(
                catalogRecommender.answersToPreferences(answers)
            );
            if (!tasteDNA) {
                tasteDNA = { source: 'fallback', answers, created_at: new Date().toISOString() };
            }
            source = 'fallback';
        }

        // 3) Enrich the cards with Member 2 (RAG/LLM) explanations — best-effort,
        //    so a slow/offline Member 2 never blocks the game→recs flow.
        recommendations = await enrichRecommendations(recommendations, tasteDNA);

        // Persist Taste DNA + responses on the session (non-fatal on failure).
        try {
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
        } catch (dbErr) {
            console.error('⚠️  Failed to persist session taste DNA:', dbErr.message);
        }

        res.json({
            success: true,
            session_id: sessionId,
            taste_dna: tasteDNA,
            recommendations,
            source,
            is_guest: true,
            message: source === 'member1'
                ? 'Recommendations generated from your Taste DNA!'
                : 'Guest profile created! (Showing popular picks — recommender offline.)'
        });

    } catch (error) {
        console.error('Game response error:', error);
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Get recommendations for an existing session (used by the Recommendations
// page when there's no navigation state / localStorage, e.g. "Try Again").
// NOTE: the frontend consumes this response directly, so exploitation /
// exploration are returned at the TOP LEVEL (not nested under `recommendations`).
app.get('/api/recommendations', async (req, res) => {
    try {
        const { sessionId } = req.query;

        // Load any Taste DNA we previously saved for this session.
        let tasteDNA = null;
        if (sessionId) {
            try {
                const s = await pool.query(
                    'SELECT taste_dna FROM sessions WHERE session_id = $1',
                    [sessionId]
                );
                if (s.rows.length && s.rows[0].taste_dna) {
                    tasteDNA = typeof s.rows[0].taste_dna === 'string'
                        ? JSON.parse(s.rows[0].taste_dna)
                        : s.rows[0].taste_dna;
                }
            } catch (e) {
                console.error('⚠️  Could not load session taste DNA:', e.message);
            }
        }

        let recommendations = null;
        try {
            const result = await getMember1Recommendations([], tasteDNA || {}, 24);
            recommendations = result.recommendations;
        } catch (err) {
            console.error('⚠️  member1 service unavailable, using DB fallback:', err.message);
        }

        const isEmpty = !recommendations ||
            ((recommendations.exploitation || []).length === 0 &&
             (recommendations.exploration || []).length === 0);

        if (isEmpty) {
            // Personalize the CSV fallback with any saved Taste DNA for this
            // session. Handle both shapes we may have stored: a member1 DNA
            // object (attribute weight maps) or a fallback record that kept the
            // raw {attribute,value} answers. Empty => top-rated popular picks.
            const prefs = (tasteDNA && Array.isArray(tasteDNA.answers))
                ? catalogRecommender.answersToPreferences(tasteDNA.answers)
                : catalogRecommender.dnaToPreferences(tasteDNA || {});
            recommendations = getFallbackRecommendations(prefs);
        }

        // Enrich with Member 2 (RAG/LLM) explanations — best-effort.
        recommendations = await enrichRecommendations(recommendations, tasteDNA);

        res.json({
            success: true,
            session_id: sessionId || null,
            taste_dna: tasteDNA,
            exploitation: recommendations.exploitation,
            exploration: recommendations.exploration
        });

    } catch (error) {
        console.error('Get recommendations error:', error);
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// ==================== MEMBER2 (RAG/LLM) ROUTES ====================
// Thin proxies over the Member 2 FastAPI service so the frontend can hit a
// single origin (the Node backend on :5000) instead of talking to Member 2
// directly. These power natural-language food search / Q&A and per-dish
// explanations. They are public (menu data is not sensitive) and degrade
// gracefully when Member 2 is offline.

// POST /api/ask — open-ended food question answering (RAG).
// Body: { query, filters?, top_k? } → { success, answer, sources, grounded }
app.post('/api/ask', async (req, res) => {
    const { query, filters = null, top_k } = req.body || {};
    if (!query || !String(query).trim()) {
        return res.status(400).json({ success: false, error: 'query is required' });
    }
    const q = String(query).trim();
    const k = top_k || 3;

    // Local, dependency-free fallback so "Ask Foodgram" still returns useful
    // dishes (with images/price) even when Member 2 is disabled, offline, or its
    // LLM key is missing. Keeps the feature working instead of showing "offline".
    const catalogFallback = () => {
        const matches = catalogRecommender.searchCatalog(q, Math.max(9, k));
        if (!matches.length) {
            return {
                success: true, available: true, grounded: false, sources: [], fallback: true,
                answer: "I couldn't find a dish matching that. Try a cuisine, ingredient, or something like “spicy chicken under Rs. 800”.",
            };
        }
        return {
            success: true, available: true, grounded: false, fallback: true,
            answer: `Here's what I found for “${q}”:`,
            sources: matches,
        };
    };

    if (!member2Service.isEnabled()) {
        return res.json(catalogFallback());
    }
    try {
        const result = await member2Service.ask(q, filters, k);
        // If Member 2 answered but found nothing to ground on, prefer the
        // catalog matches over a bare "no information" reply.
        if (!result || !result.answer || (Array.isArray(result.sources) && result.sources.length === 0)) {
            const fb = catalogFallback();
            if (fb.sources && fb.sources.length) return res.json(fb);
        }
        return res.json({
            success: true,
            query: result.query,
            answer: result.answer,
            sources: result.sources || [],
            grounded: result.grounded !== false,
            available: true,
        });
    } catch (error) {
        console.error('⚠️  /api/ask (member2) unavailable, using catalog fallback:', error.message);
        return res.json(catalogFallback());
    }
});

// GET /api/search — semantic food search with optional filters.
// Query: query, veg_status?, food_type?, category?, price_min?, price_max?, top_k?
app.get('/api/search', async (req, res) => {
    const { query, veg_status, food_type, category, price_min, price_max, top_k } = req.query;
    if (!query || !String(query).trim()) {
        return res.status(400).json({ success: false, error: 'query is required' });
    }
    const q = String(query).trim();
    const limit = parseInt(top_k) || 6;

    // Catalog fallback: keep search working (with images/price) when Member 2 is off.
    const searchFallback = () => {
        const results = catalogRecommender.searchCatalog(q, limit);
        return { success: true, query: q, results, total: results.length, above_threshold: results.length > 0, available: true, fallback: true };
    };

    if (!member2Service.isEnabled()) {
        return res.json(searchFallback());
    }
    try {
        const filters = {};
        if (veg_status) filters.veg_status = veg_status;
        if (food_type) filters.food_type = food_type;
        if (category) filters.category = category;
        if (price_min !== undefined) filters.price_min = price_min;
        if (price_max !== undefined) filters.price_max = price_max;

        const result = await member2Service.search(q, filters, limit);
        return res.json({
            success: true,
            query: result.query,
            results: result.results || [],
            total: result.total || (result.results ? result.results.length : 0),
            above_threshold: result.above_threshold !== false,
            available: true,
        });
    } catch (error) {
        console.error('⚠️  /api/search (member2) unavailable, using catalog fallback:', error.message);
        return res.json(searchFallback());
    }
});

// GET /api/food/:foodId/explain?query=... — ask about one specific dish.
// Defaults to "Tell me about this dish" so the food-detail page can call it
// with no query. Returns a grounded answer or a friendly fallback.
app.get('/api/food/:foodId/explain', async (req, res) => {
    const { foodId } = req.params;
    const query = (req.query.query && String(req.query.query).trim()) || 'Tell me about this dish.';

    // Fallback: answer from the dish's own catalog description when Member 2 is off.
    const explainFallback = () => {
        const dish = catalogRecommender.getById(foodId);
        if (dish && dish.description) {
            return { success: true, food_id: foodId, query, answer: dish.description, grounded: false, available: true, fallback: true };
        }
        return { success: true, answer: '', grounded: false, available: false };
    };

    if (!member2Service.isEnabled()) {
        return res.json(explainFallback());
    }
    try {
        const result = await member2Service.askSpecific(foodId, query);
        if (!result || !result.answer) return res.json(explainFallback());
        return res.json({
            success: true,
            food_id: foodId,
            query,
            answer: result.answer,
            grounded: result.grounded !== false,
            available: true,
        });
    } catch (error) {
        console.error('⚠️  /api/food/:id/explain (member2) unavailable, using catalog fallback:', error.message);
        return res.json(explainFallback());
    }
});

// GET /api/member2/health — is the RAG/LLM service reachable?
app.get('/api/member2/health', async (req, res) => {
    if (!member2Service.isEnabled()) {
        return res.json({ enabled: false, status: 'disabled' });
    }
    try {
        const h = await member2Service.healthCheck();
        return res.json({ enabled: true, status: h.status || 'unknown', components: h.components || {} });
    } catch (error) {
        return res.json({ enabled: true, status: 'unreachable', error: error.message });
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

    // Ensure the DB has the columns/tables the new features need.
    ensureSchema();

    // Warm the CSV catalog so the first recommendation request is instant and
    // any path problem surfaces at boot rather than mid-request.
    try {
        const n = catalogRecommender.getCount();
        console.log(`🍽️  Menu catalog ready: ${n} dishes (CSV fallback with images)`);
    } catch (e) {
        console.error('⚠️  Could not preload menu catalog:', e.message);
    }

    // Report Member 2 (RAG/LLM) wiring so misconfiguration is obvious at boot.
    if (member2Service.isEnabled()) {
        console.log(`🧠 Member2 (RAG/LLM) enrichment ON → ${process.env.MEMBER2_API_URL || 'http://localhost:8001'}`);
    } else {
        console.log(`🧠 Member2 (RAG/LLM) enrichment OFF (MEMBER2_ENABLED=false)`);
    }
    console.log(`\n📋 Available endpoints:`);
    console.log(`   GET  /api/health`);
    console.log(`   GET  /api/auth/session-status`);
    console.log(`   POST /api/auth/signup`);
    console.log(`   POST /api/auth/login`);
    console.log(`   GET  /api/users/me      (auth)`);
    console.log(`   PUT  /api/users/me      (auth)`);
    console.log(`   GET  /api/foods`);
    console.log(`   GET  /api/game/questions`);
    console.log(`   GET  /api/game/photo-rounds`);
    console.log(`   POST /api/game/responses`);
    console.log(`   GET  /api/recommendations`);
    console.log(`   GET  /api/favorites     (auth)`);
    console.log(`   POST /api/favorites     (auth)`);
    console.log(`   DEL  /api/favorites/:id (auth)`);
    console.log(`   GET  /api/orders        (auth)`);
    console.log(`   POST /api/orders        (auth)`);
    console.log(`   POST /api/feedback`);
    console.log(`   POST /api/ask            (member2 RAG Q&A)`);
    console.log(`   GET  /api/search         (member2 semantic search)`);
    console.log(`   GET  /api/food/:id/explain (member2)`);
    console.log(`   GET  /api/member2/health`);
    console.log(`   POST /api/checkout`);
    console.log(`\n✅ Server ready!`);
});

module.exports = app;