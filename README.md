# ASC 606 PDF Parser

This project provides a Python script designed to parse PDF files and extract information related to the ASC 606 revenue recognition standard. The script processes PDF documents in a specified directory and summarizes the five steps of revenue recognition, writing the results to text files for easy reference.

## Features

- Extract text from PDF files using `PyMuPDF`.
- Identify and summarize the five steps of ASC 606 revenue recognition:
  1. Contract Identification
  2. Performance Obligations
  3. Transaction Price Determination
  4. Transaction Price Allocation
  5. Revenue Recognition
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

### Command Line Arguments

- `--debug`: Enable detailed debug logging for troubleshooting purposes.

### Running the Script

To run the script, execute the following command:

```bash
python Asc606-Parser.py
```

If you want to enable detailed debug logging, use:

```bash
python Asc606-Parser.py --debug
```

The script will process all PDF files in the `pdf_files_to_parse` directory and save the summary outputs to the `output_files` directory.

### Example Workflow

1. Place all PDF files that you want to process in the `pdf_files_to_parse` directory.
2. Run the script as described in the "Usage" section.
3. Check the `output_files` directory for the generated text files containing summaries of the ASC 606 analysis.

## Logging

The script logs its actions and errors during execution. By default, it uses the `INFO` logging level, but you can enable `DEBUG` logging by using the `--debug` flag.

## Notes

- Ensure that the `pdf_files_to_parse` directory exists and contains valid PDF files for processing.
- Summaries for each processed PDF will be saved in the `output_files` directory with the same name as the PDF file but with a `.txt` extension.

## License

This project is provided under the MIT License.
