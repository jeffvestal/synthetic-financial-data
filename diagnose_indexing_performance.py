#!/usr/bin/env python3
"""
Performance diagnostic script to identify indexing bottlenecks.
Tests timestamp updating vs bulk indexing performance separately.
"""

import os
import sys
import json
import time
from datetime import datetime
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

# Setup environment
os.environ['ES_API_KEY'] = os.getenv('ES_API_KEY', '')
os.environ['ES_ENDPOINT_URL'] = os.getenv('ES_ENDPOINT_URL', 'https://localhost:9200')

# Add scripts to path
scripts_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scripts')
lib_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib')
sys.path.insert(0, scripts_dir)
sys.path.insert(0, lib_dir)

from elasticsearch import Elasticsearch, helpers
from timestamp_updater import TimestampUpdater
from config import ES_CONFIG

class PerformanceTester:
    def __init__(self, test_file='generated_data/generated_holdings.jsonl', max_docs=10000):
        self.test_file = test_file
        self.max_docs = max_docs
        self.es_client = None
        
    def connect_es(self):
        """Connect to Elasticsearch if credentials available."""
        if ES_CONFIG['endpoint_url'] and ES_CONFIG['api_key']:
            try:
                self.es_client = Elasticsearch(
                    ES_CONFIG['endpoint_url'],
                    api_key=ES_CONFIG['api_key'],
                    request_timeout=60,
                    verify_certs=False
                )
                info = self.es_client.info()
                print(f"Connected to Elasticsearch: {info['version']['number']}")
                return True
            except Exception as e:
                print(f"Could not connect to Elasticsearch: {e}")
                return False
        return False
    
    def test_read_only(self):
        """Test 1: Just read and parse JSON documents."""
        print("\n=== TEST 1: Read and Parse JSON ===")
        start_time = time.time()
        doc_count = 0
        
        with open(self.test_file, 'r') as f:
            for line in f:
                if doc_count >= self.max_docs:
                    break
                doc = json.loads(line)
                doc_count += 1
        
        elapsed = time.time() - start_time
        print(f"Read {doc_count} documents in {elapsed:.2f} seconds")
        print(f"Rate: {doc_count/elapsed:.0f} docs/second")
        return elapsed
    
    def test_timestamp_update(self):
        """Test 2: Read and update timestamps (no ES)."""
        print("\n=== TEST 2: Read + Update Timestamps ===")
        start_time = time.time()
        doc_count = 0
        
        # Determine document type based on file
        doc_type = 'holdings' if 'holdings' in self.test_file else 'accounts'
        
        with open(self.test_file, 'r') as f:
            for line in f:
                if doc_count >= self.max_docs:
                    break
                doc = json.loads(line)
                # Update timestamps
                updated_doc = TimestampUpdater.update_document_timestamps(doc, doc_type, 0)
                doc_count += 1
        
        elapsed = time.time() - start_time
        print(f"Read and updated {doc_count} documents in {elapsed:.2f} seconds")
        print(f"Rate: {doc_count/elapsed:.0f} docs/second")
        
        # Calculate overhead
        read_time = self.test_read_only()
        update_overhead = elapsed - read_time
        print(f"Timestamp update overhead: {update_overhead:.2f} seconds ({update_overhead/elapsed*100:.1f}% of total)")
        return elapsed
    
    def test_bulk_prepare(self, with_timestamps=False):
        """Test 3: Prepare bulk requests (no ES)."""
        test_name = "with timestamp updates" if with_timestamps else "without timestamps"
        print(f"\n=== TEST 3: Prepare Bulk Requests ({test_name}) ===")
        start_time = time.time()
        doc_count = 0
        actions = []
        
        doc_type = 'holdings' if 'holdings' in self.test_file else 'accounts'
        index_name = 'test_index'
        id_field = 'holding_id' if 'holdings' in self.test_file else 'account_id'
        
        with open(self.test_file, 'r') as f:
            for line in f:
                if doc_count >= self.max_docs:
                    break
                doc = json.loads(line)
                
                if with_timestamps:
                    doc = TimestampUpdater.update_document_timestamps(doc, doc_type, 0)
                
                action = {
                    "_index": index_name,
                    "_id": doc.get(id_field, doc_count),
                    "_source": doc
                }
                actions.append(action)
                doc_count += 1
        
        elapsed = time.time() - start_time
        print(f"Prepared {doc_count} bulk actions in {elapsed:.2f} seconds")
        print(f"Rate: {doc_count/elapsed:.0f} docs/second")
        return elapsed, actions
    
    def test_bulk_index_single_thread(self, batch_size=1000, with_timestamps=False):
        """Test 4: Full bulk indexing - single thread."""
        if not self.es_client:
            print("\n=== TEST 4: Bulk Indexing (SKIPPED - No ES connection) ===")
            return
        
        test_name = "with timestamps" if with_timestamps else "without timestamps"
        print(f"\n=== TEST 4: Single-Thread Bulk Indexing ({test_name}) ===")
        print(f"Batch size: {batch_size}")
        
        # Prepare actions
        _, actions = self.test_bulk_prepare(with_timestamps)
        
        # Create test index
        test_index = 'perf_test_single'
        try:
            self.es_client.indices.delete(index=test_index, ignore=[404])
            self.es_client.indices.create(index=test_index)
        except:
            pass
        
        # Update index name in actions
        for action in actions:
            action['_index'] = test_index
        
        # Measure bulk indexing
        start_time = time.time()
        success_count = 0
        
        # Process in batches
        for i in range(0, len(actions), batch_size):
            batch = actions[i:i+batch_size]
            try:
                batch_success, _ = helpers.bulk(
                    self.es_client,
                    batch,
                    chunk_size=batch_size,
                    request_timeout=60,
                    raise_on_error=False
                )
                success_count += batch_success
            except Exception as e:
                print(f"Batch error: {e}")
        
        elapsed = time.time() - start_time
        print(f"Indexed {success_count} documents in {elapsed:.2f} seconds")
        print(f"Rate: {success_count/elapsed:.0f} docs/second")
        
        # Cleanup
        try:
            self.es_client.indices.delete(index=test_index)
        except:
            pass
    
    def test_bulk_index_parallel(self, batch_size=1000, workers=8, with_timestamps=False):
        """Test 5: Full bulk indexing - parallel workers."""
        if not self.es_client:
            print("\n=== TEST 5: Parallel Bulk Indexing (SKIPPED - No ES connection) ===")
            return
        
        test_name = "with timestamps" if with_timestamps else "without timestamps"
        print(f"\n=== TEST 5: Parallel Bulk Indexing ({test_name}) ===")
        print(f"Batch size: {batch_size}, Workers: {workers}")
        
        # Prepare actions
        _, actions = self.test_bulk_prepare(with_timestamps)
        
        # Create test index
        test_index = 'perf_test_parallel'
        try:
            self.es_client.indices.delete(index=test_index, ignore=[404])
            self.es_client.indices.create(index=test_index)
        except:
            pass
        
        # Update index name
        for action in actions:
            action['_index'] = test_index
        
        # Create batches
        batches = []
        for i in range(0, len(actions), batch_size):
            batches.append(actions[i:i+batch_size])
        
        # Measure parallel indexing
        start_time = time.time()
        success_count = 0
        lock = threading.Lock()
        
        def process_batch(batch):
            nonlocal success_count
            try:
                batch_success, _ = helpers.bulk(
                    self.es_client,
                    batch,
                    chunk_size=len(batch),
                    request_timeout=60,
                    raise_on_error=False
                )
                with lock:
                    success_count += batch_success
                return batch_success
            except Exception as e:
                print(f"Worker error: {e}")
                return 0
        
        # Process batches in parallel
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [executor.submit(process_batch, batch) for batch in batches]
            for future in as_completed(futures):
                try:
                    future.result()
                except:
                    pass
        
        elapsed = time.time() - start_time
        print(f"Indexed {success_count} documents in {elapsed:.2f} seconds")
        print(f"Rate: {success_count/elapsed:.0f} docs/second")
        
        # Cleanup
        try:
            self.es_client.indices.delete(index=test_index)
        except:
            pass

