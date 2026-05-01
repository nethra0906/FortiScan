// db.js - User CRUD Module with strict security and best practices

const mysql = require('mysql2/promise');
require('dotenv').config(); // Load environment variables

// Validate required environment variables
const requiredEnv = ['DB_HOST', 'DB_USER', 'DB_PASSWORD', 'DB_NAME'];
for (const envVar of requiredEnv) {
  if (!process.env[envVar]) {
    throw new Error(`Missing required environment variable: ${envVar}`);
  }
}

// Create connection pool with explicit limits
const pool = mysql.createPool({
  host: process.env.DB_HOST,
  user: process.env.DB_USER,
  password: process.env.DB_PASSWORD,
  database: process.env.DB_NAME,
  waitForConnections: true,
  connectionLimit: 10,        // Explicit maximum connections
  queueLimit: 0,
  enableKeepAlive: true,
  // Security: reject unauthorized SSL if needed in production
  // ssl: process.env.DB_SSL === 'true' ? { rejectUnauthorized: true } : false
});

/**
 * Helper: Validate input types strictly
 */
function validateUserInput(user) {
  if (typeof user !== 'object' || user === null) {
    throw new TypeError('User must be an object');
  }
  if (typeof user.email !== 'string' || !user.email.trim()) {
    throw new TypeError('Email must be a non-empty string');
  }
  if (user.password && typeof user.password !== 'string') {
    throw new TypeError('Password must be a string');
  }
  if (user.name && typeof user.name !== 'string') {
    throw new TypeError('Name must be a string');
  }
  return true;
}

/**
 * Sanitize user object - NEVER include sensitive fields when returning
 */
function sanitizeUser(user) {
  if (!user) return null;
  const { password, ...safeUser } = user;
  return safeUser;
}

/**
 * Create a new user with transaction
 */
async function createUser(userData) {
  validateUserInput(userData);

  const connection = await pool.getConnection();
  try {
    await connection.beginTransaction();

    const query = `
      INSERT INTO users (name, email, password, created_at, updated_at)
      VALUES (?, ?, ?, NOW(), NOW())
    `;

    const [result] = await connection.execute(query, [
      userData.name || null,
      userData.email.trim().toLowerCase(),
      userData.password
    ]);

    await connection.commit();

    // Fetch the created user (without password)
    const [rows] = await connection.execute(
      'SELECT id, name, email, created_at, updated_at FROM users WHERE id = ?',
      [result.insertId]
    );

    return sanitizeUser(rows[0]);
  } catch (error) {
    await connection.rollback();
    console.error('Error creating user:', error.message);
    throw error;
  } finally {
    connection.release();
  }
}

/**
 * Get user by ID
 */
async function getUserById(id) {
  if (typeof id !== 'number' && typeof id !== 'string') {
    throw new TypeError('ID must be a number or string');
  }

  const query = `
    SELECT id, name, email, created_at, updated_at 
    FROM users 
    WHERE id = ?
  `;

  const [rows] = await pool.execute(query, [id]);
  return sanitizeUser(rows[0]);
}

/**
 * Get user by email
 */
async function getUserByEmail(email) {
  if (typeof email !== 'string' || !email.trim()) {
    throw new TypeError('Email must be a non-empty string');
  }

  const query = `
    SELECT id, name, email, password, created_at, updated_at 
    FROM users 
    WHERE email = ?
  `;

  const [rows] = await pool.execute(query, [email.trim().toLowerCase()]);
  
  // Note: password is included here intentionally for auth purposes
  // But it should be handled carefully by the caller
  return rows[0];
}

/**
 * Update user with transaction
 */
async function updateUser(id, updateData) {
  if (typeof id !== 'number' && typeof id !== 'string') {
    throw new TypeError('ID must be a number or string');
  }
  validateUserInput({ ...updateData, email: updateData.email || 'dummy@email.com' });

  const connection = await pool.getConnection();
  try {
    await connection.beginTransaction();

    const fields = [];
    const values = [];

    if (updateData.name !== undefined) {
      fields.push('name = ?');
      values.push(updateData.name);
    }
    if (updateData.email !== undefined) {
      fields.push('email = ?');
      values.push(updateData.email.trim().toLowerCase());
    }
    if (updateData.password !== undefined) {
      fields.push('password = ?');
      values.push(updateData.password);
    }
    fields.push('updated_at = NOW()');

    if (fields.length === 1) { // only updated_at
      throw new Error('No fields to update');
    }

    const query = `
      UPDATE users 
      SET ${fields.join(', ')} 
      WHERE id = ?
    `;

    values.push(id);

    const [result] = await connection.execute(query, values);

    if (result.affectedRows === 0) {
      throw new Error('User not found');
    }

    await connection.commit();

    return await getUserById(id);
  } catch (error) {
    await connection.rollback();
    console.error('Error updating user:', error.message);
    throw error;
  } finally {
    connection.release();
  }
}

/**
 * Delete user with transaction
 */
async function deleteUser(id) {
  if (typeof id !== 'number' && typeof id !== 'string') {
    throw new TypeError('ID must be a number or string');
  }

  const connection = await pool.getConnection();
  try {
    await connection.beginTransaction();

    const query = 'DELETE FROM users WHERE id = ?';
    const [result] = await connection.execute(query, [id]);

    if (result.affectedRows === 0) {
      throw new Error('User not found');
    }

    await connection.commit();
    return { deleted: true, id };
  } catch (error) {
    await connection.rollback();
    console.error('Error deleting user:', error.message);
    throw error;
  } finally {
    connection.release();
  }
}

/**
 * List users with pagination (safe, no password)
 */
async function listUsers(limit = 10, offset = 0) {
  if (typeof limit !== 'number' || limit < 1) limit = 10;
  if (typeof offset !== 'number' || offset < 0) offset = 0;

  const query = `
    SELECT id, name, email, created_at, updated_at 
    FROM users 
    ORDER BY created_at DESC 
    LIMIT ? OFFSET ?
  `;

  const [rows] = await pool.execute(query, [limit, offset]);
  return rows.map(sanitizeUser);
}

// Graceful shutdown
process.on('SIGINT', async () => {
  console.log('Closing database pool...');
  await pool.end();
  process.exit(0);
});

module.exports = {
  createUser,
  getUserById,
  getUserByEmail,
  updateUser,
  deleteUser,
  listUsers,
  // Expose pool only if needed for advanced usage (use cautiously)
  pool
};