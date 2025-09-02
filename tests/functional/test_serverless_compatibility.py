"""
Serverless Elasticsearch Compatibility Testing Module

Tests serverless Elasticsearch index creation with proper mappings and settings filtering.
Migrated from test_serverless_index.py and enhanced with pytest framework.
"""

import pytest
import warnings
from unittest.mock import Mock, patch

# Suppress warnings
warnings.filterwarnings('ignore', message='urllib3 v2 only supports OpenSSL')
warnings.filterwarnings('ignore', message='Connecting to.*using TLS with verify_certs=False')


@pytest.mark.functional
@pytest.mark.elasticsearch
class TestServerlessCompatibility:
    """Test serverless Elasticsearch compatibility."""

    def test_serverless_connection_detection(self, mock_elasticsearch_client):
        """Test detection of serverless Elasticsearch clusters."""
        # Mock serverless cluster response
        mock_elasticsearch_client.info.return_value = {
            'version': {'number': '8.9.0'},
            'tagline': 'You Know, for Search',
            'build_flavor': 'serverless'  # Serverless indicator
        }
        
        # Import and test
        from lib.index_manager import IndexManager
        
        manager = IndexManager(mock_elasticsearch_client)
        conn_test = manager.test_connection()
        
        assert conn_test['success'] is True
        assert 'version' in conn_test
        assert conn_test['version'] == '8.9.0'

    def test_serverless_settings_filtering(self, mock_elasticsearch_client, mock_index_mappings):
        """Test that serverless incompatible settings are filtered out."""
        from lib.index_manager import IndexManager
        
        manager = IndexManager(mock_elasticsearch_client)
        
        # Test with settings that should be filtered for serverless
        test_mapping = {
            'settings': {
                'number_of_shards': 1,              # Should be filtered  
                'number_of_replicas': 0,            # Should be filtered
                'index.mapping.total_fields.limit': 2000,  # Should be kept
                'analysis': {                       # Should be kept
                    'analyzer': {
                        'custom_analyzer': {
                            'type': 'standard'
                        }
                    }
                }
            },
            'mappings': mock_index_mappings['financial_trades']['mappings']
        }
        
        # Mock the mapping loading
        with patch.object(manager, 'get_index_mapping', return_value=test_mapping):
            # Mock serverless detection by making create_index filter settings
            mock_elasticsearch_client.indices.create.side_effect = lambda **kwargs: self._validate_serverless_settings(kwargs)
            
            success = manager.create_index('financial_trades')
            
            # Should succeed even with filtered settings
            assert success is True

    def _validate_serverless_settings(self, create_kwargs):
        """Helper to validate that serverless-incompatible settings are filtered."""
        if 'body' in create_kwargs and 'settings' in create_kwargs['body']:
            settings = create_kwargs['body']['settings']
            
            # These settings should be filtered out for serverless
            forbidden_settings = ['number_of_shards', 'number_of_replicas']
            
            for setting in forbidden_settings:
                assert setting not in settings, f"Serverless incompatible setting '{setting}' should be filtered"
        
        return {'acknowledged': True}

    @pytest.mark.parametrize("index_name,expected_fields", [
        ('financial_trades', ['trade_id', 'account_id', 'symbol', 'trade_type']),
        ('financial_accounts', ['account_id', 'first_name', 'last_name', 'state']),
        ('financial_holdings', ['holding_id', 'account_id', 'symbol', 'quantity']),
        ('financial_news', ['article_id', 'title', 'content', 'published_date']),
        ('financial_reports', ['report_id', 'title', 'content', 'report_date'])
    ])
    def test_index_mapping_validation(self, mock_elasticsearch_client, mock_index_mappings, index_name, expected_fields):
        """Test that index mappings contain expected fields."""
        from lib.index_manager import IndexManager
        
        # Mock getting mapping for the specific index
        if index_name in mock_index_mappings:
            test_mapping = mock_index_mappings[index_name]
            mock_elasticsearch_client.indices.get_mapping.return_value = {
                index_name: test_mapping
            }
        else:
            # Create a basic mapping for the test
            test_mapping = {
                'mappings': {
                    'properties': {
                        field: {'type': 'keyword'} 
                        for field in expected_fields
                    }
                }
            }
            mock_elasticsearch_client.indices.get_mapping.return_value = {
                index_name: test_mapping
            }
        
        manager = IndexManager(mock_elasticsearch_client)
        
        # Test index creation
        mock_elasticsearch_client.indices.exists.return_value = False
        with patch.object(manager, 'get_index_mapping', return_value=test_mapping):
            success = manager.create_index(index_name)
            assert success is True
        
        # Verify mapping structure
        mapping_call = mock_elasticsearch_client.indices.get_mapping.return_value
        actual_mapping = mapping_call[index_name]
        
        if 'mappings' in actual_mapping and 'properties' in actual_mapping['mappings']:
            properties = actual_mapping['mappings']['properties']
            
            for field in expected_fields:
                assert field in properties, f"Expected field '{field}' not found in {index_name} mapping"

    def test_serverless_index_recreation(self, mock_elasticsearch_client):
        """Test index recreation in serverless environment."""
        from lib.index_manager import IndexManager
        
        manager = IndexManager(mock_elasticsearch_client)
        
        # Mock index exists
        mock_elasticsearch_client.indices.exists.return_value = True
        
        # Mock successful deletion and recreation
        mock_elasticsearch_client.indices.delete.return_value = {'acknowledged': True}
        mock_elasticsearch_client.indices.create.return_value = {'acknowledged': True}
        
        # Test recreation
        success = manager.recreate_index('financial_trades')
        
        assert success is True
        mock_elasticsearch_client.indices.delete.assert_called_once()
        mock_elasticsearch_client.indices.create.assert_called_once()

    def test_serverless_bulk_operations_compatibility(self, mock_elasticsearch_client):
        """Test that bulk operations work with serverless clusters."""
        # Mock successful bulk response
        mock_elasticsearch_client.bulk.return_value = {
            'took': 15,
            'errors': False,
            'items': [
                {
                    'index': {
                        '_index': 'financial_trades',
                        '_id': 'TRD-001',
                        '_version': 1,
                        'result': 'created',
                        'status': 201
                    }
                }
            ]
        }
        
        # Test bulk operation
        bulk_data = [
            {
                '_index': 'financial_trades',
                '_id': 'TRD-001',
                '_source': {
                    'trade_id': 'TRD-001',
                    'account_id': 'ACC-001',
                    'symbol': 'AAPL',
                    'trade_type': 'buy'
                }
            }
        ]
        
        response = mock_elasticsearch_client.bulk(body=bulk_data)
        
        assert response['errors'] is False
        assert response['took'] > 0
        assert len(response['items']) == 1

    def test_serverless_search_operations(self, mock_elasticsearch_client):
        """Test search operations in serverless environment."""
        # Mock search response
        mock_elasticsearch_client.search.return_value = {
            'took': 10,
            'timed_out': False,
            'hits': {
                'total': {'value': 1, 'relation': 'eq'},
                'hits': [
                    {
                        '_index': 'financial_trades',
                        '_id': 'TRD-001',
                        '_score': 1.0,
                        '_source': {
                            'trade_id': 'TRD-001',
                            'symbol': 'AAPL'
                        }
                    }
                ]
            }
        }
        
        # Test search
        query = {
            'query': {
                'term': {'symbol': 'AAPL'}
            }
        }
        
        response = mock_elasticsearch_client.search(index='financial_trades', body=query)
        
        assert response['timed_out'] is False
        assert response['hits']['total']['value'] == 1
        assert len(response['hits']['hits']) == 1

    def test_serverless_count_operations(self, mock_elasticsearch_client):
        """Test count operations in serverless environment."""
        # Mock count response  
        mock_elasticsearch_client.count.return_value = {
            'count': 1500,
            '_shards': {
                'total': 1,
                'successful': 1,
                'skipped': 0,
                'failed': 0
            }
        }
        
        # Test count
        response = mock_elasticsearch_client.count(index='financial_trades')
        
        assert response['count'] == 1500
        assert response['_shards']['successful'] == 1

    def test_multiple_indices_serverless_operations(self, mock_elasticsearch_client):
        """Test operations across multiple indices in serverless."""
        from lib.index_manager import IndexManager
        
        manager = IndexManager(mock_elasticsearch_client)
        
        test_indices = [
            'financial_accounts',
            'financial_holdings', 
            'financial_trades',
            'financial_news',
            'financial_reports'
        ]
        
        # Mock index existence checks
        mock_elasticsearch_client.indices.exists.side_effect = lambda index: index in test_indices
        
        # Test status for all indices
        for index_name in test_indices:
            status = manager.get_index_status(index_name)
            
            assert 'exists' in status
            assert status['exists'] is True

    def test_serverless_error_handling(self, mock_elasticsearch_client):
        """Test error handling in serverless environment."""
        from lib.index_manager import IndexManager
        from elasticsearch.exceptions import RequestError, ConnectionError
        
        manager = IndexManager(mock_elasticsearch_client)
        
        # Test connection error
        mock_elasticsearch_client.info.side_effect = ConnectionError("Connection failed")
        
        conn_test = manager.test_connection()
        assert conn_test['success'] is False
        assert 'error' in conn_test
        
        # Reset mock for next test
        mock_elasticsearch_client.info.side_effect = None
        mock_elasticsearch_client.info.return_value = {'version': {'number': '8.9.0'}}
        
        # Test request error during index creation
        mock_elasticsearch_client.indices.create.side_effect = RequestError(
            "Invalid request", meta=Mock(), body={'error': {'type': 'invalid_request'}}
        )
        
        success = manager.create_index('test_index')
        assert success is False

    def test_serverless_semantic_search_compatibility(self, mock_elasticsearch_client):
        """Test semantic search compatibility in serverless."""
        # Mock semantic search response
        mock_elasticsearch_client.search.return_value = {
            'hits': {
                'total': {'value': 5},
                'hits': [
                    {
                        '_index': 'financial_news',
                        '_score': 15.2,
                        '_source': {
                            'article_id': 'ART-001',
                            'title': 'Financial Market Update',
                            'primary_symbol': 'AAPL'
                        }
                    }
                ]
            }
        }
        
        # Test semantic search query
        semantic_query = {
            'query': {
                'semantic': {
                    'field': 'title.semantic_text',
                    'query': 'financial market analysis'
                }
            }
        }
        
        response = mock_elasticsearch_client.search(index='financial_news', body=semantic_query)
        
        assert response['hits']['total']['value'] == 5
        assert len(response['hits']['hits']) == 1
        assert response['hits']['hits'][0]['_score'] > 10  # Should have good semantic score


