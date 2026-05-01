// controllers/authController.js
const crypto = require('crypto');
const bcrypt = require('bcryptjs');
const User = require('../models/User');
const PasswordResetToken = require('../models/PasswordResetToken');
const { sendPasswordResetEmail } = require('../utils/sendEmail');

// POST /api/auth/forgot-password
const requestPasswordReset = async (req, res) => {
  const { email } = req.body;

  if (!email) {
    return res.status(400).json({ message: 'Email is required' });
  }

  const user = await User.findOne({ email });
  if (!user) {
    // Don't reveal if email exists (security)
    return res.status(200).json({ 
      message: 'If an account with that email exists, a password reset link has been sent.' 
    });
  }

  // Delete any existing reset token for this user
  await PasswordResetToken.deleteMany({ userId: user._id });

  // Generate secure random token
  const resetToken = crypto.randomBytes(32).toString('hex');

  // Hash the token before storing (defense-in-depth)
  const hashedToken = await bcrypt.hash(resetToken, 12);

  await new PasswordResetToken({
    userId: user._id,
    token: hashedToken,
  }).save();

  // Create reset link (use your frontend URL in production)
  const resetLink = `${process.env.CLIENT_URL}/reset-password?token=${resetToken}&id=${user._id}`;

  try {
    await sendPasswordResetEmail(user.email, resetLink);
    res.status(200).json({
      message: 'Password reset link sent to your email.',
    });
  } catch (error) {
    console.error('Email sending failed:', error);
    res.status(500).json({ message: 'Failed to send email. Please try again later.' });
  }
};

// POST /api/auth/reset-password
const resetPassword = async (req, res) => {
  const { token, userId, newPassword } = req.body;

  if (!token || !userId || !newPassword) {
    return res.status(400).json({ message: 'Token, userId, and new password are required' });
  }

  if (newPassword.length < 8) {
    return res.status(400).json({ message: 'Password must be at least 8 characters long' });
  }

  const resetTokenRecord = await PasswordResetToken.findOne({ userId });
  if (!resetTokenRecord) {
    return res.status(400).json({ message: 'Invalid or expired reset token' });
  }

  // Compare the provided plain token with the hashed version in DB
  const isValidToken = await bcrypt.compare(token, resetTokenRecord.token);
  if (!isValidToken) {
    return res.status(400).json({ message: 'Invalid or expired reset token' });
  }

  const user = await User.findById(userId);
  if (!user) {
    return res.status(404).json({ message: 'User not found' });
  }

  // Update password (pre-save hook will hash it)
  user.password = newPassword;
  await user.save();

  // Invalidate the token (single-use)
  await PasswordResetToken.deleteOne({ _id: resetTokenRecord._id });

  res.status(200).json({ message: 'Password has been reset successfully. You can now log in with your new password.' });
};

module.exports = {
  requestPasswordReset,
  resetPassword,
};