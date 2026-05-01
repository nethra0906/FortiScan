// models/userModel.js
import pool from '../config/db.js';

/**
 * User Model with basic CRUD operations
 */

const User = {
  // CREATE
  async create(userData) {
    const { name, email, age, role = 'user' } = userData;

    const query = `
      INSERT INTO users (name, email, age, role)
      VALUES ($1, $2, $3, $4)
      RETURNING *;
    `;

    const values = [name, email, age, role];

    try {
      const result = await pool.query(query, values);
      return result.rows[0];
    } catch (error) {
      if (error.code === '23505') { // unique_violation
        throw new Error('Email already exists');
      }
      throw error;
    }
  },

  // READ ALL with optional pagination
  async findAll({ limit = 10, offset = 0 } = {}) {
    const query = `
      SELECT id, name, email, age, role, created_at, updated_at
      FROM users
      ORDER BY created_at DESC
      LIMIT $1 OFFSET $2;
    `;

    const result = await pool.query(query, [limit, offset]);
    return result.rows;
  },

  // READ ONE by ID
  async findById(id) {
    const query = `
      SELECT id, name, email, age, role, created_at, updated_at
      FROM users
      WHERE id = $1;
    `;

    const result = await pool.query(query, [id]);
    return result.rows[0];
  },

  // READ ONE by Email
  async findByEmail(email) {
    const query = `
      SELECT * FROM users WHERE email = $1;
    `;

    const result = await pool.query(query, [email]);
    return result.rows[0];
  },

  // UPDATE
  async update(id, userData) {
    const { name, email, age, role } = userData;

    const query = `
      UPDATE users
      SET 
        name = COALESCE($1, name),
        email = COALESCE($2, email),
        age = COALESCE($3, age),
        role = COALESCE($4, role),
        updated_at = CURRENT_TIMESTAMP
      WHERE id = $5
      RETURNING *;
    `;

    const values = [name, email, age, role, id];

    const result = await pool.query(query, values);
    return result.rows[0];
  },

  // DELETE
  async delete(id) {
    const query = `
      DELETE FROM users
      WHERE id = $1
      RETURNING *;
    `;

    const result = await pool.query(query, [id]);
    return result.rows[0];
  },

  // Optional: Count total users
  async count() {
    const result = await pool.query('SELECT COUNT(*) FROM users');
    return parseInt(result.rows[0].count);
  }
};

export default User;