const crypto = require('crypto');
const bcrypt = require('bcryptjs');
const { promisify } = require('util');

// Helper to hash token with SHA-256
const hashToken = (token) => {
  return crypto.createHash('sha256').update(token).digest();
};

// POST /api/auth/forgot-password
exports.forgotPassword = async (req, res) => {
  const { email } = req.body;

  if (!email) {
    return res.status(400).json({ message: 'Email is required' });
  }

  try {
    // 1. Find user by email (case insensitive recommended)
    const user = await User.findOne({ 
      email: email.toLowerCase().trim() 
    });

    // Always return the same response to prevent email enumeration
    if (!user) {
      // Simulate processing time for invalid emails
      await new Promise(resolve => setTimeout(resolve, 200));
      return res.status(200).json({
        message: 'If an account with that email exists, a password reset link has been sent.'
      });
    }

    // 2. Generate cryptographically secure token (NEVER use Math.random())
    const resetToken = crypto.randomBytes(32).toString('hex');

    // 3. Hash the token (store only hash in DB)
    const tokenHash = hashToken(resetToken);

    // 4. Set expiry to 1 hour (maximum as per requirement)
    const expiresAt = new Date(Date.now() + 60 * 60 * 1000); // 1 hour

    // 5. Save hashed token + expiry to user document
    user.resetPasswordToken = tokenHash;
    user.resetPasswordExpires = expiresAt;
    await user.save();

    // TODO: Send email with the plain token
    // Example:
    // const resetUrl = `${process.env.FRONTEND_URL}/reset-password/${resetToken}`;
    // await sendResetEmail(user.email, resetUrl);

    // Return identical response regardless of email validity
    return res.status(200).json({
      message: 'If an account with that email exists, a password reset link has been sent.'
    });

  } catch (error) {
    console.error('Forgot password error:', error);
    // Still return the same generic message on server error
    return res.status(200).json({
      message: 'If an account with that email exists, a password reset link has been sent.'
    });
  }
};

// POST /api/auth/reset-password
exports.resetPassword = async (req, res) => {
  const { token, newPassword } = req.body;

  if (!token || !newPassword) {
    return res.status(400).json({ message: 'Token and new password are required' });
  }

  if (newPassword.length < 8) {
    return res.status(400).json({ message: 'Password must be at least 8 characters long' });
  }

  try {
    // Hash the incoming token for comparison
    const tokenHash = hashToken(token);

    // Find user with matching token hash
    const user = await User.findOne({
      resetPasswordToken: tokenHash,
      resetPasswordExpires: { $gt: new Date() } // not expired
    });

    if (!user) {
      return res.status(400).json({ message: 'Invalid or expired token' });
    }

    // 1. Verify token using timingSafeEqual (prevents timing attacks)
    // Note: We already queried by hash, but we do explicit comparison for safety
    const isTokenValid = crypto.timingSafeEqual(
      Buffer.from(user.resetPasswordToken),
      Buffer.from(tokenHash)
    );

    if (!isTokenValid) {
      return res.status(400).json({ message: 'Invalid or expired token' });
    }

    // 2. Hash the new password with bcrypt
    const salt = await bcrypt.genSalt(12);
    const hashedPassword = await bcrypt.hash(newPassword, salt);

    // 3. Update password and immediately invalidate the token
    user.password = hashedPassword;
    user.resetPasswordToken = undefined;   // Delete token
    user.resetPasswordExpires = undefined; // Delete expiry

    await user.save();

    return res.status(200).json({
      message: 'Password has been reset successfully. You can now login with your new password.'
    });

  } catch (error) {
    console.error('Reset password error:', error);
    return res.status(500).json({ message: 'Something went wrong. Please try again.' });
  }
};