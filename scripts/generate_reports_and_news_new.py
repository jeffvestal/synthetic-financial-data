import random
from datetime import datetime, timedelta
import uuid
import json
import time
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
import warnings

# Suppress urllib3 warning about LibreSSL compatibility
warnings.filterwarnings("ignore", message="urllib3 v2 only supports OpenSSL 1.1.1+", category=UserWarning)

# Third-party libraries
from tqdm import tqdm

# Local imports
from config import (
    ES_CONFIG, FILE_PATHS, GENERATION_SETTINGS, CONTENT_SETTINGS,
    FIELD_NAMES, GEMINI_CONFIG, validate_config
)
from symbols_config import (
    STOCK_SYMBOLS_AND_INFO, ETF_SYMBOLS_AND_INFO, get_asset_info, ALL_ASSET_SYMBOLS
)
from common_utils import (
    configure_gemini, call_gemini_api, load_prompt_template,
    create_elasticsearch_client, ingest_data_to_es, clear_file_if_exists,
    log_with_timestamp, create_progress_bar, get_current_timestamp
)
from symbol_manager import SymbolManager

# --- Configuration (loaded from config module) ---
# All configuration now centralized in config.py
PROMPT_FILES = FILE_PATHS['prompts']
NUM_SPECIFIC_NEWS_PER_ASSET = GENERATION_SETTINGS['news']['num_specific_per_asset']
NUM_GENERAL_NEWS_ARTICLES = GENERATION_SETTINGS['news']['num_general_articles']
NUM_SPECIFIC_ASSETS_FOR_NEWS = GENERATION_SETTINGS['news']['num_specific_assets_for_news']

NUM_SPECIFIC_REPORTS_PER_ASSET = GENERATION_SETTINGS['reports']['num_specific_per_asset']
NUM_THEMATIC_REPORTS = GENERATION_SETTINGS['reports']['num_thematic_reports']
NUM_SPECIFIC_ASSETS_FOR_REPORTS = GENERATION_SETTINGS['reports']['num_specific_assets_for_reports']

# File paths from config
GENERATED_NEWS_FILE = FILE_PATHS['generated_news']
GENERATED_REPORTS_FILE = FILE_PATHS['generated_reports']

# Index names from config
NEWS_INDEX = ES_CONFIG['indices']['news']
REPORTS_INDEX = ES_CONFIG['indices']['reports']

# Field names from config
PRIMARY_SYMBOL_FIELD_NAME = FIELD_NAMES['primary_symbol']

# Content options from config
SENTIMENT_OPTIONS = CONTENT_SETTINGS['sentiment_options']
NEWS_EVENT_THEMES = CONTENT_SETTINGS['news_event_themes']
GENERAL_MARKET_EVENTS = CONTENT_SETTINGS['general_market_events']
REPORT_TYPES = CONTENT_SETTINGS['report_types']
REPORT_FOCUS_THEMES = CONTENT_SETTINGS['report_focus_themes']
THEME_INDUSTRIES = CONTENT_SETTINGS['theme_industries']

# Initialize symbol manager
symbol_manager = SymbolManager()

# Global model instance
gemini_model = None


