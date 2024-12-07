import os
import time
import subprocess
import logging
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

import openai
# Configure OpenAI API Key
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')  # Add your API key here
if not OPENAI_API_KEY:
    logging.warning("OPENAI_API_KEY is not set. AI summary feature will be disabled.")
    AI_SUPPORT_ENABLED = False
else:
    AI_SUPPORT_ENABLED = True
    openai.api_key = OPENAI_API_KEY  # Configure the global OpenAI client


def generate_ai_summary(file_path):
    """Generate an AI summary for the given text file using OpenAI."""
    try:
        # Read the file content for summarization
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()

        # Truncate text to fit within token limits
        truncated_text = text[:2048]

        # Call OpenAI for summarization
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an AI assistant specializing in accounting document summaries. Provide a concise summary."},
                {"role": "user", "content": f"Please summarize the following document:\n\n{truncated_text}"}
            ]
        )
        summary = response["choices"][0]["message"]["content"].strip()
        return summary

    except Exception as e:
        logging.error(f"Error during AI summarization: {e}")
        return "An unexpected error occurred while generating the summary."

@app.route('/')
def index():
    openai_key_available = bool(os.getenv('OPENAI_API_KEY'))  # Dynamically check the key
    logging.debug(f"OPENAI_API_KEY detected: {openai_key_available}")
    return render_template('index.html', ai_enabled=openai_key_available)

@app.route('/upload', methods=['POST'])
def upload_file():
    openai_key_available = bool(os.getenv('OPENAI_API_KEY'))  # Check for OpenAI API key
    if 'file' not in request.files:
        return render_template('index.html', ai_enabled=openai_key_available, error_message="No file part in the request")

    file = request.files['file']
    form_type = request.form.get('form_type')  # Get the selected form type
    generate_summary = request.form.get('ai_summary', 'false').lower() == 'true'  # Check if AI Summary is toggled

    if not file or file.filename == '':
        return render_template('index.html', ai_enabled=openai_key_available, error_message="No selected file")

    if allowed_file(file.filename):
        # Save the uploaded file
        form_folder = get_form_folder(form_type)
        file_path = os.path.join(form_folder, file.filename)
        file.save(file_path)

        # Set file permissions
        os.chmod(file_path, 0o644)

        # Scan the uploaded file with ClamAV, if available
        if not scan_with_clamav(file_path):
            os.remove(file_path)
            return render_template('index.html', ai_enabled=openai_key_available, error_message="File contains a virus or could not be scanned!")

        # Check if the file is a valid PDF
        if not is_valid_pdf(file_path):
            os.remove(file_path)
            return render_template('index.html', ai_enabled=openai_key_available, error_message="Invalid or corrupted PDF file.")

        # Generate AI summary if toggled
        if generate_summary:
            output_txt_file = os.path.join(OUTPUT_FOLDER, f"{os.path.splitext(file.filename)[0]}.txt")
            # Ensure the text file exists before summarizing
            if os.path.exists(output_txt_file):
                summary = generate_ai_summary(output_txt_file)
                if summary:
                    # Convert summary to HTML
                    import markdown
                    summary_html = markdown.markdown(summary)
                    logging.info(f"AI Summary Output: {summary_html}")
                    return render_template(
                        'index.html',
                        ai_summary=summary_html,
                        ai_enabled=openai_key_available,
                        success_message="AI Summary generated."
                    )
                else:
                    return render_template('index.html', ai_enabled=openai_key_available, error_message="Failed to generate AI Summary.")
            else:
                logging.error(f"Text file for summarization not found: {output_txt_file}")
                return render_template('index.html', ai_enabled=openai_key_available, error_message="Text file not found for summarization.")

        # Output the result file and display success message
        output_file = f"{os.path.splitext(file.filename)[0]}.txt"
        success_message = "No viruses found. Parsing PDF..."
        download_link = url_for('download_file', filename=output_file)

        return render_template(
            'index.html',
            ai_enabled=openai_key_available,
            success_message=success_message,
            output_file=output_file,
            download_link=download_link
        )
    else:
        return render_template('index.html', ai_enabled=openai_key_available, error_message="File type not allowed. Only PDF files are accepted.")

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(OUTPUT_FOLDER, filename, as_attachment=True)

@app.route('/ask', methods=['POST'])
def ask_question():
    user_query = request.form.get('user_query', None)
    if not user_query:
        return render_template('index.html', error_message="Please enter a question to ask.")

    # Assume the last uploaded file is used
    uploaded_file_path = os.path.join(OUTPUT_FOLDER, "last_uploaded_file.txt")

    if os.path.exists(uploaded_file_path):
        with open(uploaded_file_path, 'r', encoding='utf-8') as file:
            text = file.read()

        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an AI assistant specializing in accounting document summaries. Provide a concise summary."},
                    {"role": "user", "content": f"Please summarize the following document:\n\n{truncated_text}"}
                ]
            )
            answer = response["choices"][0]["message"]["content"].strip()

            return render_template(
                'index.html',
                success_message="Here's the response to your question.",
                ai_summary=answer
            )

        except Exception as e:
            logging.error(f"Error answering question: {e}")
            return render_template('index.html', error_message="An unexpected error occurred while answering your question.")
    else:
        return render_template('index.html', error_message="No document available for querying.")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)