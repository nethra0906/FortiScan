// routes/userRoutes.js
import express from 'express';
import User from '../models/userModel.js';

const router = express.Router();

// Create User
router.post('/', async (req, res) => {
  try {
    const user = await User.create(req.body);
    res.status(201).json({ success: true, data: user });
  } catch (error) {
    res.status(400).json({ success: false, message: error.message });
  }
});

// Get All Users
router.get('/', async (req, res) => {
  try {
    const { limit, page = 1 } = req.query;
    const offset = (page - 1) * (limit || 10);
    const users = await User.findAll({ limit, offset });
    const total = await User.count();

    res.json({
      success: true,
      data: users,
      pagination: { page: Number(page), limit, total }
    });
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
  }
});

// Get User by ID
router.get('/:id', async (req, res) => {
  try {
    const user = await User.findById(req.params.id);
    if (!user) return res.status(404).json({ success: false, message: 'User not found' });
    res.json({ success: true, data: user });
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
  }
});

// Update User
router.put('/:id', async (req, res) => {
  try {
    const user = await User.update(req.params.id, req.body);
    if (!user) return res.status(404).json({ success: false, message: 'User not found' });
    res.json({ success: true, data: user });
  } catch (error) {
    res.status(400).json({ success: false, message: error.message });
  }
});

// Delete User
router.delete('/:id', async (req, res) => {
  try {
    const user = await User.delete(req.params.id);
    if (!user) return res.status(404).json({ success: false, message: 'User not found' });
    res.json({ success: true, message: 'User deleted successfully', data: user });
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
  }
});

export default router;