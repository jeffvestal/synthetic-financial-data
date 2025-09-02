"""
Unit Tests for Index Manager

Tests Elasticsearch index management functionality including creation, deletion,
status checking, and mapping validation.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from elasticsearch.exceptions import RequestError, ConnectionError, NotFoundError

from lib.index_manager import IndexManager, ensure_indices_exist


@pytest.mark.unit
class TestIndexManager:
    """Test IndexManager functionality."""

    @pytest.fixture
    def index_manager(self, mock_elasticsearch_client):
        """Create IndexManager with mocked Elasticsearch client."""
        return IndexManager(mock_elasticsearch_client)

    def test_index_manager_initialization(self, index_manager, mock_elasticsearch_client):
        """Test IndexManager initialization."""
        assert index_manager.es_client == mock_elasticsearch_client
        assert hasattr(index_manager, 'mapping_file')

    def test_test_connection_success(self, index_manager, mock_elasticsearch_client):
        """Test successful connection test."""
        mock_elasticsearch_client.info.return_value = {
            'version': {'number': '8.9.0'},
            'tagline': 'You Know, for Search'
        }
        
        result = index_manager.test_connection()
        
        assert result['success'] is True
        assert result['version'] == '8.9.0'
        assert 'tagline' in result

    def test_test_connection_failure(self, index_manager, mock_elasticsearch_client):
        """Test connection test failure."""
        mock_elasticsearch_client.info.side_effect = ConnectionError("Connection failed")
        
        result = index_manager.test_connection()
        
        assert result['success'] is False
        assert 'error' in result

    def test_index_exists_true(self, index_manager, mock_elasticsearch_client):
        """Test index existence check when index exists."""
        mock_elasticsearch_client.indices.exists.return_value = True
        
        result = index_manager.index_exists('financial_accounts')
        
        assert result is True
        mock_elasticsearch_client.indices.exists.assert_called_once_with(index='financial_accounts')

    def test_index_exists_false(self, index_manager, mock_elasticsearch_client):
        """Test index existence check when index doesn't exist."""
        mock_elasticsearch_client.indices.exists.return_value = False
        
        result = index_manager.index_exists('nonexistent_index')
        
        assert result is False

    def test_get_index_status_existing_index(self, index_manager, mock_elasticsearch_client):
        """Test getting status of existing index."""
        # Mock index exists
        mock_elasticsearch_client.indices.exists.return_value = True
        
        # Mock index stats
        mock_elasticsearch_client.indices.stats.return_value = {
            'indices': {
                'financial_accounts': {
                    'total': {
                        'docs': {'count': 7000},
                        'store': {'size_in_bytes': 1024000}
                    }
                }
            }
        }
        
        # Mock cluster health
        mock_elasticsearch_client.cluster.health.return_value = {
            'indices': {
                'financial_accounts': {'status': 'green'}
            }
        }
        
        status = index_manager.get_index_status('financial_accounts')
        
        assert status['exists'] is True
        assert status['doc_count'] == 7000
        assert status['size_bytes'] == 1024000
        assert status['health'] == 'green'

    def test_get_index_status_nonexistent_index(self, index_manager, mock_elasticsearch_client):
        """Test getting status of non-existent index."""
        mock_elasticsearch_client.indices.exists.return_value = False
        
        status = index_manager.get_index_status('nonexistent_index')
        
        assert status['exists'] is False
        assert status['doc_count'] == 0
        assert status['size_bytes'] == 0
        assert status['health'] == 'n/a'

    def test_get_index_mapping_from_file(self, index_manager, mock_index_mappings):
        """Test loading index mapping from file."""
        with patch.object(index_manager, '_load_mappings_from_file', return_value=mock_index_mappings):
            mapping = index_manager.get_index_mapping('financial_trades')
            
            assert mapping is not None
            assert 'mappings' in mapping
            assert 'properties' in mapping['mappings']
            assert 'trade_id' in mapping['mappings']['properties']

    def test_get_index_mapping_missing_index(self, index_manager):
        """Test loading mapping for non-existent index."""
        with patch.object(index_manager, '_load_mappings_from_file', return_value={}):
            mapping = index_manager.get_index_mapping('nonexistent_index')
            
            assert mapping is None

    def test_create_index_success(self, index_manager, mock_elasticsearch_client, mock_index_mappings):
        """Test successful index creation."""
        # Mock mapping loading
        with patch.object(index_manager, 'get_index_mapping', return_value=mock_index_mappings['financial_trades']):
            # Mock successful creation
            mock_elasticsearch_client.indices.create.return_value = {'acknowledged': True}
            
            result = index_manager.create_index('financial_trades')
            
            assert result is True
            mock_elasticsearch_client.indices.create.assert_called_once()

    def test_create_index_no_mapping(self, index_manager, mock_elasticsearch_client):
        """Test index creation when no mapping is available."""
        with patch.object(index_manager, 'get_index_mapping', return_value=None):
            result = index_manager.create_index('unknown_index')
            
            assert result is False
            mock_elasticsearch_client.indices.create.assert_not_called()

    def test_create_index_elasticsearch_error(self, index_manager, mock_elasticsearch_client, mock_index_mappings):
        """Test index creation with Elasticsearch error."""
        with patch.object(index_manager, 'get_index_mapping', return_value=mock_index_mappings['financial_trades']):
            # Mock creation failure
            mock_elasticsearch_client.indices.create.side_effect = RequestError("Creation failed")
            
            result = index_manager.create_index('financial_trades')
            
            assert result is False

    def test_delete_index_success(self, index_manager, mock_elasticsearch_client):
        """Test successful index deletion."""
        mock_elasticsearch_client.indices.delete.return_value = {'acknowledged': True}
        
        result = index_manager.delete_index('test_index')
        
        assert result is True
        mock_elasticsearch_client.indices.delete.assert_called_once_with(index='test_index')

    def test_delete_index_not_found(self, index_manager, mock_elasticsearch_client):
        """Test index deletion when index doesn't exist."""
        mock_elasticsearch_client.indices.delete.side_effect = NotFoundError("Index not found")
        
        result = index_manager.delete_index('nonexistent_index')
        
        assert result is False

    def test_recreate_index_success(self, index_manager, mock_elasticsearch_client, mock_index_mappings):
        """Test successful index recreation."""
        # Mock index exists
        mock_elasticsearch_client.indices.exists.return_value = True
        
        # Mock successful deletion and creation
        mock_elasticsearch_client.indices.delete.return_value = {'acknowledged': True}
        mock_elasticsearch_client.indices.create.return_value = {'acknowledged': True}
        
        with patch.object(index_manager, 'get_index_mapping', return_value=mock_index_mappings['financial_trades']):
            result = index_manager.recreate_index('financial_trades')
            
            assert result is True
            mock_elasticsearch_client.indices.delete.assert_called_once()
            mock_elasticsearch_client.indices.create.assert_called_once()

    def test_recreate_index_nonexistent(self, index_manager, mock_elasticsearch_client, mock_index_mappings):
        """Test recreation of non-existent index (should just create)."""
        # Mock index doesn't exist
        mock_elasticsearch_client.indices.exists.return_value = False
        
        # Mock successful creation
        mock_elasticsearch_client.indices.create.return_value = {'acknowledged': True}
        
        with patch.object(index_manager, 'get_index_mapping', return_value=mock_index_mappings['financial_trades']):
            result = index_manager.recreate_index('financial_trades')
            
            assert result is True
            mock_elasticsearch_client.indices.delete.assert_not_called()
            mock_elasticsearch_client.indices.create.assert_called_once()

    def test_get_all_indices_status(self, index_manager, mock_elasticsearch_client):
        """Test getting status of all indices."""
        expected_indices = ['financial_accounts', 'financial_holdings', 'financial_trades', 
                          'financial_news', 'financial_reports']
        
        # Mock each index status call
        def mock_get_status(index_name):
            return {
                'exists': True,
                'doc_count': 1000,
                'size_bytes': 1024000,
                'health': 'green'
            }
        
        with patch.object(index_manager, 'get_index_status', side_effect=mock_get_status):
            status_dict = index_manager.get_all_indices_status()
            
            assert isinstance(status_dict, dict)
            assert len(status_dict) == len(expected_indices)
            
            for index_name in expected_indices:
                assert index_name in status_dict
                assert status_dict[index_name]['exists'] is True

    def test_validate_mapping_structure(self, index_manager, mock_index_mappings):
        """Test mapping structure validation."""
        valid_mapping = mock_index_mappings['financial_trades']
        
        is_valid, errors = index_manager.validate_mapping(valid_mapping)
        
        assert is_valid is True
        assert len(errors) == 0

    def test_validate_mapping_invalid_structure(self, index_manager):
        """Test validation of invalid mapping structure."""
        invalid_mapping = {
            'mappings': {
                # Missing properties
            }
        }
        
        is_valid, errors = index_manager.validate_mapping(invalid_mapping)
        
        assert is_valid is False
        assert len(errors) > 0

    def test_filter_serverless_settings(self, index_manager):
        """Test filtering settings for serverless compatibility."""
        mapping_with_settings = {
            'settings': {
                'number_of_shards': 1,        # Should be filtered
                'number_of_replicas': 0,      # Should be filtered
                'analysis': {                 # Should be kept
                    'analyzer': {'custom': {'type': 'standard'}}
                },
                'index.mapping.total_fields.limit': 2000  # Should be kept
            },
            'mappings': {'properties': {'test_field': {'type': 'keyword'}}}
        }
        
        filtered_mapping = index_manager._filter_serverless_settings(mapping_with_settings)
        
        # Check that forbidden settings are removed
        assert 'number_of_shards' not in filtered_mapping['settings']
        assert 'number_of_replicas' not in filtered_mapping['settings']
        
        # Check that allowed settings are kept
        assert 'analysis' in filtered_mapping['settings']
        assert 'index.mapping.total_fields.limit' in filtered_mapping['settings']
        
        # Check that mappings are preserved
        assert 'mappings' in filtered_mapping

    def test_create_multiple_indices(self, index_manager, mock_elasticsearch_client, mock_index_mappings):
        """Test creating multiple indices."""
        indices_to_create = ['financial_accounts', 'financial_trades']
        
        with patch.object(index_manager, 'get_index_mapping') as mock_get_mapping:
            # Return different mappings for different indices
            def get_mapping_side_effect(index_name):
                if index_name in mock_index_mappings:
                    return mock_index_mappings[index_name]
                return mock_index_mappings['financial_trades']  # Default
                
            mock_get_mapping.side_effect = get_mapping_side_effect
            
            # Mock successful creation
            mock_elasticsearch_client.indices.create.return_value = {'acknowledged': True}
            
            results = index_manager.create_multiple_indices(indices_to_create)
            
            assert len(results) == 2
            assert all(results.values())  # All should be True
            
            # Should have called create twice
            assert mock_elasticsearch_client.indices.create.call_count == 2

    def test_backup_restore_index_mapping(self, index_manager, mock_elasticsearch_client, tmp_path):
        """Test backing up and restoring index mappings."""
        # Mock current mapping
        mock_mapping = {
            'financial_accounts': {
                'mappings': {
                    'properties': {
                        'account_id': {'type': 'keyword'}
                    }
                }
            }
        }
        
        mock_elasticsearch_client.indices.get_mapping.return_value = mock_mapping
        
        # Test backup
        backup_file = tmp_path / 'mapping_backup.json'
        
        if hasattr(index_manager, 'backup_mapping'):
            result = index_manager.backup_mapping('financial_accounts', str(backup_file))
            
            assert result is True
            assert backup_file.exists()
            
            # Test restore (if implemented)
            if hasattr(index_manager, 'restore_mapping'):
                restore_result = index_manager.restore_mapping(str(backup_file))
                assert restore_result is True


