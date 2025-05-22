import os
# import argparse # No longer needed for GUI
import logging
import pathlib
import requests # For checking LM Studio connection
import tkinter as tk
from tkinter import filedialog, scrolledtext, ttk
import threading
import queue

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import ApiVlmOptions, ResponseFormat, VlmPipelineOptions
from docling.pipeline.vlm_pipeline import VlmPipeline

# --- Global logger setup (will be configured in PdfConverterApp) ---
logger = logging.getLogger(__name__) # Use a named logger
# Basic config removed from here, will be set up in App

# --- Core Processing Logic (modified to accept logger/queue for GUI updates) ---

def check_lm_studio_connection(app_queue: queue.Queue = None):
    """Checks if LM Studio is running and accessible."""
    url = "http://192.168.17.6:1234/v1/models"
    message_prefix = "LM Studio: "
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        if app_queue: app_queue.put( (logging.INFO, message_prefix + "Successfully connected.") )
        else: logger.info(message_prefix + "Successfully connected.")
        return True
    except requests.exceptions.RequestException as e:
        error_msg = f"Failed to connect to LM Studio at {url}. Ensure it's running. Error: {e}"
        if app_queue: app_queue.put( (logging.ERROR, message_prefix + error_msg) )
        else: logger.error(message_prefix + error_msg)
        return False

def lm_studio_vlm_options(model: str) -> ApiVlmOptions:
    """Configures the VLM options for LM Studio."""
    prompt = (
        "The user will provide an image of a document page and will ask you to OCR the page to markdown. "
        "If the image contains text, you should OCR the text and respond with the markdown. "
        "If the image does not contain text, you should respond with the following text: <NO_TEXT_FOUND>"
    )
    return ApiVlmOptions(
        url="http://192.168.17.6:1234/v1/chat/completions",
        params=dict(model=model, max_tokens=8192, temperature=0.1),
        prompt=prompt,
        timeout=300,
        scale=0.5,
        response_format=ResponseFormat.MARKDOWN
    )

def process_single_pdf(pdf_path: pathlib.Path, output_dir: pathlib.Path, model_name: str, app_queue: queue.Queue = None):
    """
    Converts a single PDF file to Markdown using docling and LM Studio.
    Logs progress via app_queue if provided.
    """
    msg_prefix = f"PDF '{pdf_path.name}': "
    if app_queue: app_queue.put((logging.INFO, msg_prefix + "Starting processing."))
    else: logger.info(msg_prefix + "Starting processing.")

    try:
        pipeline_options = VlmPipelineOptions(enable_remote_services=True)
        pipeline_options.vlm_options = lm_studio_vlm_options(model=model_name)
        pdf_options = PdfFormatOption(ocr_strategy="vlm")

        doc_converter = DocumentConverter(
            pipeline_options=pipeline_options,
            input_format_options={InputFormat.PDF: pdf_options}
        )
        doc_converter.register_pipeline(InputFormat.PDF, VlmPipeline)

        if app_queue: app_queue.put((logging.INFO, msg_prefix + f"Converting with model {model_name}..."))
        else: logger.info(msg_prefix + f"Converting with model {model_name}...")
        
        result = doc_converter.convert(pdf_path)

        if result and result.document:
            markdown_content = result.document.export_to_markdown()
            output_file_name = f"{pdf_path.stem}_content.md"
            output_file_path = output_dir / output_file_name

            with open(output_file_path, "w", encoding="utf-8") as f:
                f.write(markdown_content)
            
            success_msg = f"Successfully converted to Markdown: {output_file_path}"
            if app_queue: app_queue.put((logging.INFO, msg_prefix + success_msg))
            else: logger.info(msg_prefix + success_msg)
            return True, output_file_path
        else:
            error_msg = "Failed to convert. Result or document was empty."
            if app_queue: app_queue.put((logging.ERROR, msg_prefix + error_msg))
            else: logger.error(msg_prefix + error_msg)
            return False, None

    except Exception as e:
        error_msg = f"Error during processing: {e}"
        if app_queue: app_queue.put((logging.ERROR, msg_prefix + error_msg, True)) # True for exc_info
        else: logger.error(msg_prefix + error_msg, exc_info=True)
        return False, None

