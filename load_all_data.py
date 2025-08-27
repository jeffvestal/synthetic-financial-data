#!/usr/bin/env python3
"""
Fast loading script for ALL data with optimal settings.
Loads all 5 indices with timestamps updated to current time.
~20 seconds total vs several minutes with control.py
"""

import os
import sys
import time
from datetime import datetime

# Optimal settings discovered through testing
BULK_SIZE = 1000
PARALLEL_WORKERS = 24

# Set environment variables
os.environ['UPDATE_TIMESTAMPS_ON_LOAD'] = 'true'
os.environ['ES_BULK_BATCH_SIZE'] = str(BULK_SIZE)
os.environ['PARALLEL_BULK_WORKERS'] = str(PARALLEL_WORKERS)

# Add scripts to path
scripts_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scripts')
sys.path.insert(0, scripts_dir)

from common_utils import create_elasticsearch_client, ingest_data_to_es

def load_all_data():
    """Load all data with detailed progress logging."""
    
    print(f"\n{'='*60}")
    print(f"🚀 FAST DATA LOADER - ALL INDICES")
    print(f"{'='*60}")
    print(f"Settings: {BULK_SIZE} batch, {PARALLEL_WORKERS} workers, timestamps→now")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    # Create ES client
    try:
        es_client = create_elasticsearch_client()
        print("✓ Connected to Elasticsearch\n")
    except Exception as e:
        print(f"✗ Failed to connect to Elasticsearch: {e}")
        print("\nMake sure ES_ENDPOINT_URL and ES_API_KEY are set")
        return False
    
    # Define all indices to load
    indices_to_load = [
        ('generated_data/generated_accounts.jsonl', 'financial_accounts', 'account_id', 'Accounts'),
        ('generated_data/generated_holdings.jsonl', 'financial_holdings', 'holding_id', 'Holdings'),
        ('generated_data/generated_asset_details.jsonl', 'financial_asset_details', 'symbol', 'Assets'),
        ('generated_data/generated_news.jsonl', 'financial_news', 'article_id', 'News'),
        ('generated_data/generated_reports.jsonl', 'financial_reports', 'report_id', 'Reports'),
    ]
    
    # Check which files exist
    available_indices = []
    total_docs = 0
    for filepath, index_name, id_field, display_name in indices_to_load:
        if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
            with open(filepath, 'r') as f:
                line_count = sum(1 for _ in f)
            available_indices.append((filepath, index_name, id_field, display_name, line_count))
            total_docs += line_count
            print(f"  📁 {display_name}: {line_count:,} documents")
    
    if not available_indices:
        print("\n✗ No data files found! Generate data first.")
        return False
    
    print(f"\n📊 Total: {total_docs:,} documents across {len(available_indices)} indices")
    print("=" * 60)
    
    # Process each index
    overall_start = time.time()
    success_count = 0
    
    for filepath, index_name, id_field, display_name, doc_count in available_indices:
        print(f"\n⏳ Loading {display_name}...", end='', flush=True)
        index_start = time.time()
        
        try:
            ingest_data_to_es(
                es_client,
                filepath,
                index_name,
                id_field,
                batch_size=BULK_SIZE,
                parallel_bulk_workers=PARALLEL_WORKERS,
                update_timestamps=True
            )
            
            elapsed = time.time() - index_start
            print(f" ✓ {elapsed:.1f}s ({doc_count/elapsed:.0f} docs/sec)")
            success_count += 1
            
        except Exception as e:
            print(f" ✗ Failed: {e}")
    
    # Summary
    overall_elapsed = time.time() - overall_start
    print(f"\n{'='*60}")
    print(f"✅ COMPLETE: {success_count}/{len(available_indices)} indices loaded")
    print(f"⏱️  Total time: {overall_elapsed:.1f} seconds")
    print(f"📈 Average: {total_docs/overall_elapsed:.0f} docs/second")
    print(f"🕐 Finished: {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*60}\n")
    
    return success_count == len(available_indices)

if __name__ == "__main__":
    # Force unbuffered output
    sys.stdout.reconfigure(line_buffering=True)
    sys.stderr.reconfigure(line_buffering=True)
    
    success = load_all_data()
    sys.exit(0 if success else 1)