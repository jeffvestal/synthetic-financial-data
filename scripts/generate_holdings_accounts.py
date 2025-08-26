import random
from datetime import datetime, timedelta
import uuid
import json
import sys
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

# Third-party libraries
from faker import Faker

# Local imports
from config import (
    ES_CONFIG, FILE_PATHS, GENERATION_SETTINGS, ACCOUNT_SETTINGS,
    PRICE_SETTINGS, HOLDINGS_SETTINGS, validate_config
)
from symbols_config import (
    STOCK_SYMBOLS_AND_INFO, ETF_SYMBOLS_AND_INFO, BOND_TYPES,
    ALL_ASSET_INFO, get_asset_info
)
from common_utils import (
    create_elasticsearch_client, ingest_data_to_es, clear_file_if_exists,
    generate_random_datetime, get_random_price, get_current_timestamp,
    log_with_timestamp, create_progress_bar
)
from symbol_manager import SymbolManager

fake = Faker()

# --- Configuration (loaded from config module) ---
NUM_ACCOUNTS = GENERATION_SETTINGS['accounts']['num_accounts']
MIN_HOLDINGS_PER_ACCOUNT = GENERATION_SETTINGS['accounts']['min_holdings_per_account']
MAX_HOLDINGS_PER_ACCOUNT = GENERATION_SETTINGS['accounts']['max_holdings_per_account']

# --- File Paths (from config) ---
GENERATED_ACCOUNTS_FILE = FILE_PATHS['generated_accounts']
GENERATED_HOLDINGS_FILE = FILE_PATHS['generated_holdings']
GENERATED_ASSET_DETAILS_FILE = FILE_PATHS['generated_asset_details']

# --- Elasticsearch Index Names ---
ACCOUNTS_INDEX = ES_CONFIG['indices']['accounts']
HOLDINGS_INDEX = ES_CONFIG['indices']['holdings']
ASSET_DETAILS_INDEX = ES_CONFIG['indices']['asset_details']

print(f"Using Elasticsearch endpoint: {ES_CONFIG['endpoint_url']}")
print(f"Using API key: {'*' * 20 if ES_CONFIG['api_key'] else 'NOT SET'}")

# --- Symbol Data (loaded from symbols_config module) ---
# All symbol data is now centralized in symbols_config.py




# --- Account Generation Constants (from config) ---
ACCOUNT_TYPES = ACCOUNT_SETTINGS['types']
RISK_PROFILES = ACCOUNT_SETTINGS['risk_profiles']
CONTACT_PREFS = ACCOUNT_SETTINGS['contact_preferences']
US_STATES = ACCOUNT_SETTINGS['us_states']

# --- Initialize Symbol Manager ---
symbol_manager = SymbolManager()


# Helper functions are now imported from common_utils module


