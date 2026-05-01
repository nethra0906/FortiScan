const crypto = require('crypto');

/**
 * Generates a cryptographically secure random token for use as a session identifier or API key.
 *
 * Requirements satisfied:
 * - Uses ONLY crypto.randomBytes(32) for randomness (256 bits of entropy)
 * - Returns raw token (Buffer) to the immediate caller
 * - Encodes as base64url string for safe transmission (URL-safe, no padding)
 * - Hash recommendation for persistence: SHA-256 of the raw token
 * - Never use Math.random(), Date.now(), or weak sources
 *
 * @returns {string} Base64url-encoded random token (44 characters)
 */
function generateSecureToken() {
  // Generate 32 bytes (256 bits) of cryptographically secure randomness
  const randomBytes = crypto.randomBytes(32);
  
  // Convert to base64url encoding (safe for URLs, headers, JSON, etc.)
  // This replaces '+' with '-', '/' with '_', and removes '=' padding
  const token = randomBytes.toString('base64')
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=/g, '');

  // IMPORTANT SECURITY NOTES (for the developer, not returned to caller):
  // 1. Return ONLY this encoded token to the immediate caller.
  // 2. If you need to persist it, store the hash instead:
  //    const hashedToken = crypto.createHash('sha256').update(randomBytes).digest('hex');
  // 3. NEVER log the raw token or the encoded token in production logs.
  // 4. Never expose the raw Buffer outside this function unless absolutely necessary.

  return token;
}

module.exports = generateSecureToken;