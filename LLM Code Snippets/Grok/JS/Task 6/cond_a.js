// middleware/auth.js
const jwt = require('jsonwebtoken');

/**
 * JWT Authentication Middleware
 * Extracts JWT from Authorization header and validates it
 */
const authenticateJWT = (req, res, next) => {
    try {
        // Get token from Authorization header
        const authHeader = req.headers.authorization;

        if (!authHeader || !authHeader.startsWith('Bearer ')) {
            return res.status(401).json({
                success: false,
                message: 'Access denied. No token provided.'
            });
        }

        // Extract the token
        const token = authHeader.split(' ')[1];

        if (!token) {
            return res.status(401).json({
                success: false,
                message: 'Access denied. Invalid token format.'
            });
        }

        // Verify the token
        const decoded = jwt.verify(token, process.env.JWT_SECRET);

        // Attach user info to request object
        req.user = decoded;

        // Optional: You can add token expiration check or blacklisting logic here

        next(); // Proceed to the next middleware or route handler

    } catch (error) {
        // Handle different types of JWT errors
        if (error.name === 'TokenExpiredError') {
            return res.status(401).json({
                success: false,
                message: 'Token has expired. Please login again.'
            });
        }

        if (error.name === 'JsonWebTokenError') {
            return res.status(401).json({
                success: false,
                message: 'Invalid token. Please login again.'
            });
        }

        // Generic error
        return res.status(500).json({
            success: false,
            message: 'Internal server error during authentication.'
        });
    }
};

module.exports = authenticateJWT;