def generate_news_articles(num_specific: int, num_general: int, output_filepath: str):
    """Generates synthetic news articles using Gemini API and writes to file."""
    news_articles_generated = 0
    specific_news_template = load_prompt_template(PROMPT_FILES["specific_news"])
    general_news_template = load_prompt_template(PROMPT_FILES["general_news"])

    if not specific_news_template or not general_news_template:
        print("Could not load news prompt templates. Exiting news generation.")
        return 0

    print(f"\\nGenerating news articles to '{output_filepath}'...")
    with open(output_filepath, 'a') as f:  # Open in append mode
        # Generate specific news (tied to assets)
        print("Generating specific news articles...")
        
        # Use symbol manager to get symbols
        available_symbols = symbol_manager.get_stocks_and_etfs()  # Stocks and ETFs only
        specific_assets_to_cover = random.sample(
            available_symbols,
            min(NUM_SPECIFIC_ASSETS_FOR_NEWS, len(available_symbols))
        )

        for symbol in create_progress_bar(specific_assets_to_cover, "Specific News"):
            current_datetime_str = get_current_timestamp()
            asset_info = get_asset_info(symbol)
            
            if not asset_info:
                continue

            prompt = specific_news_template.format(
                COMPANY_NAME=asset_info['name'],
                SYMBOL=symbol,
                SECTOR=asset_info['sector'],
                SENTIMENT=random.choice(SENTIMENT_OPTIONS),
                EVENT_THEME=random.choice(NEWS_EVENT_THEMES),
                CURRENT_DATETIME_STRING=current_datetime_str
            )
            generated_data = call_gemini_api(prompt, gemini_model)
            time.sleep(GEMINI_CONFIG['request_delay_seconds'])

            if generated_data:
                article = {
                    'article_id': str(uuid.uuid4()),
                    'title': generated_data.get('title', 'No Title'),
                    'content': generated_data.get('content', 'No content generated.'),
                    'source': generated_data.get('source', random.choice(
                        ["Financial Today", "Global Market News", "Investment Daily"])),
                    'published_date': current_datetime_str,
                    'url': f"http://fakenews.com/article/{uuid.uuid4().hex[:8]}",
                    'entities': generated_data.get('entities', [symbol, asset_info['sector']]),
                    'sentiment': generated_data.get('sentiment', 'neutral'),
                    'last_updated': get_current_timestamp(),
                    'primary_symbol': generated_data.get('primary_symbol', symbol),
                    'company_symbol': generated_data.get('company_symbol', None)
                }
                f.write(json.dumps(article) + '\n')
                news_articles_generated += 1

        # Generate general market news
        print("Generating general market news articles...")
        for i in create_progress_bar(range(num_general), "General News"):
            current_datetime_str = get_current_timestamp()
            prompt = general_news_template.format(
                SENTIMENT=random.choice(SENTIMENT_OPTIONS),
                MARKET_EVENT=random.choice(GENERAL_MARKET_EVENTS),
                CURRENT_DATETIME_STRING=current_datetime_str
            )
            generated_data = call_gemini_api(prompt, gemini_model)
            time.sleep(GEMINI_CONFIG['request_delay_seconds'])

            if generated_data:
                article = {
                    'article_id': str(uuid.uuid4()),
                    'title': generated_data.get('title', 'Market Update'),
                    'content': generated_data.get('content', 'No content generated.'),
                    'source': generated_data.get('source', random.choice(
                        ["Financial Today", "Global Market News", "Investment Daily"])),
                    'published_date': current_datetime_str,
                    'url': f"http://fakenews.com/article/{uuid.uuid4().hex[:8]}",
                    'entities': generated_data.get('entities', ["Market", "Economy"]),
                    'sentiment': generated_data.get('sentiment', 'neutral'),
                    'last_updated': get_current_timestamp(),
                    'primary_symbol': generated_data.get('primary_symbol', None),
                    'company_symbol': generated_data.get('company_symbol', None)
                }
                f.write(json.dumps(article) + '\n')
                news_articles_generated += 1

    return news_articles_generated


