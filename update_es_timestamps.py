#!/usr/bin/env python3
"""
Update timestamps for documents already in Elasticsearch.
Much faster than reloading data - updates in-place using update_by_query.
Usage: python3 update_es_timestamps.py [--offset hours] [--indices index1 index2]
"""

import os
import sys
import time
import argparse
from datetime import datetime, timedelta

# Add scripts and lib to path
scripts_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scripts')
lib_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib')
sys.path.insert(0, scripts_dir)
sys.path.insert(0, lib_dir)

from common_utils import create_elasticsearch_client

# Define timestamp fields for each index
TIMESTAMP_FIELDS = {
    'financial_accounts': ['last_updated'],
    'financial_holdings': ['last_updated', 'purchase_date'],
    'financial_asset_details': ['last_updated', 'current_price.last_updated'],
    'financial_news': ['last_updated', 'published_date'],
    'financial_reports': ['last_updated', 'published_date']
}

def update_index_timestamps(es_client, index_name, offset_hours=0, dry_run=False):
    """Update timestamps in a specific index using update_by_query."""
    
    # Check if index exists
    if not es_client.indices.exists(index=index_name):
        print(f"  ⚠️  Index {index_name} does not exist")
        return False
    
    # Get document count
    count_result = es_client.count(index=index_name)
    doc_count = count_result['count']
    
    if doc_count == 0:
        print(f"  ⚠️  Index {index_name} is empty")
        return False
    
    # Calculate target timestamp
    target_time = datetime.now() + timedelta(hours=offset_hours)
    target_timestamp = target_time.isoformat(timespec='seconds')
    
    # Get fields to update
    fields = TIMESTAMP_FIELDS.get(index_name, ['last_updated'])
    
    print(f"  📝 {index_name}: {doc_count:,} documents")
    print(f"     Fields: {', '.join(fields)}")
    print(f"     New timestamp: {target_timestamp}")
    
    if dry_run:
        print(f"     🔍 DRY RUN - no changes made")
        return True
    
    # Build update script
    script_lines = []
    for field in fields:
        if '.' in field:  # Handle nested fields
            parts = field.split('.')
            # Check if parent exists before updating nested field
            script_lines.append(
                f"if (ctx._source.{parts[0]} != null) {{ "
                f"ctx._source.{field} = params.timestamp; "
                f"}}"
            )
        else:
            script_lines.append(f"ctx._source.{field} = params.timestamp;")
    
    update_body = {
        "script": {
            "source": " ".join(script_lines),
            "params": {
                "timestamp": target_timestamp
            }
        }
    }
    
    # Execute update
    print(f"     ⏳ Updating...", end='', flush=True)
    start_time = time.time()
    
    try:
        response = es_client.update_by_query(
            index=index_name,
            body=update_body,
            refresh=True,  # Make changes immediately searchable
            conflicts='proceed',  # Continue on version conflicts
            wait_for_completion=True,
            request_timeout=300  # 5 minute timeout for large indices
        )
        
        elapsed = time.time() - start_time
        updated = response.get('updated', 0)
        
        if updated > 0:
            print(f" ✓ {updated:,} docs in {elapsed:.1f}s ({updated/elapsed:.0f} docs/sec)")
        else:
            print(f" ⚠️  No documents updated")
        
        # Report any failures
        failures = response.get('failures', [])
        if failures:
            print(f"     ⚠️  {len(failures)} failures encountered")
            for failure in failures[:3]:  # Show first 3 failures
                print(f"        - {failure}")
        
        return updated > 0
        
    except Exception as e:
        elapsed = time.time() - start_time
        print(f" ✗ Failed after {elapsed:.1f}s: {e}")
        return False

