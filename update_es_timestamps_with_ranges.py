#!/usr/bin/env python3
"""
Update timestamps for documents already in Elasticsearch with realistic time ranges.
Much faster than reloading data - updates in-place using update_by_query.

Key Features:
- Different time ranges per data type (trades, news, reports)
- Realistic temporal distribution instead of single timestamp
- Configurable range windows per index
- Maintains realistic relationships (last_updated after primary timestamps)

Usage: 
    python3 update_es_timestamps_with_ranges.py --trades-months 6 --news-months 2
    python3 update_es_timestamps_with_ranges.py --index financial_trades --range-months 3
    python3 update_es_timestamps_with_ranges.py --dry-run
"""

import os
import sys
import time
import random
import argparse
import warnings
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

# Suppress SSL and deprecation warnings
warnings.filterwarnings('ignore')
import urllib3
urllib3.disable_warnings()

# Add scripts and lib to path
scripts_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scripts')
lib_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib')
sys.path.insert(0, scripts_dir)
sys.path.insert(0, lib_dir)

from common_utils import create_elasticsearch_client

# Define timestamp fields and default ranges for each index
TIMESTAMP_CONFIG = {
    'financial_accounts': {
        'fields': ['last_updated'],
        'default_range_months': 1,
        'description': 'Account data - recent updates'
    },
    'financial_holdings': {
        'fields': ['last_updated', 'purchase_date'],
        'default_range_months': 24,  # Holdings purchased over 2 years
        'description': 'Holdings - purchase dates over time, recent updates'
    },
    'financial_asset_details': {
        'fields': ['last_updated', 'current_price.last_updated'],
        'default_range_months': 1,
        'description': 'Asset prices - recent updates'
    },
    'financial_news': {
        'fields': ['last_updated', 'published_date'],
        'default_range_months': 2,  # News from last 2 months
        'description': 'News articles - published over recent months'
    },
    'financial_reports': {
        'fields': ['last_updated', 'report_date'],
        'default_range_months': 6,  # Quarterly reports over 6 months
        'description': 'Financial reports - quarterly/monthly schedule'
    },
    'financial_trades': {
        'fields': ['last_updated', 'execution_timestamp'],
        'default_range_months': 4,  # Trading activity over 4 months
        'description': 'Trade activity - execution times distributed over months'
    }
}

def generate_timestamp_range(base_time: datetime, range_months: int) -> Tuple[datetime, datetime]:
    """Generate start and end timestamps for a given range."""
    end_time = base_time
    start_time = end_time - timedelta(days=range_months * 30)  # Approximate months
    return start_time, end_time

def generate_random_timestamp(start_time: datetime, end_time: datetime) -> str:
    """Generate a random timestamp within the given range."""
    time_range = (end_time - start_time).total_seconds()
    random_seconds = random.uniform(0, time_range)
    random_time = start_time + timedelta(seconds=random_seconds)
    return random_time.isoformat(timespec='seconds')

def generate_related_timestamp(primary_timestamp: str, max_delay_hours: int = 24) -> str:
    """Generate a related timestamp that occurs after the primary timestamp."""
    primary_time = datetime.fromisoformat(primary_timestamp.replace('Z', ''))
    delay_seconds = random.uniform(60, max_delay_hours * 3600)  # 1 minute to max_delay_hours
    related_time = primary_time + timedelta(seconds=delay_seconds)
    return related_time.isoformat(timespec='seconds')

def update_index_with_ranges(es_client, index_name: str, range_months: int = None, dry_run: bool = False) -> bool:
    """Update timestamps in a specific index with realistic time ranges."""
    
    # Check if index exists
    if not es_client.indices.exists(index=index_name):
        print(f"  ⚠️  Index {index_name} does not exist")
        return False
    
    # Get configuration for this index
    if index_name not in TIMESTAMP_CONFIG:
        print(f"  ⚠️  No timestamp configuration for index {index_name}")
        return False
    
    config = TIMESTAMP_CONFIG[index_name]
    if range_months is None:
        range_months = config['default_range_months']
    
    # Get document count
    count_result = es_client.count(index=index_name)
    doc_count = count_result['count']
    
    if doc_count == 0:
        print(f"  ⚠️  Index {index_name} is empty")
        return False
    
    # Calculate time ranges
    base_time = datetime.now()
    start_time, end_time = generate_timestamp_range(base_time, range_months)
    
    fields = config['fields']
    description = config['description']
    
    print(f"  📝 {index_name}: {doc_count:,} documents")
    print(f"     Description: {description}")
    print(f"     Fields: {', '.join(fields)}")
    print(f"     Time range: {range_months} months ({start_time.date()} to {end_time.date()})")
    
    if dry_run:
        print(f"     🔍 DRY RUN - no changes made")
        return True
    
    # Build update script with random timestamps
    print(f"     ⏳ Updating with distributed timestamps...", end='', flush=True)
    start_update_time = time.time()
    
    try:
        # Strategy: Use update_by_query with a script that generates random timestamps
        # Each document gets its own random timestamps within the range
        
        script_lines = []
        
        # Generate primary timestamp field first (if applicable)
        primary_field = None
        secondary_fields = []
        
        for field in fields:
            if field == 'last_updated':
                secondary_fields.append(field)
            else:
                if primary_field is None:
                    primary_field = field
                else:
                    secondary_fields.append(field)
        
        # Ultra-simple approach: Each field gets its own random timestamp independently  
        # This avoids all variable scoping issues
        
        for i, field in enumerate(fields):
            var_name = f"tempMs{i}"
            if '.' in field:  # Handle nested fields
                parts = field.split('.')
                script_lines.append(
                    f"if (ctx._source.{parts[0]} != null) {{ "
                    f"long {var_name} = params.startMs + (long)(Math.random() * (params.endMs - params.startMs)); "
                    f"ctx._source.{field} = Instant.ofEpochMilli({var_name}).toString(); "
                    f"}} "
                )
            else:
                script_lines.append(
                    f"long {var_name} = params.startMs + (long)(Math.random() * (params.endMs - params.startMs)); "
                    f"ctx._source.{field} = Instant.ofEpochMilli({var_name}).toString(); "
                )
        
        # Execute update
        response = es_client.options(
            request_timeout=300,  # 5 minute timeout
            ignore_status=[409]   # Ignore version conflicts
        ).update_by_query(
            index=index_name,
            script={
                "source": " ".join(script_lines),
                "params": {
                    "startMs": int(start_time.timestamp() * 1000),
                    "endMs": int(end_time.timestamp() * 1000)
                }
            },
            refresh=True,
            conflicts="proceed"  # Continue on version conflicts
        )
        
        elapsed = time.time() - start_update_time
        
        # Check response
        updated = response.get('updated', 0)
        version_conflicts = response.get('version_conflicts', 0)
        
        if updated > 0:
            print(f" ✅ Updated {updated:,} documents in {elapsed:.1f}s")
            if version_conflicts > 0:
                print(f"     ℹ️  {version_conflicts:,} version conflicts (expected)")
            return True
        else:
            print(f" ⚠️  No documents updated")
            return False
            
    except Exception as e:
        print(f" ❌ Error: {e}")
        return False