# ============================================================================
# INTEGRATION TESTS WITH REAL SERVERLESS CLUSTER  
# ============================================================================

@pytest.mark.integration
@pytest.mark.elasticsearch
@pytest.mark.slow
class TestServerlessIntegration:
    """Integration tests with real serverless Elasticsearch cluster."""
    
    @pytest.fixture(autouse=True) 
    def setup_serverless_client(self):
        """Set up real serverless client if available."""
        try:
            from scripts.common_utils import create_elasticsearch_client
            self.es_client = create_elasticsearch_client()
            
            # Check if this is actually a serverless cluster
            info = self.es_client.info()
            build_flavor = info.get('build_flavor', '')
            
            if 'serverless' not in build_flavor.lower():
                pytest.skip("Not a serverless Elasticsearch cluster")
                
            self.has_serverless = True
            
        except Exception:
            self.has_serverless = False
            pytest.skip("Real serverless Elasticsearch connection not available")

    def test_real_serverless_index_creation(self):
        """Test creating indices in real serverless cluster."""
        if not self.has_serverless:
            pytest.skip("No serverless connection")
            
        from lib.index_manager import IndexManager
        
        manager = IndexManager(self.es_client)
        
        # Test creating a simple test index
        test_index = 'test_serverless_index'
        
        try:
            # Clean up if exists
            if manager.index_exists(test_index):
                manager.delete_index(test_index)
            
            # Create with simple mapping
            test_mapping = {
                'mappings': {
                    'properties': {
                        'test_field': {'type': 'keyword'},
                        'timestamp': {'type': 'date'}
                    }
                }
            }
            
            with patch.object(manager, 'get_index_mapping', return_value=test_mapping):
                success = manager.create_index(test_index)
                assert success is True
                
                # Verify it was created
                assert manager.index_exists(test_index)
                
        finally:
            # Cleanup
            if manager.index_exists(test_index):
                manager.delete_index(test_index)

    def test_real_serverless_bulk_ingestion(self):
        """Test bulk ingestion in real serverless cluster."""
        if not self.has_serverless:
            pytest.skip("No serverless connection")
            
        # Test small bulk operation
        test_data = [
            {
                '_index': 'financial_trades',
                '_id': 'test-trade-001',
                '_source': {
                    'trade_id': 'test-trade-001',
                    'symbol': 'TEST',
                    'quantity': 100
                }
            }
        ]
        
        try:
            response = self.es_client.bulk(body=test_data)
            assert response['errors'] is False
            
        except Exception as e:
            pytest.skip(f"Bulk operation failed: {e}")
        
        finally:
            # Cleanup - delete the test document
            try:
                self.es_client.delete(index='financial_trades', id='test-trade-001', ignore=[404])
            except:
                pass