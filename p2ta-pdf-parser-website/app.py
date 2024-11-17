import os
import time
import subprocess
import logging
import requests  # Add for Hugging Face API
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash
import clamd  # For communicating with the ClamAV daemon
import PyPDF2  # For verifying the file is a valid PDF

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # For flash messaging

# Update UPLOAD_FOLDER logic
UPLOAD_FOLDER = '/app/pdf_files_to_parse'
OUTPUT_FOLDER = '/app/output_files'
ALLOWED_EXTENSIONS = {'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

HUGGINGFACE_API_KEY = os.getenv('HUGGINGFACE_API_KEY')  # Add your API key here
HUGGINGFACE_SUMMARY_MODEL = "facebook/bart-large-cnn"

logging.basicConfig(level=logging.INFO)

def is_clamav_container_present():
    """Check if the ClamAV container is running by pinging."""
    try:
        result = subprocess.run(
            ["ping", "-c", "1", "clamav-container"],
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

    # Retry loop that gracefully gives up if ClamAV isn't available after a few tries.
    retry_count = 0
    max_retries = 20
    while retry_count < max_retries:
        try:
            cd = clamd.ClamdNetworkSocket(host='clamav-container', port=3310)
            cd.ping()
            logging.info("Connected to ClamAV")
            return cd
        except Exception as e:
            retry_count += 1
            logging.warning(f"ClamAV still starting. Retrying ({retry_count}/{max_retries})... | {e}")
            time.sleep(20)


clamav_client = connect_to_clamav()  # Try to establish connection at app startup

# New function to get parser script based on selected form type
def get_parser_script(form_type):
    parsers = {
        "asc606": "p2ta-pdf-parser-app/asc606-pdf-parser.py",
        "asc842": "p2ta-pdf-parser-app/asc842-pdf-parser.py",
        "asc805": "p2ta-pdf-parser-app/asc805-pdf-parser.py",
        "asc718": "p2ta-pdf-parser-app/asc718-pdf-parser.py",
        "asc815": "p2ta-pdf-parser-app/asc815-pdf-parser.py",
        "ifrs15": "p2ta-pdf-parser-app/ifrs15-pdf-parser.py",
        "asc450": "p2ta-pdf-parser-app/asc450-pdf-parser.py",
        "asc320": "p2ta-pdf-parser-app/asc320-pdf-parser.py",
        "asc330": "p2ta-pdf-parser-app/asc330-pdf-parser.py",
        "asc250": "p2ta-pdf-parser-app/asc250-pdf-parser.py",
    }
    return parsers.get(form_type)  # Return just the relative path to each parser

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

def get_form_folder(form_type):
    """Ensure the upload directory exists for the given form type."""
    form_folder = os.path.join(UPLOAD_FOLDER, form_type)
    os.makedirs(form_folder, exist_ok=True)
    return form_folder

def generate_ai_summary(file_path):
    """Generate an AI summary for the given text file."""
    with open(file_path, 'r') as file:
        text = file.read()

    headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}
    payload = {
        "inputs": text,
        "options": {"use_gpu": False}
    }
    try:
        response = requests.post(
            f"https://api-inference.huggingface.co/models/{HUGGINGFACE_SUMMARY_MODEL}",
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        result = response.json()
        return result[0]['summary_text'] if result else "No summary generated."
    except Exception as e:
        logging.error(f"Failed to generate AI summary: {e}")
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return render_template('index.html', error_message="No file part in the request")

    file = request.files['file']
    form_type = request.form['form_type']  # Get the selected form type
    generate_summary = request.form.get('generate_summary')  # Check if AI Summary is toggled

    if file.filename == '':
        return render_template('index.html', error_message="No selected file")

    if file and allowed_file(file.filename):
        # Save the uploaded file directly to `pdf_files_to_parse`
        form_folder = get_form_folder(form_type)
        file_path = os.path.join(form_folder, file.filename)
        file.save(file_path)

        # Set file permissions
        os.chmod(file_path, 0o644)

        # Scan the uploaded file with ClamAV daemon for viruses, if available
        if not scan_with_clamav(file_path):
            os.remove(file_path)  # Remove file if it's infected
            return render_template('index.html', error_message="File contains a virus or could not be scanned!")

        # Check if the file is a valid PDF
        if not is_valid_pdf(file_path):
            os.remove(file_path)  # Remove invalid file
            return render_template('index.html', error_message="Invalid or corrupted PDF file")

        # Route to the appropriate parser script
        parser_script = get_parser_script(form_type)
        if parser_script:
            try:
                if parser_script == "p2ta-pdf-parser.py":
                    subprocess.run(['python3', parser_script, '--form_type', form_type], check=True)
                else:
                    subprocess.run(['python3', parser_script], check=True)
            except subprocess.CalledProcessError as e:
                logging.error(f"Parser failed: {e}")
                return render_template('index.html', error_message="Parser failed.")

        if generate_summary:
            summary = generate_ai_summary(file_path)
            if summary:
                return render_template('index.html', ai_summary=summary, success_message="AI Summary generated.")
            else:
                return render_template('index.html', error_message="Failed to generate AI Summary.")

         # Output the result file and display success message
        output_file = f"{os.path.splitext(file.filename)[0]}.txt"
        success_message = "No viruses found. Parsing PDF..."
        return render_template('index.html', output_file=output_file, success_message=success_message)
    else:
        return render_template('index.html', error_message="File type not allowed. Only PDF files are accepted.")


@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(OUTPUT_FOLDER, filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')