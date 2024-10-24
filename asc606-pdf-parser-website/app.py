import os
import mimetypes
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash
import subprocess
import PyPDF2  # For verifying the file is a valid PDF

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # For flash messaging

UPLOAD_FOLDER = '/app/pdf_files_to_parse'
OUTPUT_FOLDER = '/app/output_files'
ALLOWED_EXTENSIONS = {'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    # Check if the file has an allowed extension (PDF in this case)
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def is_valid_pdf(file_path):
    try:
        # Attempt to open the file as a PDF using PyPDF2
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            return len(pdf_reader.pages) > 0  # Check that the PDF has at least one page
    except (PyPDF2.errors.PdfReadError, FileNotFoundError, IsADirectoryError):
        return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash("No file part in the request")
        return redirect(request.url)
    
    file = request.files['file']
    
    if file.filename == '':
        flash("No selected file")
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        # Save the uploaded file to the upload directory
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)

        # Check if the uploaded file is indeed a PDF
        if not is_valid_pdf(file_path):
            os.remove(file_path)  # Remove the invalid file
            flash("Invalid or corrupted PDF file")
            return redirect(request.url)

        # Run the parser directly within the container
        subprocess.run(['python3', '/app/asc606-pdf-parser-app/asc606-pdf-parser.py'], check=True)
        
        # Extract the output file (assuming it gets created with the same name as the PDF, but with .txt extension)
        output_file = f"{os.path.splitext(file.filename)[0]}.txt"
        return render_template('index.html', output_file=output_file)
    else:
        flash("File type not allowed. Only PDF files are accepted.")
        return redirect(request.url)

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(OUTPUT_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
