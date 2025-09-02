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
import gc  # For garbage collection in Colab
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Generator
import warnings
from urllib3.exceptions import InsecureRequestWarning, NotOpenSSLWarning
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Suppress urllib3 warnings before importing elasticsearch
warnings.filterwarnings('ignore', category=NotOpenSSLWarning)
warnings.filterwarnings('ignore', category=InsecureRequestWarning)

# Add parent directory to path for lib imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Third-party imports
import google.generativeai as genai
from elasticsearch import Elasticsearch, helpers
from tqdm import tqdm

# Local imports
from config import GEMINI_CONFIG, ES_CONFIG

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
        # Determine if we should verify certs based on endpoint
        endpoint = ES_CONFIG['endpoint_url']
        verify_certs = ES_CONFIG['verify_certs']
        
        # For Elastic Cloud endpoints, always verify certs
        if 'elastic.cloud' in endpoint or 'es.io' in endpoint:
            verify_certs = True
        
        # Suppress the security warning if we're explicitly not verifying
        if not verify_certs:
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        es_client = Elasticsearch(
            endpoint,
            api_key=ES_CONFIG['api_key'],
            request_timeout=ES_CONFIG['request_timeout'],
            verify_certs=verify_certs
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
    
    # Import TimestampUpdater once if needed (not for every document!)
    timestamp_updater = None
    doc_type = None
    if update_timestamps:
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'lib'))
        from timestamp_updater import TimestampUpdater
        timestamp_updater = TimestampUpdater
        
        # Infer doc type from index name once
        doc_type_map = {
            'financial_accounts': 'accounts',
            'financial_holdings': 'holdings',
            'financial_asset_details': 'asset_details',
            'financial_news': 'news',
            'financial_reports': 'reports'
        }
        doc_type = doc_type_map.get(index_name, 'unknown')
        
        # Debug: Show what timestamp will be used (use stderr to bypass Colab suppression)
        sample_timestamp = timestamp_updater.calculate_target_timestamp(timestamp_offset)
        print(f"  Updating timestamps to: {sample_timestamp}", file=sys.stderr)
        sys.stderr.flush()

    try:
        with open(filepath, 'r') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    doc = json.loads(line)
                    
                    # Update timestamps if requested
                    if update_timestamps and timestamp_updater:
                        doc = timestamp_updater.update_document_timestamps(doc, doc_type, timestamp_offset)
                    
                    action = {
                        "_index": index_name,
                        "_id": doc[id_key_in_doc],
                        "_source": doc,
                    }
                    current_chunk.append(action)

                    if len(current_chunk) == batch_size:
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
        yield current_chunk  # Yield the batch as a whole, not individual documents

