// middleware/session.js
const { v4: uuidv4 } = require('uuid');

const sessionMiddleware = (req, res, next) => {
    let sessionId = req.headers['x-session-id'];
    
    if (!sessionId) {
        sessionId = `guest_${uuidv4().slice(0, 8)}`;
        res.setHeader('X-Session-ID', sessionId);
    }
    
    req.sessionId = sessionId;
    next();
};

module.exports = sessionMiddleware;