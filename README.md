# PDF to Markdown Converter with Docling and LM Studio

This program converts PDF files to Markdown format using the `docling` library and a locally running Large Language Model (LLM) via LM Studio. It features a graphical user interface (GUI) for selecting input/output directories and viewing logs.

## Features

*   Converts all PDF files within a specified input directory.
*   Outputs Markdown files to a specified output directory.
*   Utilizes `docling` for PDF parsing and OCR.
*   Integrates with LM Studio for advanced OCR capabilities using local LLMs (specifically configured for `internvl3-9b`).
*   Simple GUI for ease of use.
*   Real-time logging within the GUI.

## Prerequisites

1.  **Python 3.7+**: Ensure you have Python installed.
2.  **LM Studio**:
    *   Download and install LM Studio from [https://lmstudio.ai/](https://lmstudio.ai/).
    *   Within LM Studio, download and load the `internvl3-9b` model (or a compatible model if you adjust the script).
    *   Start the AI model server in LM Studio (usually on `http://localhost:1234`).
3.  **Git** (for cloning the repository).

## Setup and Installation

1.  **Clone the repository (if applicable, otherwise download the files):**
    ```bash
    # git clone <repository_url> # Replace with actual URL if it's a git repo
    # cd <repository_name>
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Running the Application

1.  **Ensure LM Studio is running and the `internvl3-9b` model server is active.**
    *   Verify that the server is accessible, typically at `http://localhost:1234/v1/models` or `http://localhost:1234/v1/chat/completions`.

2.  **Run the Python script:**
    ```bash
    python pdf_to_word_converter.py
    ```

3.  **Using the GUI:**
    *   Click "Browse..." to select your **Input PDF Directory**.
    *   Click "Browse..." to select your **Output Directory** where the Markdown files will be saved.
    *   Click "Start Conversion".
    *   Monitor the logs in the text area for progress and any errors.
    *   A message box will appear upon completion.

## How it Works

The script uses the `docling` library to process PDF files. For OCR (Optical Character Recognition), especially for scanned or image-based PDFs, it leverages a Vision Language Model (VLM) pipeline connected to your local LM Studio instance. The `internvl3-9b` model is specified in the script to perform the OCR and extract text content into Markdown format.

## Troubleshooting

*   **LM Studio Connection Errors**:
    *   Ensure LM Studio is running.
    *   Ensure the correct model (`internvl3-9b`) is loaded in LM Studio.
    *   Ensure the "Local Server" tab in LM Studio shows the server is started and note the port (default 1234).
    *   Check your firewall settings if the script cannot connect.
*   **`docling` or other library errors**:
    *   Ensure all dependencies in `requirements.txt` are correctly installed in your virtual environment.
*   **No PDF files found**:
    *   Verify that the selected input directory contains `.pdf` files.
*   **Conversion quality**:
    *   The quality of Markdown output depends on the PDF's structure and the OCR capabilities of the LLM. For complex PDFs or very blurry scans, results may vary. The prompt in `lm_studio_vlm_options` within the script can be experimented with for potentially better results.

## Note on Word Conversion

This script currently converts PDFs to **Markdown (.md) files**. The original issue mentioned generating Word (.docx) files. To convert the generated Markdown files to Word documents, you can use tools like Pandoc:

1.  **Install Pandoc**: Follow instructions at [https://pandoc.org/installing.html](https://pandoc.org/installing.html).
2.  **Convert a Markdown file to DOCX**:
    ```bash
    pandoc input.md -o output.docx
    ```
    You can create a separate script or manually run this command for each generated Markdown file.
