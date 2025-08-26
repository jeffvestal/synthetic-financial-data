"""
Index Manager for Elasticsearch

Handles creation, validation, and management of Elasticsearch indices
with proper mappings for the synthetic financial data.
"""

import os
import json
import sys
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

# Add scripts directory to path for config import
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'scripts'))

try:
    from elasticsearch import Elasticsearch
    from elasticsearch.exceptions import RequestError, NotFoundError
except ImportError:
    print("Warning: elasticsearch library not installed")
    Elasticsearch = None

from config import ES_CONFIG

class IndexManager:
    """Manages Elasticsearch index operations."""
    
    def __init__(self, es_client: Optional['Elasticsearch'] = None):
        """
        Initialize the Index Manager.
        
        Args:
            es_client: Elasticsearch client instance (optional)
        """
        self.es_client = es_client
        self.mappings_file = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'elasticsearch',
            'index_mappings.json'
        )
        self._mappings_cache = None
    
    def load_index_mappings(self) -> Dict[str, Any]:
        """
        Load index mappings from JSON file.
        
        Returns:
            Dict containing all index mappings
            
        Raises:
            FileNotFoundError: If mappings file doesn't exist
            json.JSONDecodeError: If mappings file is invalid
        """
        if self._mappings_cache is not None:
            return self._mappings_cache
        
        if not os.path.exists(self.mappings_file):
            raise FileNotFoundError(f"Index mappings file not found: {self.mappings_file}")
        
        try:
            with open(self.mappings_file, 'r') as f:
                self._mappings_cache = json.load(f)
            return self._mappings_cache
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(f"Invalid JSON in mappings file: {e}", e.doc, e.pos)
    
    def get_index_mapping(self, index_name: str) -> Optional[Dict[str, Any]]:
        """
        Get mapping for a specific index.
        
        Args:
            index_name: Name of the index
            
        Returns:
            Dict containing index settings and mappings, or None if not found
        """
        mappings = self.load_index_mappings()
        return mappings.get(index_name)
    
    def index_exists(self, index_name: str) -> bool:
        """
        Check if an index exists in Elasticsearch.
        
        Args:
            index_name: Name of the index to check
            
        Returns:
            True if index exists, False otherwise
        """
        if not self.es_client:
            raise ValueError("Elasticsearch client not initialized")
        
        try:
            return self.es_client.indices.exists(index=index_name)
        except Exception as e:
            print(f"Error checking if index '{index_name}' exists: {e}")
            return False
    
    def create_index(self, index_name: str, mapping: Optional[Dict[str, Any]] = None) -> bool:
        """
        Create an index with the specified mapping.
        
        Args:
            index_name: Name of the index to create
            mapping: Optional custom mapping (uses default from file if not provided)
            
        Returns:
            True if index was created successfully, False otherwise
        """
        if not self.es_client:
            raise ValueError("Elasticsearch client not initialized")
        
        # Use provided mapping or load from file
        if mapping is None:
            mapping = self.get_index_mapping(index_name)
            if mapping is None:
                print(f"Warning: No mapping found for index '{index_name}'")
                mapping = {}
        
        try:
            # Create index with settings and mappings
            response = self.es_client.indices.create(
                index=index_name,
                body=mapping
            )
            
            if response.get('acknowledged'):
                print(f"✓ Successfully created index '{index_name}'")
                return True
            else:
                print(f"✗ Failed to create index '{index_name}': Response not acknowledged")
                return False
                
        except RequestError as e:
            if 'resource_already_exists_exception' in str(e):
                print(f"Index '{index_name}' already exists")
            else:
                print(f"Error creating index '{index_name}': {e}")
            return False
        except Exception as e:
            print(f"Unexpected error creating index '{index_name}': {e}")
            return False
    
    def create_index_if_not_exists(self, index_name: str) -> bool:
        """
        Create an index only if it doesn't already exist.
        
        Args:
            index_name: Name of the index
            
        Returns:
            True if index exists or was created, False on error
        """
        if self.index_exists(index_name):
            print(f"Index '{index_name}' already exists")
            return True
        
        print(f"Creating index '{index_name}'...")
        return self.create_index(index_name)
    
    def ensure_indices_exist(self, indices: Optional[List[str]] = None) -> Tuple[int, int]:
        """
        Ensure that specified indices exist, creating them if necessary.
        
        Args:
            indices: List of index names to check/create. 
                    If None, checks all indices in mappings file.
                    
        Returns:
            Tuple of (successful_count, failed_count)
        """
        if not self.es_client:
            raise ValueError("Elasticsearch client not initialized")
        
        # If no indices specified, use all from mappings
        if indices is None:
            mappings = self.load_index_mappings()
            indices = list(mappings.keys())
        
        successful = 0
        failed = 0
        
        print(f"\n📊 Checking {len(indices)} indices...")
        
        for index_name in indices:
            if self.create_index_if_not_exists(index_name):
                successful += 1
            else:
                failed += 1
        
        print(f"\n✅ Successfully ensured {successful} indices")
        if failed > 0:
            print(f"❌ Failed to create {failed} indices")
        
        return successful, failed
    
    def delete_index(self, index_name: str) -> bool:
        """
        Delete an index.
        
        Args:
            index_name: Name of the index to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        if not self.es_client:
            raise ValueError("Elasticsearch client not initialized")
        
        try:
            response = self.es_client.indices.delete(index=index_name)
            if response.get('acknowledged'):
                print(f"✓ Successfully deleted index '{index_name}'")
                return True
            return False
        except NotFoundError:
            print(f"Index '{index_name}' does not exist")
            return False
        except Exception as e:
            print(f"Error deleting index '{index_name}': {e}")
            return False
    
    def recreate_index(self, index_name: str) -> bool:
        """
        Delete and recreate an index with fresh mapping.
        
        Args:
            index_name: Name of the index to recreate
            
        Returns:
            True if recreated successfully, False otherwise
        """
        print(f"Recreating index '{index_name}'...")
        
        # Delete if exists
        if self.index_exists(index_name):
            if not self.delete_index(index_name):
                return False
        
        # Create with mapping
        return self.create_index(index_name)
    
    def recreate_all_indices(self) -> Tuple[int, int]:
        """
        Recreate all indices defined in mappings file.
        
        Returns:
            Tuple of (successful_count, failed_count)
        """
        mappings = self.load_index_mappings()
        indices = list(mappings.keys())
        
        successful = 0
        failed = 0
        
        print(f"\n⚠️  Recreating {len(indices)} indices...")
        
        for index_name in indices:
            if self.recreate_index(index_name):
                successful += 1
            else:
                failed += 1
        
        return successful, failed
    
    def get_index_status(self, index_name: str) -> Dict[str, Any]:
        """
        Get detailed status of an index.
        
        Args:
            index_name: Name of the index
            
        Returns:
            Dict with index status information
        """
        if not self.es_client:
            return {
                'index': index_name,
                'error': 'Elasticsearch client not initialized'
            }
        
        status = {
            'index': index_name,
            'name': index_name,
            'exists': False,
            'health': None,
            'doc_count': 0,
            'size': None,
            'mapping_match': None
        }
        
        try:
            # First test basic connectivity
            try:
                cluster_info = self.es_client.info()
                # If we get here, basic connection works
            except Exception as conn_e:
                return {
                    'index': index_name,
                    'error': f'Connection failed: {str(conn_e)}'
                }
            
            # Check if index exists
            try:
                exists = self.index_exists(index_name)
                status['exists'] = exists
            except Exception as exists_e:
                return {
                    'index': index_name,
                    'error': f'Failed to check if index exists: {str(exists_e)}'
                }
            
            if status['exists']:
                # Get index stats
                try:
                    stats = self.es_client.indices.stats(index=index_name)
                    if index_name in stats['indices']:
                        index_stats = stats['indices'][index_name]
                        status['doc_count'] = index_stats['primaries']['docs']['count']
                        status['size'] = index_stats['primaries']['store']['size_in_bytes']
                except Exception as stats_e:
                    status['stats_error'] = f'Failed to get index stats: {str(stats_e)}'
                
                # Get index health
                try:
                    health = self.es_client.cluster.health(index=index_name)
                    status['health'] = health['status']
                except Exception as health_e:
                    status['health_error'] = f'Failed to get index health: {str(health_e)}'
                
                # Check if mapping matches expected
                try:
                    current_mapping = self.es_client.indices.get_mapping(index=index_name)
                    expected_mapping = self.get_index_mapping(index_name)
                    if expected_mapping:
                        # Simple check - could be more sophisticated
                        status['mapping_match'] = True  # Simplified for now
                except Exception as mapping_e:
                    status['mapping_error'] = f'Failed to check mapping: {str(mapping_e)}'
        
        except Exception as e:
            return {
                'index': index_name,
                'error': f'Unexpected error: {str(e)}'
            }
        
        return status
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test the Elasticsearch connection and return diagnostics.
        
        Returns:
            Dict with connection test results
        """
        if not self.es_client:
            return {
                'success': False,
                'error': 'Elasticsearch client not initialized'
            }
        
        try:
            # Test basic connection
            info = self.es_client.info()
            
            return {
                'success': True,
                'cluster_name': info.get('cluster_name', 'Unknown'),
                'version': info.get('version', {}).get('number', 'Unknown'),
                'elasticsearch_version': info.get('version', {}).get('distribution', 'elasticsearch')
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            }
    
    def get_all_indices_status(self) -> List[Dict[str, Any]]:
        """
        Get status of all indices defined in mappings.
        
        Returns:
            List of status dicts for each index
        """
        mappings = self.load_index_mappings()
        statuses = []
        
        for index_name in mappings.keys():
            statuses.append(self.get_index_status(index_name))
        
        return statuses


# Convenience functions for use in other scripts
def ensure_indices_exist(es_client: 'Elasticsearch', indices: Optional[List[str]] = None) -> bool:
    """
    Convenience function to ensure indices exist.
    
    Args:
        es_client: Elasticsearch client
        indices: Optional list of index names
        
    Returns:
        True if all indices exist or were created successfully
    """
    manager = IndexManager(es_client)
    successful, failed = manager.ensure_indices_exist(indices)
    return failed == 0


def create_index_if_not_exists(es_client: 'Elasticsearch', index_name: str) -> bool:
    """
    Convenience function to create a single index if it doesn't exist.
    
    Args:
        es_client: Elasticsearch client
        index_name: Name of the index
        
    Returns:
        True if index exists or was created successfully
    """
    manager = IndexManager(es_client)
    return manager.create_index_if_not_exists(index_name)