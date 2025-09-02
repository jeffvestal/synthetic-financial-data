#!/usr/bin/env python3
"""
Fix the financial_trades index mapping.
This script will:
1. Check current mapping
2. If incorrect, reindex with correct mapping
"""

import warnings
# Suppress warnings before any other imports
warnings.filterwarnings('ignore', message='urllib3 v2 only supports OpenSSL')
warnings.filterwarnings('ignore', message='Connecting to.*using TLS with verify_certs=False')

import os
import sys
import json

# Add scripts to path
scripts_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scripts')
sys.path.insert(0, scripts_dir)

from common_utils import create_elasticsearch_client, log_with_timestamp
from lib.index_manager import IndexManager

def main():
    """Fix financial_trades index mapping."""
    
    log_with_timestamp("=== Checking financial_trades Index Mapping ===")
    
    # Create ES client
    try:
        es_client = create_elasticsearch_client()
        log_with_timestamp("✓ Connected to Elasticsearch")
    except Exception as e:
        log_with_timestamp(f"✗ Failed to connect: {e}")
        return 1
    
    index_name = 'financial_trades'
    manager = IndexManager(es_client)
    
    # Check if index exists
    if not es_client.indices.exists(index=index_name):
        log_with_timestamp(f"Index '{index_name}' does not exist. Creating with correct mapping...")
        if manager.create_index(index_name):
            log_with_timestamp("✓ Index created with correct mapping")
        else:
            log_with_timestamp("✗ Failed to create index")
        return 0
    
    # Get current mapping
    current_mapping = es_client.indices.get_mapping(index=index_name)
    current_props = current_mapping[index_name]['mappings'].get('properties', {})
    
    # Check if mapping is correct
    incorrect_fields = []
    for field in ['trade_id', 'account_id', 'symbol', 'trade_type', 'order_type', 'order_status']:
        field_type = current_props.get(field, {}).get('type')
        if field_type != 'keyword':
            incorrect_fields.append(f"{field}: {field_type} (should be keyword)")
    
    if not incorrect_fields:
        log_with_timestamp("✓ Mapping is already correct!")
        return 0
    
    log_with_timestamp("✗ Incorrect mapping detected:")
    for field in incorrect_fields:
        log_with_timestamp(f"  - {field}")
    
    # Ask user what to do
    log_with_timestamp("")
    log_with_timestamp("Options:")
    log_with_timestamp("1. Delete and recreate index (will lose data)")
    log_with_timestamp("2. Exit without changes")
    
    try:
        choice = input("\nEnter choice (1 or 2): ").strip()
    except:
        choice = "2"
    
    if choice == "1":
        log_with_timestamp("")
        log_with_timestamp("Deleting index...")
        es_client.indices.delete(index=index_name)
        log_with_timestamp("✓ Index deleted")
        
        log_with_timestamp("Creating index with correct mapping...")
        if manager.create_index(index_name):
            log_with_timestamp("✓ Index created with correct mapping")
            log_with_timestamp("")
            log_with_timestamp("Now you can reload the data:")
            log_with_timestamp("  python3 load_all_data.py")
            log_with_timestamp("  or")
            log_with_timestamp("  python3 load_specific_indices.py --trades")
        else:
            log_with_timestamp("✗ Failed to create index")
            return 1
    else:
        log_with_timestamp("No changes made")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())