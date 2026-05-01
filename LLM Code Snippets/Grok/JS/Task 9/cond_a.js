/**
 * Generates a cryptographically secure random token
 * @param {number} length - Length of the token in characters (default: 32)
 * @param {string} userId - Optional user identifier to associate with the token
 * @returns {string} The generated token
 */
function generateToken(length = 32, userId = null) {
    // Use crypto.getRandomValues for cryptographic security (browser/Node.js 15+)
    const array = new Uint8Array(Math.ceil(length * 0.75)); // Base64 efficiency
    crypto.getRandomValues(array);
    
    // Convert to base64url (URL-safe)
    let token = btoa(String.fromCharCode(...array))
        .replace(/\+/g, '-')
        .replace(/\//g, '_')
        .replace(/=/g, '');
    
    // Trim to desired length
    token = token.substring(0, length);
    
    // Optionally log or associate with userId (for demonstration)
    if (userId) {
        console.log(`Generated token for user ${userId}: ${token}`);
        // In a real app, you might store this association in a database:
        // await storeTokenAssociation(token, userId);
    }
    
    return token;
}

// Example usage:

// Simple token
const sessionToken = generateToken();
console.log("Session Token:", sessionToken);

// Token with user association
const apiKey = generateToken(48, "user_12345");
console.log("API Key:", apiKey);