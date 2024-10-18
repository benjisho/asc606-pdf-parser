# ASC 606 PDF Parser

This project provides a Python script to parse PDF files and extract relevant information. The script processes PDF documents in a specified directory and writes the results to text files for easy reference.

## Table of Contents
[Features](#features)

[Prerequisites](#prerequisites)

[Directory Structure](#directory-structure)

[Usage](#usage)
- [Before Your Run the Code](#before-your-run-the-code)
- [Command Line Arguments](#command-line-arguments)
- [**Option 1** Running the Script regularly](#option-1-running-the-script-regularly)
- [**Option 2** Using Docker](#option-2-using-docker)
- [**Option 3 Preferred** Running with Docker Compose](#option-3-preferred-running-with-docker-compose)
- [Logging](#logging)

[Notes](#notes)

[License](#license)

## Features

- Extract text from PDF files using PyMuPDF.
- Output summaries to text files.
- Optional `--debug` flag for additional detailed logging.

## Prerequisites

- Python 3.6+
- PyMuPDF library (`pymupdf`)

To install the required dependencies, run:

```bash
pip install -r requirements.txt
```

## Directory Structure

- `pdf_files_to_parse/`: Directory containing the PDF files to be processed.
- `output_files/`: Directory where the extracted summaries will be saved.

## Usage

### Before Your Run the Code

1. Place all PDF files that you want to process in the `pdf_files_to_parse` directory.
2. Run the script as described in the "Usage" section.
3. Check the `output_files` directory for the generated text files containing summaries of the extracted information.

### Command Line Arguments

- You may add `--debug`: Enable detailed debug logging for troubleshooting purposes.

### **Option 1** Running the Script regularly

To run the script, execute the following command:

```bash
python ./asc606-pdf-parser-app/asc606-pdf-parser.py
```

If you want to enable detailed debug logging, use:

```bash
python ./asc606-pdf-parser-app/asc606-pdf-parser.py --debug
```

The script will process all PDF files in the `pdf_files_to_parse` directory and save the summary outputs to the `output_files` directory.

### **Option 2** Using Docker

The Docker container for this project is accessible via Docker Hub.

To run the pdf-parser container with Docker:

```bash
docker run --rm -v ./pdf_files_to_parse:/pdf_files_to_parse -v ./output_files:/output_files benjisho/asc606-pdf-parser:latest
```

### **Option 3 Preferred** Running with Docker Compose

To use Docker Compose to run the container, use the following command:

```bash
# Using through a web interface
docker-compose up --build website

# Using the asc606-pdf-parser directly (easiest and fastest)
docker compose run --rm --build asc606-pdf-parser
```

This command will build the container image and start the service, removing intermediate containers after they stop.

## Logging

By default, it uses the `INFO` logging level, but you can enable `DEBUG` logging by using the `--debug` flag.

## Notes

- Ensure that the `pdf_files_to_parse` directory exists and contains valid PDF files for processing.
- Summaries for each processed PDF will be saved in the `output_files` directory with the same name as the PDF file but with a `.txt` extension.

## License

This project is provided under the MIT License.
