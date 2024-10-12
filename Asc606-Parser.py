import logging
import os
import subprocess
from pdfminer.high_level import extract_text
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Install required packages automatically if not already installed
def install_requirements():
    try:
        logging.info("Installing required packages from requirements.txt...")
        subprocess.check_call(['pip', 'install', '-r', 'requirements.txt'])
        logging.info("Finished installing required packages.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to install required packages: {e}")
        exit(1)

# Step 1: Extract text from PDF
def extract_text_from_pdf(pdf_path):
    try:
        logging.info(f"Extracting text from PDF file: {pdf_path}")
        text = extract_text(pdf_path)  # Use pdfminer.six to extract text from the PDF
        logging.info("Finished extracting text from PDF")
        return text
    except FileNotFoundError:
        logging.error(f"File not found: {pdf_path}")
        return ""
    except PermissionError:
        logging.error(f"Permission denied: {pdf_path}")
        return ""
    except ValueError as e:
        logging.error(f"Unsupported file format or corrupted PDF: {pdf_path}. Error: {e}")
        return ""
    except Exception as e:
        logging.error(f"Error extracting text from PDF: {e}")
        return ""

# Step 2: Define functions to identify ASC 606 steps
def identify_contract(text):
    # Identify the contract with a customer in the extracted text
    logging.info("Identifying contract with customer...")
    patterns = [
        r'contract.*?with.*?customer',  # Look for phrases indicating a contract with a customer
        r'agreement.*?between.*?parties'  # Look for phrases indicating an agreement between parties
    ]
    result = extract_section(text, patterns, "Identify Contract")
    logging.info(f"Result for contract identification: {result}")
    return result

def identify_performance_obligations(text):
    # Identify the performance obligations in the contract
    logging.info("Identifying performance obligations...")
    patterns = [
        r'performance obligation.*?(include|consist of)',  # Look for phrases describing performance obligations
        r'obligation.*?to provide'  # Look for obligations to provide a service or product
    ]
    result = extract_section(text, patterns, "Identify Performance Obligations")
    logging.info(f"Result for performance obligations: {result}")
    return result

def determine_transaction_price(text):
    # Determine the transaction price from the contract text
    logging.info("Determining transaction price...")
    patterns = [
        r'transaction price.*?(is|amounts to)',  # Look for phrases specifying the transaction price
        r'fee.*?for services'  # Look for fees related to services provided
    ]
    result = extract_section(text, patterns, "Determine Transaction Price")
    logging.info(f"Result for transaction price determination: {result}")
    return result

def allocate_transaction_price(text):
    # Allocate the transaction price to the performance obligations
    logging.info("Allocating transaction price...")
    patterns = [
        r'allocate.*?price.*?to.*?obligations',  # Look for phrases about allocating price to obligations
        r'pricing allocation.*?obligations'  # Look for pricing allocation details
    ]
    result = extract_section(text, patterns, "Allocate Transaction Price")
    logging.info(f"Result for transaction price allocation: {result}")
    return result

def recognize_revenue(text):
    # Recognize revenue when performance obligations are satisfied
    logging.info("Recognizing revenue...")
    patterns = [
        r'revenue.*?recognition.*?(when|upon)',  # Look for phrases indicating revenue recognition timing
        r'satisfaction.*?performance obligation'  # Look for satisfaction of performance obligations
    ]
    result = extract_section(text, patterns, "Recognize Revenue")
    logging.info(f"Result for revenue recognition: {result}")
    return result

# Step 3: Extract sections based on patterns
def extract_section(text, patterns, step_name):
    # Extract a section of text that matches one of the given patterns
    logging.info(f"Extracting section for step: {step_name}")
    all_matches = []
    for pattern in patterns:
        logging.info(f"Searching with pattern: {pattern}")
        all_matches.extend(match.group() for match in re.finditer(pattern, text, re.IGNORECASE))
    if all_matches:
        logging.info(f"Matches found: {all_matches}")
        return f"{step_name}: {'; '.join(all_matches)}"  # Return all matched text with the step name
    logging.warning(f"No matches found for step: {step_name}")  # Use warning level for no matches found
    return None  # Return None if no match is found

# Step 4: Parse and summarize ASC 606 steps
def summarize_asc606_steps(text):
    # Summarize all five steps of the ASC 606 revenue recognition process
    logging.info("Summarizing ASC 606 steps...")
    summary = []
    steps = [
        (identify_contract, "Contract Identification"),
        (identify_performance_obligations, "Performance Obligations"),
        (determine_transaction_price, "Transaction Price Determination"),
        (allocate_transaction_price, "Transaction Price Allocation"),
        (recognize_revenue, "Revenue Recognition")
    ]
    for step, description in steps:
        result = step(text)
        if result:
            summary.append(result)
        else:
            summary.append(f"{description}: Not Found")
    logging.info("Finished summarizing ASC 606 steps")
    return "\n".join(summary)  # Join all steps into a single summary string

# Main function
def main(pdf_path):
    # Main function to start the process of extracting and summarizing information from the PDF
    try:
        logging.info(f"Starting process for PDF: {pdf_path}")
        text = extract_text_from_pdf(pdf_path)  # Extract text from the provided PDF path
        if not text.strip():  # Add a check for empty or invalid text earlier in the workflow
            logging.error("No valid text extracted from PDF. Exiting.")
            return
        # Clean and preprocess the extracted text
        text = re.sub(r'\s+', ' ', text).strip()  # Remove extra whitespace and special characters
        logging.info("Extracted text:")
        if len(text) > 500:
            logging.info(text[:500] + "... [truncated]")  # Log the first 500 characters of the extracted text for verification, with truncation note
        else:
            logging.info(text)  # Log the entire text if it's less than 500 characters
        summary = summarize_asc606_steps(text)  # Summarize the ASC 606 steps based on the extracted text
        logging.info("\nRevenue Recognition Summary:\n")
        logging.info(summary)  # Log the summarized revenue recognition steps
    except FileNotFoundError:
        logging.error(f"File not found: {pdf_path}")
    except PermissionError:
        logging.error(f"Permission denied: {pdf_path}")
    except ValueError as e:
        logging.error(f"Unsupported file format or corrupted PDF: {pdf_path}. Error: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")

# Run the script
if __name__ == "__main__":
    install_requirements()  # Install the required packages before running the script
    pdf_path = "pdf_files_to_parse/sample_contract.pdf"  # Replace with the path to your PDF file
    main(pdf_path)