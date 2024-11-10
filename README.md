# PDF-2-Text for Accountants (P2TA)

This project is a Python-based solution designed to parse PDF documents related to various accounting standards, extract relevant information, and save the output as structured text files. The project includes a web-based interface and optional ClamAV antivirus scanning to ensure safe file handling for uploaded PDF files.

## Table of Contents
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Directory Structure](#directory-structure)
- [Usage](#usage)
  - [Before You Run the Code](#before-you-run-the-code)
  - [Command Line Arguments](#command-line-arguments)
  - [Option 1: Running the Script Locally](#option-1-running-the-script-locally)
  - [Option 2: Running with Docker](#option-2-running-with-docker)
  - [Option 3: Preferred Running with Docker Compose](#option-3-preferred-running-with-docker-compose)
    - [OPTIONAL: Enabling Antivirus Scanning in Docker Compose](#optional-enabling-antivirus-scanning-in-docker-compose)
- [Logging](#logging)
- [Notes](#notes)
- [License](#license)

## Features

- Extracts text from PDF files using PyMuPDF.
- Outputs parsed information to organized text files.
- Optional antivirus scanning using ClamAV.
- Optional `--debug` flag for detailed logging.

## Prerequisites

- Python 3.6+
- PyMuPDF library (`pymupdf`)
- (Optional) Docker if using containerized deployment

Install dependencies using:

```bash
pip install -r requirements.txt
```

## Directory Structure

- `pdf_files_to_parse/`: Directory containing PDF files to process.
- `output_files/`: Directory where extracted summaries are saved.
- `p2ta-pdf-parser-app/`: Core parser application, including individual parsers for accounting standards and the main parser script.
- `p2ta-pdf-parser-website/`: Flask-based web application providing a user interface.
- `virus-protection/clamav/`: Configuration files for ClamAV antivirus scanning.

## Usage

### Before You Run the Code

1. Place PDFs for processing in `pdf_files_to_parse`.
2. Run the script or use Docker commands below.
3. Check `output_files` for generated text summaries.

### Command Line Arguments

- `--form_type <type>`: Specify the accounting standard type (e.g., `asc606`, `asc718`).
- `--debug`: Enable detailed debug logging.

### Option 1: Running the Script Locally

To run the script directly:

```bash
python3 p2ta-pdf-parser-app/p2ta-pdf-parser.py --form_type asc606
```

With debug logging:

```bash
python3 p2ta-pdf-parser-app/p2ta-pdf-parser.py --form_type asc606 --debug
```

The script will process PDFs in `pdf_files_to_parse` and output summaries to `output_files`.

### Option 2: Running with Docker

To run the `pdf-parser` container alone:

```bash
docker run --rm \
  -v "$(pwd)/pdf_files_to_parse:/app/pdf_files_to_parse" \
  -v "$(pwd)/output_files:/app/output_files" \
  -e PYTHONUNBUFFERED=1 \
  benjisho/p2ta-pdf-parser:latest
```

### Option 3: Preferred Running with Docker Compose

For ease of use, Docker Compose can build and manage the containerized application:

```bash
# Build both website and parser containers
docker compose build website p2ta-pdf-parser

# Run the website service in detached mode (unsafe for production)
docker compose up -d --build website
# Or test website with
docker compose run --rm --build website

# Run p2ta-pdf-parser directly (quickest for command-line parsing)
docker compose run --rm --build p2ta-pdf-parser --form_type asc606 --debug
```

#### OPTIONAL: Enabling Antivirus Scanning in Docker Compose

For enhanced security, you can enable ClamAV to scan uploaded files in the `website` service:

```bash
docker compose -f docker-compose.yml -f ./virus-protection/clamav/docker-compose.clamav.yml up --build website clamav -d
```

> **Note:** ClamAV takes a few moments to initialize. The web application will automatically attempt to connect to ClamAV, retrying until ClamAV is available for scans.

## Logging

Logging is set to `INFO` by default, but you can enable `DEBUG` with the `--debug` flag for more detailed logging information.

## Notes

- Ensure `pdf_files_to_parse` directory exists with valid PDF files.
- Processed PDF summaries are saved to `output_files` with `.txt` extensions.
- If using ClamAV for scanning, ensure ClamAV is up-to-date to avoid warnings about outdated virus definitions.

## License

This project is provided under the MIT License.