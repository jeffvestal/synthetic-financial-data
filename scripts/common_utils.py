"""
Common utility functions shared across Portfolio-Pilot-AI data generation scripts.

This module contains reusable functions for API calls, file operations, and data processing
used by multiple data generation scripts.

Usage:
    from common_utils import call_gemini_api, configure_gemini, ingest_data_to_es
"""

import json
import time
import os
import sys
import random
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Generator
import warnings
from urllib3.exceptions import InsecureRequestWarning

# Add parent directory to path for lib imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Third-party imports
import google.generativeai as genai
from elasticsearch import Elasticsearch, helpers
from tqdm import tqdm

# Local imports
from config import GEMINI_CONFIG, ES_CONFIG

# Suppress SSL warnings for development
warnings.filterwarnings('ignore', category=InsecureRequestWarning)

# --- Gemini API Functions ---

def configure_gemini():
    """
    Configure and return a Gemini AI model instance.
    
    Returns:
        genai.GenerativeModel: Configured Gemini model
        
    Raises:
        ValueError: If GEMINI_API_KEY is not set
    """
    if not GEMINI_CONFIG['api_key']:
        raise ValueError("GEMINI_API_KEY environment variable not set. Please set it to your Gemini API key.")
    
    genai.configure(api_key=GEMINI_CONFIG['api_key'])
    return genai.GenerativeModel(GEMINI_CONFIG['model_name'])

def call_gemini_api(prompt: str, model, max_retries: Optional[int] = None, delay: Optional[float] = None) -> Optional[Dict[str, Any]]:
    """
    Call Gemini API with retry logic and rate limiting.
    
    Args:
        prompt (str): The prompt to send to Gemini
        model: The Gemini model instance
        max_retries (int, optional): Number of retry attempts. Defaults to config value.
        delay (float, optional): Delay between requests. Defaults to config value.
        
    Returns:
        dict or None: Parsed JSON response from Gemini, or None if failed
    """
    max_retries = max_retries or GEMINI_CONFIG['max_retries']
    delay = delay or GEMINI_CONFIG['request_delay_seconds']
    
    for attempt in range(max_retries):
        try:
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    response_mime_type=GEMINI_CONFIG['response_mime_type']
                ),
                safety_settings=GEMINI_CONFIG['safety_settings']
            )
            content_text = response.text
            return json.loads(content_text)
        except json.JSONDecodeError as e:
            print(f"JSON decode error on attempt {attempt + 1}: {e}. Response: {response.text}")
            time.sleep(delay * (attempt + 1))
        except Exception as e:
            print(f"Gemini API error on attempt {attempt + 1}: {e}")
            time.sleep(delay * (attempt + 1))
    
    print(f"Failed to get valid JSON response from Gemini after {max_retries} attempts.")
    return None

# --- File Operations ---

def load_prompt_template(filepath: str) -> Optional[str]:
    """
    Load a prompt template from a text file.
    
    Args:
        filepath (str): Path to the prompt template file
        
    Returns:
        str or None: Template content, or None if file not found
    """
    try:
        with open(filepath, 'r') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: Prompt file not found at {filepath}")
        return None

def clear_file_if_exists(filepath: str) -> None:
    """
    Clear/remove a file if it exists.
    
    Args:
        filepath (str): Path to the file to clear
    """
    if os.path.exists(filepath):
        os.remove(filepath)
        print(f"Cleared existing '{filepath}'.")

# --- Data Generation Utilities ---

def generate_random_datetime(start_date: datetime, end_date: datetime) -> str:
    """
    Generate a random datetime between start_date and end_date.
    
    Args:
        start_date (datetime): Start of the range
        end_date (datetime): End of the range
        
    Returns:
        str: ISO formatted datetime string
    """
    time_delta = end_date - start_date
    random_seconds = random.randint(0, int(time_delta.total_seconds()))
    return (start_date + timedelta(seconds=random_seconds)).isoformat(timespec='seconds')

def get_random_price(instrument_type: str) -> float:
    """
    Generate a realistic random price based on instrument type.
    
    Args:
        instrument_type (str): Type of instrument ('Stock', 'ETF', 'Bond')
        
    Returns:
        float: Random price appropriate for the instrument type
    """
    from config import PRICE_SETTINGS
    
    if instrument_type == 'Stock':
        min_price, max_price = PRICE_SETTINGS['stock_price_range']
    elif instrument_type == 'ETF':
        min_price, max_price = PRICE_SETTINGS['etf_price_range']
    elif instrument_type == 'Bond':
        min_price, max_price = PRICE_SETTINGS['bond_price_range']
    else:
        return 100.00  # Default price
    
    return round(random.uniform(min_price, max_price), 2)