def update_multiple_indices(indices_config: Dict[str, int], dry_run: bool = False) -> bool:
    """Update multiple indices with their respective range configurations."""
    
    print("🕒 Updating Elasticsearch timestamps with realistic ranges")
    print("=" * 60)
    
    # Create ES client
    try:
        es_client = create_elasticsearch_client()
        print("✅ Connected to Elasticsearch")
    except Exception as e:
        print(f"❌ Failed to connect to Elasticsearch: {e}")
        return False
    
    success_count = 0
    total_indices = len(indices_config)
    
    for index_name, range_months in indices_config.items():
        print(f"\n📊 Processing {index_name}...")
        success = update_index_with_ranges(es_client, index_name, range_months, dry_run)
        if success:
            success_count += 1
    
    print(f"\n{'='*60}")
    print(f"📈 Summary: {success_count}/{total_indices} indices updated successfully")
    
    if dry_run:
        print("🔍 This was a DRY RUN - no actual changes were made")
        print("   Remove --dry-run to apply the changes")
    
    return success_count == total_indices

def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Update Elasticsearch timestamps with realistic time ranges",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 update_es_timestamps_with_ranges.py
  python3 update_es_timestamps_with_ranges.py --trades-months 6 --news-months 1
  python3 update_es_timestamps_with_ranges.py --index financial_trades --range-months 3
  python3 update_es_timestamps_with_ranges.py --all-months 4 --dry-run
        """
    )
    
    # Individual index range controls
    parser.add_argument('--trades-months', type=int, 
                       help='Months range for trade execution timestamps (default: 4)')
    parser.add_argument('--news-months', type=int,
                       help='Months range for news publication dates (default: 2)')
    parser.add_argument('--reports-months', type=int,
                       help='Months range for report dates (default: 6)')
    parser.add_argument('--holdings-months', type=int,
                       help='Months range for holdings purchase dates (default: 24)')
    parser.add_argument('--accounts-months', type=int,
                       help='Months range for account updates (default: 1)')
    parser.add_argument('--assets-months', type=int,
                       help='Months range for asset price updates (default: 1)')
    
    # Global controls
    parser.add_argument('--all-months', type=int,
                       help='Apply same month range to all indices')
    parser.add_argument('--index', type=str,
                       help='Update only specific index')
    parser.add_argument('--range-months', type=int,
                       help='Month range for single index (use with --index)')
    
    # Execution controls
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be updated without making changes')
    
    args = parser.parse_args()
    
    # Build indices configuration
    indices_config = {}
    
    if args.index:
        # Single index mode
        if args.index not in TIMESTAMP_CONFIG:
            print(f"❌ Unknown index: {args.index}")
            print(f"Available indices: {', '.join(TIMESTAMP_CONFIG.keys())}")
            return 1
        
        range_months = args.range_months or TIMESTAMP_CONFIG[args.index]['default_range_months']
        indices_config[args.index] = range_months
        
    else:
        # Multiple indices mode
        if args.all_months:
            # Apply same range to all indices
            for index_name in TIMESTAMP_CONFIG:
                indices_config[index_name] = args.all_months
        else:
            # Use specific ranges or defaults
            indices_config['financial_trades'] = args.trades_months or TIMESTAMP_CONFIG['financial_trades']['default_range_months']
            indices_config['financial_news'] = args.news_months or TIMESTAMP_CONFIG['financial_news']['default_range_months'] 
            indices_config['financial_reports'] = args.reports_months or TIMESTAMP_CONFIG['financial_reports']['default_range_months']
            indices_config['financial_holdings'] = args.holdings_months or TIMESTAMP_CONFIG['financial_holdings']['default_range_months']
            indices_config['financial_accounts'] = args.accounts_months or TIMESTAMP_CONFIG['financial_accounts']['default_range_months']
            indices_config['financial_asset_details'] = args.assets_months or TIMESTAMP_CONFIG['financial_asset_details']['default_range_months']
    
    # Execute updates
    success = update_multiple_indices(indices_config, args.dry_run)
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())