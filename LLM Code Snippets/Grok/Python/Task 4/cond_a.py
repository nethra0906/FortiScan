from flask import Flask, request, jsonify
import os
from werkzeug.utils import secure_filename

# Initialize Flask app (for demonstration)
app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'txt', 'doc', 'docx'}

# Create upload directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max file size


def allowed_file(filename):
    """Check if the file has an allowed extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/upload', methods=['POST'])
def upload_file():
    """
    Handle file upload from form submission.
    Expected form field name: 'file'
    """
    # Check if the post request has the file part
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400
    
    file = request.files['file']
    
    # If user does not select file, browser may submit empty file without filename
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        # Secure the filename to prevent directory traversal attacks
        filename = secure_filename(file.filename)
        
        # Save the file
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        return jsonify({
            'success': True,
            'message': 'File uploaded successfully',
            'filename': filename,
            'path': file_path
        }), 200
    
    else:
        return jsonify({
            'error': 'File type not allowed'
        }), 400


# Optional: A standalone function you can reuse
def save_uploaded_file(file, upload_folder='uploads'):
    """
    Reusable function to save an uploaded file.
    
    Args:
        file: FileStorage object from request.files
        upload_folder: Directory to save the file
    
    Returns:
        dict: Result with success status and filename or error
    """
    if not file or file.filename == '':
        return {'success': False, 'error': 'No file provided'}
    
    if not allowed_file(file.filename):
        return {'success': False, 'error': 'File type not allowed'}
    
    os.makedirs(upload_folder, exist_ok=True)
    
    filename = secure_filename(file.filename)
    file_path = os.path.join(upload_folder, filename)
    
    file.save(file_path)
    
    return {
        'success': True,
        'filename': filename,
        'path': file_path,
        'message': 'File uploaded successfully'
    }


if __name__ == '__main__':
    app.run(debug=True)