def process_pdf_folder(input_folder_str: str, output_folder_str: str, app_queue: queue.Queue):
    """
    Processes PDFs from input_folder to output_folder, reporting via app_queue.
    """
    app_queue.put((logging.INFO, "Starting PDF to Markdown conversion process."))
    app_queue.put(("status", "Checking LM Studio connection..."))

    if not check_lm_studio_connection(app_queue):
        app_queue.put((logging.ERROR, "LM Studio connection check failed. Please ensure LM Studio is running, a model is loaded, and the server is started."))
        app_queue.put((logging.ERROR, "Aborting PDF processing. Refer to Docling and LM Studio documentation for setup."))
        app_queue.put(("status", "Error: LM Studio connection failed."))
        return

    input_path = pathlib.Path(input_folder_str)
    output_path_obj = pathlib.Path(output_folder_str)

    if not input_path.is_dir():
        app_queue.put((logging.ERROR, f"Input folder not found: {input_folder_str}"))
        app_queue.put(("status", "Error: Input folder not found."))
        return

    app_queue.put(("status", f"Creating output folder: {output_folder_str}"))
    if not output_path_obj.exists():
        try:
            output_path_obj.mkdir(parents=True, exist_ok=True)
            app_queue.put((logging.INFO, f"Created output folder: {output_folder_str}"))
        except Exception as e:
            app_queue.put((logging.ERROR, f"Could not create output folder {output_folder_str}: {e}"))
            app_queue.put(("status", "Error: Could not create output folder."))
            return

    model_name = "internvl3-8b-instruct" # As specified
    
    app_queue.put(("status", f"Scanning for PDF files in {input_folder_str}..."))
    pdf_internvl3-9bth.glob("*.pdf"))
    if not pdf_files:
        app_queue.put((logging.INFO, f"No PDF files found in {input_folder_str}"))
        app_queue.put(("status", "No PDF files found."))
        return

    app_queue.put((logging.INFO, f"Found {len(pdf_files)} PDF file(s) to process in {input_folder_str}."))
    
    successful_conversions = 0
    failed_conversions = 0
    failed_files_list = []

    for i, pdf_file_path in enumerate(pdf_files):
        app_queue.put(("status", f"Processing file {i+1}/{len(pdf_files)}: {pdf_file_path.name}"))
        if pdf_file_path.is_file():
            app_queue.put((logging.INFO, f"Starting conversion for: {pdf_file_path.name}"))
            success, md_file_path = process_single_pdf(pdf_file_path, output_path_obj, model_name, app_queue)
            if success:
                successful_conversions += 1
            else:
                failed_conversions += 1
                failed_files_list.append(pdf_file_path.name)
        else:
            app_queue.put((logging.WARNING, f"Skipping non-file item: {pdf_file_path.name}"))

    summary_msg = "--- Conversion Summary ---"
    app_queue.put((logging.INFO, summary_msg))
    app_queue.put((logging.INFO, f"Total PDF files found: {len(pdf_files)}"))
    app_queue.put((logging.INFO, f"Successful conversions: {successful_conversions}"))
    app_queue.put((logging.INFO, f"Failed conversions: {failed_conversions}"))
    if failed_files_list:
        app_queue.put((logging.WARNING, f"Files that failed conversion: {', '.join(failed_files_list)}"))
    app_queue.put((logging.INFO, "--------------------------"))
    app_queue.put(("status", f"Done. {successful_conversions} succeeded, {failed_conversions} failed."))
    app_queue.put(("finished", None)) # Signal completion


# --- Tkinter GUI Application ---

class TextHandler(logging.Handler):
    """Custom logging handler to redirect logs to a tkinter Text widget."""
    def __init__(self, text_widget, app_queue):
        super().__init__()
        self.text_widget = text_widget
        self.app_queue = app_queue
        self.formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        self.setLevel(logging.INFO)

    def emit(self, record):
        # Send log record to be processed in the main GUI thread
        self.app_queue.put(("log", self.format(record)))


class PdfConverterApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PDF to Markdown Converter")
        self.geometry("800x600")

        self.app_queue = queue.Queue()

        self.input_dir = tk.StringVar()
        self.output_dir = tk.StringVar()

        self._setup_ui()
        self._setup_logging()
        
        self.after(100, self.process_app_queue) # Check queue periodically

    def _setup_logging(self):
        # Configure the root logger or a specific logger
        # Using __name__ logger from the top of the file
        global logger 
        logger.setLevel(logging.INFO)
        
        # Remove any existing handlers to avoid duplicate logs if script is re-run
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
            
        # Add our custom TextHandler
        # Note: TextHandler now uses app_queue to send log messages, not directly writing
        # We can still add a streamhandler for console output if desired
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(stream_handler) # For console visibility

        # The TextHandler is implicitly used by how process_pdf_folder puts messages on app_queue

    def _setup_ui(self):
        # Frame for directory selection
        dir_frame = ttk.Frame(self, padding="10")
        dir_frame.pack(fill=tk.X, padx=10, pady=5)

        # Input directory
        ttk.Label(dir_frame, text="Input PDF Directory:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.input_entry = ttk.Entry(dir_frame, textvariable=self.input_dir, width=60, state="readonly")
        self.input_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
        self.browse_input_btn = ttk.Button(dir_frame, text="Browse...", command=self._browse_input)
        self.browse_input_btn.grid(row=0, column=2, padx=5, pady=5)

        # Output directory
        ttk.Label(dir_frame, text="Output Directory:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.output_entry = ttk.Entry(dir_frame, textvariable=self.output_dir, width=60, state="readonly")
        self.output_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.EW)
        self.browse_output_btn = ttk.Button(dir_frame, text="Browse...", command=self._browse_output)
        self.browse_output_btn.grid(row=1, column=2, padx=5, pady=5)
        
        dir_frame.columnconfigure(1, weight=1) # Make entry field expand

        # Log display area
        log_frame = ttk.LabelFrame(self, text="Logs", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, state="disabled", height=15)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # Control frame
        control_frame = ttk.Frame(self, padding="10")
        control_frame.pack(fill=tk.X, padx=10, pady=5)

        self.start_button = ttk.Button(control_frame, text="Start Conversion", command=self.start_conversion_thread)
        self.start_button.pack(pady=5)

        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Idle")
        status_bar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W, padding="2 5")
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _browse_input(self):
        dir_path = filedialog.askdirectory(title="Select Input PDF Directory")
        if dir_path:
            self.input_dir.set(dir_path)
            self.log_message(f"Input directory selected: {dir_path}", logging.INFO)

    def _browse_output(self):
        dir_path = filedialog.askdirectory(title="Select Output Directory")
        if dir_path:
            self.output_dir.set(dir_path)
            self.log_message(f"Output directory selected: {dir_path}", logging.INFO)

    def log_message(self, message, level=logging.INFO):
        # This method is now primarily for GUI-initiated logs.
        # Logs from the processing thread will come via app_queue.
        formatted_message = f"{logging.getLevelName(level)}: {message}" # Simple format
        self._insert_log_text(formatted_message)

    def _insert_log_text(self, message):
        self.log_text.configure(state="normal")
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.configure(state="disabled")
        self.log_text.see(tk.END) # Scroll to the end

    def update_status(self, message):
        self.status_var.set(message)

    def start_conversion_thread(self):
        input_d = self.input_dir.get()
        output_d = self.output_dir.get()

        if not input_d or not output_d:
            self.log_message("Please select both input and output directories.", logging.WARNING)
            tk.messagebox.showwarning("Missing Paths", "Please select both input and output directories.")
            return

        self.log_text.configure(state="normal")
        self.log_text.delete(1.0, tk.END) # Clear previous logs
        self.log_text.configure(state="disabled")

        self.log_message("Starting conversion process...", logging.INFO)
        self.update_status("Processing...")
        self.start_button.config(state="disabled")
        self.browse_input_btn.config(state="disabled")
        self.browse_output_btn.config(state="disabled")

        # Run process_pdf_folder in a separate thread
        self.conversion_thread = threading.Thread(
            target=process_pdf_folder,
            args=(input_d, output_d, self.app_queue),
            daemon=True # Allows main app to exit even if thread is running
        )
        self.conversion_thread.start()

    def process_app_queue(self):
        try:
            while True: # Process all messages currently in the queue
                message_type, payload = self.app_queue.get_nowait()

                if message_type == "log":
                    self._insert_log_text(payload) # payload is already formatted log string
                elif message_type == logging.INFO: # Direct log level from processing functions
                    self._insert_log_text(f"INFO: {payload}")
                elif message_type == logging.ERROR:
                     # Check if exc_info was passed (as a third element in a tuple)
                    if isinstance(payload, tuple) and len(payload) > 1 and payload[1] is True:
                        self._insert_log_text(f"ERROR: {payload[0]} (See console for traceback)")
                    else:
                        self._insert_log_text(f"ERROR: {payload}")
                elif message_type == logging.WARNING:
                    self._insert_log_text(f"WARNING: {payload}")
                elif message_type == "status":
                    self.update_status(payload)
                elif message_type == "finished":
                    self.start_button.config(state="normal")
                    self.browse_input_btn.config(state="normal")
                    self.browse_output_btn.config(state="normal")
                    # Status already set by the final status message from process_pdf_folder
                    tk.messagebox.showinfo("Conversion Complete", "PDF processing has finished.")


        except queue.Empty: # No messages in queue
            pass
        finally:
            self.after(100, self.process_app_queue) # Schedule next check


def main():
    # No longer parsing command-line args, instantiate and run the GUI app
    app = PdfConverterApp()
    app.mainloop()

if __name__ == "__main__":
    main()
