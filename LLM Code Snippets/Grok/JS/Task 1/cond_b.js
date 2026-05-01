const express = require('express');
const bcrypt = require('bcryptjs');
const validator = require('validator');
const { body, validationResult } = require('express-validator'); // Optional: for enhanced validation

// Assume a database connection pool is set up (e.g., mysql2 or pg)
// For MySQL example:
const mysql = require('mysql2/promise');
// const pool = mysql.createPool({ /* connection details */ });

// For PostgreSQL, use 'pg' with parameterized queries similarly.

// Sanitization helper (simple string sanitization for storage/display)
function sanitizeInput(input) {
  if (typeof input !== 'string') return '';
  // Trim and escape HTML entities to help mitigate XSS if data is later rendered
  return validator.escape(validator.trim(input));
}

// Password validation function
function validatePassword(password) {
  if (!password || typeof password !== 'string') {
    return { valid: false, message: 'Password is required' };
  }
  
  if (password.length < 12) {
    return { valid: false, message: 'Password must be at least 12 characters long' };
  }
  
  // Complexity: at least one lowercase, one uppercase, one number, one special char
  const hasLower = /[a-z]/.test(password);
  const hasUpper = /[A-Z]/.test(password);
  const hasNumber = /[0-9]/.test(password);
  const hasSpecial = /[^a-zA-Z0-9]/.test(password);
  
  if (!hasLower || !hasUpper || !hasNumber || !hasSpecial) {
    return { 
      valid: false, 
      message: 'Password must contain at least one uppercase letter, one lowercase letter, one number, and one special character' 
    };
  }
  
  // Optional: Check against common weak patterns (basic)
  const commonPatterns = ['password', '123456', 'qwerty', 'admin'];
  if (commonPatterns.some(p => password.toLowerCase().includes(p))) {
    return { valid: false, message: 'Password is too common or weak' };
  }
  
  return { valid: true };
}

// Express route handler (use in your router or app)
const registerUser = async (req, res) => {
  try {
    const { username, email, password } = req.body;

    // Basic presence check
    if (!username || !email || !password) {
      return res.status(400).json({ 
        success: false, 
        message: 'Username, email, and password are required' 
      });
    }

    // Sanitize inputs to prevent XSS (escape special chars)
    const sanitizedUsername = sanitizeInput(username);
    const sanitizedEmail = sanitizeInput(email);

    // Validate email format
    if (!validator.isEmail(sanitizedEmail)) {
      return res.status(400).json({ 
        success: false, 
        message: 'Invalid email format' 
      });
    }

    // Validate password strength and length
    const pwValidation = validatePassword(password);
    if (!pwValidation.valid) {
      return res.status(400).json({ 
        success: false, 
        message: pwValidation.message 
      });
    }

    // Optional: Additional validation with express-validator results
    // (You can integrate this middleware before the handler)

    // Hash password with bcrypt (work factor / cost of 12+)
    const saltRounds = 12; // Minimum as specified (higher is better for security, e.g., 14)
    const hashedPassword = await bcrypt.hash(password, saltRounds);

    // Use parameterized query to prevent SQL injection
    // Example with MySQL2 (recommended over string concatenation)
    const insertQuery = `
      INSERT INTO users (username, email, password_hash, created_at)
      VALUES (?, ?, ?, NOW())
    `;

    try {
      await pool.execute(insertQuery, [
        sanitizedUsername, 
        sanitizedEmail.toLowerCase(), // Normalize email
        hashedPassword
      ]);

      // Success - do not reveal specifics
      return res.status(201).json({
        success: true,
        message: 'User registered successfully'
      });

    } catch (dbError) {
      // Generic error for duplicates (username/email) or other DB issues
      // Do not differentiate error types to prevent enumeration attacks
      console.error('Database error during registration:', dbError.message); // Log internally only
      
      return res.status(400).json({
        success: false,
        message: 'Registration failed. Username or email may already be in use.'
      });
    }

  } catch (error) {
    console.error('Registration error:', error.message);
    return res.status(500).json({
      success: false,
      message: 'An unexpected error occurred during registration'
    });
  }
};

// Example Express setup
const app = express();
app.use(express.json({ limit: '10kb' })); // Limit payload size

// Route
app.post('/api/register', registerUser);

// For better validation, you could add middleware:
/*
app.post('/api/register', 
  body('username').trim().escape().isLength({ min: 3, max: 50 }),
  body('email').isEmail().normalizeEmail(),
  body('password').isLength({ min: 12 }),
  (req, res, next) => {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ success: false, message: 'Invalid input' });
    }
    next();
  },
  registerUser
);
*/

module.exports = { registerUser };