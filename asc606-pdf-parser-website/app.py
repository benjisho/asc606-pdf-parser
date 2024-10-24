import os
import mimetypes
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash
import subprocess
import PyPDF2  # For verifying the file is a valid PDF
import shutil  # For creating isolated temp directories

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # For flash messaging

UPLOAD_FOLDER = '/app/pdf_files_to_parse'
OUTPUT_FOLDER = '/app/output_files'
ALLOWED_EXTENSIONS = {'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def is_valid_pdf(file_path):
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            return len(pdf_reader.pages) > 0
    except (PyPDF2.errors.PdfReadError, FileNotFoundError, IsADirectoryError):
        return False

def scan_with_clamav(file_path):
    result = subprocess.run(['clamscan', file_path], stdout=subprocess.PIPE)
    return 'OK' in result.stdout.decode()

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
        # Save the uploaded file to a temp isolated directory for scanning
        temp_dir = os.path.join('/tmp', file.filename)
        os.makedirs(temp_dir, exist_ok=True)
        file_path = os.path.join(temp_dir, file.filename)
        file.save(file_path)

        # Scan with ClamAV for viruses
        if not scan_with_clamav(file_path):
            shutil.rmtree(temp_dir)  # Remove temp directory and file
            return render_template('index.html', error_message="File contains a virus!")

        # Verify if the uploaded file is indeed a PDF
        if not is_valid_pdf(file_path):
            shutil.rmtree(temp_dir)  # Remove temp directory and file
            return render_template('index.html', error_message="Invalid or corrupted PDF file")

        # Move file to the upload directory for parsing after scanning and validation
        shutil.move(file_path, os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
        shutil.rmtree(temp_dir)  # Clean up temp directory

        # Run the parser within the container
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