# --- Main Data Generation Function ---
def generate_financial_data(output_accounts_filepath: str, output_holdings_filepath: str, output_asset_details_filepath: str,
                            num_accounts: int = NUM_ACCOUNTS, min_holdings_per_account: int = MIN_HOLDINGS_PER_ACCOUNT,
                            max_holdings_per_account: int = MAX_HOLDINGS_PER_ACCOUNT):

    total_accounts_generated = 0
    total_holdings_generated = 0
    unique_assets_generated = 0

    asset_details_map = {}  # Use a map to store unique assets by symbol

    # Use config for purchase date ranges
    start_purchase_date_range = datetime.now() - timedelta(days=365 * HOLDINGS_SETTINGS['purchase_date_range_years'])
    end_purchase_date_range = datetime.now() - timedelta(days=HOLDINGS_SETTINGS['purchase_date_buffer_days'])

    # Use symbol manager for consistent symbol access
    all_stock_symbols = symbol_manager.get_stock_symbols()
    all_etf_symbols = symbol_manager.get_etf_symbols()
    all_bond_symbols = symbol_manager.get_bond_symbols()

    current_datetime = datetime.now()  # Use one consistent current datetime for updates

    print(f"\nGenerating financial accounts, holdings, and asset details to files...")

    # Open files in append mode, or ensure they are cleared before calling (handled by main execution block)
    with open(output_accounts_filepath, 'a') as accounts_f, \
         open(output_holdings_filepath, 'a') as holdings_f, \
         open(output_asset_details_filepath, 'a') as assets_f:

        for i in create_progress_bar(range(num_accounts), "Generating Accounts & Holdings"):
            account_id = f"ACC{i:05d}-{uuid.uuid4().hex[:4]}"  # More unique ID

            # Generate account-level data
            first_name = fake.first_name()
            last_name = fake.last_name()

            account_info = {
                'account_id': account_id,
                'first_name': first_name,
                'last_name': last_name,
                'account_holder_name': f"{first_name} {last_name}",  # For convenience
                'state': random.choice(US_STATES),
                'zip_code': fake.postcode(),
                'account_type': random.choice(ACCOUNT_TYPES),
                'risk_profile': random.choice(RISK_PROFILES),
                'contact_preference': random.choice(CONTACT_PREFS),
                'total_portfolio_value': 0.0,  # Will be updated after holdings are added
                'last_updated': get_current_timestamp()
            }

            current_account_holdings_value = 0.0
            num_holdings = random.randint(min_holdings_per_account, max_holdings_per_account)

            for j in range(num_holdings):
                holding_id = f"{account_id}-H{j:02d}-{uuid.uuid4().hex[:4]}"
                instrument_type = random.choice(['Stock', 'ETF', 'Bond'])  # Randomly choose instrument type

                symbol = None
                asset_name = ""
                sector = ""
                index_membership = []
                country_of_origin = ""
                bond_details = None

                # Determine asset-specific details using symbol manager
                if instrument_type == 'Stock':
                    symbol = random.choice(all_stock_symbols)
                elif instrument_type == 'ETF':
                    symbol = random.choice(all_etf_symbols)
                else:  # Bond
                    symbol = random.choice(all_bond_symbols)
                
                # Get asset info using centralized function
                asset_info = get_asset_info(symbol)
                if not asset_info:
                    continue  # Skip if no asset info found
                
                asset_name = asset_info['name']
                sector = asset_info['sector']
                index_membership = asset_info.get('indices', [])
                country_of_origin = asset_info.get('country', 'USA')
                
                # Handle bond-specific details
                bond_details = None
                if instrument_type == 'Bond':
                    bond_details = {
                        "issuer": asset_info.get('issuer', 'Unknown'),
                        "maturity_date": (datetime.now() + timedelta(days=random.randint(365 * 2, 365 * 20))).strftime('%Y-%m-%d'),
                        "coupon_rate": round(random.uniform(0.005, 0.08), 4)
                    }

                # Generate prices for asset_details (these will be unique per asset symbol)
                if symbol not in asset_details_map:
                    current_price_value = get_random_price(instrument_type)
                    min_fluc, max_fluc = PRICE_SETTINGS['price_fluctuation_range']
                    previous_closing_price_value = round(current_price_value * random.uniform(min_fluc, max_fluc), 2)

                    # Simulate previous close date as yesterday or recent past
                    prev_close_date = (current_datetime - timedelta(days=random.randint(1, 5))).isoformat(
                        timespec='seconds')

                    asset_detail = {
                        'symbol': symbol,
                        'asset_name': asset_name,
                        'instrument_type': instrument_type,
                        'sector': sector,
                        'index_membership': index_membership,
                        'country_of_origin': country_of_origin,
                        'current_price': {
                            'price': current_price_value,
                            'last_updated': get_current_timestamp()
                        },
                        'previous_closing_price': {
                            'price': previous_closing_price_value,
                            'prev_close_date': prev_close_date
                        },
                        'bond_details': bond_details,  # Will be None for stocks/ETFs
                        'last_updated': get_current_timestamp()
                    }
                    asset_details_map[symbol] = asset_detail  # Add to map
                    assets_f.write(json.dumps(asset_detail) + '\n')  # Write unique asset detail to file
                    unique_assets_generated += 1

                # Generate holding-specific details using config
                if instrument_type == 'Stock':
                    min_qty, max_qty = HOLDINGS_SETTINGS['stock_quantity_range']
                    quantity = random.randint(min_qty, max_qty)
                elif instrument_type == 'ETF':
                    min_qty, max_qty = HOLDINGS_SETTINGS['etf_quantity_range']
                    quantity = random.randint(min_qty, max_qty)
                else:  # Bond
                    quantity = random.choice(HOLDINGS_SETTINGS['bond_face_values'])

                purchase_price = get_random_price(instrument_type)  # Purchase price is unique to holding
                purchase_date = generate_random_datetime(start_purchase_date_range,
                                                         end_purchase_date_range)  # Datetime now

                # Use the current price from asset_details_map for calculating total value
                asset_current_price_value = asset_details_map[symbol]['current_price']['price']
                is_high_value = (quantity * asset_current_price_value) > HOLDINGS_SETTINGS['high_value_threshold']

                holding_data = {
                    'holding_id': holding_id,
                    'account_id': account_id,
                    'symbol': symbol,  # Link to asset_details
                    'quantity': quantity,
                    'purchase_price': purchase_price,
                    'purchase_date': purchase_date,
                    'is_high_value': is_high_value,
                    'last_updated': get_current_timestamp()
                }
                holdings_f.write(json.dumps(holding_data) + '\n')  # Write holding to file
                total_holdings_generated += 1
                current_account_holdings_value += (
                            quantity * asset_current_price_value)  # Calculate total value based on current asset price

            account_info['total_portfolio_value'] = round(current_account_holdings_value, 2)
            accounts_f.write(json.dumps(account_info) + '\n')  # Write account to file
            total_accounts_generated += 1

    return total_accounts_generated, total_holdings_generated, unique_assets_generated


