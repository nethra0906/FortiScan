// controllers/authController.js
const bcrypt = require('bcryptjs');
const session = require('express-session'); // Make sure it's set up in app.js

// Assuming you have a User model (e.g., Mongoose or Sequelize)
const User = require('../models/User');

/**
 * User Login with Session Management
 * POST /api/auth/login
 */
const login = async (req, res) => {
  const { username, password } = req.body;

  // Input validation
  if (!username || !password) {
    return res.status(400).json({
      success: false,
      message: 'Username and password are required'
    });
  }

  try {
    // Find user by username
    const user = await User.findOne({ username });

    if (!user) {
      return res.status(401).json({
        success: false,
        message: 'Invalid username or password'
      });
    }

    // Verify password
    const isPasswordValid = await bcrypt.compare(password, user.password);

    if (!isPasswordValid) {
      return res.status(401).json({
        success: false,
        message: 'Invalid username or password'
      });
    }

    // Regenerate session to prevent session fixation attacks
    req.session.regenerate((err) => {
      if (err) {
        console.error('Session regeneration error:', err);
        return res.status(500).json({
          success: false,
          message: 'Internal server error'
        });
      }

      // Set session data
      req.session.user = {
        id: user._id,
        username: user.username,
        email: user.email,
        role: user.role || 'user'
      };

      // Save session explicitly (good practice)
      req.session.save((err) => {
        if (err) {
          console.error('Session save error:', err);
          return res.status(500).json({
            success: false,
            message: 'Failed to create session'
          });
        }

        // Successful login response
        res.status(200).json({
          success: true,
          message: 'Login successful',
          user: {
            id: user._id,
            username: user.username,
            email: user.email,
            role: user.role || 'user'
          }
        });
      });
    });

  } catch (error) {
    console.error('Login error:', error);
    res.status(500).json({
      success: false,
      message: 'Internal server error'
    });
  }
};

module.exports = { login };