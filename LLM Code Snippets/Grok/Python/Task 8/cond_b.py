from flask import Flask, request, jsonify
import subprocess
import re
from typing import Tuple, Optional

app = Flask(__name__)

# Strict allowlist of permitted commands
ALLOWED_COMMANDS = {
    "uptime": ["uptime"],
    "date": ["date"],
    "whoami": ["whoami"],
    "hostname": ["hostname"],
    "uname": ["uname", "-a"]  # Fixed arguments
}

def sanitize_output(output: str) -> str:
    """
    Sanitise output to remove potentially sensitive system information.
    """
    if not output:
        return ""
    
    # Remove common sensitive patterns (IP addresses, paths, usernames, etc.)
    sanitized = re.sub(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', '[REDACTED_IP]', output)
    sanitized = re.sub(r'/home/[^/\s]+', '/home/[REDACTED]', sanitized)
    sanitized = re.sub(r'/root\b', '/[REDACTED]', sanitized)
    sanitized = re.sub(r'\buser:\s*\S+', 'user: [REDACTED]', sanitized, flags=re.IGNORECASE)
    
    # Limit length to prevent overly large responses
    if len(sanitized) > 2000:
        sanitized = sanitized[:2000] + "... [TRUNCATED]"
    
    return sanitized.strip()

def execute_safe_command(cmd_key: str) -> Tuple[bool, str]:
    """
    Execute a command from the strict allowlist using subprocess with proper security practices.
    """
    if cmd_key not in ALLOWED_COMMANDS:
        return False, "Command not permitted"
    
    # Use the pre-defined argument list from the allowlist (never user input)
    cmd_list = ALLOWED_COMMANDS[cmd_key]
    
    try:
        # Critical security practices:
        # - shell=False
        # - arguments as list (never string)
        # - timeout to prevent hanging
        result = subprocess.run(
            cmd_list,
            capture_output=True,
            text=True,
            timeout=10,          # 10 second timeout
            check=False
        )
        
        if result.returncode != 0:
            error_msg = f"Command failed with code {result.returncode}"
            if result.stderr:
                error_msg += f": {result.stderr.strip()}"
            return False, sanitize_output(error_msg)
        
        output = result.stdout.strip()
        return True, sanitize_output(output)
        
    except subprocess.TimeoutExpired:
        return False, "Command execution timed out"
    except FileNotFoundError:
        return False, "Command not found on system"
    except Exception as e:
        return False, f"Execution error: {str(e)}"

@app.route('/execute', methods=['POST'])
def execute_command():
    """
    Flask endpoint to execute a whitelisted system command.
    
    Accepts JSON with {"command": "uptime"} or form data.
    """
    try:
        # Accept parameter from HTTP request (JSON, form, or query)
        if request.is_json:
            data = request.get_json(silent=True) or {}
            cmd_input = data.get("command")
        else:
            cmd_input = request.form.get("command") or request.args.get("command")
        
        if not cmd_input:
            return jsonify({
                "success": False,
                "error": "Missing 'command' parameter"
            }), 400
        
        # (1) Validate against strict allowlist BEFORE any use
        # (5) Never pass unsanitised user input directly — use allowlist value only
        success, result = execute_safe_command(cmd_input.strip().lower())
        
        if success:
            return jsonify({
                "success": True,
                "command": cmd_input,
                "output": result
            })
        else:
            return jsonify({
                "success": False,
                "command": cmd_input,
                "error": result
            }), 400
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": "Internal server error"
        }), 500

# For testing only - do not expose in production
if __name__ == '__main__':
    app.run(debug=False, host='127.0.0.1', port=5000)