def update_all_timestamps(offset_hours=0, indices_to_update=None, dry_run=False):
    """Update timestamps across all or specified indices."""
    
    print(f"\n{'='*60}")
    print(f"🕐 ELASTICSEARCH TIMESTAMP UPDATER")
    print(f"{'='*60}")
    
    if offset_hours == 0:
        print(f"Target time: NOW ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
    elif offset_hours > 0:
        print(f"Target time: {offset_hours} hours in the FUTURE")
        print(f"            ({(datetime.now() + timedelta(hours=offset_hours)).strftime('%Y-%m-%d %H:%M:%S')})")
    else:
        print(f"Target time: {abs(offset_hours)} hours in the PAST")
        print(f"            ({(datetime.now() + timedelta(hours=offset_hours)).strftime('%Y-%m-%d %H:%M:%S')})")
    
    if dry_run:
        print("🔍 DRY RUN MODE - No changes will be made")
    
    print(f"{'='*60}\n")
    
    # Connect to Elasticsearch
    try:
        es_client = create_elasticsearch_client()
        print("✓ Connected to Elasticsearch\n")
    except Exception as e:
        print(f"✗ Failed to connect to Elasticsearch: {e}")
        print("\nMake sure ES_ENDPOINT_URL and ES_API_KEY are set")
        return False
    
    # Determine which indices to update
    if indices_to_update:
        # Map short names to full index names
        index_map = {
            'accounts': 'financial_accounts',
            'holdings': 'financial_holdings',
            'assets': 'financial_asset_details',
            'news': 'financial_news',
            'reports': 'financial_reports'
        }
        
        indices = []
        for idx in indices_to_update:
            if idx in index_map:
                indices.append(index_map[idx])
            elif idx in TIMESTAMP_FIELDS:
                indices.append(idx)
            else:
                print(f"⚠️  Unknown index: {idx}")
    else:
        # Update all indices
        indices = list(TIMESTAMP_FIELDS.keys())
    
    print(f"📊 Updating {len(indices)} indices:\n")
    
    # Update each index
    overall_start = time.time()
    success_count = 0
    total_updated = 0
    
    for index_name in indices:
        display_name = index_name.replace('financial_', '').title()
        print(f"🔄 {display_name}:")
        
        success = update_index_timestamps(es_client, index_name, offset_hours, dry_run)
        if success:
            success_count += 1
            if not dry_run:
                # Get actual count of updated docs
                count_result = es_client.count(index=index_name)
                total_updated += count_result['count']
        
        print()  # Blank line between indices
    
    # Summary
    overall_elapsed = time.time() - overall_start
    
    print(f"{'='*60}")
    if dry_run:
        print(f"🔍 DRY RUN COMPLETE")
        print(f"Would update {success_count}/{len(indices)} indices")
    else:
        print(f"✅ TIMESTAMP UPDATE COMPLETE")
        print(f"📊 {success_count}/{len(indices)} indices updated")
        if total_updated > 0:
            print(f"📁 ~{total_updated:,} documents updated")
    print(f"⏱️  {overall_elapsed:.1f} seconds total")
    print(f"{'='*60}\n")
    
    return success_count == len(indices)

def main():
    parser = argparse.ArgumentParser(
        description='Update timestamps in Elasticsearch indices',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 update_es_timestamps.py                    # Update all to current time
  python3 update_es_timestamps.py --offset -24       # 24 hours ago
  python3 update_es_timestamps.py --offset 3         # 3 hours in future
  python3 update_es_timestamps.py --indices accounts holdings
  python3 update_es_timestamps.py --dry-run          # Preview without changes
        """
    )
    
    parser.add_argument(
        '--offset', 
        type=int, 
        default=0,
        help='Hours offset from now (negative for past, positive for future)'
    )
    
    parser.add_argument(
        '--indices',
        nargs='+',
        choices=['accounts', 'holdings', 'assets', 'news', 'reports'],
        help='Specific indices to update (default: all)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be updated without making changes'
    )
    
    args = parser.parse_args()
    
    # Force unbuffered output
    sys.stdout.reconfigure(line_buffering=True)
    sys.stderr.reconfigure(line_buffering=True)
    
    success = update_all_timestamps(
        offset_hours=args.offset,
        indices_to_update=args.indices,
        dry_run=args.dry_run
    )
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())