def generate_reports(num_specific: int, num_thematic: int, output_filepath: str):
    """Generates synthetic reports using Gemini API and writes to file."""
    reports_generated = 0
    specific_report_template = load_prompt_template(PROMPT_FILES["specific_report"])
    thematic_report_template = load_prompt_template(PROMPT_FILES["thematic_report"])

    if not specific_report_template or not thematic_report_template:
        print("Could not load report prompt templates. Exiting report generation.")
        return 0

    print(f"\\nGenerating reports to '{output_filepath}'...")
    with open(output_filepath, 'a') as f:  # Open in append mode
        # Generate specific reports (tied to assets)
        print("Generating specific company reports...")
        
        # Use symbol manager to get symbols
        available_symbols = symbol_manager.get_stocks_and_etfs()
        specific_assets_to_cover = random.sample(
            available_symbols,
            min(NUM_SPECIFIC_ASSETS_FOR_REPORTS, len(available_symbols))
        )

        for symbol in create_progress_bar(specific_assets_to_cover, "Specific Reports"):
            current_datetime_str = get_current_timestamp()
            asset_info = get_asset_info(symbol)
            
            if not asset_info:
                continue

            prompt = specific_report_template.format(
                COMPANY_NAME=asset_info['name'],
                SYMBOL=symbol,
                SECTOR=asset_info['sector'],
                REPORT_TYPE=random.choice(REPORT_TYPES),
                FOCUS_THEME=random.choice(REPORT_FOCUS_THEMES),
                SENTIMENT=random.choice(SENTIMENT_OPTIONS),
                CURRENT_DATETIME_STRING=current_datetime_str
            )
            generated_data = call_gemini_api(prompt, gemini_model)
            time.sleep(GEMINI_CONFIG['request_delay_seconds'])

            if generated_data:
                report = {
                    'report_id': str(uuid.uuid4()),
                    'title': generated_data.get('title', 'Company Report'),
                    'content': generated_data.get('content', 'No content generated.'),
                    'source': generated_data.get('source', random.choice(
                        ["Analyst Insights", "Financial Research Corp", "Market Analysis Group"])),
                    'published_date': current_datetime_str,
                    'url': f"http://fakereports.com/report/{uuid.uuid4().hex[:8]}",
                    'entities': generated_data.get('entities', [symbol, asset_info['sector']]),
                    'sentiment': generated_data.get('sentiment', 'neutral'),
                    'last_updated': get_current_timestamp(),
                    'primary_symbol': generated_data.get('primary_symbol', symbol),
                    'company_symbol': generated_data.get('company_symbol', None)
                }
                f.write(json.dumps(report) + '\n')
                reports_generated += 1

        # Generate thematic reports
        print("Generating thematic industry reports...")
        for i in create_progress_bar(range(num_thematic), "Thematic Reports"):
            current_datetime_str = get_current_timestamp()
            prompt = thematic_report_template.format(
                THEME_INDUSTRY=random.choice(THEME_INDUSTRIES),
                SENTIMENT=random.choice(SENTIMENT_OPTIONS),
                FOCUS_THEME=random.choice(REPORT_FOCUS_THEMES),
                CURRENT_DATETIME_STRING=current_datetime_str
            )
            generated_data = call_gemini_api(prompt, gemini_model)
            time.sleep(GEMINI_CONFIG['request_delay_seconds'])

            if generated_data:
                report = {
                    'report_id': str(uuid.uuid4()),
                    'title': generated_data.get('title', 'Industry Report'),
                    'content': generated_data.get('content', 'No content generated.'),
                    'source': generated_data.get('source', random.choice(
                        ["Analyst Insights", "Financial Research Corp", "Market Analysis Group"])),
                    'published_date': current_datetime_str,
                    'url': f"http://fakereports.com/report/{uuid.uuid4().hex[:8]}",
                    'entities': generated_data.get('entities', ["Industry", "Market"]),
                    'sentiment': generated_data.get('sentiment', 'neutral'),
                    'last_updated': get_current_timestamp(),
                    'primary_symbol': generated_data.get('primary_symbol', None),
                    'company_symbol': generated_data.get('company_symbol', None)
                }
                f.write(json.dumps(report) + '\n')
                reports_generated += 1

    return reports_generated


