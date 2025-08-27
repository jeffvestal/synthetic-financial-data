#!/usr/bin/env python3
"""
Direct loading script with detailed logging to diagnose slowness.
Bypasses control.py and TaskExecutor to show actual progress.
"""

import os
import sys
import time
from datetime import datetime

# Set environment variables for the settings
os.environ['UPDATE_TIMESTAMPS_ON_LOAD'] = 'true'
os.environ['ES_BULK_BATCH_SIZE'] = '1000'
os.environ['PARALLEL_BULK_WORKERS'] = '24'
os.environ['MAX_PARALLEL_INDICES'] = '5'

# Add scripts to path
scripts_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scripts')
sys.path.insert(0, scripts_dir)

from common_utils import create_elasticsearch_client, ingest_data_to_es

def load_data():
    """Load all data with detailed progress logging."""
    
    print(f"\n{'='*60}")
    print(f"DIRECT DATA LOADING WITH PROGRESS LOGGING")
    print(f"{'='*60}")
    print(f"Settings:")
    print(f"  - Bulk size: 1000")
    print(f"  - Parallel workers: 24")
    print(f"  - Update timestamps: YES")
    print(f"  - Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    # Create ES client
    try:
        es_client = create_elasticsearch_client()
        print("✓ Connected to Elasticsearch\n")
    except Exception as e:
        print(f"✗ Failed to connect to Elasticsearch: {e}")
        return
    
    # Define what to load
    indices_to_load = [
        ('generated_data/generated_accounts.jsonl', 'financial_accounts', 'account_id', 'Accounts'),
        ('generated_data/generated_holdings.jsonl', 'financial_holdings', 'holding_id', 'Holdings'),
        ('generated_data/generated_asset_details.jsonl', 'financial_asset_details', 'symbol', 'Asset Details'),
        ('generated_data/generated_news.jsonl', 'financial_news', 'article_id', 'News'),
        ('generated_data/generated_reports.jsonl', 'financial_reports', 'report_id', 'Reports'),
    ]
    
    # Check which files exist
    available_indices = []
    for filepath, index_name, id_field, display_name in indices_to_load:
        if os.path.exists(filepath):
            size = os.path.getsize(filepath)
            if size > 0:
                # Count lines
                with open(filepath, 'r') as f:
                    line_count = sum(1 for _ in f)
                available_indices.append((filepath, index_name, id_field, display_name, line_count))
                print(f"  Found {display_name}: {line_count:,} documents")
    
    if not available_indices:
        print("\n✗ No data files found to load!")
        return
    
    print(f"\nStarting ingestion of {len(available_indices)} indices...\n")
    print("=" * 60)
    
    # Process each index
    overall_start = time.time()
    
    for filepath, index_name, id_field, display_name, doc_count in available_indices:
        print(f"\n>>> Loading {display_name} ({doc_count:,} documents)")
        print(f"    Index: {index_name}")
        print(f"    Start time: {datetime.now().strftime('%H:%M:%S')}")
        print("-" * 40)
        
        index_start = time.time()
        
        try:
            # This will call our modified ingest_data_to_es with progress logging
            ingest_data_to_es(
                es_client,
                filepath,
                index_name,
                id_field,
                batch_size=1000,
                parallel_bulk_workers=24,
                update_timestamps=True
            )
            
            index_elapsed = time.time() - index_start
            docs_per_sec = doc_count / index_elapsed if index_elapsed > 0 else 0
            
            print(f"\n    ✓ {display_name} complete!")
            print(f"    Time: {index_elapsed:.1f} seconds")
            print(f"    Speed: {docs_per_sec:.0f} docs/second")
            
        except Exception as e:
            print(f"\n    ✗ {display_name} failed: {e}")
        
        print("-" * 40)
    
    overall_elapsed = time.time() - overall_start
    print(f"\n{'='*60}")
    print(f"ALL LOADING COMPLETE")
    print(f"Total time: {overall_elapsed:.1f} seconds ({overall_elapsed/60:.1f} minutes)")
    print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    # Force unbuffered output
    import sys
    sys.stdout.reconfigure(line_buffering=True)
    sys.stderr.reconfigure(line_buffering=True)
    
    load_data()