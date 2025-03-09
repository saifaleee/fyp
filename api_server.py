import os
import time
import uuid
import shutil
from flask import Flask, request, jsonify, send_file
import subprocess
import threading
from werkzeug.utils import secure_filename

# Import MasterScript for direct calling
from MasterScript import process_single_video

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'Processed_Videos'
ALLOWED_EXTENSIONS = {'mp4', 'mov', 'avi'}
MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100 MB max upload

# Create necessary folders
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Track processing status
processing_status = {}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/process_video', methods=['POST'])
def process_video():
    # Check if video file is present in the request
    if 'video' not in request.files:
        return jsonify({'error': 'No video file provided'}), 400
    
    file = request.files['video']
    
    # Check if the file is valid
    if file.filename == '':
        return jsonify({'error': 'Empty filename'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': f'File type not allowed. Supported types: {", ".join(ALLOWED_EXTENSIONS)}'}), 400
    
    # Generate a unique ID for this processing task
    task_id = str(uuid.uuid4())
    
    # Create unique filename to avoid conflicts
    original_filename = secure_filename(file.filename)
    base_name = os.path.splitext(original_filename)[0]
    unique_filename = f"{base_name}_{task_id}.mp4"
    file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
    
    # Save the uploaded file
    file.save(file_path)
    
    # Update status
    processing_status[task_id] = {
        'status': 'uploading',
        'progress': 0,
        'original_filename': original_filename,
        'unique_filename': unique_filename,
        'started_at': time.time()
    }
    
    # Start processing in a separate thread
    thread = threading.Thread(target=process_video_task, args=(task_id, file_path, base_name))
    thread.start()
    
    # Return the task ID so the client can check status
    return jsonify({
        'task_id': task_id,
        'message': 'Video uploaded and processing started'
    })

def process_video_task(task_id, video_path, base_name):
    try:
        # Update status
        processing_status[task_id]['status'] = 'processing'
        processing_status[task_id]['progress'] = 10
        
        # Process the video using MasterScript
        output_folder = os.path.join(PROCESSED_FOLDER, base_name)
        
        # Option 1: Call process_single_video directly
        process_single_video(video_path, output_folder)
        
        # Option 2: Run MasterScript.py as a subprocess (uncomment if preferred)
        # process = subprocess.Popen(
        #     ["python", "MasterScript.py", video_path, output_folder],
        #     stdout=subprocess.PIPE,
        #     stderr=subprocess.PIPE
        # )
        # stdout, stderr = process.communicate()
        
        # Update status
        processing_status[task_id]['status'] = 'completed'
        processing_status[task_id]['progress'] = 100
        processing_status[task_id]['output_folder'] = output_folder
        processing_status[task_id]['completed_at'] = time.time()
        
        # Find the output files
        visualization_file = os.path.join(output_folder, f"{base_name}_visualization.mp4")
        keypoints_file = os.path.join(output_folder, f"{base_name}_keypoints.mp4")
        
        if not os.path.exists(visualization_file):
            visualization_file = None
        if not os.path.exists(keypoints_file):
            keypoints_file = None
        
        processing_status[task_id]['visualization_file'] = visualization_file
        processing_status[task_id]['keypoints_file'] = keypoints_file
        
    except Exception as e:
        # Update status on error
        processing_status[task_id]['status'] = 'error'
        processing_status[task_id]['error'] = str(e)
        print(f"Error processing video: {e}")

@app.route('/api/status/<task_id>', methods=['GET'])
def get_status(task_id):
    if task_id not in processing_status:
        return jsonify({'error': 'Task ID not found'}), 404
    
    return jsonify(processing_status[task_id])

@app.route('/api/download/<task_id>/<file_type>', methods=['GET'])
def download_file(task_id, file_type):
    if task_id not in processing_status:
        return jsonify({'error': 'Task ID not found'}), 404
    
    task = processing_status[task_id]
    
    if task['status'] != 'completed':
        return jsonify({'error': 'Processing not yet complete', 'status': task['status']}), 400
    
    if file_type == 'visualization':
        file_path = task.get('visualization_file')
        if not file_path or not os.path.exists(file_path):
            return jsonify({'error': 'Visualization file not found'}), 404
    elif file_type == 'keypoints':
        file_path = task.get('keypoints_file')
        if not file_path or not os.path.exists(file_path):
            return jsonify({'error': 'Keypoints file not found'}), 404
    else:
        return jsonify({'error': 'Invalid file type. Use "visualization" or "keypoints"'}), 400
    
    # Return the file
    return send_file(file_path, as_attachment=True)

@app.route('/api/cleanup/<task_id>', methods=['DELETE'])
def cleanup(task_id):
    if task_id not in processing_status:
        return jsonify({'error': 'Task ID not found'}), 404
    
    # Get task info
    task = processing_status[task_id]
    
    # Delete the original uploaded file if it exists
    upload_path = os.path.join(UPLOAD_FOLDER, task.get('unique_filename', ''))
    if os.path.exists(upload_path):
        os.remove(upload_path)
    
    # Delete the task from status dictionary
    del processing_status[task_id]
    
    return jsonify({'message': 'Cleanup completed'})

if __name__ == '__main__':
    # Run API server
    app.run(host='0.0.0.0', port=5000, debug=True) 