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
if not HUGGINGFACE_API_KEY:
    logging.warning("HUGGINGFACE_API_KEY is not set. AI summary feature will be disabled.")
    AI_SUPPORT_ENABLED = False
else:
    AI_SUPPORT_ENABLED = True

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

def sanitize_text(text):
    """Sanitize text by removing problematic characters."""
    return text.encode('utf-8', 'ignore').decode('utf-8', 'ignore')


def generate_ai_summary(file_path):
    """Generate an AI summary for the given text file."""
    if not AI_SUPPORT_ENABLED:
        logging.info("AI Summary feature is disabled because HUGGINGFACE_API_KEY is not set.")
        return "AI Summary feature is disabled."

    try:
        # Read and sanitize the file content
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()
        text = sanitize_text(text)  # Ensure the text is sanitized
    except FileNotFoundError as e:
        logging.error(f"File not found: {file_path}")
        return "Error: Text file not found for summarization."
    except UnicodeDecodeError as e:
        logging.warning(f"UnicodeDecodeError encountered: {e}. Attempting re-encoding.")
        try:
            # Handle decoding error by re-encoding the file
            with open(file_path, 'rb') as file:
                raw_data = file.read()
            text = raw_data.decode('latin1').encode('utf-8').decode('utf-8')
        except Exception as inner_e:
            logging.error(f"Re-encoding failed: {inner_e}")
            return "Error: Failed to decode the text file."
    except Exception as e:
        logging.error(f"Unexpected error reading file for AI summary: {e}")
        return "Error reading the text file for summarization."

    if not text.strip():
        logging.warning("The input text for summarization is empty.")
        return "The file contains no text for summarization."

    # Prepare payload for Hugging Face API
    headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}
    payload = {
        "inputs": f"Summarize the following text as an accountant with structured Markdown. Use headings (e.g., ## Topic), bullet points, and numbered lists for clarity:\n\n{text[:1024]}",
        "options": {"use_gpu": False}
    }

    # Attempt API call with retries
    for attempt in range(3):  # Retry up to 3 times
        try:
            response = requests.post(
                f"https://api-inference.huggingface.co/models/{HUGGINGFACE_SUMMARY_MODEL}",
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()

            # Ensure only the summary text is extracted
            if isinstance(result, list) and 'summary_text' in result[0]:
                return result[0]['summary_text']
            else:
                logging.warning(f"Unexpected response format: {result}")
                return "No summary generated."
        except requests.exceptions.HTTPError as e:
            logging.error(f"HTTPError during Hugging Face API request (attempt {attempt + 1}/3): {e}")
            if attempt == 2:  # On final attempt, fail
                return "Failed to connect to the AI summarization service."
        except Exception as e:
            logging.error(f"Unexpected error during AI summarization: {e}")
            return "An unexpected error occurred while generating the summary."

@app.route('/')
def index():
    huggingface_key_available = bool(os.getenv('HUGGINGFACE_API_KEY'))  # Dynamically check the key
    logging.debug(f"HUGGINGFACE_API_KEY detected: {huggingface_key_available}")
    return render_template('index.html', ai_enabled=huggingface_key_available)

@app.route('/upload', methods=['POST'])
def upload_file():
    huggingface_key_available = bool(os.getenv('HUGGINGFACE_API_KEY'))  # Dynamic check for key
    if 'file' not in request.files:
        return render_template('index.html', ai_enabled=huggingface_key_available, error_message="No file part in the request")

    file = request.files['file']
    form_type = request.form.get('form_type')  # Get the selected form type
    generate_summary = request.form.get('ai_summary', 'false').lower() == 'true'  # Check if AI Summary is toggled

    if not file or file.filename == '':
        return render_template('index.html', ai_enabled=huggingface_key_available, error_message="No selected file")

    if allowed_file(file.filename):
        # Save the uploaded file directly to `pdf_files_to_parse`
        form_folder = get_form_folder(form_type)
        file_path = os.path.join(form_folder, file.filename)
        file.save(file_path)

        # Set file permissions
        os.chmod(file_path, 0o644)

        # Scan the uploaded file with ClamAV daemon for viruses, if available
        if not scan_with_clamav(file_path):
            os.remove(file_path)  # Remove file if it's infected
            return render_template('index.html', ai_enabled=huggingface_key_available, error_message="File contains a virus or could not be scanned!")

        # Check if the file is a valid PDF
        if not is_valid_pdf(file_path):
            os.remove(file_path)  # Remove invalid files
            return render_template('index.html', ai_enabled=huggingface_key_available, error_message="Invalid or corrupted PDF file.")

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
                return render_template('index.html', ai_enabled=huggingface_key_available, error_message="Parser failed.")
            
            # Generate AI summary if toggled
            if generate_summary:
                output_txt_file = os.path.join(OUTPUT_FOLDER, f"{os.path.splitext(file.filename)[0]}.txt")
                if os.path.exists(output_txt_file):  # Ensure the text file exists before summarizing
                    summary = generate_ai_summary(output_txt_file)
                    if summary:
                        # Pass only the AI output
                        import markdown
                        summary_html = markdown.markdown(summary)  # Convert Markdown to HTML
                        logging.info(f"AI Summary Output: {summary_html}")
                        return render_template(
                            'index.html',
                            ai_summary=summary_html,  # Only the AI-generated summary is passed
                            ai_enabled=huggingface_key_available,
                            success_message="AI Summary generated."
                        )
                    else:
                        return render_template('index.html', ai_enabled=huggingface_key_available, error_message="Failed to generate AI Summary.")
                else:
                    logging.error(f"Text file for summarization not found: {output_txt_file}")
                    return render_template('index.html', ai_enabled=huggingface_key_available, error_message="Text file not found for summarization.")

        # Output the result file and display success message
        output_file = f"{os.path.splitext(file.filename)[0]}.txt"
        success_message = "No viruses found. Parsing PDF..."
        download_link = url_for('download_file', filename=output_file)

        return render_template(
            'index.html',
            ai_enabled=huggingface_key_available,
            success_message=success_message,
            output_file=output_file,
            download_link=download_link
        )
    else:
        return render_template('index.html', ai_enabled=huggingface_key_available, error_message="File type not allowed. Only PDF files are accepted.")

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(OUTPUT_FOLDER, filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')