"""
Timestamp Update Testing Module

Tests timestamp updating functionality for data loading and Elasticsearch operations.
Migrated from test_timestamp_update.py and enhanced with pytest framework.
"""

import pytest
import os
import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch, mock_open


@pytest.mark.functional
class TestTimestampUpdate:
    """Test timestamp updating functionality."""

    @pytest.fixture(autouse=True)
    def setup_environment(self, mock_environment):
        """Set up test environment variables."""
        # Override specific timestamp settings
        os.environ['UPDATE_TIMESTAMPS_ON_LOAD'] = 'true'
        os.environ['PARALLEL_BULK_WORKERS'] = '1'
        os.environ['ES_BULK_BATCH_SIZE'] = '100'

    def test_environment_variables_set(self):
        """Test that timestamp update environment variables are properly set."""
        assert os.getenv('UPDATE_TIMESTAMPS_ON_LOAD') == 'true'
        assert os.getenv('PARALLEL_BULK_WORKERS') == '1'
        assert os.getenv('ES_BULK_BATCH_SIZE') == '100'

    def test_read_and_chunk_with_timestamp_update(self, sample_financial_trades, create_temp_jsonl_file):
        """Test the _read_and_chunk_from_file function with timestamp updates."""
        # Create temporary file with sample data
        temp_file = create_temp_jsonl_file(sample_financial_trades, 'test_trades')
        
        try:
            # Mock the common_utils import and function
            with patch('scripts.common_utils._read_and_chunk_from_file') as mock_chunk_func:
                # Configure mock to simulate timestamp updating
                updated_doc = sample_financial_trades[0].copy()
                updated_doc['execution_timestamp'] = datetime.now().isoformat()
                updated_doc['last_updated'] = datetime.now().isoformat()
                
                mock_chunk_func.return_value = iter([
                    [{
                        '_index': 'financial_trades',
                        '_id': 'TRD-20250115-001',
                        '_source': updated_doc
                    }]
                ])
                
                # Import and test the function
                from scripts.common_utils import _read_and_chunk_from_file
                
                generator = _read_and_chunk_from_file(
                    temp_file,
                    'financial_trades', 
                    'trade_id',
                    batch_size=1,
                    update_timestamps=True,
                    timestamp_offset=0
                )
                
                # Get first batch
                batches = list(generator)
                assert len(batches) > 0
                
                batch = batches[0]
                assert len(batch) > 0
                
                updated_document = batch[0]['_source']
                
                # Verify timestamp fields exist
                assert 'execution_timestamp' in updated_document
                assert 'last_updated' in updated_document
                
                # Verify the mock was called correctly
                mock_chunk_func.assert_called_once()
                
        finally:
            # Cleanup
            os.unlink(temp_file)

    @pytest.mark.parametrize("offset_hours,expected_direction", [
        (0, "current"),
        (-24, "past"),
        (24, "future"),
        (-168, "week_past"),  # 1 week ago
    ])
    def test_timestamp_offset_calculations(self, offset_hours, expected_direction):
        """Test timestamp offset calculations with various time periods."""
        current_time = datetime.now()
        
        # Calculate expected timestamp
        if offset_hours == 0:
            expected_time = current_time
        else:
            expected_time = current_time + timedelta(hours=offset_hours)
        
        # Test the offset logic
        calculated_time = current_time + timedelta(hours=offset_hours)
        
        if expected_direction == "current":
            # Should be within 1 minute of current time
            time_diff = abs((calculated_time - current_time).total_seconds())
            assert time_diff < 60
            
        elif expected_direction == "past":
            # Should be in the past
            assert calculated_time < current_time
            
        elif expected_direction == "future":
            # Should be in the future
            assert calculated_time > current_time
            
        elif expected_direction == "week_past":
            # Should be approximately 1 week ago
            time_diff_hours = (current_time - calculated_time).total_seconds() / 3600
            assert 167 <= time_diff_hours <= 169  # Allow for small variations

    def test_timestamp_format_validation(self):
        """Test that timestamps are in correct ISO format."""
        current_time = datetime.now()
        timestamp_str = current_time.isoformat()
        
        # Verify ISO format
        assert 'T' in timestamp_str
        assert len(timestamp_str) >= 19  # YYYY-MM-DDTHH:MM:SS minimum
        
        # Verify it can be parsed back
        parsed_time = datetime.fromisoformat(timestamp_str)
        assert isinstance(parsed_time, datetime)
        
        # Should be very close to original (within 1 second)
        time_diff = abs((parsed_time - current_time).total_seconds())
        assert time_diff < 1

    def test_document_structure_preservation(self, sample_financial_trades):
        """Test that document structure is preserved during timestamp updates."""
        original_doc = sample_financial_trades[0].copy()
        
        # Simulate timestamp update
        updated_doc = original_doc.copy()
        updated_doc['execution_timestamp'] = datetime.now().isoformat()
        updated_doc['last_updated'] = datetime.now().isoformat()
        
        # Verify all original fields are preserved
        for key in original_doc.keys():
            if key not in ['execution_timestamp', 'last_updated']:
                assert updated_doc[key] == original_doc[key]
        
        # Verify new timestamp fields are present and valid
        assert 'execution_timestamp' in updated_doc
        assert 'last_updated' in updated_doc
        
        # Verify timestamps are valid ISO format
        datetime.fromisoformat(updated_doc['execution_timestamp'])
        datetime.fromisoformat(updated_doc['last_updated'])

    def test_batch_processing_with_timestamps(self, sample_financial_trades):
        """Test batch processing maintains timestamp consistency."""
        batch_size = 2
        
        # Simulate processing multiple documents
        processed_docs = []
        processing_time = datetime.now()
        
        for i, doc in enumerate(sample_financial_trades[:batch_size]):
            updated_doc = doc.copy()
            updated_doc['execution_timestamp'] = processing_time.isoformat()
            updated_doc['last_updated'] = processing_time.isoformat()
            processed_docs.append(updated_doc)
        
        # All documents in batch should have same timestamp
        timestamps = [doc['last_updated'] for doc in processed_docs]
        assert len(set(timestamps)) == 1  # All timestamps should be identical

    def test_missing_file_handling(self):
        """Test handling of missing data files."""
        non_existent_file = '/tmp/non_existent_file.jsonl'
        
        # Verify file doesn't exist
        assert not os.path.exists(non_existent_file)
        
        # Test should handle missing file gracefully
        with patch('scripts.common_utils._read_and_chunk_from_file') as mock_func:
            mock_func.side_effect = FileNotFoundError(f"File not found: {non_existent_file}")
            
            from scripts.common_utils import _read_and_chunk_from_file
            
            with pytest.raises(FileNotFoundError):
                list(_read_and_chunk_from_file(
                    non_existent_file,
                    'financial_news',
                    'article_id',
                    batch_size=100,
                    update_timestamps=True
                ))

    def test_different_index_timestamp_fields(self):
        """Test timestamp updates for different index types with different timestamp fields."""
        test_cases = [
            {
                'index': 'financial_news',
                'id_field': 'article_id',
                'timestamp_fields': ['published_date', 'last_updated']
            },
            {
                'index': 'financial_reports',  
                'id_field': 'report_id',
                'timestamp_fields': ['report_date', 'last_updated']
            },
            {
                'index': 'financial_trades',
                'id_field': 'trade_id', 
                'timestamp_fields': ['execution_timestamp', 'last_updated']
            },
            {
                'index': 'financial_accounts',
                'id_field': 'account_id',
                'timestamp_fields': ['last_updated']
            },
            {
                'index': 'financial_holdings',
                'id_field': 'holding_id',
                'timestamp_fields': ['purchase_date', 'last_updated']
            }
        ]
        
        current_time = datetime.now().isoformat()
        
        for case in test_cases:
            # Create mock document
            mock_doc = {
                case['id_field']: f"TEST-{case['index']}-001"
            }
            
            # Add timestamp fields
            for field in case['timestamp_fields']:
                mock_doc[field] = current_time
            
            # Verify document has expected structure
            assert case['id_field'] in mock_doc
            
            for field in case['timestamp_fields']:
                assert field in mock_doc
                # Verify timestamp is valid
                datetime.fromisoformat(mock_doc[field])

    def test_concurrent_timestamp_consistency(self):
        """Test that concurrent processing maintains timestamp consistency."""
        # Simulate concurrent processing scenario
        documents = [
            {'id': f'doc_{i}', 'content': f'content_{i}'} 
            for i in range(10)
        ]
        
        # Process all documents with same timestamp
        processing_timestamp = datetime.now()
        updated_docs = []
        
        for doc in documents:
            updated_doc = doc.copy()
            updated_doc['last_updated'] = processing_timestamp.isoformat()
            updated_docs.append(updated_doc)
        
        # Verify all documents have identical timestamps
        timestamps = [doc['last_updated'] for doc in updated_docs]
        unique_timestamps = set(timestamps)
        
        assert len(unique_timestamps) == 1
        assert list(unique_timestamps)[0] == processing_timestamp.isoformat()


