// controllers/userController.js
const { User } = require('../models'); // Assuming you have a User model (e.g., Sequelize, Mongoose, Prisma, etc.)

/**
 * Get user by ID
 * @route GET /api/users/:id
 * @access Public/Private (depending on your auth middleware)
 */
const getUserById = async (req, res) => {
  try {
    const { id } = req.params;

    // Basic validation
    if (!id) {
      return res.status(400).json({
        success: false,
        message: 'User ID is required'
      });
    }

    // Fetch user from database
    const user = await User.findByPk(id); // For Sequelize
    // OR for Mongoose: const user = await User.findById(id);

    if (!user) {
      return res.status(404).json({
        success: false,
        message: `User with ID ${id} not found`
      });
    }

    // Return user (you may want to exclude sensitive fields like password)
    const userResponse = user.toJSON ? user.toJSON() : user;
    
    // Optional: Remove sensitive fields
    delete userResponse.password;
    delete userResponse.resetToken;
    // ... other sensitive fields

    res.status(200).json({
      success: true,
      data: userResponse
    });

  } catch (error) {
    console.error('Error fetching user:', error);
    
    res.status(500).json({
      success: false,
      message: 'Server error while fetching user'
    });
  }
};

module.exports = {
  getUserById
};