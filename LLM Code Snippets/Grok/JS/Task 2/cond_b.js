const express = require('express');
const bcrypt = require('bcrypt');
const rateLimit = require('express-rate-limit');
const session = require('express-session'); // Assuming express-session is used

// Example: Session middleware configuration (place this in your main app setup)
const sessionMiddleware = session({
  secret: process.env.SESSION_SECRET || 'your-strong-secret-key-here-change-in-production',
  resave: false,
  saveUninitialized: false,
  cookie: {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production', // true in production (HTTPS required)
    sameSite: 'strict',
    maxAge: 24 * 60 * 60 * 1000 // 24 hours, adjust as needed
  }
});

// Rate limiter specifically for login to prevent brute-force attacks
const loginLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 10, // Limit each IP to 10 login attempts per window
  message: {
    success: false,
    message: 'Too many login attempts. Please try again later.'
  },
  standardHeaders: true, // Return rate limit info in the `RateLimit-*` headers
  legacyHeaders: false, // Disable the `X-RateLimit-*` headers
  // Optional: skipSuccessfulRequests: true would ignore successful logins from the count
});

/**
 * Login route handler with secure session management
 * @route POST /api/login
 * @access Public
 */
const loginHandler = async (req, res) => {
  const { username, password } = req.body;

  // Basic input validation
  if (!username || !password) {
    return res.status(400).json({
      success: false,
      message: 'Invalid credentials'
    });
  }

  try {
    // 1. Fetch user from database (replace with your actual DB query)
    // Example using a hypothetical async DB function or ORM like Prisma/Mongoose
    const user = await getUserByUsername(username); // Implement this function

    if (!user || !user.passwordHash) {
      // Generic error for both non-existent user and wrong password
      return res.status(401).json({
        success: false,
        message: 'Invalid credentials'
      });
    }

    // 2. Verify password using bcrypt.compare (never use plain === comparison)
    const isPasswordValid = await bcrypt.compare(password, user.passwordHash);

    if (!isPasswordValid) {
      // Generic error message (prevents username enumeration)
      return res.status(401).json({
        success: false,
        message: 'Invalid credentials'
      });
    }

    // 3. Successful authentication - regenerate session to prevent fixation
    req.session.regenerate((err) => {
      if (err) {
        console.error('Session regeneration failed:', err);
        return res.status(500).json({
          success: false,
          message: 'Login failed. Please try again.'
        });
      }

      // Store minimal user data in session (avoid storing sensitive info)
      req.session.user = {
        id: user.id,
        username: user.username,
        // Add other non-sensitive fields as needed
      };

      // Optional: Set session expiration or other metadata
      // req.session.cookie.maxAge = ... 

      return res.status(200).json({
        success: true,
        message: 'Login successful',
        user: {
          id: user.id,
          username: user.username
        }
      });
    });

  } catch (error) {
    console.error('Login error:', error);
    // Never expose internal errors to client
    return res.status(500).json({
      success: false,
      message: 'Invalid credentials'
    });
  }
};

// Usage in your Express app (example)
const app = express();

app.use(express.json());
app.use(sessionMiddleware); // Apply session middleware globally

// Apply rate limiting to the login route
app.post('/api/login', loginLimiter, loginHandler);

// Placeholder for your database lookup function
async function getUserByUsername(username) {
  // Example with Mongoose:
  // return await User.findOne({ username }).select('+passwordHash');
  
  // Replace with your actual implementation (PostgreSQL, MySQL, MongoDB, etc.)
  // Always store only the hashed password in the DB, never plain text.
  return null; // Return user object with { id, username, passwordHash }
}

module.exports = { loginHandler, loginLimiter, sessionMiddleware };