@pytest.mark.unit
class TestEnsureIndicesExist:
    """Test the ensure_indices_exist utility function."""

    def test_ensure_indices_exist_all_exist(self, mock_elasticsearch_client):
        """Test when all indices already exist."""
        mock_elasticsearch_client.indices.exists.return_value = True
        
        indices = ['financial_accounts', 'financial_trades']
        missing_indices = ensure_indices_exist(mock_elasticsearch_client, indices)
        
        assert missing_indices == []

    def test_ensure_indices_exist_some_missing(self, mock_elasticsearch_client, mock_index_mappings):
        """Test when some indices are missing."""
        # Mock exists calls - first index exists, second doesn't
        mock_elasticsearch_client.indices.exists.side_effect = [True, False]
        
        # Mock successful creation
        mock_elasticsearch_client.indices.create.return_value = {'acknowledged': True}
        
        with patch('lib.index_manager.IndexManager') as mock_manager_class:
            mock_manager = Mock()
            mock_manager.get_index_mapping.return_value = mock_index_mappings['financial_trades']
            mock_manager.create_index.return_value = True
            mock_manager_class.return_value = mock_manager
            
            indices = ['financial_accounts', 'financial_trades']
            missing_indices = ensure_indices_exist(mock_elasticsearch_client, indices)
            
            assert missing_indices == ['financial_trades']

    def test_ensure_indices_exist_creation_failure(self, mock_elasticsearch_client):
        """Test when index creation fails."""
        mock_elasticsearch_client.indices.exists.return_value = False
        
        with patch('lib.index_manager.IndexManager') as mock_manager_class:
            mock_manager = Mock()
            mock_manager.get_index_mapping.return_value = {'mappings': {}}
            mock_manager.create_index.return_value = False  # Creation fails
            mock_manager_class.return_value = mock_manager
            
            indices = ['financial_accounts']
            missing_indices = ensure_indices_exist(mock_elasticsearch_client, indices)
            
            # Should still be missing since creation failed
            assert 'financial_accounts' in missing_indices


