const express = require('express');
const multer = require('multer');
const path = require('path');
const { v4: uuidv4 } = require('uuid');
const fs = require('fs');

// Ensure upload directory exists (outside static serve path)
const uploadDir = path.join(__dirname, '../uploads/private');
if (!fs.existsSync(uploadDir)) {
  fs.mkdirSync(uploadDir, { recursive: true });
}

// Allowed extensions (safe types)
const allowedExtensions = new Set(['.jpg', '.jpeg', '.png', '.pdf']);

// Allowed MIME types (more reliable than extension)
const allowedMimeTypes = new Set([
  'image/jpeg',
  'image/png',
  'application/pdf'
]);

// Multer configuration with security best practices
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, uploadDir);
  },
  filename: (req, file, cb) => {
    // Generate UUID-based filename, completely discard original name
    const ext = path.extname(file.originalname).toLowerCase();
    const newFilename = `${uuidv4()}${ext}`;
    cb(null, newFilename);
  }
});

// File filter: checks BOTH extension and mimetype
const fileFilter = (req, file, cb) => {
  const ext = path.extname(file.originalname).toLowerCase();
  const isAllowedExt = allowedExtensions.has(ext);
  const isAllowedMime = allowedMimeTypes.has(file.mimetype);

  if (isAllowedExt && isAllowedMime) {
    cb(null, true); // Accept file
  } else {
    // Reject with error
    const error = new Error('Invalid file type. Only JPG, JPEG, PNG, and PDF files are allowed.');
    error.code = 'INVALID_FILE_TYPE';
    cb(error, false);
  }
};

// Multer instance with limits and security
const upload = multer({
  storage: storage,
  fileFilter: fileFilter,
  limits: {
    fileSize: 10 * 1024 * 1024 // 10MB limit
  }
});

// Express route handler
const uploadFile = (req, res, next) => {
  upload.single('file')(req, res, (err) => {
    if (err) {
      if (err.code === 'LIMIT_FILE_SIZE') {
        return res.status(400).json({
          success: false,
          error: 'File size exceeds the 10MB limit.'
        });
      }
      
      if (err.code === 'INVALID_FILE_TYPE') {
        return res.status(400).json({
          success: false,
          error: err.message
        });
      }

      // Other multer or unknown errors
      return res.status(400).json({
        success: false,
        error: err.message || 'File upload failed.'
      });
    }

    if (!req.file) {
      return res.status(400).json({
        success: false,
        error: 'No file uploaded.'
      });
    }

    // Success response
    res.status(200).json({
      success: true,
      message: 'File uploaded successfully.',
      filename: req.file.filename,
      originalname: req.file.originalname, // for reference only
      size: req.file.size,
      mimetype: req.file.mimetype
    });
  });
};

module.exports = { uploadFile };