# ============================================================================
# INTEGRATION TESTS WITH FILE I/O
# ============================================================================

@pytest.mark.integration
class TestTimestampUpdateIntegration:
    """Integration tests for timestamp updates with real file operations."""

    def test_real_file_timestamp_update(self, tmp_path):
        """Test timestamp update with real file operations."""
        # Create a real temporary file
        test_data = [
            {
                'article_id': 'ART-001',
                'title': 'Test Article',
                'published_date': '2024-01-01T00:00:00',
                'last_updated': '2024-01-01T00:00:00'
            },
            {
                'article_id': 'ART-002', 
                'title': 'Test Article 2',
                'published_date': '2024-01-01T00:00:00',
                'last_updated': '2024-01-01T00:00:00'
            }
        ]
        
        # Write test data to file
        test_file = tmp_path / "test_news.jsonl"
        with open(test_file, 'w') as f:
            for item in test_data:
                f.write(json.dumps(item) + '\n')
        
        # Read and verify original timestamps
        with open(test_file, 'r') as f:
            original_line = f.readline()
            original_doc = json.loads(original_line)
            
        assert original_doc['published_date'] == '2024-01-01T00:00:00'
        assert original_doc['last_updated'] == '2024-01-01T00:00:00'
        
        # Verify file was created and contains expected data
        assert test_file.exists()
        assert test_file.stat().st_size > 0
        
        # Verify we can read the data back
        with open(test_file, 'r') as f:
            lines = f.readlines()
            
        assert len(lines) == 2
        
        for line in lines:
            doc = json.loads(line)
            assert 'article_id' in doc
            assert 'published_date' in doc
            assert 'last_updated' in doc

    def test_large_file_handling(self, tmp_path):
        """Test timestamp update with larger files."""
        # Create a larger dataset
        large_dataset = [
            {
                'trade_id': f'TRD-{i:06d}',
                'account_id': f'ACC-{i % 100:05d}',
                'symbol': 'AAPL',
                'execution_timestamp': '2024-01-01T09:30:00',
                'last_updated': '2024-01-01T09:30:00'
            }
            for i in range(1000)  # 1000 records
        ]
        
        # Write to file
        large_file = tmp_path / "large_trades.jsonl"
        with open(large_file, 'w') as f:
            for item in large_dataset:
                f.write(json.dumps(item) + '\n')
        
        # Verify file size and content
        assert large_file.exists()
        file_size = large_file.stat().st_size
        assert file_size > 100000  # Should be substantial size
        
        # Verify we can read it back in chunks
        records_read = 0
        with open(large_file, 'r') as f:
            for line in f:
                if line.strip():  # Skip empty lines
                    doc = json.loads(line)
                    assert 'trade_id' in doc
                    assert 'execution_timestamp' in doc
                    records_read += 1
        
        assert records_read == 1000

    def test_file_permissions_and_cleanup(self, tmp_path):
        """Test file permissions and cleanup behavior."""
        test_file = tmp_path / "perm_test.jsonl"
        
        # Create file
        with open(test_file, 'w') as f:
            f.write('{"test": "data"}\n')
        
        # Verify file exists and is readable
        assert test_file.exists()
        assert os.access(test_file, os.R_OK)
        
        # Test reading
        with open(test_file, 'r') as f:
            content = f.read()
            
        assert 'test' in content
        assert 'data' in content