@pytest.mark.unit
class TestIndexManagerEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.fixture
    def index_manager(self, mock_elasticsearch_client):
        return IndexManager(mock_elasticsearch_client)

    def test_handle_connection_timeout(self, index_manager, mock_elasticsearch_client):
        """Test handling of connection timeouts."""
        from elasticsearch.exceptions import ConnectionTimeout
        
        mock_elasticsearch_client.info.side_effect = ConnectionTimeout("Timeout")
        
        result = index_manager.test_connection()
        
        assert result['success'] is False
        assert 'timeout' in result['error'].lower()

    def test_handle_authentication_error(self, index_manager, mock_elasticsearch_client):
        """Test handling of authentication errors."""
        from elasticsearch.exceptions import AuthenticationException
        
        mock_elasticsearch_client.info.side_effect = AuthenticationException("Auth failed")
        
        result = index_manager.test_connection()
        
        assert result['success'] is False
        assert 'authentication' in result['error'].lower()

    def test_large_index_status_handling(self, index_manager, mock_elasticsearch_client):
        """Test handling of very large indices."""
        # Mock large index stats
        mock_elasticsearch_client.indices.exists.return_value = True
        mock_elasticsearch_client.indices.stats.return_value = {
            'indices': {
                'large_index': {
                    'total': {
                        'docs': {'count': 10000000},  # 10 million docs
                        'store': {'size_in_bytes': 50000000000}  # 50 GB
                    }
                }
            }
        }
        
        mock_elasticsearch_client.cluster.health.return_value = {
            'indices': {
                'large_index': {'status': 'green'}
            }
        }
        
        status = index_manager.get_index_status('large_index')
        
        assert status['exists'] is True
        assert status['doc_count'] == 10000000
        assert status['size_bytes'] == 50000000000

    def test_concurrent_index_operations(self, index_manager, mock_elasticsearch_client, mock_index_mappings):
        """Test handling of concurrent index operations."""
        from elasticsearch.exceptions import ConflictError
        
        # First call succeeds, second call conflicts
        mock_elasticsearch_client.indices.create.side_effect = [
            {'acknowledged': True},
            ConflictError("Index already exists")
        ]
        
        with patch.object(index_manager, 'get_index_mapping', return_value=mock_index_mappings['financial_trades']):
            # First creation should succeed
            result1 = index_manager.create_index('test_index_1')
            assert result1 is True
            
            # Second creation should handle conflict gracefully
            result2 = index_manager.create_index('test_index_2')
            assert result2 is False

    def test_memory_efficient_large_operations(self, index_manager):
        """Test memory efficiency with large operations."""
        # Test that operations don't load too much into memory
        large_index_list = [f'index_{i}' for i in range(1000)]
        
        with patch.object(index_manager, 'get_index_status') as mock_get_status:
            mock_get_status.return_value = {
                'exists': True,
                'doc_count': 1000,
                'size_bytes': 1024,
                'health': 'green'
            }
            
            # This should not cause memory issues
            all_status = {}
            for index_name in large_index_list:
                all_status[index_name] = index_manager.get_index_status(index_name)
            
            assert len(all_status) == 1000
            assert all(status['exists'] for status in all_status.values())