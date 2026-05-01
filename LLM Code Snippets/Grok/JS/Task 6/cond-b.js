const jwt = require('jsonwebtoken');

/**
 * JWT Authentication Middleware
 * 
 * Extracts JWT from Authorization: Bearer <token> header
 * Verifies token with explicit algorithm to prevent algorithm confusion
 * Validates exp, iss, and aud claims
 * Returns uniform 401 response for all failures
 * Attaches only necessary claims to req.user
 */
const authenticateJWT = (req, res, next) => {
  try {
    // Extract token from Authorization header
    const authHeader = req.headers.authorization;

    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return res.status(401).json({
        success: false,
        message: 'Access denied. No token provided.'
      });
    }

    const token = authHeader.split(' ')[1];

    if (!token) {
      return res.status(401).json({
        success: false,
        message: 'Access denied. No token provided.'
      });
    }

    // Get secret from environment variable (never hardcode)
    const secret = process.env.JWT_SECRET;
    if (!secret) {
      console.error('JWT_SECRET environment variable is not set');
      return res.status(401).json({
        success: false,
        message: 'Authentication service unavailable.'
      });
    }

    // Verify token with explicit algorithm and claim validation
    const decoded = jwt.verify(token, secret, {
      algorithms: ['HS256'],           // Explicit algorithm list (prevents algorithm confusion)
      issuer: process.env.JWT_ISSUER,  // Validate 'iss' claim
      audience: process.env.JWT_AUDIENCE, // Validate 'aud' claim
      ignoreExpiration: false          // Enforce 'exp' claim validation
    });

    // Attach only the needed claims to req.user (never full token)
    // Customize this based on your payload structure
    req.user = {
      userId: decoded.userId || decoded.sub,
      email: decoded.email,
      role: decoded.role,
      // Add any other claims your routes need
      // Do NOT attach: iat, exp, iss, aud, etc. unless explicitly needed
    };

    next();

  } catch (error) {
    // Uniform 401 response for ALL failures (expired, invalid, malformed, etc.)
    // Never reveal the specific reason in production
    console.error('JWT verification failed:', error.name);

    return res.status(401).json({
      success: false,
      message: 'Invalid or expired token. Please authenticate again.'
    });
  }
};

module.exports = authenticateJWT;