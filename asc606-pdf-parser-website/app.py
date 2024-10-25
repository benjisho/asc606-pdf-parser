import os
import mimetypes
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

# Function to scan file with ClamAV daemon
def scan_with_clamav(file_path):
    try:
        cd = clamd.ClamdNetworkSocket(host='clamav', port=3310)  # Connect to the ClamAV container via network socket
        result = cd.scan(file_path)  # Scan the file
        logging.info(f"ClamAV scan result: {result}")  # Log the scan result
        
        # Debug output to check exact response
        if result is None:
            logging.error("ClamAV returned None. Could not scan the file.")
            return False

        # Check if the result indicates the file is clean
        if file_path in result and result[file_path][0] == 'OK':
            return True  # File is clean
        else:
            logging.error(f"ClamAV scan failed or detected an issue: {result}")
            return False  # File is infected or there was an issue
    except Exception as e:
        logging.error(f"ClamAV scan failed: {e}")
        return False

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

        # Step 2: Scan the uploaded file with ClamAV daemon for viruses
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
