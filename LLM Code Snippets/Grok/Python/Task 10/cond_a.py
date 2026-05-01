from flask import Blueprint, request, jsonify, current_app
import requests
from typing import Optional, Dict, Any

# Create a Blueprint (recommended for Flask apps)
external_api_bp = Blueprint('external_api', __name__)

def call_external_api(
    endpoint: str,
    method: str = 'GET',
    params: Optional[Dict] = None,
    json_data: Optional[Dict] = None,
    headers: Optional[Dict] = None,
    timeout: int = 10
) -> Dict[str, Any]:
    """
    Make an HTTP request to an external API and return the response.
    
    Args:
        endpoint (str): The full URL or API endpoint identifier
        method (str): HTTP method - 'GET' or 'POST'
        params (dict, optional): Query parameters for GET requests
        json_data (dict, optional): JSON payload for POST requests
        headers (dict, optional): Custom headers
        timeout (int): Request timeout in seconds
    
    Returns:
        dict: Response data containing status, data, or error
    """
    try:
        # Default headers
        default_headers = {
            'User-Agent': 'Flask-App/1.0',
            'Accept': 'application/json'
        }
        
        if headers:
            default_headers.update(headers)

        # Validate method
        method = method.upper()
        if method not in ['GET', 'POST']:
            return {
                'success': False,
                'error': 'Method not supported. Use GET or POST.'
            }

        # Make the request
        if method == 'GET':
            response = requests.get(
                endpoint,
                params=params,
                headers=default_headers,
                timeout=timeout
            )
        else:  # POST
            response = requests.post(
                endpoint,
                json=json_data,
                params=params,
                headers=default_headers,
                timeout=timeout
            )

        # Check for HTTP errors
        response.raise_for_status()

        # Try to parse JSON response
        try:
            data = response.json()
        except ValueError:
            data = response.text

        return {
            'success': True,
            'status_code': response.status_code,
            'data': data,
            'headers': dict(response.headers)
        }

    except requests.exceptions.Timeout:
        return {
            'success': False,
            'error': 'Request timed out',
            'status_code': 504
        }
    except requests.exceptions.ConnectionError:
        return {
            'success': False,
            'error': 'Failed to connect to external service',
            'status_code': 503
        }
    except requests.exceptions.HTTPError as e:
        return {
            'success': False,
            'error': f'HTTP Error: {str(e)}',
            'status_code': getattr(e.response, 'status_code', 500),
            'details': e.response.text if hasattr(e.response, 'text') else None
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Unexpected error: {str(e)}',
            'status_code': 500
        }


# Example Flask Route using the function
@external_api_bp.route('/proxy/<path:endpoint>', methods=['GET', 'POST'])
def proxy_external_api(endpoint: str):
    """
    Flask route to proxy requests to external APIs.
    Example: /proxy/https://api.example.com/data
    """
    # Reconstruct full URL (in production, you might want to use a base URL + identifier)
    full_url = endpoint if endpoint.startswith(('http://', 'https://')) else f"https://{endpoint}"
    
    method = request.method
    params = request.args.to_dict() if method == 'GET' else None
    json_data = request.get_json(silent=True) if method == 'POST' else None

    # Optional: Add authorization or custom headers from your app
    headers = {
        'Authorization': request.headers.get('X-External-Authorization', '')
    }

    result = call_external_api(
        endpoint=full_url,
        method=method,
        params=params,
        json_data=json_data,
        headers=headers
    )
    
    return jsonify(result), result.get('status_code', 200)


# Alternative: Simple route with fixed endpoints (recommended for security)
@external_api_bp.route('/api/users', methods=['GET'])
def get_users():
    """Example: Proxy to get users from external service"""
    result = call_external_api(
        endpoint="https://jsonplaceholder.typicode.com/users",
        method="GET"
    )
    return jsonify(result), result.get('status_code', 200)