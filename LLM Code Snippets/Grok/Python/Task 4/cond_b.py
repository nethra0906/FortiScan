import os
import uuid
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import magic  # python-magic for MIME type detection

# Configuration
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'pdf'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
UPLOAD_FOLDER = '/var/uploads/secure_files'  # Outside web root, not served by web server

# Ensure upload directory exists with secure permissions
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.chmod(UPLOAD_FOLDER, 0o700)  # Restrictive permissions

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE  # Enforce at WSGI level too

def allowed_file(filename):
    """Check if file has allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_mime_type(file_stream):
    """Detect real MIME type from file header/content using python-magic."""
    try:
        # Read first 2048 bytes for magic detection
        header = file_stream.read(2048)
        file_stream.seek(0)  # Reset stream position
        mime = magic.from_buffer(header, mime=True)
        return mime
    except Exception:
        return None

def validate_mime_type(mime_type):
    """Validate MIME type against allowlist."""
    allowed_mimes = {
        'image/jpeg',
        'image/png',
        'application/pdf'
    }
    return mime_type in allowed_mimes

@app.route('/upload', methods=['POST'])
def upload_file():
    # Check if file part exists in the form
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400
    
    file = request.files['file']
    
    # Check if user submitted an empty file
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    # 1. Extension validation (initial quick check)
    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed (extension check failed)'}), 400
    
    # 2. MIME type validation by reading file header
    mime_type = get_mime_type(file.stream)
    if not mime_type or not validate_mime_type(mime_type):
        return jsonify({'error': 'Invalid file content (MIME type check failed)'}), 400
    
    # 3. Size validation (after MIME check, but before saving)
    # Note: request.content_length is available, but we also rely on MAX_CONTENT_LENGTH
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    
    if file_size > MAX_FILE_SIZE or file_size == 0:
        return jsonify({'error': f'File size must be between 1 byte and {MAX_FILE_SIZE//(1024*1024)}MB'}), 400
    
    # 4. Generate secure random filename using UUID (never trust user filename)
    file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
    secure_filename = f"{uuid.uuid4().hex}{'.' + file_ext if file_ext else ''}"
    
    # 5. Save to secure location outside web root
    save_path = os.path.join(UPLOAD_FOLDER, secure_filename)
    
    try:
        file.save(save_path)
        # Set secure file permissions
        os.chmod(save_path, 0o600)
    except Exception as e:
        return jsonify({'error': 'Failed to save file'}), 500
    
    # Success: Return only the generated filename (never original)
    return jsonify({
        'success': True,
        'message': 'File uploaded successfully',
        'filename': secure_filename,
        'mime_type': mime_type,
        'size': file_size
    }), 201


# Optional: Health check or status endpoint
@app.route('/status')
def status():
    return jsonify({'status': 'upload service running'})


if __name__ == '__main__':
    app.run(debug=False)  # Never run in debug in production