def main():
    print("=" * 60)
    print("ELASTICSEARCH INDEXING PERFORMANCE DIAGNOSTIC")
    print("=" * 60)
    
    # Check which file to test
    test_files = [
        'generated_data/generated_holdings.jsonl',
        'generated_data/generated_accounts.jsonl',
        'generated_data/generated_news.jsonl'
    ]
    
    test_file = None
    for f in test_files:
        if os.path.exists(f):
            # Count lines
            with open(f, 'r') as file:
                line_count = sum(1 for _ in file)
            print(f"Found: {f} ({line_count} documents)")
            if not test_file or 'holdings' in f:  # Prefer holdings as it's largest
                test_file = f
    
    if not test_file:
        print("ERROR: No data files found. Please generate data first.")
        return
    
    print(f"\nUsing test file: {test_file}")
    tester = PerformanceTester(test_file, max_docs=10000)
    
    # Run tests
    print("\n" + "=" * 60)
    
    # Test 1: Read speed
    tester.test_read_only()
    
    # Test 2: Timestamp update speed
    tester.test_timestamp_update()
    
    # Test 3: Bulk preparation
    tester.test_bulk_prepare(with_timestamps=False)
    tester.test_bulk_prepare(with_timestamps=True)
    
    # Tests 4-5: Bulk indexing (if ES available)
    if tester.connect_es():
        # Test without timestamps
        tester.test_bulk_index_single_thread(batch_size=1000, with_timestamps=False)
        tester.test_bulk_index_parallel(batch_size=1000, workers=8, with_timestamps=False)
        
        # Test with timestamps
        tester.test_bulk_index_single_thread(batch_size=1000, with_timestamps=True)
        tester.test_bulk_index_parallel(batch_size=1000, workers=8, with_timestamps=True)
        
        # Test with your exact settings
        print("\n" + "=" * 60)
        print("TESTING YOUR EXACT SETTINGS")
        print("=" * 60)
        tester.test_bulk_index_parallel(batch_size=1000, workers=16, with_timestamps=True)
    else:
        print("\nSkipping Elasticsearch tests - no connection available")
        print("Set ES_ENDPOINT_URL and ES_API_KEY environment variables to test indexing")
    
    print("\n" + "=" * 60)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()