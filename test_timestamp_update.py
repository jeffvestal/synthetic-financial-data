#!/usr/bin/env python3
"""
Test script to verify timestamp updating is working.
Run this directly to bypass the TaskExecutor output suppression.
"""

import os
import sys
import json
from datetime import datetime

# Set the environment variable
os.environ['UPDATE_TIMESTAMPS_ON_LOAD'] = 'true'
os.environ['PARALLEL_BULK_WORKERS'] = '1'
os.environ['ES_BULK_BATCH_SIZE'] = '100'

# Add the project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import after setting environment
from scripts.common_utils import _read_and_chunk_from_file

print("Testing timestamp update functionality...")
print(f"Current time: {datetime.now().isoformat()}")
print(f"UPDATE_TIMESTAMPS_ON_LOAD env var: {os.getenv('UPDATE_TIMESTAMPS_ON_LOAD')}")

# Test with a small batch
test_file = 'generated_data/generated_news.jsonl'
if os.path.exists(test_file):
    print(f"\nReading first document from {test_file}...")
    
    # Read first line to show original
    with open(test_file, 'r') as f:
        first_line = f.readline()
        original_doc = json.loads(first_line)
        print(f"Original timestamps:")
        print(f"  published_date: {original_doc.get('published_date', 'N/A')}")
        print(f"  last_updated: {original_doc.get('last_updated', 'N/A')}")
    
    # Now test the update function
    print("\nTesting timestamp update...")
    generator = _read_and_chunk_from_file(
        test_file, 
        'financial_news',
        'article_id',
        batch_size=1,
        update_timestamps=True,
        timestamp_offset=0
    )
    
    # Get first batch
    for batch in generator:
        if batch:
            updated_doc = batch[0]['_source']
            print(f"\nUpdated timestamps:")
            print(f"  published_date: {updated_doc.get('published_date', 'N/A')}")
            print(f"  last_updated: {updated_doc.get('last_updated', 'N/A')}")
            break
else:
    print(f"File not found: {test_file}")
    print("Please ensure you have generated data files.")