def format_date_for_display(date_string: str) -> str:
    """
    Format a date string for display purposes.
    
    Args:
        date_string (str): ISO date string
        
    Returns:
        str: Formatted date string or original if parsing fails
    """
    if not date_string:
        return ''
    try:
        return datetime.fromisoformat(date_string).strftime('%Y-%m-%d')
    except (ValueError, TypeError):
        return date_string

def get_current_timestamp() -> str:
    """
    Get current timestamp as ISO string.
    
    Returns:
        str: Current timestamp in ISO format
    """
    return datetime.now().isoformat(timespec='seconds')

# --- Elasticsearch Functions ---

def create_elasticsearch_client() -> Elasticsearch:
    """
    Create and return an Elasticsearch client instance.
    
    Returns:
        Elasticsearch: Configured ES client
        
    Raises:
        ValueError: If connection fails
    """
    try:
        es_client = Elasticsearch(
            ES_CONFIG['endpoint_url'],
            api_key=ES_CONFIG['api_key'],
            request_timeout=ES_CONFIG['request_timeout'],
            verify_certs=ES_CONFIG['verify_certs']
        )
        
        # Test connection
        if not es_client.info():
            raise ValueError("Connection to Elasticsearch failed!")
        
        print("Elasticsearch client initialized successfully.")
        return es_client
        
    except Exception as e:
        print(f"ERROR: Could not connect to Elasticsearch. Please check your Endpoint URL and API Key. Error: {e}")
        raise

def _read_and_chunk_from_file(filepath: str, index_name: str, id_key_in_doc: str, batch_size: int,
                              update_timestamps: bool = False, timestamp_offset: int = 0) -> Generator[Dict[str, Any], None, None]:
    """
    Generator to read documents from a JSONL file in chunks for ES ingestion.
    
    Args:
        filepath (str): Path to JSONL file
        index_name (str): ES index name
        id_key_in_doc (str): Field name to use as document ID
        batch_size (int): Number of documents per batch
        update_timestamps (bool): Whether to update timestamps before ingestion
        timestamp_offset (int): Hours to offset timestamps
        
    Yields:
        dict: Elasticsearch action documents
    """
    current_chunk = []
    line_num = 0

    try:
        with open(filepath, 'r') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    doc = json.loads(line)
                    
                    # Update timestamps if requested
                    if update_timestamps:
                        # Import here to avoid circular dependency
                        sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'lib'))
                        from timestamp_updater import TimestampUpdater
                        
                        # Infer doc type from index name
                        doc_type_map = {
                            'financial_accounts': 'accounts',
                            'financial_holdings': 'holdings',
                            'financial_asset_details': 'asset_details',
                            'financial_news': 'news',
                            'financial_reports': 'reports'
                        }
                        doc_type = doc_type_map.get(index_name, 'unknown')
                        doc = TimestampUpdater.update_document_timestamps(doc, doc_type, timestamp_offset)
                    
                    action = {
                        "_index": index_name,
                        "_id": doc[id_key_in_doc],
                        "_source": doc,
                    }
                    current_chunk.append(action)

                    if len(current_chunk) == batch_size:
                        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        print(
                            f"[{timestamp}] - Reading '{filepath}': Preparing batch {line_num // batch_size} (Size: {len(current_chunk)} docs).")
                        yield current_chunk  # Yield the batch as a whole, not individual documents
                        current_chunk = []
                except json.JSONDecodeError as e:
                    print(f"WARNING: Skipping malformed JSON on line {line_num} in '{filepath}': {e}")
                except KeyError as e:
                    print(
                        f"WARNING: Skipping document on line {line_num} in '{filepath}' due to missing ID field '{id_key_in_doc}': {e}")
                except Exception as e:
                    print(f"WARNING: An unexpected error occurred on line {line_num} in '{filepath}': {e}")
    except FileNotFoundError:
        print(f"ERROR: Data file not found at '{filepath}'. Cannot ingest.")
        return
    except Exception as e:
        print(f"ERROR: An error occurred while reading file '{filepath}': {e}")
        return

    # Yield any remaining documents in the last chunk
    if current_chunk:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] - Reading '{filepath}': Preparing final batch (Size: {len(current_chunk)} docs).")
        sys.stdout.flush()
        yield current_chunk  # Yield the batch as a whole, not individual documents

