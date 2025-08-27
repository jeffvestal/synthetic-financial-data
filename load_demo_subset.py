#!/usr/bin/env python3
"""
Load a smaller subset of data for quick demos.
- Only 5000 holdings (instead of 122k)
- All accounts, news, reports, assets
Perfect for demos that need to load in <5 seconds.
"""

import os
import sys
import time
from datetime import datetime
import json

# Demo settings - smaller batches for quick loading
DEMO_HOLDINGS_LIMIT = 5000
BULK_SIZE = 1000
PARALLEL_WORKERS = 8  # Less workers for demo

# Set environment variables
os.environ['UPDATE_TIMESTAMPS_ON_LOAD'] = 'true'
os.environ['ES_BULK_BATCH_SIZE'] = str(BULK_SIZE)
os.environ['PARALLEL_BULK_WORKERS'] = str(PARALLEL_WORKERS)

# Add scripts to path
scripts_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scripts')
sys.path.insert(0, scripts_dir)

from common_utils import create_elasticsearch_client, ingest_data_to_es

def load_demo_subset():
    """Load demo subset with limited holdings."""
    
    print(f"\n{'='*60}")
    print(f"🎭 DEMO DATA LOADER - Quick Subset")
    print(f"{'='*60}")
    print(f"Loading subset: {DEMO_HOLDINGS_LIMIT:,} holdings + all other data")
    print(f"Expected time: <5 seconds")
    print(f"{'='*60}\n")
    
    # Create ES client
    try:
        es_client = create_elasticsearch_client()
        print("✓ Connected to Elasticsearch\n")
    except Exception as e:
        print(f"✗ Failed to connect: {e}")
        return False
    
    overall_start = time.time()
    success_count = 0
    total_loaded = 0
    
    # 1. Load limited holdings first (largest dataset)
    holdings_file = 'generated_data/generated_holdings.jsonl'
    if os.path.exists(holdings_file):
        print(f"⏳ Loading Holdings subset ({DEMO_HOLDINGS_LIMIT:,} docs)...", end='', flush=True)
        
        # Create temporary subset file
        temp_file = 'generated_data/temp_holdings_subset.jsonl'
        try:
            with open(holdings_file, 'r') as infile, open(temp_file, 'w') as outfile:
                for i, line in enumerate(infile):
                    if i >= DEMO_HOLDINGS_LIMIT:
                        break
                    outfile.write(line)
            
            # Load the subset
            start_time = time.time()
            ingest_data_to_es(
                es_client,
                temp_file,
                'financial_holdings',
                'holding_id',
                batch_size=BULK_SIZE,
                parallel_bulk_workers=PARALLEL_WORKERS,
                update_timestamps=True
            )
            elapsed = time.time() - start_time
            print(f" ✓ {elapsed:.1f}s")
            success_count += 1
            total_loaded += DEMO_HOLDINGS_LIMIT
            
            # Clean up temp file
            os.remove(temp_file)
            
        except Exception as e:
            print(f" ✗ Failed: {e}")
            if os.path.exists(temp_file):
                os.remove(temp_file)
    
    # 2. Load all other indices (they're small)
    other_indices = [
        ('generated_data/generated_accounts.jsonl', 'financial_accounts', 'account_id', 'Accounts'),
        ('generated_data/generated_asset_details.jsonl', 'financial_asset_details', 'symbol', 'Assets'),
        ('generated_data/generated_news.jsonl', 'financial_news', 'article_id', 'News'),
        ('generated_data/generated_reports.jsonl', 'financial_reports', 'report_id', 'Reports'),
    ]
    
    for filepath, index_name, id_field, display_name in other_indices:
        if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
            continue
        
        # Count docs
        with open(filepath, 'r') as f:
            doc_count = sum(1 for _ in f)
        
        print(f"⏳ Loading {display_name} ({doc_count:,} docs)...", end='', flush=True)
        start_time = time.time()
        
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
            elapsed = time.time() - start_time
            print(f" ✓ {elapsed:.1f}s")
            success_count += 1
            total_loaded += doc_count
            
        except Exception as e:
            print(f" ✗ Failed: {e}")
    
    # Summary
    overall_elapsed = time.time() - overall_start
    print(f"\n{'='*60}")
    print(f"✅ DEMO DATA LOADED")
    print(f"📊 {success_count}/5 indices loaded")
    print(f"📁 {total_loaded:,} total documents")
    print(f"⏱️  {overall_elapsed:.1f} seconds")
    print(f"{'='*60}")
    print(f"\n🎯 Perfect for quick demos!")
    
    return success_count > 0

if __name__ == "__main__":
    # Force unbuffered output
    sys.stdout.reconfigure(line_buffering=True)
    sys.stderr.reconfigure(line_buffering=True)
    
    success = load_demo_subset()
    sys.exit(0 if success else 1)