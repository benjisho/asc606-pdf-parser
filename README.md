# ASC 606 PDF Parser

This project provides a Python script and web-based service to parse PDF files, extract relevant information, and save the results to text files. It also includes optional ClamAV antivirus scanning for uploaded PDF files.

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

## Usage

### Before You Run the Code

1. Place PDFs for processing in `pdf_files_to_parse`.
2. Run the script or use Docker commands below.
3. Check `output_files` for generated text summaries.

### Command Line Arguments

- `--debug`: Enable detailed debug logging.

### Option 1: Running the Script Locally

To run the script directly:

```bash
python ./asc606-pdf-parser-app/asc606-pdf-parser.py
```

With debug logging:

```bash
python ./asc606-pdf-parser-app/asc606-pdf-parser.py --debug
```

The script will process PDFs in `pdf_files_to_parse` and output summaries to `output_files`.

### Option 2: Running with Docker

To run the `pdf-parser` container alone:

```bash
docker run --rm \
  -v "$(pwd)/pdf_files_to_parse:/app/pdf_files_to_parse" \
  -v "$(pwd)/output_files:/app/output_files" \
  -e PYTHONUNBUFFERED=1 \
  benjisho/asc606-pdf-parser:latest
```

### Option 3: Preferred Running with Docker Compose

For ease of use, Docker Compose can build and manage the containerized application:

```bash
# Build both website and parser containers
docker compose build website asc606-pdf-parser

# Run the website service in detached mode (unsafe for production)
docker compose up -d --build website
# Or test website with
docker compose run --rm --build website

# Run asc606-pdf-parser directly (quickest for command-line parsing)
docker compose run --rm --build asc606-pdf-parser
```

#### OPTIONAL: Enabling Antivirus Scanning in Docker Compose

For enhanced security, you can enable ClamAV to scan uploaded files in the `website` service:

```bash
docker compose -f docker-compose.yml -f ./virus-protection/clamav/docker-compose.clamav.yml up --build website clamav -d
```

> **Note:** ClamAV takes a few moments to initialize. The web application will automatically attempt to connect to ClamAV, retrying until ClamAV is available for scans.

## Logging

Logging is set to `INFO` by default, but you can enable `DEBUG` with the `--debug` flag.

## Notes

- Ensure `pdf_files_to_parse` directory exists with valid PDF files.
- Processed PDF summaries are saved to `output_files` with `.txt` extensions.

## License

This project is provided under the MIT License.