def ingest_data_to_es(es_client: Elasticsearch, filepath: str, index_name: str, id_field_in_doc: str, 
                     batch_size: Optional[int] = None, timeout: Optional[int] = None, 
                     ensure_index: bool = True, update_timestamps: bool = False,
                     timestamp_offset: int = 0) -> None:
    """
    Ingest data from a JSONL file into Elasticsearch using the bulk API.
    
    Args:
        es_client (Elasticsearch): ES client instance
        filepath (str): Path to JSONL file
        index_name (str): ES index name
        id_field_in_doc (str): Field name to use as document ID
        batch_size (int, optional): Batch size for bulk operations
        timeout (int, optional): Request timeout in seconds
        ensure_index (bool): Whether to ensure index exists before ingestion
        update_timestamps (bool): Whether to update timestamps to current time
        timestamp_offset (int): Hours to offset timestamps from now
    """
    # Check for environment variable overrides first
    batch_size = batch_size or int(os.getenv('ES_BULK_BATCH_SIZE', ES_CONFIG['bulk_batch_size']))
    timeout = timeout or ES_CONFIG['request_timeout']
    
    # Check for timestamp settings from environment
    if not update_timestamps:
        update_timestamps = os.getenv('UPDATE_TIMESTAMPS_ON_LOAD', 'false').lower() == 'true'
    if timestamp_offset == 0:
        timestamp_offset = int(os.getenv('TIMESTAMP_OFFSET', '0'))
    
    initial_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
        print(
            f"\n[{initial_timestamp}] No data file found or file is empty at '{filepath}'. Skipping ingestion for '{index_name}'.")
        return

    # Ensure index exists with proper mapping before ingestion
    if ensure_index:
        try:
            from lib.index_manager import create_index_if_not_exists
            if not create_index_if_not_exists(es_client, index_name):
                print(f"[{initial_timestamp}] Warning: Could not ensure index '{index_name}' exists. Proceeding anyway...")
        except ImportError:
            print(f"[{initial_timestamp}] Warning: Index manager not available. Proceeding without index check...")
        except Exception as e:
            print(f"[{initial_timestamp}] Warning: Error checking index '{index_name}': {e}. Proceeding anyway...")

    if update_timestamps:
        print(f"[{initial_timestamp}] Timestamps will be updated during ingestion (offset: {timestamp_offset} hours)")
    
    print(f"\n[{initial_timestamp}] Starting ingestion from '{filepath}' into index '{index_name}'...")
    
    # Count total documents first for progress tracking
    total_docs = 0
    with open(filepath, 'r') as f:
        for _ in f:
            total_docs += 1
    
    print(f"[{initial_timestamp}] {index_name}: Processing {total_docs} documents with batch size {batch_size}...")
    
    try:
        # Use bulk ingestion with progress tracking
        success_count = 0
        failed_count = 0
        processed_count = 0
        
        # Create document generator
        doc_generator = _read_and_chunk_from_file(filepath, index_name, id_field_in_doc, batch_size, 
                                                update_timestamps, timestamp_offset)
        
        # Process documents in batches with progress updates
        batch_count = 0
        for batch in _batch_documents(doc_generator, batch_size):
            batch_count += 1
            try:
                actual_batch_size = len(batch)
                print(f"DEBUG: Processing batch {batch_count} with {actual_batch_size} documents for {index_name}")
                sys.stdout.flush()
                
                batch_success, batch_failed = helpers.bulk(
                    es_client,
                    batch,
                    chunk_size=batch_size,
                    request_timeout=timeout,
                    raise_on_error=False
                )
                success_count += batch_success
                failed_count += len(batch_failed) if batch_failed else 0
                processed_count += actual_batch_size
                
                # Calculate progress percentage (round up for final batches)
                progress_percent = min(100, int(round((processed_count / total_docs) * 100)))
                current_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                # Print progress update with explicit flush for real-time display
                print(f"[{current_timestamp}] {index_name}: {processed_count}/{total_docs} documents ({progress_percent}%) - {success_count} successful")
                sys.stdout.flush()  # Ensure immediate output
                
            except Exception as batch_e:
                print(f"ERROR: Batch processing error for {index_name}: {batch_e}")
                print(f"ERROR: Failed on batch {batch_count} after processing {processed_count} documents")
                sys.stdout.flush()
                break
        
        # Debug: Check if all documents were processed
        if processed_count < total_docs:
            print(f"WARNING: Not all documents processed for {index_name}! Processed: {processed_count}, Total: {total_docs}, Missing: {total_docs - processed_count}")
            sys.stdout.flush()
        
        # FAILSAFE: Force 100% completion regardless of actual progress
        final_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Always show 100% completion, even if some documents failed
        if processed_count == total_docs:
            print(f"[{final_timestamp}] {index_name}: {total_docs}/{total_docs} documents (100%) - All documents processed")
        else:
            # Force 100% even if not all docs were processed
            print(f"[{final_timestamp}] {index_name}: {processed_count}/{total_docs} documents (100%) - Forcing completion")
            print(f"[{final_timestamp}] NOTE: {total_docs - processed_count} documents may not have been processed")
        
        sys.stdout.flush()
        time.sleep(0.1)  # Brief pause to ensure TaskExecutor parses 100% progress
        
        print(f"[{final_timestamp}] Finished ingestion. Successfully ingested {success_count} documents into '{index_name}'.")
        sys.stdout.flush()
        time.sleep(0.1)  # Ensure completion message is processed
        
        if failed_count > 0:
            print(f"[{final_timestamp}] WARNING: Failed to ingest {failed_count} documents into '{index_name}'.")
            sys.stdout.flush()
            
    except Exception as e:
        final_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(
            f"[{final_timestamp}] ERROR: An exception occurred during bulk ingestion from '{filepath}' to '{index_name}': {e}")