# --- Main Execution ---
if __name__ == "__main__":
    log_with_timestamp("Starting news and reports generation process...")

    # --- Control Flags ---
    DO_GENERATE_NEWS = True
    DO_GENERATE_REPORTS = True
    DO_INGEST_NEWS = True
    DO_INGEST_REPORTS = True

    # 1. Validate configuration based on what we're doing
    # Only check for Gemini API if we're generating new content
    needs_gemini = DO_GENERATE_NEWS or DO_GENERATE_REPORTS
    needs_elasticsearch = DO_INGEST_NEWS or DO_INGEST_REPORTS
    
    is_valid, errors = validate_config(
        check_gemini=needs_gemini,
        check_elasticsearch=needs_elasticsearch
    )
    if not is_valid:
        print("WARNING: Configuration validation failed:")
        for error in errors:
            print(f"  - {error}")
        
        # Check what's missing and disable appropriate features
        es_missing = any("ES_API_KEY" in error for error in errors)
        gemini_missing = any("GEMINI_API_KEY" in error for error in errors)
        
        if es_missing:
            print("Disabling Elasticsearch ingestion.")
            DO_INGEST_NEWS = False
            DO_INGEST_REPORTS = False
        
        if gemini_missing:
            print("Disabling content generation (requires GEMINI_API_KEY).")
            DO_GENERATE_NEWS = False
            DO_GENERATE_REPORTS = False
        
        # If no generation possible but files exist, we could still ingest them
        if gemini_missing and not (DO_GENERATE_NEWS or DO_GENERATE_REPORTS):
            # Check if existing files can be used for ingestion
            news_file_exists = os.path.exists(GENERATED_NEWS_FILE)
            reports_file_exists = os.path.exists(GENERATED_REPORTS_FILE)
            
            if (news_file_exists or reports_file_exists) and not es_missing:
                print("Found existing data files. Ingestion could be performed if ES is configured.")
                if news_file_exists:
                    print(f"  • {GENERATED_NEWS_FILE} exists")
                if reports_file_exists:
                    print(f"  • {GENERATED_REPORTS_FILE} exists")
            
            if not news_file_exists and not reports_file_exists:
                print("ERROR: No generation or ingestion tasks remaining. Please set GEMINI_API_KEY to generate content.")
                print("You can configure API keys through the control app (Configure Settings).")
                sys.exit(1)
            elif es_missing:
                print("INFO: Existing files found but cannot ingest without ES_API_KEY.")
                print("You can configure API keys through the control app (Configure Settings).")
                sys.exit(0)  # Exit successfully since there's nothing we can do
        
        print("Continuing with available features only...")

    # 2. Initialize Gemini model (only if generating)
    if DO_GENERATE_NEWS or DO_GENERATE_REPORTS:
        try:
            gemini_model = configure_gemini()
            print("Gemini model initialized successfully.")
        except Exception as e:
            print(f"ERROR: Could not initialize Gemini model: {e}")
            sys.exit(1)

    # 3. Generate News Articles (if enabled)
    if DO_GENERATE_NEWS:
        log_with_timestamp("--- Generating News Articles ---")
        clear_file_if_exists(GENERATED_NEWS_FILE)
        
        total_news = generate_news_articles(
            num_specific=NUM_SPECIFIC_NEWS_PER_ASSET * NUM_SPECIFIC_ASSETS_FOR_NEWS,
            num_general=NUM_GENERAL_NEWS_ARTICLES,
            output_filepath=GENERATED_NEWS_FILE
        )
        print(f"Total generated news articles saved to file: {total_news}")
    else:
        print("Skipping news generation as DO_GENERATE_NEWS is False.")

    # 4. Generate Reports (if enabled)
    if DO_GENERATE_REPORTS:
        log_with_timestamp("--- Generating Reports ---")
        clear_file_if_exists(GENERATED_REPORTS_FILE)
        
        total_reports = generate_reports(
            num_specific=NUM_SPECIFIC_REPORTS_PER_ASSET * NUM_SPECIFIC_ASSETS_FOR_REPORTS,
            num_thematic=NUM_THEMATIC_REPORTS,
            output_filepath=GENERATED_REPORTS_FILE
        )
        print(f"Total generated reports saved to file: {total_reports}")
    else:
        print("Skipping report generation as DO_GENERATE_REPORTS is False.")

    log_with_timestamp("Data generation phase complete.")

    # 5. Initialize Elasticsearch client (only if any ingestion is enabled)
    es_client = None
    if DO_INGEST_NEWS or DO_INGEST_REPORTS:
        print("\\nInitializing Elasticsearch client for ingestion...")
        try:
            es_client = create_elasticsearch_client()
        except Exception as e:
            print(f"ERROR: Could not connect to Elasticsearch: {e}")
            print("Continuing with local file generation only. You can configure API keys through the control app (Configure Settings).")
            es_client = None
            # Disable ES ingestion flags to continue with file generation
            DO_INGEST_NEWS = False
            DO_INGEST_REPORTS = False

    # 6. Ingest Data into Elasticsearch in parallel (if enabled)
    ingestion_tasks = []
    if DO_INGEST_NEWS:
        ingestion_tasks.append((GENERATED_NEWS_FILE, NEWS_INDEX, "article_id", "News Articles"))
    if DO_INGEST_REPORTS:
        ingestion_tasks.append((GENERATED_REPORTS_FILE, REPORTS_INDEX, "report_id", "Reports"))
    
    if ingestion_tasks:
        log_with_timestamp("--- Starting Parallel Elasticsearch Ingestion ---")
        
        def ingest_index(task_info):
            filepath, index_name, id_field, display_name = task_info
            try:
                log_with_timestamp(f"--- Ingesting {display_name} ---")
                sys.stdout.flush()  # Ensure immediate output
                ingest_data_to_es(es_client, filepath, index_name, id_field)
                result = f"{display_name}: Success"
                log_with_timestamp(f"Completed: {result}")
                sys.stdout.flush()  # Ensure immediate output
                return result
            except Exception as e:
                error_msg = f"{display_name}: Error - {str(e)}"
                print(f"ERROR: {error_msg}")
                sys.stdout.flush()  # Ensure immediate output
                return error_msg
        
        # Use ThreadPoolExecutor for parallel ingestion with proper synchronization
        max_parallel = min(len(ingestion_tasks), 2)  # Limit to 2 concurrent ingestions for this script
        completed_tasks = 0
        total_tasks = len(ingestion_tasks)
        
        with ThreadPoolExecutor(max_workers=max_parallel) as executor:
            future_to_task = {executor.submit(ingest_index, task): task[3] for task in ingestion_tasks}
            
            # Wait for all futures with a timeout
            import concurrent.futures
            try:
                for future in as_completed(future_to_task, timeout=1800):  # 30 minute timeout
                    task_name = future_to_task[future]
                    completed_tasks += 1
                    try:
                        result = future.result(timeout=60)  # 1 minute timeout per result
                        log_with_timestamp(f"Progress: {completed_tasks}/{total_tasks} indices completed")
                        sys.stdout.flush()
                    except concurrent.futures.TimeoutError:
                        log_with_timestamp(f"ERROR: Task {task_name} timed out")
                        sys.stdout.flush()
                    except Exception as e:
                        log_with_timestamp(f"Failed: {task_name} - {str(e)}")
                        sys.stdout.flush()
            except concurrent.futures.TimeoutError:
                log_with_timestamp("ERROR: Overall ingestion timed out after 30 minutes")
                sys.stdout.flush()
            
            # Don't wait for shutdown in Colab - just let it finish naturally
            pass
        
        # Signal all parallel ingestion completed
        log_with_timestamp(f"All parallel ingestion completed successfully ({completed_tasks}/{total_tasks} indices)")
        sys.stdout.flush()
        time.sleep(0.2)  # Ensure TaskExecutor processes completion
    else:
        print("Skipping all ingestion as no indices are enabled.")

    final_completion_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Create summary of what was done
    generated_items = []
    original_generation_flags = {'news': True, 'reports': True}  # Original intent
    current_generation_flags = {'news': DO_GENERATE_NEWS, 'reports': DO_GENERATE_REPORTS}
    
    for item, was_intended in original_generation_flags.items():
        if was_intended and current_generation_flags[item]:
            generated_items.append(item)
    
    ingested_items = []
    original_ingestion_flags = {'news': True, 'reports': True}  # Original intent
    current_ingestion_flags = {'news': DO_INGEST_NEWS, 'reports': DO_INGEST_REPORTS}
    
    for item, was_intended in original_ingestion_flags.items():
        if was_intended and current_ingestion_flags[item]:
            ingested_items.append(item)
    
    # Print detailed summary
    print(f"\n[{final_completion_timestamp}] ✅ Script execution completed!")
    if generated_items:
        print(f"  📊 Generated: {', '.join(generated_items)}")
    elif any(original_generation_flags.values()):
        print("  📊 Generation: Skipped (GEMINI_API_KEY not configured)")
        print("      💡 Configure API keys via: python3 control.py → Configure Settings")
        
    if ingested_items:
        print(f"  🔍 Ingested to Elasticsearch: {', '.join(ingested_items)}")
    elif any(original_ingestion_flags.values()):
        # Some ingestion was intended but skipped
        skipped_reason = "API keys not configured" if not ES_CONFIG.get('api_key') else "Connection failed"
        print(f"  🔍 Elasticsearch ingestion: Skipped ({skipped_reason})")
        print(f"      💡 Configure API keys via: python3 control.py → Configure Settings")
    
    if generated_items or ingested_items:
        print(f"  🎉 Files available in: generated_data/")
    sys.stdout.flush()
    time.sleep(0.2)  # Final pause to ensure all messages are processed