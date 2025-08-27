#!/usr/bin/env python3
"""
Find optimal bulk size and worker count for Elasticsearch indexing.
Tests various combinations to find the sweet spot.
"""

import os
import sys
import json
import time
from datetime import datetime
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import itertools

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

class OptimalSettingsFinder:
    def __init__(self, test_file='generated_data/generated_holdings.jsonl', test_docs=50000):
        self.test_file = test_file
        self.test_docs = test_docs  # Use more docs for realistic test
        self.es_client = None
        self.test_data = []
        self.results = []
        
    def connect_es(self):
        """Connect to Elasticsearch."""
        if ES_CONFIG['endpoint_url'] and ES_CONFIG['api_key']:
            try:
                self.es_client = Elasticsearch(
                    ES_CONFIG['endpoint_url'],
                    api_key=ES_CONFIG['api_key'],
                    request_timeout=120,
                    verify_certs=False,
                    max_retries=3,
                    retry_on_timeout=True
                )
                info = self.es_client.info()
                print(f"Connected to Elasticsearch: {info['version']['number']}")
                return True
            except Exception as e:
                print(f"Could not connect to Elasticsearch: {e}")
                return False
        return False
    
    def prepare_test_data(self, with_timestamps=True):
        """Load test data once to reuse across tests."""
        print(f"\nPreparing {self.test_docs} test documents...")
        
        doc_type = 'holdings' if 'holdings' in self.test_file else 'accounts'
        id_field = 'holding_id' if 'holdings' in self.test_file else 'account_id'
        
        actions = []
        doc_count = 0
        
        with open(self.test_file, 'r') as f:
            for line in f:
                if doc_count >= self.test_docs:
                    break
                    
                doc = json.loads(line)
                
                if with_timestamps:
                    doc = TimestampUpdater.update_document_timestamps(doc, doc_type, 0)
                
                action = {
                    "_index": "perf_test",
                    "_id": doc.get(id_field, doc_count),
                    "_source": doc
                }
                actions.append(action)
                doc_count += 1
        
        self.test_data = actions
        print(f"Prepared {len(self.test_data)} documents for testing")
        return len(self.test_data)
    
    def test_configuration(self, batch_size, num_workers, test_name=""):
        """Test a specific configuration of batch size and workers."""
        if not self.es_client or not self.test_data:
            return None
        
        # Create fresh test index
        test_index = 'perf_test'
        try:
            self.es_client.indices.delete(index=test_index, ignore=[404])
            self.es_client.indices.create(
                index=test_index,
                body={
                    "settings": {
                        "number_of_shards": 2,
                        "number_of_replicas": 0,
                        "refresh_interval": "-1",  # Disable refresh during bulk
                        "index": {
                            "translog": {
                                "flush_threshold_size": "1gb"  # Reduce flushing
                            }
                        }
                    }
                }
            )
        except Exception as e:
            print(f"Index creation error: {e}")
            return None
        
        # Update all actions to use test index
        for action in self.test_data:
            action['_index'] = test_index
        
        # Create batches
        batches = []
        for i in range(0, len(self.test_data), batch_size):
            batches.append(self.test_data[i:i+batch_size])
        
        print(f"\n{test_name}")
        print(f"Testing: batch_size={batch_size}, workers={num_workers}")
        print(f"Total batches: {len(batches)}")
        
        # Run the test
        start_time = time.time()
        success_count = 0
        error_count = 0
        lock = threading.Lock()
        
        def process_batch(batch):
            nonlocal success_count, error_count
            try:
                batch_success, batch_errors = helpers.bulk(
                    self.es_client,
                    batch,
                    chunk_size=len(batch),
                    request_timeout=120,
                    raise_on_error=False,
                    raise_on_exception=False
                )
                with lock:
                    success_count += batch_success
                    if batch_errors:
                        error_count += len(batch_errors)
                return batch_success
            except Exception as e:
                with lock:
                    error_count += len(batch)
                print(f"  Worker error: {e}")
                return 0
        
        # Process batches
        if num_workers == 1:
            # Single-threaded
            for batch in batches:
                process_batch(batch)
        else:
            # Multi-threaded
            with ThreadPoolExecutor(max_workers=num_workers) as executor:
                futures = [executor.submit(process_batch, batch) for batch in batches]
                for future in as_completed(futures):
                    try:
                        future.result(timeout=30)
                    except Exception as e:
                        print(f"  Future error: {e}")
        
        elapsed = time.time() - start_time
        docs_per_sec = success_count / elapsed if elapsed > 0 else 0
        
        # Force refresh to ensure all docs are searchable
        try:
            self.es_client.indices.refresh(index=test_index)
            # Verify doc count
            count_result = self.es_client.count(index=test_index)
            actual_count = count_result['count']
        except:
            actual_count = 0
        
        result = {
            'batch_size': batch_size,
            'workers': num_workers,
            'total_docs': len(self.test_data),
            'success_count': success_count,
            'error_count': error_count,
            'actual_count': actual_count,
            'elapsed_time': elapsed,
            'docs_per_sec': docs_per_sec,
            'avg_batch_time': elapsed / len(batches) if batches else 0
        }
        
        print(f"  Results: {success_count}/{len(self.test_data)} docs in {elapsed:.2f}s")
        print(f"  Speed: {docs_per_sec:.0f} docs/sec")
        print(f"  Verified count: {actual_count}")
        if error_count > 0:
            print(f"  ERRORS: {error_count}")
        
        # Cleanup
        try:
            self.es_client.indices.delete(index=test_index)
        except:
            pass
        
        # Small delay between tests to let ES recover
        time.sleep(2)
        
        return result
    
    def find_optimal_settings(self):
        """Test various combinations to find optimal settings."""
        print("\n" + "=" * 60)
        print("FINDING OPTIMAL BULK SIZE AND WORKER COUNT")
        print("=" * 60)
        
        # Test configurations - start conservative, then push limits
        batch_sizes = [500, 1000, 2000, 5000, 10000, 20000]
        worker_counts = [1, 2, 4, 8, 16, 24, 32]
        
        # Phase 1: Find optimal batch size with moderate workers
        print("\n" + "=" * 60)
        print("PHASE 1: Finding Optimal Batch Size (8 workers)")
        print("=" * 60)
        
        batch_results = []
        for batch_size in batch_sizes:
            result = self.test_configuration(batch_size, 8, f"Test {len(batch_results)+1}/{len(batch_sizes)}")
            if result:
                batch_results.append(result)
                self.results.append(result)
            
            # Stop if performance degrades significantly
            if len(batch_results) >= 2:
                if batch_results[-1]['docs_per_sec'] < batch_results[-2]['docs_per_sec'] * 0.8:
                    print(f"\nPerformance degraded at batch_size={batch_size}, stopping batch size tests")
                    break
        
        # Find best batch size
        best_batch = max(batch_results, key=lambda x: x['docs_per_sec'])
        optimal_batch = best_batch['batch_size']
        print(f"\nOptimal batch size: {optimal_batch} ({best_batch['docs_per_sec']:.0f} docs/sec)")
        
        # Phase 2: Find optimal worker count with best batch size
        print("\n" + "=" * 60)
        print(f"PHASE 2: Finding Optimal Worker Count (batch_size={optimal_batch})")
        print("=" * 60)
        
        worker_results = []
        for workers in worker_counts:
            result = self.test_configuration(optimal_batch, workers, f"Test {len(worker_results)+1}/{len(worker_counts)}")
            if result:
                worker_results.append(result)
                self.results.append(result)
            
            # Stop if performance degrades significantly
            if len(worker_results) >= 2:
                if worker_results[-1]['docs_per_sec'] < worker_results[-2]['docs_per_sec'] * 0.9:
                    print(f"\nPerformance degraded at workers={workers}, stopping worker tests")
                    break
        
        # Find best worker count
        best_worker = max(worker_results, key=lambda x: x['docs_per_sec'])
        optimal_workers = best_worker['workers']
        print(f"\nOptimal workers: {optimal_workers} ({best_worker['docs_per_sec']:.0f} docs/sec)")
        
        # Phase 3: Fine-tune around the optimal point
        print("\n" + "=" * 60)
        print("PHASE 3: Fine-tuning Around Optimal Settings")
        print("=" * 60)
        
        # Test variations around optimal
        fine_tune_configs = [
            (optimal_batch // 2, optimal_workers),
            (optimal_batch, optimal_workers // 2) if optimal_workers > 1 else None,
            (optimal_batch * 2, optimal_workers),
            (optimal_batch, optimal_workers * 2) if optimal_workers < 32 else None,
            (optimal_batch // 2, optimal_workers * 2) if optimal_workers < 32 else None,
            (optimal_batch * 2, optimal_workers // 2) if optimal_workers > 1 else None,
        ]
        
        fine_tune_configs = [c for c in fine_tune_configs if c]  # Remove None values
        
        for i, (batch, workers) in enumerate(fine_tune_configs):
            result = self.test_configuration(batch, workers, f"Fine-tune {i+1}/{len(fine_tune_configs)}")
            if result:
                self.results.append(result)
        
        # Final results
        print("\n" + "=" * 60)
        print("FINAL RESULTS - TOP 5 CONFIGURATIONS")
        print("=" * 60)
        
        sorted_results = sorted(self.results, key=lambda x: x['docs_per_sec'], reverse=True)
        
        print(f"\n{'Rank':<5} {'Batch':<8} {'Workers':<8} {'Docs/sec':<12} {'Total Time':<12} {'Errors':<8}")
        print("-" * 60)
        
        for i, result in enumerate(sorted_results[:5]):
            print(f"{i+1:<5} {result['batch_size']:<8} {result['workers']:<8} "
                  f"{result['docs_per_sec']:<12.0f} {result['elapsed_time']:<12.2f} {result['error_count']:<8}")
        
        # Best overall
        best_overall = sorted_results[0]
        print("\n" + "=" * 60)
        print("RECOMMENDED SETTINGS")
        print("=" * 60)
        print(f"Batch Size: {best_overall['batch_size']}")
        print(f"Workers: {best_overall['workers']}")
        print(f"Expected Speed: {best_overall['docs_per_sec']:.0f} docs/sec")
        
        # Calculate time for full dataset
        full_docs = 122923  # financial_holdings
        expected_time = full_docs / best_overall['docs_per_sec']
        print(f"\nExpected time for 122,923 documents: {expected_time:.0f} seconds ({expected_time/60:.1f} minutes)")
        
        print("\n" + "=" * 60)
        print("COMMAND TO USE")
        print("=" * 60)
        print(f"!python3 control.py --custom --accounts --news --reports --elasticsearch \\")
        print(f"    --update-timestamps-on-load --bulk-size {best_overall['batch_size']} \\")
        print(f"    --max-parallel-indices 5 --parallel-bulk-workers {best_overall['workers']}")
        
        return best_overall

def main():
    # Check for test file
    test_files = [
        'generated_data/generated_holdings.jsonl',
        'generated_data/generated_accounts.jsonl',
    ]
    
    test_file = None
    for f in test_files:
        if os.path.exists(f):
            with open(f, 'r') as file:
                line_count = sum(1 for _ in file)
            print(f"Found: {f} ({line_count} documents)")
            if not test_file or 'holdings' in f:
                test_file = f
    
    if not test_file:
        print("ERROR: No data files found. Please generate data first.")
        return
    
    # Use more documents for realistic testing (but not all 122k)
    test_docs = min(50000, line_count)  # Use up to 50k docs for testing
    
    print(f"\nUsing {test_docs} documents from {test_file} for testing")
    print("This will take several minutes to complete...\n")
    
    finder = OptimalSettingsFinder(test_file, test_docs)
    
    if not finder.connect_es():
        print("ERROR: Could not connect to Elasticsearch")
        print("Set ES_ENDPOINT_URL and ES_API_KEY environment variables")
        return
    
    # Prepare test data once
    finder.prepare_test_data(with_timestamps=True)
    
    # Find optimal settings
    best_settings = finder.find_optimal_settings()

if __name__ == "__main__":
    main()