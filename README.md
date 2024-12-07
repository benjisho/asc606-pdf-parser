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
  - [Option 3: Preferred - Running with Docker Compose](#option-3-preferred---running-with-docker-compose)
    - [OPTIONAL: Enabling Antivirus Scanning in Docker Compose](#optional-enabling-antivirus-scanning-in-docker-compose)
- [Add HTTPS Support](#add-https-support)
  - [Generate SSL self-signed certificate into `certs/` directory](#generate-ssl-self-signed-certificate-into-certs-directory)
  - [Enable HTTPS in the `docker-compose.yml`](#enable-https-in-the-docker-composeyml)
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

1. Place PDFs for processing in `pdf_files_to_parse/<the-relevant-directory>`.
  > Example `pdf_files_to_parse/asc606/your-asc606-pdf-file.pdf`
2. Run the script or use Docker commands below.
3. Check `output_files` for generated text summaries.

### Command Line Arguments

- `--form_type <type>`: Specify the accounting standard type (e.g., `asc606`, `asc718`).
- `--debug`: Enable detailed debug logging.

### Option 1: Running the Script Locally

To run the script directly:

> use the **p2ta-pdf-parser_without_docker.py** file!

```bash
python3 p2ta-pdf-parser-app/p2ta-pdf-parser_without_docker.py --form_type asc606
```

With debug logging:

```bash
python3 p2ta-pdf-parser-app/p2ta-pdf-parser_without_docker.py --form_type asc606 --debug
```

The script will process PDFs in `pdf_files_to_parse` and output summaries to `output_files`.

### Option 2: Running with Docker

1. To run the `pdf-parser` container alone:

```bash
docker run --rm \
  -v "$(pwd)/pdf_files_to_parse:/app/pdf_files_to_parse" \
  -v "$(pwd)/output_files:/app/output_files" \
  -e PYTHONUNBUFFERED=1 \
  benjisho/p2ta-pdf-parser:v2.0.1 --form_type asc606 --debug
```

2. To run the `website + antivirus` containers - follow the steps in the [official Dockerhub page](https://hub.docker.com/r/benjisho/p2ta-pdf-parser-website)

### Option 3: Preferred - Running with Docker Compose

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

#### Wait until clamav fully started using the logs command!
docker compose -f docker-compose.yml -f ./virus-protection/clamav/docker-compose.clamav.yml logs -f
```

> **Note:** ClamAV takes a few moments to initialize. The web application will automatically attempt to connect to ClamAV, retrying until ClamAV is available for scans.

## Add HTTPS Support

### Generate SSL self-signed certificate into `certs/` directory

> **Note:** This section is relevant if you haven't generated a well-known SSL certificate from a certified authority.
> These will guide you on creating a self-signed certificate, useful for testing or development purposes.

1. Run the following command to generate a 2048-bit RSA private key, which is used to decrypt traffic:

```bash
openssl genrsa -out nginx/ssl/server.key 2048
```

2. Run the following command to generate a certificate, using the private key from the previous step.

```bash
openssl req -new -key nginx/ssl/server.key -out nginx/ssl/server.csr
```

3. Run the following command to self-sign the certificate with the private key, for a period of validity of 365 days:

```bash
openssl x509 -req -days 365 -in nginx/ssl/server.csr -signkey nginx/ssl/server.key -out nginx/ssl/server.crt
```

4. Copy the certificate file to the certificate directory `nginx/ssl/`

### Enable HTTPS in the `docker-compose.yml`

5. Uncommment the HTTPS Nginx server service in the `docker-compose.yml`

## Logging

Logging is set to `INFO` by default, but you can enable `DEBUG` with the `--debug` flag for more detailed logging information.

## Notes

- Ensure `pdf_files_to_parse` directory exists with valid PDF files.
- Processed PDF summaries are saved to `output_files` with `.txt` extensions.
- If using ClamAV for scanning, ensure ClamAV is up-to-date to avoid warnings about outdated virus definitions.

## License

This project is provided under the MIT License.