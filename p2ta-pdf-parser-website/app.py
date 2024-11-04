import os
import time
import subprocess
import logging
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash
import clamd  # For communicating with the ClamAV daemon
import PyPDF2  # For verifying the file is a valid PDF
import shutil  # For creating isolated temp directories

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # For flash messaging

UPLOAD_FOLDER = '/app/pdf_files_to_parse'
OUTPUT_FOLDER = '/app/output_files'
ALLOWED_EXTENSIONS = {'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

logging.basicConfig(level=logging.INFO)

def is_clamav_container_present():
    """Check if the ClamAV container is running by pinging."""
    try:
        result = subprocess.run(
            ["ping", "-c", "1", "p2ta-pdf-parser-clamav-1"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False
        )
        if result.returncode == 0:
            logging.info("ClamAV container detected. Starting website service with antivirus scanning.")
            return True
        else:
            logging.info("No ClamAV container detected. Starting website service without antivirus scanning.")
            return False
    except Exception as e:
        logging.error(f"Error checking for ClamAV container: {e}")
        return False

def connect_to_clamav():
    """If ClamAV is available, connect or wait indefinitely until it becomes available."""
    if not is_clamav_container_present():
        logging.info("ClamAV is not running. Starting website without antivirus scanning.")
        return None

    # Endless retry loop until ClamAV is available
    while True:
        try:
            cd = clamd.ClamdNetworkSocket(host='p2ta-pdf-parser-clamav-1', port=3310)
            cd.ping()  # Ping to ensure ClamAV is reachable
            logging.info("Connected to ClamAV")
            return cd
        except Exception as e:
            logging.warning(f"ClamAV still starting. Waiting... | {e}")
            time.sleep(10)

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
    clamav_scan_path = file_path.replace('/app/pdf_files_to_parse', '/scan')
    if clamav_client:  # Only scan if ClamAV is available
        try:
            result = clamav_client.scan(clamav_scan_path)
            logging.info(f"ClamAV scan result: {result}")
            
            if result is None:
                logging.warning("ClamAV scan returned None. Skipping scan.")
                return True  # Assume clean if no scan result

            # Match ClamAV response format by using clamav_scan_path as the key
            scan_result = result.get(clamav_scan_path)
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
        # Step 1: Save the uploaded file directly to `pdf_files_to_parse`
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)

        # Set file permissions
        os.chmod(file_path, 0o644)

        # Step 2: Scan the uploaded file with ClamAV daemon for viruses, if available
        if not scan_with_clamav(file_path):
            os.remove(file_path)  # Remove file if it's infected
            return render_template('index.html', error_message="File contains a virus or could not be scanned!")

        # Step 3: Check if the file is a valid PDF
        if not is_valid_pdf(file_path):
            os.remove(file_path)  # Remove invalid file
            return render_template('index.html', error_message="Invalid or corrupted PDF file")

        # Step 4: Parse the PDF
        subprocess.run(['python3', '/app/p2ta-pdf-parser-app/p2ta-pdf-parser.py'], check=True)

        # Step 5: Output the result file and display success message
        output_file = f"{os.path.splitext(file.filename)[0]}.txt"
        success_message = "No viruses found. Parsing PDF..."
        return render_template('index.html', output_file=output_file, success_message=success_message)
    else:
        return render_template('index.html', error_message="File type not allowed. Only PDF files are accepted.")


@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(OUTPUT_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
