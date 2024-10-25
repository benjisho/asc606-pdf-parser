import os
import mimetypes
import subprocess
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash
import clamd  # For communicating with the ClamAV daemon
import PyPDF2  # For verifying the file is a valid PDF
import shutil  # For creating isolated temp directories
import logging  # For logging

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # For flash messaging

UPLOAD_FOLDER = '/app/pdf_files_to_parse'
OUTPUT_FOLDER = '/app/output_files'
ALLOWED_EXTENSIONS = {'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Set up logging to capture more information about ClamAV issues
logging.basicConfig(level=logging.INFO)

# Optional ClamAV setup - attempt to connect to ClamAV if available
def connect_to_clamav():
    try:
        cd = clamd.ClamdNetworkSocket(host='clamav', port=3310)
        cd.ping()  # Ping to ensure ClamAV is reachable
        logging.info("Connected to ClamAV")
        return cd
    except Exception as e:
        logging.warning(f"ClamAV not available: {e}")
        return None

clamav_client = connect_to_clamav()  # Try to establish connection at app startup

# Function to check if file extension is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Function to check if a file is a valid PDF
def is_valid_pdf(file_path):
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            return len(pdf_reader.pages) > 0
    except (PyPDF2.errors.PdfReadError, FileNotFoundError, IsADirectoryError):
        return False

# Function to scan file with ClamAV if available
def scan_with_clamav(file_path):
    if clamav_client:
        try:
            result = clamav_client.scan(file_path)
            logging.info(f"ClamAV scan result: {result}")  # Log the scan result
            
            if result is None:
                logging.warning("ClamAV scan result is None. Skipping scan.")
                return True

            scan_result = result.get(file_path)
            return scan_result and scan_result[0] == 'OK'
        except Exception as e:
            logging.error(f"ClamAV scan failed: {e}")
            return False
    else:
        logging.info("ClamAV is not available, skipping virus scan.")
        return True  # Assume clean if ClamAV is unavailable

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return render_template('index.html', error_message="No file part in the request")

    file = request.files['file']

    if file.filename == '':
        return render_template('index.html', error_message="No selected file")

    if file and allowed_file(file.filename):
        # Step 1: Upload the file to a temporary directory to isolate it
        temp_dir = os.path.join('/tmp', file.filename)
        os.makedirs(temp_dir, exist_ok=True)
        file_path = os.path.join(temp_dir, file.filename)
        file.save(file_path)

        # Set file permissions to read and write for the owner, no execute permissions
        os.chmod(file_path, 0o600)

        # Step 2: Scan the uploaded file with ClamAV daemon for viruses, if available
        if not scan_with_clamav(file_path):
            shutil.rmtree(temp_dir)  # Remove temp directory and file
            return render_template('index.html', error_message="File contains a virus or could not be scanned!")

        # Step 3: Check if the file is a valid PDF
        if not is_valid_pdf(file_path):
            shutil.rmtree(temp_dir)  # Remove temp directory and file
            return render_template('index.html', error_message="Invalid or corrupted PDF file")

        # Step 4: Move the validated file to the upload directory for parsing
        shutil.move(file_path, os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
        shutil.rmtree(temp_dir)  # Clean up temp directory after processing

        # Step 5: Parse the PDF
        subprocess.run(['python3', '/app/asc606-pdf-parser-app/asc606-pdf-parser.py'], check=True)

        output_file = f"{os.path.splitext(file.filename)[0]}.txt"
        return render_template('index.html', output_file=output_file)
    else:
        return render_template('index.html', error_message="File type not allowed. Only PDF files are accepted.")

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(OUTPUT_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