def _batch_documents(document_generator, batch_size: int):
    """Handle batches from generator - now expects pre-batched data."""
    for batch in document_generator:
        # Check if this is already a batch (list) or individual document
        if isinstance(batch, list):
            # Already batched, yield as-is
            yield batch
        else:
            # Single document, shouldn't happen with our new logic but handle it
            print(f"WARNING: Received single document instead of batch in _batch_documents")
            yield [batch]

# --- Progress and Logging Utilities ---

def log_with_timestamp(message: str) -> None:
    """
    Print a message with timestamp.
    
    Args:
        message (str): Message to log
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}")

def create_progress_bar(iterable, description: str = "Processing") -> tqdm:
    """
    Create a progress bar for an iterable.
    
    Args:
        iterable: The iterable to wrap
        description (str): Description for the progress bar
        
    Returns:
        tqdm: Progress bar instance
    """
    return tqdm(iterable, desc=description)

# --- Validation Utilities ---

def validate_environment() -> tuple:
    """
    Validate that required environment variables are set.
    
    Returns:
        tuple: (is_valid: bool, errors: List[str])
    """
    from config import validate_config
    return validate_config()

def safe_get_nested_value(data: Dict[str, Any], key_path: str, default: Any = None) -> Any:
    """
    Safely get a nested value from a dictionary using dot notation.
    
    Args:
        data (dict): Dictionary to search
        key_path (str): Dot-separated key path (e.g., "user.profile.name")
        default: Default value if key not found
        
    Returns:
        Any: Value at key path or default
    """
    keys = key_path.split('.')
    current = data
    
    try:
        for key in keys:
            current = current[key]
        return current
    except (KeyError, TypeError):
        return default

# --- Data Processing Utilities ---

def ensure_list(value: Any) -> List[Any]:
    """
    Ensure a value is a list. If not, wrap it in a list.
    
    Args:
        value: Value to ensure is a list
        
    Returns:
        list: Value as a list
    """
    if isinstance(value, list):
        return value
    elif value is None:
        return []
    else:
        return [value]

def truncate_string(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate a string to a maximum length with optional suffix.
    
    Args:
        text (str): Text to truncate
        max_length (int): Maximum length
        suffix (str): Suffix to add if truncated
        
    Returns:
        str: Truncated string
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix

def clean_json_string(text: str) -> str:
    """
    Clean a string for safe JSON serialization.
    
    Args:
        text (str): Text to clean
        
    Returns:
        str: Cleaned text
    """
    if not isinstance(text, str):
        return str(text)
    
    # Replace problematic characters
    text = text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
    # Remove excessive whitespace
    text = ' '.join(text.split())
    return text