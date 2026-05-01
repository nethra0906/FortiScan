const express = require('express');
const router = express.Router();

// Assuming you have a database connection pool (e.g., mysql2/promise)
const db = require('../config/database'); // Adjust path as needed

/**
 * GET /users/:id
 * Fetch user record by ID with proper security measures
 */
router.get('/users/:id', async (req, res) => {
  try {
    const userIdParam = req.params.id;

    // (2) Validate that user ID is a positive integer
    const userId = parseInt(userIdParam, 10);
    if (isNaN(userId) || userId <= 0) {
      return res.status(400).json({
        success: false,
        message: 'Invalid user ID. Must be a positive integer.'
      });
    }

    // (3) Authorization check: user can only access their own record or must be admin
    const authenticatedUser = req.user; // Assumes middleware like passport/jwt has attached req.user

    if (!authenticatedUser) {
      return res.status(401).json({
        success: false,
        message: 'Authentication required'
      });
    }

    const isOwner = authenticatedUser.id === userId;
    const isAdmin = authenticatedUser.role === 'admin';

    if (!isOwner && !isAdmin) {
      return res.status(403).json({
        success: false,
        message: 'Forbidden: You can only access your own profile'
      });
    }

    // (1) Parameterized query - never use template literals or concatenation
    const [rows] = await db.execute(
      'SELECT id, username, email, first_name, last_name, role, created_at, updated_at ' +
      'FROM users WHERE id = ?',
      [userId]
    );

    if (rows.length === 0) {
      return res.status(404).json({
        success: false,
        message: 'User not found'
      });
    }

    const user = rows[0];

    // (5) Password hash is already excluded via SELECT (safer than deleting from object)

    // Return success response
    return res.status(200).json({
      success: true,
      data: user
    });

  } catch (error) {
    // (4) Catch database errors and return generic 500 without leaking details
    console.error('Database error in getUserById:', error);
    return res.status(500).json({
      success: false,
      message: 'Internal server error'
    });
  }
});

module.exports = router;