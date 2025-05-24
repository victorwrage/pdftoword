import os
import logging
import pathlib
import requests
import argparse
from dotenv import load_dotenv
from docx import Document # For python-docx, will be used later
from pdf2image import convert_from_path, pdf2image # Handling pdf2image exceptions
import tempfile
import shutil
import json

# Load environment variables from .env file
load_dotenv()

# --- Global logger setup ---
# Basic config for console logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Constants ---
UMI_OCR_API_URL = "http://127.0.0.1:1224/api/ocr" # Default Umi-OCR API URL
PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"
PERPLEXITY_SYSTEM_PROMPT = "You are a helpful assistant that processes text."
PERPLEXITY_USER_PROMPT_CONTENT = "整理内容格式，去掉不合理的空格及回车符，标题、副标题、正文使用合适的字号，表格转化为适合Word表格的格式，禁止修改原来的内容。以下是待处理的文本：\n\n{}"

def main():
    perplexity_api_key = os.getenv("PERPLEXITY_API_KEY")
    if not perplexity_api_key:
        logger.error("PERPLEXITY_API_KEY environment variable not found. Perplexity processing will be skipped.")
        # Depending on requirements, could exit here: return

    parser = argparse.ArgumentParser(description="Convert PDF files to Word documents using OCR and AI.")
    parser.add_argument("--input_path", type=str, required=True,
                        help="Path to the input PDF file or a directory containing PDF files.")
    parser.add_argument("--output_dir", type=str, required=True,
                        help="Directory where the output Word documents will be saved.")
    
    args = parser.parse_args()

    input_path = pathlib.Path(args.input_path)
    output_dir = pathlib.Path(args.output_dir)

    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Ensured output directory exists: {output_dir}")
    except Exception as e:
        logger.error(f"Could not create output directory {output_dir}: {e}")
        return

    pdf_files_to_process = []
    if input_path.is_file():
        if input_path.suffix.lower() == ".pdf":
            pdf_files_to_process.append(input_path)
        else:
            logger.warning(f"Input path is a file, but not a PDF: {input_path}. Skipping.")
    elif input_path.is_dir():
        logger.info(f"Scanning directory for PDF files: {input_path}")
        # Using set to avoid duplicates if both .pdf and .PDF exist with same name stem
        pdf_files_set = set()
        pdf_files_set.update(input_path.glob("*.pdf"))
        pdf_files_set.update(input_path.glob("*.PDF"))
        pdf_files_to_process = list(pdf_files_set)
    else:
        logger.error(f"Input path {input_path} is not a valid file or directory.")
        return

    if not pdf_files_to_process:
        logger.info(f"No PDF files found to process at {input_path}.")
        return

    logger.info(f"Output directory: {output_dir}")
    logger.info(f"Identified {len(pdf_files_to_process)} PDF file(s) for processing.")

    for pdf_file_path in pdf_files_to_process:
        logger.info(f"--- Starting processing for PDF: {pdf_file_path.name} ---")
        pages_content_for_word = [] # Store Perplexity-processed text for each page

        with tempfile.TemporaryDirectory(prefix="pdf_images_", dir=output_dir) as temp_image_dir_str:
            temp_image_dir = pathlib.Path(temp_image_dir_str)
            logger.info(f"Created temporary directory for images: {temp_image_dir}")

            try:
                logger.info(f"Converting PDF to images: {pdf_file_path.name}")
                # convert_from_path returns a list of PIL Image objects.
                # We need to save them to files to get paths for Umi-OCR.
                # Using output_folder and fmt ensures images are saved.
                # Poppler path might be needed for Windows: poppler_path=r"C:\path\to\poppler\bin"
                images_from_path = convert_from_path(
                    pdf_path=pdf_file_path,
                    output_folder=temp_image_dir,
                    fmt='png',
                    output_file=f"{pdf_file_path.stem}_page" # Generates names like file_page-0001-1.png, file_page-0002-1.png etc.
                )
                logger.info(f"Successfully converted {len(images_from_path)} page(s) to images in {temp_image_dir}")
                
                # Get sorted list of image paths
                # The output_file prefix helps, but pdf2image might add its own numbering.
                # Globbing and sorting is a reliable way to get them in order.
                image_paths = sorted(list(temp_image_dir.glob(f'{pdf_file_path.stem}_page*.png')))

                if not image_paths: # Double check if images were created
                    logger.warning(f"No images found in {temp_image_dir} after conversion for {pdf_file_path.name}. Skipping OCR for this PDF.")
                    continue


            except pdf2image.exceptions.PDFInfoNotInstalledError:
                logger.error(
                    "Poppler not found. pdf2image requires Poppler to be installed and in PATH. "
                    "Please install Poppler and try again. "
                    "On Debian/Ubuntu: sudo apt-get install poppler-utils. On macOS: brew install poppler."
                )
                continue # Skip to next PDF
            except Exception as e:
                logger.error(f"Error during PDF to image conversion for {pdf_file_path.name}: {e}", exc_info=True)
                continue # Skip to next PDF

            for image_idx, image_path in enumerate(image_paths):
                logger.info(f"Processing image {image_idx + 1}/{len(image_paths)}: {image_path.name}")
                desensitized_page_text = "" # Changed variable name for clarity
                try:
                    with open(image_path, 'rb') as f:
                        files = {'file': (image_path.name, f, 'image/png')}
                        # Umi-OCR options can be sent as JSON in the 'data' field if needed
                        # Example: options = {"ocr_engine": "PaddleOCR", "lang": "en"}
                        # data_payload = {"options": json.dumps(options)}
                        # For now, using default Umi-OCR settings
                        response = requests.post(UMI_OCR_API_URL, files=files, timeout=60) # Increased timeout for OCR
                    
                    response.raise_for_status() # Raises HTTPError for bad responses (4XX or 5XX)
                    ocr_result = response.json()

                    if ocr_result.get("code") == 200 and ocr_result.get("data"):
                        for item in ocr_result["data"]:
                            desensitized_page_text += item.get("text", "") + "\n"
                        
                        # Apply desensitization
                        original_length = len(desensitized_page_text)
                        desensitized_page_text = desensitized_page_text.replace("江河", "公司A")
                        desensitized_page_text = desensitized_page_text.replace("军工", "JG")
                        desensitized_length = len(desensitized_page_text)

                        if original_length != desensitized_length:
                            logger.info(f"Applied desensitization to text from {image_path.name}. Length before: {original_length}, after: {desensitized_length}.")
                        else:
                            logger.info(f"Text from {image_path.name} processed (no desensitization terms found).")

                        logger.info(f"Page OCR successful for {image_path.name}. Extracted text length (after desensitization): {len(desensitized_page_text.strip())}")
                        if len(desensitized_page_text.strip()) > 0:
                             logger.debug(f"Extracted text snippet (desensitized): {desensitized_page_text.strip()[:100]}...")
                        # Removed: all_text_from_pdf += page_text (will be handled after Perplexity)
                    elif ocr_result.get("code") == 200 and not ocr_result.get("data"): # Success but no text found
                        logger.info(f"Umi-OCR found no text on page {image_path.name}.")
                        # desensitized_page_text remains empty
                    else: # Umi-OCR returned an error or unexpected format
                        error_msg = ocr_result.get('message', 'Unknown Umi-OCR error')
                        logger.error(f"Umi-OCR error for {image_path.name} (Code: {ocr_result.get('code')}): {error_msg}")
                    # desensitized_page_text remains empty or as previously set if error in middle of data
                
                except requests.exceptions.ConnectionError:
                    logger.error(f"Umi-OCR API connection failed at {UMI_OCR_API_URL}. Is Umi-OCR running? Skipping Perplexity for this page and subsequent pages of this PDF.")
                    pages_content_for_word.append(desensitized_page_text.strip()) # Save what we have
                    break 
                except requests.exceptions.Timeout:
                    logger.error(f"Umi-OCR API request timed out for {image_path.name}. Skipping Perplexity for this page.")
                except requests.exceptions.RequestException as e:
                    logger.error(f"Umi-OCR API request failed for {image_path.name}: {e}", exc_info=True)
                except json.JSONDecodeError:
                    logger.error(f"Failed to decode JSON response from Umi-OCR for {image_path.name}. Response: {response.text[:200]}")
                except Exception as e:
                    logger.error(f"An unexpected error occurred processing {image_path.name} with Umi-OCR: {e}", exc_info=True)
                
                # --- Process with Perplexity API ---
                processed_text_for_page = desensitized_page_text.strip() # Default to desensitized text
                if desensitized_page_text.strip() and perplexity_api_key: # Only process if there's text and API key
                    logger.info(f"Starting Perplexity processing for page from {image_path.name}...")
                    payload = {
                        "model": "llama-3-sonar-large-32k-online",
                        "messages": [
                            {"role": "system", "content": PERPLEXITY_SYSTEM_PROMPT},
                            {"role": "user", "content": PERPLEXITY_USER_PROMPT_CONTENT.format(desensitized_page_text.strip())}
                        ]
                    }
                    headers = {
                        "Authorization": f"Bearer {perplexity_api_key}",
                        "Accept": "application/json",
                        "Content-Type": "application/json"
                    }
                    try:
                        response = requests.post(PERPLEXITY_API_URL, headers=headers, json=payload, timeout=120)
                        response.raise_for_status()
                        perplexity_result = response.json()
                        
                        if perplexity_result.get("choices") and perplexity_result["choices"][0].get("message"):
                            processed_text_for_page = perplexity_result["choices"][0]["message"].get("content", "").strip()
                            logger.info(f"Perplexity processing successful for page from {image_path.name}. Output length: {len(processed_text_for_page)}")
                            logger.debug(f"Perplexity processed snippet: {processed_text_for_page[:100]}...")
                        else:
                            logger.error(f"Perplexity API error: Unexpected response structure for page from {image_path.name}. {perplexity_result}")
                            # Fallback to desensitized_page_text already assigned to processed_text_for_page
                    except requests.exceptions.RequestException as e:
                        logger.error(f"Perplexity API request failed for page from {image_path.name}: {e}")
                    except Exception as e: # Catch any other error during Perplexity call
                        logger.error(f"Error processing with Perplexity for page from {image_path.name}: {e}", exc_info=True)
                elif not perplexity_api_key and desensitized_page_text.strip():
                    logger.warning(f"Perplexity API key not available. Skipping Perplexity processing for page from {image_path.name}.")
                
                pages_content_for_word.append(processed_text_for_page)

            # After processing all images for a PDF with Perplexity
            if pages_content_for_word:
                doc = Document()
                for page_idx, page_content in enumerate(pages_content_for_word):
                    # Split by newlines to try and preserve some paragraph structure
                    paragraphs = page_content.split('\n')
                    for para_text in paragraphs:
                        if para_text.strip(): # Add non-empty paragraphs
                            doc.add_paragraph(para_text)
                    
                    # Add page break if it's not the last page's content
                    if page_idx < len(pages_content_for_word) - 1:
                        doc.add_page_break()
                
                word_output_filename = output_dir / f"{pdf_file_path.stem}.docx"
                try:
                    doc.save(word_output_filename)
                    logger.info(f"Successfully saved Word document to {word_output_filename}")
                except Exception as e:
                    logger.error(f"Failed to save Word document {word_output_filename}: {e}", exc_info=True)
            else:
                logger.info(f"No content (after Perplexity processing) to save for PDF '{pdf_file_path.name}'. Word document not created.")

        # The TemporaryDirectory context manager handles cleanup automatically upon exiting the 'with' block.
        logger.info(f"Temporary image directory for {pdf_file_path.name} has been cleaned up.")
        logger.info(f"--- Finished processing for PDF: {pdf_file_path.name} ---")

    logger.info("All PDF processing finished.")

if __name__ == "__main__":
    main()
