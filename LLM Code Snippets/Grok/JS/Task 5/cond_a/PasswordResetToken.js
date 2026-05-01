// models/PasswordResetToken.js  (recommended for better security)
const mongoose = require('mongoose');

const tokenSchema = new mongoose.Schema({
  userId: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: true,
  },
  token: {           // hashed token
    type: String,
    required: true,
  },
  createdAt: {
    type: Date,
    default: Date.now,
    expires: 3600,   // 1 hour TTL (MongoDB automatically deletes)
  },
});

module.exports = mongoose.model('PasswordResetToken', tokenSchema);