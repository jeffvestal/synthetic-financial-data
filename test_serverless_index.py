#!/usr/bin/env python3
"""
Test script to verify serverless Elasticsearch index creation with proper mappings.
This tests the fix for serverless compatibility in IndexManager.
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

def test_serverless_index_creation():
    """Test creating financial_trades index in serverless mode."""
    
    log_with_timestamp("=== Testing Serverless Index Creation ===")
    
    # Create ES client
    try:
        es_client = create_elasticsearch_client()
        log_with_timestamp("✓ Connected to Elasticsearch")
    except Exception as e:
        log_with_timestamp(f"✗ Failed to connect: {e}")
        return 1
    
    # Test connection to verify serverless mode
    manager = IndexManager(es_client)
    conn_test = manager.test_connection()
    if conn_test['success']:
        log_with_timestamp(f"✓ Elasticsearch version: {conn_test.get('version', 'Unknown')}")
        log_with_timestamp(f"✓ Distribution: {conn_test.get('elasticsearch_version', 'Unknown')}")
    else:
        log_with_timestamp(f"✗ Connection test failed: {conn_test.get('error')}")
        return 1
    
    # Test creating financial_trades index
    index_name = 'financial_trades'
    log_with_timestamp(f"\nTesting creation of '{index_name}' index...")
    
    # Check if it exists first
    if manager.index_exists(index_name):
        log_with_timestamp(f"Index '{index_name}' already exists")
        
        # Get current mapping
        try:
            current_mapping = es_client.indices.get_mapping(index=index_name)
            current_props = current_mapping[index_name]['mappings'].get('properties', {})
            
            # Check field types
            log_with_timestamp("\nCurrent field mappings:")
            test_fields = ['trade_id', 'account_id', 'symbol', 'trade_type', 'order_type', 'order_status']
            all_correct = True
            
            for field in test_fields:
                field_type = current_props.get(field, {}).get('type', 'not found')
                is_correct = field_type == 'keyword'
                status = "✓" if is_correct else "✗"
                log_with_timestamp(f"  {status} {field}: {field_type}")
                if not is_correct:
                    all_correct = False
            
            if all_correct:
                log_with_timestamp("\n✓ All mappings are correct!")
            else:
                log_with_timestamp("\n✗ Some mappings are incorrect")
                log_with_timestamp("\nWould you like to recreate the index? (y/n)")
                try:
                    if input().lower() == 'y':
                        log_with_timestamp("Recreating index...")
                        if manager.recreate_index(index_name):
                            log_with_timestamp("✓ Index recreated successfully")
                        else:
                            log_with_timestamp("✗ Failed to recreate index")
                except:
                    log_with_timestamp("Skipping recreation")
        except Exception as e:
            log_with_timestamp(f"Error checking mapping: {e}")
    else:
        # Try to create it
        log_with_timestamp(f"Creating '{index_name}' index...")
        
        # Load the mapping
        mapping = manager.get_index_mapping(index_name)
        if mapping:
            log_with_timestamp(f"✓ Found mapping definition for '{index_name}'")
            
            # Show what settings will be used (after filtering)
            if 'settings' in mapping:
                log_with_timestamp("\nOriginal settings in mapping:")
                for key in mapping['settings'].keys():
                    log_with_timestamp(f"  - {key}")
            
            # Create the index (IndexManager will filter settings)
            success = manager.create_index(index_name)
            
            if success:
                log_with_timestamp(f"\n✓ Successfully created '{index_name}' index")
                
                # Verify the mapping was applied
                try:
                    created_mapping = es_client.indices.get_mapping(index=index_name)
                    created_props = created_mapping[index_name]['mappings'].get('properties', {})
                    
                    log_with_timestamp("\nVerifying field mappings:")
                    test_fields = ['trade_id', 'account_id', 'symbol', 'trade_type', 'order_type', 'order_status']
                    
                    for field in test_fields:
                        field_type = created_props.get(field, {}).get('type', 'not found')
                        is_correct = field_type == 'keyword'
                        status = "✓" if is_correct else "✗"
                        log_with_timestamp(f"  {status} {field}: {field_type}")
                    
                except Exception as e:
                    log_with_timestamp(f"Error verifying mapping: {e}")
            else:
                log_with_timestamp(f"\n✗ Failed to create '{index_name}' index")
                log_with_timestamp("Check the error messages above for details")
        else:
            log_with_timestamp(f"✗ No mapping found for '{index_name}'")
    
    # Test other indices
    log_with_timestamp("\n=== Testing Other Indices ===")
    other_indices = ['financial_accounts', 'financial_holdings', 'financial_asset_details', 'financial_news', 'financial_reports']
    
    for idx in other_indices:
        status = manager.get_index_status(idx)
        exists = "✓" if status.get('exists') else "✗"
        doc_count = status.get('doc_count', 0)
        log_with_timestamp(f"{exists} {idx}: {doc_count:,} documents")
    
    log_with_timestamp("\n=== Test Complete ===")
    return 0

if __name__ == "__main__":
    sys.exit(test_serverless_index_creation())