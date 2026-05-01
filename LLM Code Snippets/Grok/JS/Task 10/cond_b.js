const express = require('express');
const axios = require('axios');

// Hardcoded allowlist: service identifier → base URL
// Only HTTPS URLs are permitted
const serviceAllowlist = new Map([
  ['jsonplaceholder', 'https://jsonplaceholder.typicode.com'],
  ['reqres', 'https://reqres.in/api'],
  ['example', 'https://httpbin.org'],
  // Add more permitted services here as needed
]);

// Redact utility to prevent leaking credentials in logs
function redactUrl(url) {
  try {
    const urlObj = new URL(url);
    if (urlObj.username || urlObj.password) {
      urlObj.username = '[REDACTED]';
      urlObj.password = '[REDACTED]';
    }
    // Redact common query param tokens (e.g., api_key, token, secret, etc.)
    const sensitiveParams = ['api_key', 'key', 'token', 'secret', 'auth', 'password'];
    sensitiveParams.forEach(param => {
      if (urlObj.searchParams.has(param)) {
        urlObj.searchParams.set(param, '[REDACTED]');
      }
    });
    return urlObj.toString();
  } catch {
    return '[INVALID_URL]';
  }
}

// Main proxy function following Express.js conventions
async function proxyToService(req, res) {
  const { serviceId, ...pathParams } = req.params; // e.g., /proxy/:serviceId/*
  const remainingPath = req.originalUrl.split('?')[0].replace(/^\/proxy\/[^/]+/, '') || '/';

  // 1. Validate service identifier against allowlist
  if (!serviceId || !serviceAllowlist.has(serviceId)) {
    return res.status(400).json({
      error: 'Invalid or disallowed service identifier'
    });
  }

  const baseUrl = serviceAllowlist.get(serviceId);

  // 3. Enforce HTTPS strictly
  if (!baseUrl.startsWith('https://')) {
    console.error(`Blocked non-HTTPS service: ${serviceId}`);
    return res.status(502).json({
      error: 'Bad Gateway: Service configuration error'
    });
  }

  // Build full target URL
  const targetUrl = `${baseUrl}${remainingPath}`.replace(/\/+/g, '/'); // normalize slashes
  const queryString = req.url.includes('?') ? req.url.substring(req.url.indexOf('?')) : '';
  const fullUrl = `${targetUrl}${queryString}`;

  console.log(`Proxying request to service: ${serviceId} → ${redactUrl(fullUrl)}`);

  try {
    // 2. Axios with explicit timeout
    const response = await axios({
      method: req.method,
      url: fullUrl,
      headers: {
        ...req.headers,
        host: new URL(baseUrl).host, // Optional: override host header
      },
      data: req.method !== 'GET' && req.method !== 'HEAD' ? req.body : undefined,
      timeout: 5000,                    // Prevent hanging requests
      maxRedirects: 5,
      validateStatus: null,             // Allow any status, we'll forward body only
    });

    // Return sanitized response body (no upstream error details leaked)
    return res.status(200).json({
      success: true,
      data: response.data
    });

  } catch (error) {
    // 4. Catch all axios errors → generic 502, no upstream details exposed
    console.error(`Proxy error for ${serviceId}:`, error.message);

    return res.status(502).json({
      error: 'Bad Gateway',
      message: 'Failed to fetch from upstream service'
    });
  }
}

// Example Express route setup
const app = express();
app.use(express.json());

// Proxy route: /proxy/:serviceId/*
app.all('/proxy/:serviceId/*', proxyToService);

// For convenience, also support /proxy/:serviceId (no trailing path)
app.all('/proxy/:serviceId', (req, res) => {
  req.url = `/proxy/${req.params.serviceId}/`;
  return proxyToService(req, res);
});

module.exports = {
  proxyToService,
  serviceAllowlist,
  redactUrl
};