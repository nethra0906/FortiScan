from flask import Flask, request, jsonify
import subprocess
from typing import Optional

app = Flask(__name__)

ALLOWED_ACTIONS = {
    "status": ["systemctl", "status", "nginx"],
    "disk": ["df", "-h"],
    "uptime": ["uptime"],
    # Add only what you explicitly need
}

@app.route('/execute', methods=['POST'])
def safe_execute():
    action = request.json.get('action') if request.is_json else request.args.get('action')
    
    if not action or action not in ALLOWED_ACTIONS:
        return jsonify({"error": "Invalid or unauthorized action"}), 400
    
    try:
        # Use subprocess with argument list (never shell=True with user input)
        result = subprocess.run(
            ALLOWED_ACTIONS[action],
            capture_output=True,
            text=True,
            timeout=10,
            check=True
        )
        return jsonify({
            "action": action,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        })
    except subprocess.CalledProcessError as e:
        return jsonify({"error": "Command failed", "output": e.stderr}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500