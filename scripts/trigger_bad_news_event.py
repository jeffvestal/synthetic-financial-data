import random
from datetime import datetime, timedelta
import uuid
import json
import time
import os
import sys

# Third-party libraries
from tqdm import tqdm

# Local imports  
from config import (
    ES_CONFIG, FILE_PATHS, GENERATION_SETTINGS, CONTENT_SETTINGS,
    FIELD_NAMES, GEMINI_CONFIG, BAD_EVENT_CONFIG, EVENT_CONFIGS, validate_config
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

# --- Configuration for Controlled Generation (for THIS script ONLY) ---
# This script generates a small, specific set for triggering a demo event.
# All configuration now centralized in config.py
PROMPT_FILES = FILE_PATHS['prompts']

# Use controlled generation settings
NUM_SPECIFIC_NEWS_TO_GENERATE = GENERATION_SETTINGS['controlled']['num_specific_news']
NUM_GENERAL_NEWS_TO_GENERATE = GENERATION_SETTINGS['controlled']['num_general_news']
NUM_SPECIFIC_REPORTS_TO_GENERATE = GENERATION_SETTINGS['controlled']['num_specific_reports']
NUM_THEMATIC_REPORTS_TO_GENERATE = GENERATION_SETTINGS['controlled']['num_thematic_reports']

# File paths from config
GENERATED_NEWS_FILE = FILE_PATHS['generated_controlled_news']
GENERATED_REPORTS_FILE = FILE_PATHS['generated_controlled_reports']

# Index names from config
NEWS_INDEX = ES_CONFIG['indices']['news']
REPORTS_INDEX = ES_CONFIG['indices']['reports']

# Field names from config
PRIMARY_SYMBOL_FIELD_NAME = FIELD_NAMES['primary_symbol']

# Bad event configuration from config
BAD_EVENT_TARGET_NEWS_SYMBOL = BAD_EVENT_CONFIG['target_news_symbol']
BAD_EVENT_NEWS_THEME = BAD_EVENT_CONFIG['news_theme']
BAD_EVENT_TARGET_REPORT_SYMBOL = BAD_EVENT_CONFIG['target_report_symbol']
BAD_EVENT_REPORT_FOCUS = BAD_EVENT_CONFIG['report_focus']
BAD_EVENT_SENTIMENT = BAD_EVENT_CONFIG['sentiment']

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


def generate_controlled_news_articles(num_specific: int, num_general: int, output_filepath: str):
    """Generates controlled synthetic news articles using Gemini API for demo purposes."""
    news_articles_generated = 0
    specific_news_template = load_prompt_template(PROMPT_FILES["specific_news"])
    general_news_template = load_prompt_template(PROMPT_FILES["general_news"])

    if not specific_news_template or not general_news_template:
        print("Could not load news prompt templates. Exiting controlled news generation.")
        return 0

    print(f"\\nGenerating controlled news articles to '{output_filepath}'...")
    with open(output_filepath, 'a') as f:  # Open in append mode
        
        # 1. Generate the BAD NEWS article first (targeted negative event)
        print(f"Generating bad news article for {BAD_EVENT_TARGET_NEWS_SYMBOL}...")
        current_datetime_str = get_current_timestamp()
        bad_asset_info = get_asset_info(BAD_EVENT_TARGET_NEWS_SYMBOL)
        
        if bad_asset_info:
            prompt = specific_news_template.format(
                COMPANY_NAME=bad_asset_info['name'],
                SYMBOL=BAD_EVENT_TARGET_NEWS_SYMBOL,
                SECTOR=bad_asset_info['sector'],
                SENTIMENT=BAD_EVENT_SENTIMENT,
                EVENT_THEME=BAD_EVENT_NEWS_THEME,
                CURRENT_DATETIME_STRING=current_datetime_str
            )
            generated_data = call_gemini_api(prompt, gemini_model)
            time.sleep(GEMINI_CONFIG['request_delay_seconds'])

            if generated_data:
                article = {
                    'article_id': str(uuid.uuid4()),
                    'title': generated_data.get('title', 'Breaking: Major Corporate Development'),
                    'content': generated_data.get('content', 'No content generated.'),
                    'source': generated_data.get('source', "Breaking Financial News"),
                    'published_date': current_datetime_str,
                    'url': f"http://fakenews.com/article/{uuid.uuid4().hex[:8]}",
                    'entities': generated_data.get('entities', [BAD_EVENT_TARGET_NEWS_SYMBOL, bad_asset_info['sector']]),
                    'sentiment': BAD_EVENT_SENTIMENT,  # Force negative sentiment for demo
                    'last_updated': get_current_timestamp(),
                    'primary_symbol': BAD_EVENT_TARGET_NEWS_SYMBOL,
                    'company_symbol': generated_data.get('company_symbol', None)
                }
                f.write(json.dumps(article) + '\\n')
                news_articles_generated += 1
                print(f"✓ Generated targeted bad news for {BAD_EVENT_TARGET_NEWS_SYMBOL}")

        # 2. Generate other specific news (positive/neutral)
        print("Generating other specific news articles...")
        available_symbols = symbol_manager.get_stocks_and_etfs()
        # Exclude the bad news symbol
        other_symbols = [s for s in available_symbols if s != BAD_EVENT_TARGET_NEWS_SYMBOL]
        specific_assets_to_cover = random.sample(other_symbols, min(num_specific - 1, len(other_symbols)))

        for symbol in create_progress_bar(specific_assets_to_cover, "Other Specific News"):
            current_datetime_str = get_current_timestamp()
            asset_info = get_asset_info(symbol)
            
            if not asset_info:
                continue

            # Only positive or neutral sentiment for other news
            sentiment = random.choice(['positive', 'neutral', 'mixed'])
            prompt = specific_news_template.format(
                COMPANY_NAME=asset_info['name'],
                SYMBOL=symbol,
                SECTOR=asset_info['sector'],
                SENTIMENT=sentiment,
                EVENT_THEME=random.choice(NEWS_EVENT_THEMES),
                CURRENT_DATETIME_STRING=current_datetime_str
            )
            generated_data = call_gemini_api(prompt, gemini_model)
            time.sleep(GEMINI_CONFIG['request_delay_seconds'])

            if generated_data:
                article = {
                    'article_id': str(uuid.uuid4()),
                    'title': generated_data.get('title', 'Corporate Update'),
                    'content': generated_data.get('content', 'No content generated.'),
                    'source': generated_data.get('source', random.choice(
                        ["Financial Today", "Global Market News", "Investment Daily"])),
                    'published_date': current_datetime_str,
                    'url': f"http://fakenews.com/article/{uuid.uuid4().hex[:8]}",
                    'entities': generated_data.get('entities', [symbol, asset_info['sector']]),
                    'sentiment': generated_data.get('sentiment', sentiment),
                    'last_updated': get_current_timestamp(),
                    'primary_symbol': generated_data.get('primary_symbol', symbol),
                    'company_symbol': generated_data.get('company_symbol', None)
                }
                f.write(json.dumps(article) + '\\n')
                news_articles_generated += 1

        # 3. Generate general market news (positive/neutral)
        print("Generating general market news articles...")
        for i in create_progress_bar(range(num_general), "General News"):
            current_datetime_str = get_current_timestamp()
            sentiment = random.choice(['positive', 'neutral', 'mixed'])
            prompt = general_news_template.format(
                SENTIMENT=sentiment,
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
                    'sentiment': generated_data.get('sentiment', sentiment),
                    'last_updated': get_current_timestamp(),
                    'primary_symbol': generated_data.get('primary_symbol', None),
                    'company_symbol': generated_data.get('company_symbol', None)
                }
                f.write(json.dumps(article) + '\\n')
                news_articles_generated += 1

    return news_articles_generated


def generate_controlled_reports(num_specific: int, num_thematic: int, output_filepath: str):
    """Generates controlled synthetic reports using Gemini API for demo purposes."""
    reports_generated = 0
    specific_report_template = load_prompt_template(PROMPT_FILES["specific_report"])
    thematic_report_template = load_prompt_template(PROMPT_FILES["thematic_report"])

    if not specific_report_template or not thematic_report_template:
        print("Could not load report prompt templates. Exiting controlled report generation.")
        return 0

    print(f"\\nGenerating controlled reports to '{output_filepath}'...")
    with open(output_filepath, 'a') as f:  # Open in append mode
        
        # 1. Generate the BAD REPORT first (targeted negative event)
        print(f"Generating bad report for {BAD_EVENT_TARGET_REPORT_SYMBOL}...")
        current_datetime_str = get_current_timestamp()
        bad_asset_info = get_asset_info(BAD_EVENT_TARGET_REPORT_SYMBOL)
        
        if bad_asset_info:
            prompt = specific_report_template.format(
                COMPANY_NAME=bad_asset_info['name'],
                SYMBOL=BAD_EVENT_TARGET_REPORT_SYMBOL,
                SECTOR=bad_asset_info['sector'],
                REPORT_TYPE=random.choice(REPORT_TYPES),
                FOCUS_THEME=BAD_EVENT_REPORT_FOCUS,
                SENTIMENT=BAD_EVENT_SENTIMENT,
                CURRENT_DATETIME_STRING=current_datetime_str
            )
            generated_data = call_gemini_api(prompt, gemini_model)
            time.sleep(GEMINI_CONFIG['request_delay_seconds'])

            if generated_data:
                report = {
                    'report_id': str(uuid.uuid4()),
                    'title': generated_data.get('title', 'Critical Analysis Report'),
                    'content': generated_data.get('content', 'No content generated.'),
                    'source': generated_data.get('source', "Critical Research Analytics"),
                    'published_date': current_datetime_str,
                    'url': f"http://fakereports.com/report/{uuid.uuid4().hex[:8]}",
                    'entities': generated_data.get('entities', [BAD_EVENT_TARGET_REPORT_SYMBOL, bad_asset_info['sector']]),
                    'sentiment': BAD_EVENT_SENTIMENT,  # Force negative sentiment for demo
                    'last_updated': get_current_timestamp(),
                    'primary_symbol': BAD_EVENT_TARGET_REPORT_SYMBOL,
                    'company_symbol': generated_data.get('company_symbol', None)
                }
                f.write(json.dumps(report) + '\\n')
                reports_generated += 1
                print(f"✓ Generated targeted bad report for {BAD_EVENT_TARGET_REPORT_SYMBOL}")

        # 2. Generate other specific reports (positive/neutral)
        print("Generating other specific reports...")
        available_symbols = symbol_manager.get_stocks_and_etfs()
        # Exclude the bad report symbol
        other_symbols = [s for s in available_symbols if s != BAD_EVENT_TARGET_REPORT_SYMBOL]
        specific_assets_to_cover = random.sample(other_symbols, min(num_specific - 1, len(other_symbols)))

        for symbol in create_progress_bar(specific_assets_to_cover, "Other Specific Reports"):
            current_datetime_str = get_current_timestamp()
            asset_info = get_asset_info(symbol)
            
            if not asset_info:
                continue

            # Only positive or neutral sentiment for other reports
            sentiment = random.choice(['positive', 'neutral', 'mixed'])
            prompt = specific_report_template.format(
                COMPANY_NAME=asset_info['name'],
                SYMBOL=symbol,
                SECTOR=asset_info['sector'],
                REPORT_TYPE=random.choice(REPORT_TYPES),
                FOCUS_THEME=random.choice(REPORT_FOCUS_THEMES),
                SENTIMENT=sentiment,
                CURRENT_DATETIME_STRING=current_datetime_str
            )
            generated_data = call_gemini_api(prompt, gemini_model)
            time.sleep(GEMINI_CONFIG['request_delay_seconds'])

            if generated_data:
                report = {
                    'report_id': str(uuid.uuid4()),
                    'title': generated_data.get('title', 'Company Analysis'),
                    'content': generated_data.get('content', 'No content generated.'),
                    'source': generated_data.get('source', random.choice(
                        ["Analyst Insights", "Financial Research Corp", "Market Analysis Group"])),
                    'published_date': current_datetime_str,
                    'url': f"http://fakereports.com/report/{uuid.uuid4().hex[:8]}",
                    'entities': generated_data.get('entities', [symbol, asset_info['sector']]),
                    'sentiment': generated_data.get('sentiment', sentiment),
                    'last_updated': get_current_timestamp(),
                    'primary_symbol': generated_data.get('primary_symbol', symbol),
                    'company_symbol': generated_data.get('company_symbol', None)
                }
                f.write(json.dumps(report) + '\\n')
                reports_generated += 1

        # 3. Generate thematic reports (positive/neutral)
        print("Generating thematic industry reports...")
        for i in create_progress_bar(range(num_thematic), "Thematic Reports"):
            current_datetime_str = get_current_timestamp()
            sentiment = random.choice(['positive', 'neutral', 'mixed'])
            prompt = thematic_report_template.format(
                THEME_INDUSTRY=random.choice(THEME_INDUSTRIES),
                SENTIMENT=sentiment,
                FOCUS_THEME=random.choice(REPORT_FOCUS_THEMES),
                CURRENT_DATETIME_STRING=current_datetime_str
            )
            generated_data = call_gemini_api(prompt, gemini_model)
            time.sleep(GEMINI_CONFIG['request_delay_seconds'])

            if generated_data:
                report = {
                    'report_id': str(uuid.uuid4()),
                    'title': generated_data.get('title', 'Industry Analysis'),
                    'content': generated_data.get('content', 'No content generated.'),
                    'source': generated_data.get('source', random.choice(
                        ["Analyst Insights", "Financial Research Corp", "Market Analysis Group"])),
                    'published_date': current_datetime_str,
                    'url': f"http://fakereports.com/report/{uuid.uuid4().hex[:8]}",
                    'entities': generated_data.get('entities', ["Industry", "Market"]),
                    'sentiment': generated_data.get('sentiment', sentiment),
                    'last_updated': get_current_timestamp(),
                    'primary_symbol': generated_data.get('primary_symbol', None),
                    'company_symbol': generated_data.get('company_symbol', None)
                }
                f.write(json.dumps(report) + '\\n')
                reports_generated += 1

    return reports_generated


def run_event_generation(event_type='bad_news'):
    """
    Run event generation with specified event type.
    
    Args:
        event_type (str): Type of event to generate ('bad_news', 'market_crash', 'volatility')
    """
    global BAD_EVENT_TARGET_NEWS_SYMBOL, BAD_EVENT_NEWS_THEME, BAD_EVENT_TARGET_REPORT_SYMBOL
    global BAD_EVENT_REPORT_FOCUS, BAD_EVENT_SENTIMENT
    
    # Get event configuration
    if event_type not in EVENT_CONFIGS:
        print(f"❌ Unknown event type: {event_type}")
        print(f"Available event types: {list(EVENT_CONFIGS.keys())}")
        return
    
    event_config = EVENT_CONFIGS[event_type]
    print(f"\\n🎯 Triggering {event_type.replace('_', ' ').title()} Event")
    print(f"📋 Description: {event_config['description']}")
    
    log_with_timestamp(f"Starting controlled {event_type.replace('_', ' ')} event generation process...")
    
    # Update global variables with event-specific configuration
    BAD_EVENT_TARGET_NEWS_SYMBOL = event_config['target_news_symbol']
    BAD_EVENT_NEWS_THEME = event_config['news_theme']
    BAD_EVENT_TARGET_REPORT_SYMBOL = event_config['target_report_symbol']
    BAD_EVENT_REPORT_FOCUS = event_config['report_focus']
    BAD_EVENT_SENTIMENT = event_config['sentiment']
    
    # Generate flags based on event type
    if event_type == 'market_crash':
        # Market crash generates more content across multiple assets
        NUM_SPECIFIC_NEWS = GENERATION_SETTINGS['controlled']['num_specific_news'] * 2
        NUM_GENERAL_NEWS = GENERATION_SETTINGS['controlled']['num_general_news'] * 2
        NUM_SPECIFIC_REPORTS = GENERATION_SETTINGS['controlled']['num_specific_reports'] * 2
        NUM_THEMATIC_REPORTS = GENERATION_SETTINGS['controlled']['num_thematic_reports'] * 2
    elif event_type == 'volatility':
        # Volatility events generate mixed content
        NUM_SPECIFIC_NEWS = GENERATION_SETTINGS['controlled']['num_specific_news']
        NUM_GENERAL_NEWS = GENERATION_SETTINGS['controlled']['num_general_news'] * 3  # More general articles about volatility
        NUM_SPECIFIC_REPORTS = GENERATION_SETTINGS['controlled']['num_specific_reports']
        NUM_THEMATIC_REPORTS = GENERATION_SETTINGS['controlled']['num_thematic_reports']
    else:
        # Default bad_news amounts
        NUM_SPECIFIC_NEWS = GENERATION_SETTINGS['controlled']['num_specific_news']
        NUM_GENERAL_NEWS = GENERATION_SETTINGS['controlled']['num_general_news']
        NUM_SPECIFIC_REPORTS = GENERATION_SETTINGS['controlled']['num_specific_reports']
        NUM_THEMATIC_REPORTS = GENERATION_SETTINGS['controlled']['num_thematic_reports']
    
    # Configuration flags for controlled generation
    DO_GENERATE_NEWS = True
    DO_GENERATE_REPORTS = True
    DO_INGEST_NEWS = True
    DO_INGEST_REPORTS = True

    # 1. Validate configuration
    is_valid, errors = validate_config()
    if not is_valid:
        print("ERROR: Configuration validation failed:")
        for error in errors:
            print(f"  - {error}")
        return

    # 2. Initialize Gemini model
    if DO_GENERATE_NEWS or DO_GENERATE_REPORTS:
        try:
            global gemini_model
            gemini_model = configure_gemini()
            print("Gemini model initialized successfully.")
        except Exception as e:
            print(f"ERROR: Could not initialize Gemini model: {e}")
            return

    # 3. Generate Controlled News Articles (if enabled)
    if DO_GENERATE_NEWS:
        log_with_timestamp("--- Generating Controlled News Articles ---")
        clear_file_if_exists(GENERATED_NEWS_FILE)
        
        total_news = generate_controlled_news_articles(
            num_specific=NUM_SPECIFIC_NEWS,
            num_general=NUM_GENERAL_NEWS,
            output_filepath=GENERATED_NEWS_FILE
        )
        print(f"Total controlled news articles saved to file: {total_news}")
        print(f"✓ {event_type.replace('_', ' ').title()} news targeted at: {BAD_EVENT_TARGET_NEWS_SYMBOL} ({BAD_EVENT_NEWS_THEME})")
    else:
        print("Skipping controlled news generation.")

    # 4. Generate Controlled Reports (if enabled)
    if DO_GENERATE_REPORTS:
        log_with_timestamp("--- Generating Controlled Reports ---")
        clear_file_if_exists(GENERATED_REPORTS_FILE)
        
        total_reports = generate_controlled_reports(
            num_specific=NUM_SPECIFIC_REPORTS,
            num_thematic=NUM_THEMATIC_REPORTS,
            output_filepath=GENERATED_REPORTS_FILE
        )
        print(f"Total controlled reports saved to file: {total_reports}")
        print(f"✓ {event_type.replace('_', ' ').title()} report targeted at: {BAD_EVENT_TARGET_REPORT_SYMBOL} ({BAD_EVENT_REPORT_FOCUS})")
    else:
        print("Skipping controlled report generation.")

    log_with_timestamp("Controlled data generation phase complete.")

    # 5. Initialize Elasticsearch client (only if any ingestion is enabled)
    es_client = None
    if DO_INGEST_NEWS or DO_INGEST_REPORTS:
        print("\\nInitializing Elasticsearch client for ingestion...")
        try:
            es_client = create_elasticsearch_client()
        except Exception as e:
            print(f"ERROR: Could not connect to Elasticsearch: {e}")
            return

    # 6. Ingest Data into Elasticsearch (if enabled)
    if DO_INGEST_NEWS:
        log_with_timestamp("--- Ingesting Controlled News Articles ---")
        ingest_data_to_es(es_client, GENERATED_NEWS_FILE, NEWS_INDEX, "article_id")
    else:
        print("Skipping controlled news ingestion.")

    if DO_INGEST_REPORTS:
        log_with_timestamp("--- Ingesting Controlled Reports ---")
        ingest_data_to_es(es_client, GENERATED_REPORTS_FILE, REPORTS_INDEX, "report_id")
    else:
        print("Skipping controlled reports ingestion.")

    log_with_timestamp(f"All controlled {event_type.replace('_', ' ')} event generation and ingestion processes completed.")
    print(f"\\n🎯 {event_type.replace('_', ' ').title()} Event Summary:")
    print(f"   📰 News: {BAD_EVENT_TARGET_NEWS_SYMBOL} - {BAD_EVENT_NEWS_THEME}")
    print(f"   📊 Report: {BAD_EVENT_TARGET_REPORT_SYMBOL} - {BAD_EVENT_REPORT_FOCUS}")
    print(f"   💾 Files: {GENERATED_NEWS_FILE}, {GENERATED_REPORTS_FILE}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Trigger controlled market events for demo purposes")
    parser.add_argument('--event-type', 
                       choices=['bad_news', 'market_crash', 'volatility'],
                       default='bad_news',
                       help='Type of event to trigger (default: bad_news)')
    
    args = parser.parse_args()
    
    # Run event generation with specified type
    run_event_generation(args.event_type)