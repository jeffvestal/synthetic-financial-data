#!/usr/bin/env python3
"""
Quick reload - Delete and reload indices for clean state.
Perfect for demos or testing changes.
Usage: python3 quick_reload.py [--holdings] [--news] etc.
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

def quick_reload(indices_to_reload):
    """Delete and reload specific indices."""
    
    print(f"\n{'='*60}")
    print(f"🔄 QUICK RELOAD - Clean State")
    print(f"{'='*60}")
    print(f"Reloading: {', '.join(indices_to_reload)}")
    print(f"{'='*60}\n")
    
    # Create ES client
    try:
        es_client = create_elasticsearch_client()
        print("✓ Connected to Elasticsearch\n")
    except Exception as e:
        print(f"✗ Failed to connect: {e}")
        return False
    
    # Delete existing indices
    print("🗑️  Deleting existing indices...")
    for index_key in indices_to_reload:
        if index_key not in INDEX_CONFIG:
            continue
        _, index_name, _ = INDEX_CONFIG[index_key]
        try:
            if es_client.indices.exists(index=index_name):
                es_client.indices.delete(index=index_name)
                print(f"  ✓ Deleted {index_name}")
            else:
                print(f"  - {index_name} doesn't exist")
        except Exception as e:
            print(f"  ✗ Failed to delete {index_name}: {e}")
    
    print("\n📥 Loading fresh data...")
    
    # Prepare load queue
    load_queue = []
    total_docs = 0
    
    for index_key in indices_to_reload:
        if index_key not in INDEX_CONFIG:
            continue
            
        filepath, index_name, id_field = INDEX_CONFIG[index_key]
        
        if not os.path.exists(filepath):
            print(f"  ⚠️  No data file for {index_key}")
            continue
        
        with open(filepath, 'r') as f:
            line_count = sum(1 for _ in f)
        
        load_queue.append((filepath, index_name, id_field, index_key.title(), line_count))
        total_docs += line_count
        print(f"  📁 {index_key.title()}: {line_count:,} documents")
    
    if not load_queue:
        print("\n✗ No data to load!")
        return False
    
    print("=" * 60)
    
    # Load each index
    overall_start = time.time()
    success_count = 0
    
    for filepath, index_name, id_field, display_name, doc_count in load_queue:
        print(f"⏳ Loading {display_name}...", end='', flush=True)
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
            print(f" ✓ {elapsed:.1f}s")
            success_count += 1
            
        except Exception as e:
            print(f" ✗ Failed: {e}")
    
    # Summary
    overall_elapsed = time.time() - overall_start
    print(f"\n{'='*60}")
    print(f"✅ RELOAD COMPLETE")
    print(f"📊 {success_count}/{len(load_queue)} indices")
    print(f"⏱️  {overall_elapsed:.1f} seconds total")
    print(f"{'='*60}\n")
    
    return success_count == len(load_queue)

def main():
    parser = argparse.ArgumentParser(description='Quick reload indices (delete + reload)')
    parser.add_argument('--accounts', action='store_true', help='Reload accounts')
    parser.add_argument('--holdings', action='store_true', help='Reload holdings')
    parser.add_argument('--assets', action='store_true', help='Reload assets')
    parser.add_argument('--news', action='store_true', help='Reload news')
    parser.add_argument('--reports', action='store_true', help='Reload reports')
    parser.add_argument('--all', action='store_true', help='Reload all indices')
    
    args = parser.parse_args()
    
    # Determine which indices to reload
    if args.all:
        indices_to_reload = list(INDEX_CONFIG.keys())
    else:
        indices_to_reload = []
        if args.accounts: indices_to_reload.append('accounts')
        if args.holdings: indices_to_reload.append('holdings')
        if args.assets: indices_to_reload.append('assets')
        if args.news: indices_to_reload.append('news')
        if args.reports: indices_to_reload.append('reports')
    
    if not indices_to_reload:
        # Default to news and reports (quick demo data)
        indices_to_reload = ['news', 'reports']
        print("No indices specified, defaulting to news and reports")
    
    # Force unbuffered output
    sys.stdout.reconfigure(line_buffering=True)
    sys.stderr.reconfigure(line_buffering=True)
    
    success = quick_reload(indices_to_reload)
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())