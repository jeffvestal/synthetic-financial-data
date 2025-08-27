#!/usr/bin/env python3
"""
Load only specific indices with optimal settings.
Usage: python3 load_specific_indices.py --accounts --holdings --news
"""

import os
import sys
import time
import argparse
from datetime import datetime

# Optimal settings
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

# Index configurations
INDEX_CONFIG = {
    'accounts': ('generated_data/generated_accounts.jsonl', 'financial_accounts', 'account_id'),
    'holdings': ('generated_data/generated_holdings.jsonl', 'financial_holdings', 'holding_id'),
    'assets': ('generated_data/generated_asset_details.jsonl', 'financial_asset_details', 'symbol'),
    'news': ('generated_data/generated_news.jsonl', 'financial_news', 'article_id'),
    'reports': ('generated_data/generated_reports.jsonl', 'financial_reports', 'report_id'),
}

def load_specific_indices(indices_to_load):
    """Load specific indices with progress logging."""
    
    print(f"\n{'='*60}")
    print(f"🎯 SELECTIVE DATA LOADER")
    print(f"{'='*60}")
    print(f"Loading: {', '.join(indices_to_load)}")
    print(f"Settings: {BULK_SIZE} batch, {PARALLEL_WORKERS} workers")
    print(f"{'='*60}\n")
    
    # Create ES client
    try:
        es_client = create_elasticsearch_client()
        print("✓ Connected to Elasticsearch\n")
    except Exception as e:
        print(f"✗ Failed to connect: {e}")
        return False
    
    # Prepare indices
    load_queue = []
    total_docs = 0
    
    for index_key in indices_to_load:
        if index_key not in INDEX_CONFIG:
            print(f"⚠️  Unknown index: {index_key}")
            continue
            
        filepath, index_name, id_field = INDEX_CONFIG[index_key]
        
        if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
            print(f"⚠️  No data file for {index_key}")
            continue
        
        with open(filepath, 'r') as f:
            line_count = sum(1 for _ in f)
        
        load_queue.append((filepath, index_name, id_field, index_key.title(), line_count))
        total_docs += line_count
        print(f"  📁 {index_key.title()}: {line_count:,} documents")
    
    if not load_queue:
        print("\n✗ No valid indices to load!")
        return False
    
    print(f"\n📊 Total: {total_docs:,} documents")
    print("=" * 60)
    
    # Load each index
    overall_start = time.time()
    success_count = 0
    
    for filepath, index_name, id_field, display_name, doc_count in load_queue:
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
    print(f"✅ COMPLETE: {success_count}/{len(load_queue)} indices loaded")
    print(f"⏱️  Total time: {overall_elapsed:.1f} seconds")
    if overall_elapsed > 0:
        print(f"📈 Average: {total_docs/overall_elapsed:.0f} docs/second")
    print(f"{'='*60}\n")
    
    return success_count == len(load_queue)

def main():
    parser = argparse.ArgumentParser(description='Load specific Elasticsearch indices')
    parser.add_argument('--accounts', action='store_true', help='Load accounts index')
    parser.add_argument('--holdings', action='store_true', help='Load holdings index')
    parser.add_argument('--assets', action='store_true', help='Load asset details index')
    parser.add_argument('--news', action='store_true', help='Load news index')
    parser.add_argument('--reports', action='store_true', help='Load reports index')
    parser.add_argument('--all', action='store_true', help='Load all indices')
    
    args = parser.parse_args()
    
    # Determine which indices to load
    if args.all:
        indices_to_load = list(INDEX_CONFIG.keys())
    else:
        indices_to_load = []
        if args.accounts: indices_to_load.append('accounts')
        if args.holdings: indices_to_load.append('holdings')
        if args.assets: indices_to_load.append('assets')
        if args.news: indices_to_load.append('news')
        if args.reports: indices_to_load.append('reports')
    
    if not indices_to_load:
        print("No indices specified. Use --help for options.")
        print("\nExamples:")
        print("  python3 load_specific_indices.py --holdings --news")
        print("  python3 load_specific_indices.py --all")
        return 1
    
    # Force unbuffered output
    sys.stdout.reconfigure(line_buffering=True)
    sys.stderr.reconfigure(line_buffering=True)
    
    success = load_specific_indices(indices_to_load)
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())