# ES ingestion functions are now imported from common_utils module


# --- Main Execution ---
if __name__ == "__main__":
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting data generation process...")

    # --- Control Flags for Accounts, Holdings, Assets ---
    DO_GENERATE_ACCOUNTS_AND_HOLDINGS = False  # Controls generation of all three related files
    DO_INGEST_ACCOUNTS = True
    DO_INGEST_HOLDINGS = True
    DO_INGEST_ASSET_DETAILS = True

    # 1. Validate environment variables for credentials
    # ES credentials validation for ingestion
    if (not ES_CONFIG['endpoint_url'] or not ES_CONFIG['api_key']) and \
            (DO_INGEST_ACCOUNTS or DO_INGEST_HOLDINGS or DO_INGEST_ASSET_DETAILS):
        print("ERROR: ES_ENDPOINT_URL or ES_API_KEY environment variables are not set. Cannot ingest data. Exiting.")
        sys.exit(1)

    # 2. Generate Accounts, Holdings, and Asset Details (if enabled)
    if DO_GENERATE_ACCOUNTS_AND_HOLDINGS:
        print(f"--- Generating Accounts, Holdings, and Asset Details ({datetime.now().strftime('%H:%M:%S')}) ---")
        # Clear existing files before new generation
        for fpath in [GENERATED_ACCOUNTS_FILE, GENERATED_HOLDINGS_FILE, GENERATED_ASSET_DETAILS_FILE]:
            clear_file_if_exists(fpath)

        total_accounts, total_holdings, total_assets = generate_financial_data(
            output_accounts_filepath=GENERATED_ACCOUNTS_FILE,
            output_holdings_filepath=GENERATED_HOLDINGS_FILE,
            output_asset_details_filepath=GENERATED_ASSET_DETAILS_FILE
        )
        print(f"Total generated accounts saved to file: {total_accounts}")
        print(f"Total generated holdings saved to file: {total_holdings}")
        print(f"Total generated unique assets saved to file: {total_assets}")
    else:
        print("Skipping accounts, holdings, and asset details generation as DO_GENERATE_ACCOUNTS_AND_HOLDINGS is False.")

    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Data generation phase complete.")

    # 4. Initialize Elasticsearch client (only if any ingestion is enabled for THIS script's data)
    es_client = None
    if DO_INGEST_ACCOUNTS or DO_INGEST_HOLDINGS or DO_INGEST_ASSET_DETAILS:
        print("\nInitializing Elasticsearch client for ingestion...")
        try:
            es_client = create_elasticsearch_client()
            
            # Ensure all required indices exist with proper mappings
            print("Checking and creating indices if needed...")
            # The ingest_data_to_es function will automatically ensure indices exist
            # but we can do it explicitly here for clarity
            
        except Exception as e:
            print(f"ERROR: Could not connect to Elasticsearch. Please check your Endpoint URL and API Key. Error: {e}")
            raise


    # 5. Ingest Data into Elasticsearch in parallel (if enabled)
    ingestion_tasks = []
    if DO_INGEST_ACCOUNTS:
        ingestion_tasks.append((GENERATED_ACCOUNTS_FILE, ACCOUNTS_INDEX, "account_id", "Accounts"))
    if DO_INGEST_HOLDINGS:
        ingestion_tasks.append((GENERATED_HOLDINGS_FILE, HOLDINGS_INDEX, "holding_id", "Holdings"))
    if DO_INGEST_ASSET_DETAILS:
        ingestion_tasks.append((GENERATED_ASSET_DETAILS_FILE, ASSET_DETAILS_INDEX, "symbol", "Asset Details"))
    
    if ingestion_tasks:
        log_with_timestamp("--- Starting Parallel Elasticsearch Ingestion ---")
        
        def ingest_index(task_info):
            filepath, index_name, id_field, display_name = task_info
            try:
                log_with_timestamp(f"--- Ingesting {display_name} ---")
                ingest_data_to_es(es_client, filepath, index_name, id_field)
                return f"{display_name}: Success"
            except Exception as e:
                error_msg = f"{display_name}: Error - {str(e)}"
                print(f"ERROR: {error_msg}")
                return error_msg
        
        # Use ThreadPoolExecutor for parallel ingestion
        max_parallel = min(len(ingestion_tasks), 3)  # Limit to 3 concurrent ingestions
        with ThreadPoolExecutor(max_workers=max_parallel) as executor:
            future_to_task = {executor.submit(ingest_index, task): task[3] for task in ingestion_tasks}
            
            for future in as_completed(future_to_task):
                task_name = future_to_task[future]
                try:
                    result = future.result()
                    log_with_timestamp(f"Completed: {result}")
                except Exception as e:
                    log_with_timestamp(f"Failed: {task_name} - {str(e)}")
    else:
        print("Skipping all ingestion as no indices are enabled.")

    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] All data generation and ingestion processes completed.")