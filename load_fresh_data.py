#!/usr/bin/env python3
"""
Load only freshly generated data files.
Checks modification time and only loads files created/modified in the last hour.
Useful after generating new data.
"""

import os
import sys
import time
from datetime import datetime, timedelta

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

from common_utils import create_elasticsearch_client, ingest_data_to_es, wait_for_inference_endpoint_if_needed

def load_fresh_data(hours_threshold=1):
    """Load only recently modified data files."""
    
    print(f"\n{'='*60}")
    print(f"🆕 FRESH DATA LOADER")
    print(f"{'='*60}")
    print(f"Loading files modified in last {hours_threshold} hour(s)")
    print(f"Settings: {BULK_SIZE} batch, {PARALLEL_WORKERS} workers")
    print(f"{'='*60}\n")
    
    # Create ES client
    try:
        es_client = create_elasticsearch_client()
        print("✓ Connected to Elasticsearch\n")
    except Exception as e:
        print(f"✗ Failed to connect: {e}")
        return False
    
    # Check all data files
    data_files = [
        ('generated_data/generated_accounts.jsonl', 'financial_accounts', 'account_id', 'Accounts'),
        ('generated_data/generated_holdings.jsonl', 'financial_holdings', 'holding_id', 'Holdings'),
        ('generated_data/generated_asset_details.jsonl', 'financial_asset_details', 'symbol', 'Assets'),
        ('generated_data/generated_news.jsonl', 'financial_news', 'article_id', 'News'),
        ('generated_data/generated_reports.jsonl', 'financial_reports', 'report_id', 'Reports'),
    ]
    
    # Find fresh files
    cutoff_time = time.time() - (hours_threshold * 3600)
    fresh_files = []
    total_docs = 0
    
    print("🔍 Checking file timestamps...")
    for filepath, index_name, id_field, display_name in data_files:
        if not os.path.exists(filepath):
            continue
        
        # Check modification time
        mod_time = os.path.getmtime(filepath)
        if mod_time < cutoff_time:
            age_hours = (time.time() - mod_time) / 3600
            print(f"  ⏭️  Skipping {display_name} (modified {age_hours:.1f} hours ago)")
            continue
        
        # Count documents
        with open(filepath, 'r') as f:
            line_count = sum(1 for _ in f)
        
        if line_count == 0:
            continue
        
        fresh_files.append((filepath, index_name, id_field, display_name, line_count))
        total_docs += line_count
        
        age_minutes = (time.time() - mod_time) / 60
        print(f"  ✅ {display_name}: {line_count:,} docs (modified {age_minutes:.0f} min ago)")
    
    if not fresh_files:
        print(f"\n📭 No fresh data files found (modified in last {hours_threshold} hour)")
        print("Generate new data or use load_all_data.py to load existing files")
        return False
    
    print(f"\n📊 Loading {len(fresh_files)} fresh indices ({total_docs:,} documents)")
    print("=" * 60)
    
    # Check inference endpoint if semantic indices are present
    index_names = [idx[1] for idx in fresh_files]
    endpoint_ready = wait_for_inference_endpoint_if_needed(index_names)
    
    # Filter out semantic indices if endpoint not ready
    if not endpoint_ready:
        semantic_indices = ['financial_news', 'financial_reports']
        fresh_files = [idx for idx in fresh_files if idx[1] not in semantic_indices]
        print(f"📊 Adjusted: {len(fresh_files)} indices ({sum(idx[4] for idx in fresh_files):,} documents)")
    
    # Load fresh files
    overall_start = time.time()
    success_count = 0
    
    for filepath, index_name, id_field, display_name, doc_count in fresh_files:
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
    print(f"✅ FRESH DATA LOADED")
    print(f"📊 {success_count}/{len(fresh_files)} indices")
    print(f"⏱️  {overall_elapsed:.1f} seconds total")
    if overall_elapsed > 0:
        print(f"📈 {total_docs/overall_elapsed:.0f} docs/second average")
    print(f"{'='*60}\n")
    
    return success_count == len(fresh_files)

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Load recently generated data')
    parser.add_argument('--hours', type=int, default=1,
                       help='Load files modified within last N hours (default: 1)')
    
    args = parser.parse_args()
    
    # Force unbuffered output
    sys.stdout.reconfigure(line_buffering=True)
    sys.stderr.reconfigure(line_buffering=True)
    
    success = load_fresh_data(args.hours)
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())