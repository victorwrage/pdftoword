# Python PDF to Word Converter (with OCR and AI Formatting)

## Overview

This command-line tool converts PDF files into editable Word (`.docx`) documents. It leverages a multi-step process:

*   **PDF Page to Image**: Converts each page of the input PDF into an image.
*   **OCR with Umi-OCR**: Uses a locally running instance of Umi-OCR to extract text from these images.
*   **Text Desensitization**: Automatically replaces predefined sensitive terms in the extracted text (e.g., "江河" becomes "公司A", "军工" becomes "JG").
*   **AI-Powered Formatting with Perplexity API**: Sends the desensitized text to the Perplexity API for content reformatting and structuring. This step aims to improve spacing, paragraph breaks, and attempts to convert textual representations of tables into a more structured format based on a specific prompt.
*   **Word Document Generation**: Compiles the processed text from all pages into a single `.docx` file, with page breaks corresponding to the original PDF pages.

## Features

*   Processes a single PDF file or all PDF files within a specified directory.
*   Page-by-page text extraction using Umi-OCR.
*   Configurable text desensitization (currently hardcoded for "江河" and "军工").
*   Content refinement and formatting via Perplexity API.
*   Generates `.docx` files with page breaks to mirror original PDF page structure.
*   Command-line interface for batch processing.

## Prerequisites

1.  **Python 3.7+**: Ensure Python is installed on your system.
2.  **Umi-OCR**: A locally running instance of Umi-OCR is required.
    *   GitHub: [https://github.com/hiroi-sora/Umi-OCR](https://github.com/hiroi-sora/Umi-OCR)
    *   The script expects the Umi-OCR API to be accessible at its default URL: `http://127.0.0.1:1224/api/ocr`. Ensure Umi-OCR is running and its HTTP API service is enabled.
3.  **Perplexity API Key**: A valid API key from Perplexity AI.
    *   You'll need to sign up for Perplexity AI and obtain an API key.
4.  **Poppler**: Required by the `pdf2image` library to convert PDF pages into images.
    *   Installation instructions (which include Poppler setup): [https://pdf2image.readthedocs.io/en/latest/installation.html](https://pdf2image.readthedocs.io/en/latest/installation.html)
5.  **Git** (Optional): For cloning this repository. If you downloaded the code as a ZIP, Git is not needed.

## Setup and Installation

1.  **Clone the repository (optional):**
    If you have Git, clone the repository. Otherwise, download and extract the source code.
    ```bash
    # git clone <repository_url> # Replace with actual URL if it's a git repo
    # cd <repository_name>
    ```

2.  **Create a virtual environment (recommended):**
    This isolates project dependencies.
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies:**
    Navigate to the project directory in your terminal and run:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Create the `.env` file:**
    In the root directory of the project, create a file named `.env`. This file will store your Perplexity API key. Add the following line to it, replacing `your_perplexity_api_key_here` with your actual key:
    ```env
    PERPLEXITY_API_KEY=your_perplexity_api_key_here
    ```

## Running the Application

Execute the script from the command line, providing the input path and output directory.

**Basic command structure:**
```bash
python pdf_to_word_converter.py --input_path <path_to_input_pdf_or_dir> --output_dir <path_to_output_dir>
```

**Arguments:**
*   `--input_path`: Path to the input PDF file or a directory containing PDF files.
*   `--output_dir`: Directory where the output Word documents will be saved. This directory will be created if it doesn't exist.

**Example (single PDF file):**
```bash
python pdf_to_word_converter.py --input_path "documents/annual_report.pdf" --output_dir "processed_reports/"
```

**Example (entire directory of PDFs):**
```bash
python pdf_to_word_converter.py --input_path "source_pdfs/" --output_dir "converted_word_docs/"
```

## How it Works

The script processes PDFs through the following pipeline:

1.  **PDF Page Conversion**: Each page of an input PDF is converted into a PNG image.
2.  **Image to Text (Umi-OCR)**: These images are sent one by one to the Umi-OCR HTTP API for text extraction.
3.  **Text Desensitization**: The extracted text from each page undergoes a desensitization step where specific keywords ("江河", "军工") are replaced.
4.  **Content Formatting (Perplexity API)**: The desensitized text for each page is then sent to the Perplexity API. A specific prompt guides the API to reformat the content, adjust spacing, attempt to structure table-like text for Word, etc., without altering the core information.
5.  **Word Document Assembly**: The processed text from all pages is compiled into a new Word (`.docx`) document. Page breaks are inserted between the content of each original PDF page.

## Troubleshooting/Notes

*   **Umi-OCR Not Running**: Ensure your local Umi-OCR application is running and its HTTP API service is enabled and accessible at `http://127.0.0.1:1224/api/ocr`.
*   **Perplexity API Key**:
    *   Verify that the `PERPLEXITY_API_KEY` in your `.env` file is correct and valid.
    *   Ensure your Perplexity account has sufficient credits/quota for API usage.
    *   If the key is missing or invalid, Perplexity processing will be skipped, and the Word document will be generated from desensitized Umi-OCR output.
*   **Poppler Installation**: `pdf2image` relies on Poppler. If you see errors related to PDF conversion or Poppler not being found, ensure it's correctly installed and added to your system's PATH as per the `pdf2image` documentation.
*   **Conversion Quality**:
    *   The final quality of the Word document depends heavily on the original PDF's quality (e.g., scanned vs. digitally born, resolution), the accuracy of Umi-OCR, and Perplexity API's interpretation of the text and formatting prompt.
    *   Complex layouts, very small text, or poor-quality scans may lead to suboptimal results.
*   **Table Formatting**: The script relies on the Perplexity API's ability to understand the "convert to Word table format" instruction in the prompt. Results for tables can vary significantly based on the table's complexity and the AI's interpretation. Manual adjustments to tables in the output Word document may be necessary.
*   **Desensitization Terms**: The current desensitization terms ("江河" -> "公司A", "军工" -> "JG") are hardcoded in the Python script. To change these, you would need to modify the `pdf_to_word_converter.py` file.

## Current Key Dependencies

The tool relies on several key Python libraries, managed via `requirements.txt`:

*   `requests`: For making HTTP requests to Umi-OCR and Perplexity API.
*   `python-docx`: For creating and manipulating Word (`.docx`) documents.
*   `pdf2image`: For converting PDF pages to images.
*   `python-dotenv`: For managing environment variables (specifically the Perplexity API key from the `.env` file).

Refer to `requirements.txt` for a full list of dependencies.
