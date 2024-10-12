import logging
import os
import subprocess
import re
from pdfminer.high_level import extract_text
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Install required packages automatically if not already installed
def install_requirements():
    try:
        logging.info("Installing required packages from requirements.txt...")
        # Use subprocess to install the required packages
        subprocess.check_call(['pip', 'install', '-r', 'requirements.txt'])
        logging.info("Finished installing required packages.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to install required packages: {e}")
        exit(1)

# Step 1: Extract text from PDF
def extract_text_from_pdf(pdf_path):
    try:
        logging.info(f"Extracting text from PDF file: {pdf_path}")
        # Extract text from the given PDF file using pdfminer.six
        text = extract_text(pdf_path)
        logging.info("Finished extracting text from PDF")
        return text
    except FileNotFoundError:
        # Handle case where the file is not found
        logging.error(f"File not found: {pdf_path}")
        return ""
    except PermissionError:
        # Handle case where the file cannot be accessed due to permission issues
        logging.error(f"Permission denied: {pdf_path}")
        return ""
    except ValueError as e:
        # Handle case where the file format is unsupported or the PDF is corrupted
        logging.error(f"Unsupported file format or corrupted PDF: {pdf_path}. Error: {e}")
        return ""
    except Exception as e:
        # Handle any other exceptions that may occur
        logging.error(f"Error extracting text from PDF: {e}")
        return ""

# Step 2: Define functions to identify ASC 606 steps
def identify_contract(text):
    logging.info("Identifying contract with customer...")
    # Define patterns to search for contract-related information
    patterns = [
        r'contract.*?with.*?customer',  # Look for phrases indicating a contract with a customer
        r'agreement.*?between.*?parties'  # Look for phrases indicating an agreement between parties
    ]
    # Extract matching sections from the text
    result = extract_section(text, patterns, "Identify Contract")
    logging.info(f"Result for contract identification: {result}")
    return result

def identify_performance_obligations(text):
    logging.info("Identifying performance obligations...")
    # Define patterns to search for performance obligations
    patterns = [
        r'performance obligation.*?(include|consist of)',  # Look for phrases describing performance obligations
        r'obligation.*?to provide'  # Look for obligations to provide a service or product
    ]
    # Extract matching sections from the text
    result = extract_section(text, patterns, "Identify Performance Obligations")
    logging.info(f"Result for performance obligations: {result}")
    return result

def determine_transaction_price(text):
    logging.info("Determining transaction price...")
    # Define patterns to search for transaction price information
    patterns = [
        r'transaction price.*?(is|amounts to)',  # Look for phrases specifying the transaction price
        r'fee.*?for services'  # Look for fees related to services provided
    ]
    # Extract matching sections from the text
    result = extract_section(text, patterns, "Determine Transaction Price")
    logging.info(f"Result for transaction price determination: {result}")
    return result

def allocate_transaction_price(text):
    logging.info("Allocating transaction price...")
    # Define patterns to search for allocation details
    patterns = [
        r'allocate.*?price.*?to.*?obligations',  # Look for phrases about allocating price to obligations
        r'pricing allocation.*?obligations'  # Look for pricing allocation details
    ]
    # Extract matching sections from the text
    result = extract_section(text, patterns, "Allocate Transaction Price")
    logging.info(f"Result for transaction price allocation: {result}")
    return result

def recognize_revenue(text):
    logging.info("Recognizing revenue...")
    # Define patterns to search for revenue recognition information
    patterns = [
        r'revenue.*?recognition.*?(when|upon)',  # Look for phrases indicating revenue recognition timing
        r'satisfaction.*?performance obligation'  # Look for satisfaction of performance obligations
    ]
    # Extract matching sections from the text
    result = extract_section(text, patterns, "Recognize Revenue")
    logging.info(f"Result for revenue recognition: {result}")
    return result

# Step 3: Extract sections based on patterns
def extract_section(text, patterns, step_name):
    logging.info(f"Extracting section for step: {step_name}")
    all_matches = []
    for pattern in patterns:
        logging.info(f"Searching with pattern: {pattern}")
        # Use regex to find all matches for the given pattern
        matches = list(re.finditer(pattern, text, re.IGNORECASE))
        if matches:
            logging.info(f"Matches found with pattern '{pattern}': {[match.group() for match in matches]}")
        all_matches.extend(match.group() for match in matches)
    if all_matches:
        # Log and return all matched text with the step name
        logging.info(f"All matches found for step '{step_name}': {all_matches}")
        return f"{step_name}: {'; '.join(all_matches)}"
    # Log a warning if no matches are found
    logging.warning(f"No matches found for step: {step_name}")
    return None  # Return None if no match is found

# Step 4: Parse and summarize ASC 606 steps
def summarize_asc606_steps(text):
    logging.info("Summarizing ASC 606 steps...")
    summary = []
    # Define the steps and their descriptions
    steps = [
        (identify_contract, "Contract Identification"),
        (identify_performance_obligations, "Performance Obligations"),
        (determine_transaction_price, "Transaction Price Determination"),
        (allocate_transaction_price, "Transaction Price Allocation"),
        (recognize_revenue, "Revenue Recognition")
    ]
    # Iterate through each step and generate the summary
    for step, description in steps:
        logging.info(f"Processing step: {description}")
        result = step(text)
        if result:
            logging.info(f"Step result: {result}")
            summary.append(result)
        else:
            logging.warning(f"No information found for step: {description}")
            summary.append(f"{description}: Not Found")
    logging.info("Finished summarizing ASC 606 steps")
    return "\n".join(summary)  # Join all steps into a single summary string

# Main function
def main():
    # Main function to start the process of extracting and summarizing information from all PDFs in the directory
    pdf_directory = "pdf_files_to_parse"
    # Check if the directory exists
    if not os.path.exists(pdf_directory):
        logging.error(f"Directory not found: {pdf_directory}")
        return
    # Get a list of all PDF files in the directory
    pdf_files = [f for f in os.listdir(pdf_directory) if f.endswith('.pdf')]
    if not pdf_files:
        logging.error(f"No PDF files found in directory: {pdf_directory}")
        return
    # Iterate through each PDF file and process it
    for pdf_file in pdf_files:
        pdf_path = os.path.join(pdf_directory, pdf_file)
        try:
            logging.info(f"Starting process for PDF: {pdf_path}")
            text = extract_text_from_pdf(pdf_path)  # Extract text from the provided PDF path
            if not text.strip():  # Add a check for empty or invalid text earlier in the workflow
                logging.error("No valid text extracted from PDF. Skipping.")
                continue
            # Clean and preprocess the extracted text
            text = re.sub(r'\s+', ' ', text).strip()  # Remove extra whitespace and special characters
            logging.info("Extracted text:")
            # Log the extracted text, truncating if it's too long
            if len(text) > 500:
                logging.info(f"Extracted text (truncated): {text[:500]}...")
            else:
                logging.info(f"Extracted text: {text}")
            # Summarize the ASC 606 steps based on the extracted text
            summary = summarize_asc606_steps(text)
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
    main()