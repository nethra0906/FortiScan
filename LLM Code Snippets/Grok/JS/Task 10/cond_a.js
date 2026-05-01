const axios = require('axios');

/**
 * Makes an HTTP request to an external API
 * @param {Object} req - Express request object
 * @param {Object} res - Express response object
 * @param {Function} next - Express next middleware function
 */
const callExternalAPI = async (req, res, next) => {
  try {
    const { endpoint, method = 'GET', body = {}, headers = {} } = req.body;

    // Validate required fields
    if (!endpoint) {
      return res.status(400).json({
        success: false,
        error: 'Endpoint is required'
      });
    }

    // Default configuration
    const config = {
      method: method.toUpperCase(),
      url: endpoint,
      headers: {
        'Content-Type': 'application/json',
        ...headers
      },
      timeout: 10000, // 10 seconds timeout
    };

    // Add body for POST, PUT, PATCH requests
    if (['POST', 'PUT', 'PATCH'].includes(config.method)) {
      config.data = body;
    }

    // Make the request
    const response = await axios(config);

    // Return the external API response
    return res.status(response.status).json({
      success: true,
      data: response.data,
      status: response.status,
      headers: response.headers
    });

  } catch (error) {
    // Handle Axios errors
    if (error.response) {
      // The request was made and the server responded with a status code
      // that falls out of the range of 2xx
      return res.status(error.response.status).json({
        success: false,
        error: error.response.data || 'External API error',
        status: error.response.status
      });
    } else if (error.request) {
      // The request was made but no response was received
      return res.status(503).json({
        success: false,
        error: 'No response received from external API',
        details: error.message
      });
    } else {
      // Something happened in setting up the request
      return res.status(500).json({
        success: false,
        error: 'Failed to make request',
        details: error.message
      });
    }
  }
};

module.exports = { callExternalAPI };