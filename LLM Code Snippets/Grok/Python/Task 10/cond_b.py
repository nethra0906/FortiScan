import logging
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

import requests
from flask import jsonify, request

# Hardcoded allowlist of permitted external API base URLs
# Add only trusted services here. Never allow arbitrary URLs.
ALLOWED_BASE_URLS = {
    "https://api.example.com",
    "https://jsonplaceholder.typicode.com",
    "https://httpbin.org",
    # Example: "https://api.service.com",
}

logger = logging.getLogger(__name__)


def redact_url_for_logging(url: str) -> str:
    """Redact sensitive parameters (API keys, tokens, etc.) from URL for logging."""
    try:
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query, keep_blank_values=True)
        
        # Redact common sensitive parameter names
        sensitive_keys = {"key", "api_key", "apikey", "token", "auth", "secret", "password", "access_token"}
        
        redacted = False
        for key in list(query_params.keys()):
            if key.lower() in sensitive_keys:
                query_params[key] = ["[REDACTED]"]
                redacted = True
        
        if redacted:
            new_query = urlencode(query_params, doseq=True)
            parsed = parsed._replace(query=new_query)
            return urlunparse(parsed)
        
        return url
    except Exception:
        # If redaction fails, return a safe placeholder
        return "[URL-REDACTION-FAILED]"


def call_external_api(service_id: str, endpoint: str = "", method: str = "GET", 
                     json_data: dict = None, params: dict = None, headers: dict = None):
    """
    Makes a safe HTTP request to a whitelisted external API.
    
    Args:
        service_id (str): Identifier for the target service (must map to allowed base URL)
        endpoint (str): API endpoint path (e.g., "/users/123")
        method (str): HTTP method (GET, POST, etc.)
        json_data (dict, optional): JSON payload for POST/PUT/etc.
        params (dict, optional): Query parameters
        headers (dict, optional): Additional headers
    
    Returns:
        Flask response (JSON) with sanitized data or error
    """
    # 1. Validate service_id against hardcoded allowlist
    if service_id not in ALLOWED_BASE_URLS:
        logger.warning(f"Blocked request to non-allowed service: {service_id}")
        return jsonify({
            "error": "Service not allowed",
            "message": "The requested external service is not permitted."
        }), 403

    base_url = service_id  # service_id is the full base URL in our allowlist

    # 2. Safely construct the full URL (never from raw user-controlled input directly)
    # We only append a sanitized endpoint path
    if endpoint:
        # Ensure endpoint starts with / if provided
        if not endpoint.startswith("/"):
            endpoint = "/" + endpoint
        full_url = base_url.rstrip("/") + endpoint
    else:
        full_url = base_url

    # 3. Prepare request kwargs with security best practices
    request_kwargs = {
        "method": method.upper(),
        "url": full_url,
        "timeout": (3, 10),      # connect timeout=3s, read timeout=10s
        "verify": True,          # Always verify SSL certificates
        "headers": headers or {},
    }

    if json_data:
        request_kwargs["json"] = json_data
    if params:
        request_kwargs["params"] = params

    # 4. Log the request with redaction (never log full URL with secrets)
    safe_url_for_log = redact_url_for_logging(full_url)
    if params:
        safe_params = {k: "[REDACTED]" if k.lower() in {"key", "api_key", "token"} else v 
                      for k, v in params.items()}
        logger.info(f"Calling external API: {method} {safe_url_for_log} | params={safe_params}")
    else:
        logger.info(f"Calling external API: {method} {safe_url_for_log}")

    try:
        response = requests.request(**request_kwargs)

        # 5. Return sanitized response
        try:
            data = response.json()
        except ValueError:
            # Non-JSON response
            data = {"raw_content": response.text[:1000]}  # limit size

        return jsonify({
            "status": "success",
            "status_code": response.status_code,
            "data": data
        }), response.status_code

    except requests.exceptions.Timeout:
        logger.error(f"Timeout calling external service {service_id}")
        return jsonify({
            "error": "Request timeout",
            "message": "The external service did not respond in time."
        }), 504

    except requests.exceptions.SSLError:
        logger.error(f"SSL error calling external service {service_id}")
        return jsonify({
            "error": "Security error",
            "message": "Failed to establish secure connection."
        }), 502

    except requests.exceptions.RequestException as e:
        # Catch all other requests exceptions (ConnectionError, HTTPError, etc.)
        # Do NOT forward upstream error details to the client
        logger.error(f"Request exception calling {service_id}: {type(e).__name__}")
        return jsonify({
            "error": "External service unavailable",
            "message": "Failed to communicate with the external service."
        }), 502

    except Exception as e:
        # Catch any unexpected errors
        logger.exception(f"Unexpected error in call_external_api for {service_id}")
        return jsonify({
            "error": "Internal error",
            "message": "An unexpected error occurred while processing the request."
        }), 500