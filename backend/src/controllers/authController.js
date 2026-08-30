const { Pool } = require('pg');
const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');
const { v4: uuidv4 } = require('uuid');
require('dotenv').config();

const pool = new Pool({
    user: process.env.DB_USER || 'postgres',
    host: process.env.DB_HOST || 'localhost',
    database: process.env.DB_NAME || 'foodgram',
    password: process.env.DB_PASSWORD,
    port: parseInt(process.env.DB_PORT) || 5432,
});

// Generate JWT Token
const generateToken = (userId, email) => {
    return jwt.sign(
        { id: userId, email },
        process.env.JWT_SECRET || 'your-secret-key',
        { expiresIn: '7d' }
    );
};

// Hash password
const hashPassword = async (password) => {
    const salt = await bcrypt.genSalt(10);
    return await bcrypt.hash(password, salt);
};

// ==================== SIGNUP ====================
exports.signup = async (req, res) => {
    const { email, password, name, sessionId } = req.body;
    
    try {
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

        // Check if user exists
        const userCheck = await pool.query(
            'SELECT id, email FROM users WHERE email = $1',
            [email.toLowerCase()]
        );

        if (userCheck.rows.length > 0) {
            return res.status(400).json({
                success: false,
                message: 'User already exists with this email'
            });
        }

        // Hash password
        const hashedPassword = await hashPassword(password);

        // Create user
        const result = await pool.query(
            `INSERT INTO users (email, password_hash, name, session_id, created_at, last_login)
             VALUES ($1, $2, $3, $4, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
             RETURNING id, email, name, session_id, taste_dna, created_at`,
            [email.toLowerCase(), hashedPassword, name || email.split('@')[0], sessionId || null]
        );

        const user = result.rows[0];

        // Link session to user if session exists
        if (sessionId) {
            await pool.query(
                'UPDATE sessions SET user_id = $1, is_converted = TRUE WHERE session_id = $2',
                [user.id, sessionId]
            );

            // Copy taste DNA from session to user
            const session = await pool.query(
                'SELECT taste_dna, game_responses FROM sessions WHERE session_id = $1',
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
};

// ==================== LOGIN - FIXED ====================
exports.login = async (req, res) => {
    const { email, password, sessionId } = req.body;

    try {
        // Validate input
        if (!email || !password) {
            return res.status(400).json({
                success: false,
                message: 'Email and password are required'
            });
        }

        console.log(`🔍 Login attempt for: ${email}`);

        // Find user - CHECK DATABASE
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

        // Check password - COMPARE WITH HASHED PASSWORD IN DATABASE
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
};

// ==================== GET USER PROFILE ====================
exports.getProfile = async (req, res) => {
    try {
        const userId = req.user.id;

        const result = await pool.query(
            `SELECT id, email, name, taste_dna, preferences, created_at, last_login, avatar_url
             FROM users WHERE id = $1`,
            [userId]
        );

        if (result.rows.length === 0) {
            return res.status(404).json({
                success: false,
                message: 'User not found'
            });
        }

        // Get order count
        const orderCount = await pool.query(
            'SELECT COUNT(*) FROM orders WHERE user_id = $1',
            [userId]
        );

        // Get favorite count
        const favoriteCount = await pool.query(
            'SELECT COUNT(*) FROM favorites WHERE user_id = $1',
            [userId]
        );

        res.json({
            success: true,
            user: {
                ...result.rows[0],
                order_count: parseInt(orderCount.rows[0].count),
                favorite_count: parseInt(favoriteCount.rows[0].count)
            }
        });

    } catch (error) {
        console.error('Get profile error:', error);
        res.status(500).json({
            success: false,
            message: 'Failed to get profile',
            error: error.message
        });
    }
};

// ==================== UPDATE PROFILE ====================
exports.updateProfile = async (req, res) => {
    try {
        const userId = req.user.id;
        const { name, preferences, avatar_url } = req.body;

        const updates = [];
        const values = [];
        let paramCount = 1;

        if (name) {
            updates.push(`name = $${paramCount}`);
            values.push(name);
            paramCount++;
        }

        if (preferences) {
            updates.push(`preferences = $${paramCount}`);
            values.push(preferences);
            paramCount++;
        }

        if (avatar_url) {
            updates.push(`avatar_url = $${paramCount}`);
            values.push(avatar_url);
            paramCount++;
        }

        if (updates.length === 0) {
            return res.status(400).json({
                success: false,
                message: 'No fields to update'
            });
        }

        values.push(userId);
        const query = `
            UPDATE users 
            SET ${updates.join(', ')} 
            WHERE id = $${paramCount}
            RETURNING id, email, name, taste_dna, preferences, avatar_url
        `;

        const result = await pool.query(query, values);

        res.json({
            success: true,
            message: 'Profile updated successfully',
            user: result.rows[0]
        });

    } catch (error) {
        console.error('Update profile error:', error);
        res.status(500).json({
            success: false,
            message: 'Failed to update profile',
            error: error.message
        });
    }
};

// ==================== CHECK SESSION STATUS ====================
exports.checkSession = async (req, res) => {
    try {
        const { sessionId } = req.query;

        if (!sessionId) {
            return res.json({
                is_guest: true,
                is_converted: false,
                user_id: null
            });
        }

        const result = await pool.query(
            'SELECT user_id, is_converted FROM sessions WHERE session_id = $1',
            [sessionId]
        );

        if (result.rows.length === 0) {
            return res.json({
                is_guest: true,
                is_converted: false,
                user_id: null
            });
        }

        const session = result.rows[0];

        res.json({
            is_guest: !session.user_id,
            is_converted: session.is_converted,
            user_id: session.user_id
        });

    } catch (error) {
        console.error('Session check error:', error);
        res.status(500).json({
            success: false,
            message: 'Failed to check session',
            error: error.message
        });
    }
};