def ingest_data_to_es(es_client: Elasticsearch, filepath: str, index_name: str, id_field_in_doc: str, 
                     batch_size: Optional[int] = None, timeout: Optional[int] = None, 
                     ensure_index: bool = True, update_timestamps: bool = False,
                     timestamp_offset: int = 0, parallel_bulk_workers: Optional[int] = None) -> None:
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
        parallel_bulk_workers (int, optional): Number of parallel bulk workers (default 1)
    """
    # SIMPLE VERSION - Just print start/end, no complex progress tracking
    batch_size = batch_size or int(os.getenv('ES_BULK_BATCH_SIZE', ES_CONFIG['bulk_batch_size']))
    timeout = timeout or ES_CONFIG['request_timeout']
    parallel_bulk_workers = parallel_bulk_workers or int(os.getenv('PARALLEL_BULK_WORKERS', '1'))
    
    # Check for timestamp settings from environment
    if not update_timestamps:
        update_timestamps = os.getenv('UPDATE_TIMESTAMPS_ON_LOAD', 'false').lower() == 'true'
    if timestamp_offset == 0:
        timestamp_offset = int(os.getenv('TIMESTAMP_OFFSET', '0'))
    
    # Start message - use both stdout and stderr to ensure visibility
    if update_timestamps:
        msg = f"Starting: {index_name} (workers: {parallel_bulk_workers}, updating timestamps to current time)"
        print(msg)
        print(msg, file=sys.stderr)  # Also print to stderr for Colab
    else:
        print(f"Starting: {index_name} (workers: {parallel_bulk_workers})")
    sys.stdout.flush()
    sys.stderr.flush()
    
    if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
        return  # Silent failure

    # Ensure index exists
    if ensure_index:
        try:
            from lib.index_manager import create_index_if_not_exists
            create_index_if_not_exists(es_client, index_name)
        except:
            pass  # Ignore errors, just continue
    
    try:
        # Create document generator  
        doc_generator = _read_and_chunk_from_file(filepath, index_name, id_field_in_doc, batch_size, 
                                                update_timestamps, timestamp_offset)
        
        # Convert generator to list of batches for parallel processing
        all_batches = list(_batch_documents(doc_generator, batch_size))
        total_batches = len(all_batches)
        batch_counter = 0
        
        if parallel_bulk_workers == 1:
            # Original single-threaded processing
            success_count = 0
            total_count = 0
            for batch in all_batches:
                batch_counter += 1
                try:
                    batch_success, _ = helpers.bulk(
                        es_client,
                        batch,
                        chunk_size=batch_size,
                        request_timeout=timeout,
                        raise_on_error=False
                    )
                    success_count += batch_success
                    total_count += len(batch)
                    # Simple progress logging
                    timestamp = datetime.now().strftime('%H:%M:%S')
                    print(f"[{timestamp}] {index_name}: batch {batch_counter}/{total_batches} complete ({len(batch)} docs, {total_count} total)", 
                          file=sys.stderr)
                    sys.stderr.flush()
                except:
                    pass
        else:
            # Parallel bulk processing
            success_count = 0
            total_count = 0
            batch_counter = 0
            lock = threading.Lock()
            
            def process_batch(batch_info):
                nonlocal success_count, total_count, batch_counter
                batch_num, batch = batch_info
                try:
                    batch_success, _ = helpers.bulk(
                        es_client,
                        batch,
                        chunk_size=batch_size,
                        request_timeout=timeout,
                        raise_on_error=False
                    )
                    with lock:
                        success_count += batch_success
                        total_count += len(batch)
                        batch_counter += 1
                        # Simple progress logging (thread-safe)
                        timestamp = datetime.now().strftime('%H:%M:%S')
                        print(f"[{timestamp}] {index_name}: batch {batch_counter}/{total_batches} complete ({len(batch)} docs, {total_count} total)", 
                              file=sys.stderr)
                        sys.stderr.flush()
                    return True
                except Exception as e:
                    with lock:
                        batch_counter += 1
                        timestamp = datetime.now().strftime('%H:%M:%S')
                        print(f"[{timestamp}] {index_name}: batch {batch_counter}/{total_batches} FAILED", 
                              file=sys.stderr)
                        sys.stderr.flush()
                    return False
            
            # Process batches in parallel with batch numbers
            with ThreadPoolExecutor(max_workers=parallel_bulk_workers) as executor:
                # Create batch info tuples with batch numbers
                batch_infos = [(i+1, batch) for i, batch in enumerate(all_batches)]
                futures = [executor.submit(process_batch, batch_info) for batch_info in batch_infos]
                # Wait for all to complete
                for future in as_completed(futures):
                    try:
                        future.result()
                    except:
                        pass
        
        # No completion message in Colab to avoid threading issues
        pass
            
    except Exception as e:
        # Silent failure in Colab
        pass

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

# --- Inference Endpoint Functions ---

def check_inference_endpoint_needed(indices: List[str]) -> bool:
    """
    Check if any of the indices require inference endpoints.
    
    Args:
        indices: List of index names to check
        
    Returns:
        bool: True if any index needs inference endpoints
    """
    semantic_indices = ['financial_news', 'financial_reports']
    return any(idx in semantic_indices for idx in indices)

def wait_for_inference_endpoint_if_needed(indices: List[str]) -> bool:
    """
    Wait for inference endpoint if any indices need it.
    
    Args:
        indices: List of index names to load
        
    Returns:
        bool: True if ready or not needed, False if failed
    """
    if not check_inference_endpoint_needed(indices):
        return True
    
    try:
        # Import here to avoid circular imports
        from lib.inference_endpoint_checker import wait_for_elser_endpoint
        
        print("\n🔍 Semantic search indices detected. Checking inference endpoint...")
        
        success, message = wait_for_elser_endpoint(
            ES_CONFIG['endpoint_url'], 
            ES_CONFIG['api_key'],
            max_wait_seconds=300  # 5 minutes max
        )
        
        print(message)
        
        if not success:
            print("\n⚠️  Options:")
            print("1. Wait for endpoint to be deployed in Kibana")
            print("2. Continue without semantic search indices")
            
            choice = input("\nContinue without semantic indices? (y/N): ").lower()
            if choice == 'y':
                print("📝 Skipping semantic search indices...")
                return False  # Indicate to skip semantic indices
            else:
                print("❌ Stopping. Please deploy the inference endpoint and try again.")
                return False
        
        return True
        
    except ImportError:
        print("⚠️  Inference endpoint checker not available. Continuing...")
        return True
    except Exception as e:
        print(f"⚠️  Error checking inference endpoint: {e}")
        print("Continuing with loading (semantic search may fail)...")
        return True