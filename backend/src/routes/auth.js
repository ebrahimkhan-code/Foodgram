// routes/auth.js
const router = require('express').Router();
const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');

// Signup - Auto-links guest session
router.post('/auth/signup', async (req, res) => {
    const { email, password, sessionId } = req.body;
    
    // Check if user exists
    const userCheck = await db.query('SELECT * FROM users WHERE email = $1', [email]);
    if (userCheck.rows.length) {
        return res.status(400).json({ error: 'User already exists' });
    }
    
    // Hash password
    const salt = await bcrypt.genSalt(10);
    const hashedPassword = await bcrypt.hash(password, salt);
    
    // Create user
    const result = await db.query(
        `INSERT INTO users (email, password_hash, session_id) 
         VALUES ($1, $2, $3) RETURNING id, email, session_id`,
        [email, hashedPassword, sessionId]
    );
    
    const user = result.rows[0];
    
    // Link session to user
    await db.query(
        'UPDATE sessions SET user_id = $1, is_converted = TRUE WHERE session_id = $2',
        [user.id, sessionId]
    );
    
    // Copy taste DNA from session to user
    const session = await db.query(
        'SELECT taste_dna FROM sessions WHERE session_id = $1',
        [sessionId]
    );
    
    if (session.rows.length) {
        await db.query(
            'UPDATE users SET taste_dna = $1 WHERE id = $2',
            [session.rows[0].taste_dna, user.id]
        );
    }
    
    // Generate JWT token
    const token = jwt.sign(
        { id: user.id, email: user.email },
        process.env.JWT_SECRET,
        { expiresIn: '7d' }
    );
    
    res.json({
        token,
        user: {
            id: user.id,
            email: user.email,
            taste_dna: session.rows[0]?.taste_dna || {}
        },
        session_linked: true
    });
});

// Login - Auto-links guest session
router.post('/auth/login', async (req, res) => {
    const { email, password, sessionId } = req.body;
    
    // Find user
    const result = await db.query('SELECT * FROM users WHERE email = $1', [email]);
    if (!result.rows.length) {
        return res.status(401).json({ error: 'Invalid credentials' });
    }
    
    const user = result.rows[0];
    
    // Check password
    const validPassword = await bcrypt.compare(password, user.password_hash);
    if (!validPassword) {
        return res.status(401).json({ error: 'Invalid credentials' });
    }
    
    // Link session to user
    await db.query(
        'UPDATE sessions SET user_id = $1, is_converted = TRUE WHERE session_id = $2',
        [user.id, sessionId]
    );
    
    // If session has taste DNA, copy to user
    const session = await db.query(
        'SELECT taste_dna FROM sessions WHERE session_id = $1',
        [sessionId]
    );
    
    if (session.rows.length && session.rows[0].taste_dna) {
        await db.query(
            'UPDATE users SET taste_dna = $1 WHERE id = $2',
            [session.rows[0].taste_dna, user.id]
        );
    }
    
    // Generate token
    const token = jwt.sign(
        { id: user.id, email: user.email },
        process.env.JWT_SECRET,
        { expiresIn: '7d' }
    );
    
    res.json({
        token,
        user: {
            id: user.id,
            email: user.email,
            taste_dna: session.rows[0]?.taste_dna || user.taste_dna
        },
        session_linked: true
    });
});

// Check session status
router.get('/auth/session-status', async (req, res) => {
    const { sessionId } = req.query;
    
    const session = await db.query(
        'SELECT session_id, user_id, is_converted FROM sessions WHERE session_id = $1',
        [sessionId]
    );
    
    res.json({
        is_guest: session.rows.length && !session.rows[0].user_id,
        is_converted: session.rows.length && session.rows[0].is_converted,
        user_id: session.rows[0]?.user_id || null
    });
});

module.exports = router;