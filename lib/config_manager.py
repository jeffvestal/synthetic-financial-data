"""
Configuration Manager for Synthetic Financial Data Generator

Handles configuration loading, validation, presets, and environment management.
"""

import os
import json
import sys
from typing import Dict, Any, List, Tuple, Optional

# Add scripts to path to import config
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'scripts'))

try:
    from config import (
        ES_CONFIG, GEMINI_CONFIG, GENERATION_SETTINGS, 
        validate_config as validate_base_config,
        FILE_PATHS
    )
except ImportError as e:
    # Handle gracefully if config can't be loaded (e.g., missing dependencies)
    print(f"Warning: Could not load base config: {e}")
    ES_CONFIG = {}
    GEMINI_CONFIG = {}
    GENERATION_SETTINGS = {}
    FILE_PATHS = {}

class ConfigManager:
    """Manages configuration, presets, and validation."""
    
    def __init__(self):
        self.presets_file = "config_presets.json"
        self.current_overrides = {}
        
        # Built-in presets
        self.built_in_presets = {
            "small_demo": {
                "name": "small_demo",
                "description": "Small dataset for quick demos",
                "accounts": {"num_accounts": 100},
                "news": {"num_general_articles": 50, "num_specific_assets_for_news": 10},
                "reports": {"num_thematic_reports": 20, "num_specific_assets_for_reports": 5}
            },
            "full_dataset": {
                "name": "full_dataset", 
                "description": "Complete dataset with all default values",
                "accounts": {"num_accounts": 7000},
                "news": {"num_general_articles": 500, "num_specific_assets_for_news": 50},
                "reports": {"num_thematic_reports": 100, "num_specific_assets_for_reports": 20}
            },
            "test_mode": {
                "name": "test_mode",
                "description": "Minimal data for testing (no ES ingestion)",
                "accounts": {"num_accounts": 10},
                "news": {"num_general_articles": 5, "num_specific_assets_for_news": 3},
                "reports": {"num_thematic_reports": 3, "num_specific_assets_for_reports": 2},
                "ingest_elasticsearch": False
            }
        }
    
    def get_current_config(self) -> Dict[str, Any]:
        """Get current effective configuration including overrides."""
        config = {
            # Elasticsearch settings
            "es_endpoint": ES_CONFIG.get('endpoint_url', 'Not configured'),
            "es_api_key_set": bool(ES_CONFIG.get('api_key')),
            
            # Gemini settings
            "gemini_model": GEMINI_CONFIG.get('model_name', 'Not configured'),
            "gemini_api_key_set": bool(GEMINI_CONFIG.get('api_key')),
            
            # Generation settings
            "num_accounts": GENERATION_SETTINGS.get('accounts', {}).get('num_accounts', 0),
            "num_news_articles": GENERATION_SETTINGS.get('news', {}).get('num_general_articles', 0),
            "num_reports": GENERATION_SETTINGS.get('reports', {}).get('num_thematic_reports', 0),
            
            # File paths status
            "generated_data_dir": os.path.exists('generated_data'),
            "prompts_dir": os.path.exists('prompts'),
            "scripts_dir": os.path.exists('scripts'),
        }
        
        # Apply current overrides
        config.update(self.current_overrides)
        
        return config
    
    def validate_config(self) -> Tuple[bool, List[str]]:
        """Validate current configuration."""
        errors = []
        
        # Check environment variables
        if not os.getenv("GEMINI_API_KEY"):
            errors.append("GEMINI_API_KEY environment variable not set")
        
        # Check if ES is configured for ingestion
        if not os.getenv("ES_API_KEY") and not os.getenv("ES_ENDPOINT_URL"):
            errors.append("Elasticsearch not configured (ES_API_KEY and ES_ENDPOINT_URL not set)")
        
        # Check required directories
        required_dirs = ['scripts', 'prompts']
        for directory in required_dirs:
            if not os.path.exists(directory):
                errors.append(f"Required directory '{directory}' not found")
        
        # Check prompt files if prompts directory exists
        if os.path.exists('prompts'):
            required_prompts = [
                'general_market_news.txt',
                'specific_news.txt', 
                'specific_report.txt',
                'thematic_sector_report.txt'
            ]
            for prompt in required_prompts:
                if not os.path.exists(os.path.join('prompts', prompt)):
                    errors.append(f"Required prompt file '{prompt}' not found")
        
        # Try to validate using base config if available
        try:
            base_valid, base_errors = validate_base_config()
            if not base_valid:
                errors.extend(base_errors)
        except Exception as e:
            errors.append(f"Could not validate base config: {e}")
        
        return len(errors) == 0, errors
    
    def save_preset(self, name: str, config: Optional[Dict[str, Any]] = None):
        """Save current configuration as a preset."""
        if config is None:
            config = self.current_overrides.copy()
        
        presets = self._load_presets()
        
        preset = {
            "name": name,
            "description": f"Custom preset created by user",
            "config": config,
            "created_at": self._get_timestamp()
        }
        
        presets[name] = preset
        self._save_presets(presets)
    
    def load_preset(self, name: str) -> bool:
        """Load a preset configuration."""
        # Check built-in presets first
        if name in self.built_in_presets:
            preset = self.built_in_presets[name]
            self.current_overrides = preset.copy()
            self.current_overrides.pop('name', None)
            self.current_overrides.pop('description', None)
            return True
        
        # Check user presets
        presets = self._load_presets()
        if name in presets:
            preset = presets[name]
            self.current_overrides = preset.get('config', {})
            return True
        
        return False
    
    def list_presets(self) -> List[Dict[str, Any]]:
        """List all available presets."""
        presets = []
        
        # Add built-in presets
        for preset in self.built_in_presets.values():
            presets.append({
                'name': preset['name'],
                'description': preset['description'],
                'type': 'built-in'
            })
        
        # Add user presets
        user_presets = self._load_presets()
        for preset in user_presets.values():
            presets.append({
                'name': preset['name'],
                'description': preset.get('description', 'User preset'),
                'type': 'user',
                'created_at': preset.get('created_at', 'Unknown')
            })
        
        return presets
    
    def delete_preset(self, name: str) -> bool:
        """Delete a user preset."""
        if name in self.built_in_presets:
            return False  # Cannot delete built-in presets
        
        presets = self._load_presets()
        if name in presets:
            del presets[name]
            self._save_presets(presets)
            return True
        
        return False
    
    def set_override(self, key: str, value: Any):
        """Set a configuration override."""
        self.current_overrides[key] = value
    
    def clear_overrides(self):
        """Clear all configuration overrides."""
        self.current_overrides.clear()
    
    def update_config(self, path: List[str], value: Any):
        """Update a nested configuration value using a path list."""
        # Create the override key from the path
        key = '.'.join(path)
        self.current_overrides[key] = value
        
        # Also update the actual config in memory for immediate reflection
        config = self.get_config()
        target = config
        
        # Navigate to the parent of the target key
        for key_part in path[:-1]:
            if key_part not in target:
                target[key_part] = {}
            target = target[key_part]
        
        # Set the final value
        target[path[-1]] = value
    
    def get_elasticsearch_status(self) -> Dict[str, Any]:
        """Check Elasticsearch connection status."""
        status = {
            'configured': bool(os.getenv('ES_API_KEY') and os.getenv('ES_ENDPOINT_URL')),
            'endpoint': os.getenv('ES_ENDPOINT_URL', 'Not configured'),
            'api_key_set': bool(os.getenv('ES_API_KEY')),
            'connection_test': False,
            'error': None,
            'cluster_info': None
        }
        
        # Perform actual connection test if configured
        if status['configured']:
            try:
                from elasticsearch import Elasticsearch
                
                # Create ES client for testing
                es_client = Elasticsearch(
                    [status['endpoint']],
                    api_key=os.getenv('ES_API_KEY'),
                    request_timeout=10,  # Short timeout for status check
                    verify_certs=False
                )
                
                # Test connection with cluster info
                cluster_info = es_client.info()
                status['connection_test'] = True
                status['cluster_info'] = {
                    'cluster_name': cluster_info.get('cluster_name', 'Unknown'),
                    'version': cluster_info.get('version', {}).get('number', 'Unknown'),
                    'lucene_version': cluster_info.get('version', {}).get('lucene_version', 'Unknown')
                }
                
                # Test cluster health
                try:
                    health = es_client.cluster.health()
                    status['cluster_info']['status'] = health.get('status', 'unknown')
                    status['cluster_info']['number_of_nodes'] = health.get('number_of_nodes', 0)
                except Exception:
                    # Health check failed, but basic connection worked
                    status['cluster_info']['status'] = 'unknown'
                    
            except ImportError:
                status['error'] = 'Elasticsearch Python client not installed (pip install elasticsearch)'
            except Exception as e:
                status['error'] = f'Connection failed: {str(e)}'
                # Try to provide more specific error messages
                error_str = str(e).lower()
                if 'connection refused' in error_str:
                    status['error'] = 'Connection refused - is Elasticsearch running?'
                elif 'unauthorized' in error_str or 'authentication' in error_str:
                    status['error'] = 'Authentication failed - check ES_API_KEY'
                elif 'timeout' in error_str:
                    status['error'] = 'Connection timeout - check endpoint URL and network'
                elif 'ssl' in error_str or 'certificate' in error_str:
                    status['error'] = 'SSL/Certificate error - check verify_certs setting'
        
        return status
    
    def get_generation_stats(self) -> Dict[str, Any]:
        """Get statistics about generated data."""
        stats = {
            'data_directory_exists': os.path.exists('generated_data'),
            'files': {}
        }
        
        if stats['data_directory_exists']:
            data_files = [
                'generated_accounts.jsonl',
                'generated_holdings.jsonl', 
                'generated_asset_details.jsonl',
                'generated_news.jsonl',
                'generated_reports.jsonl',
                'generated_controlled_news.jsonl',
                'generated_controlled_reports.jsonl'
            ]
            
            for filename in data_files:
                filepath = os.path.join('generated_data', filename)
                if os.path.exists(filepath):
                    stats['files'][filename] = {
                        'exists': True,
                        'size': os.path.getsize(filepath),
                        'lines': self._count_lines(filepath)
                    }
                else:
                    stats['files'][filename] = {'exists': False}
        
        return stats
    
    def _load_presets(self) -> Dict[str, Any]:
        """Load user presets from file."""
        if os.path.exists(self.presets_file):
            try:
                with open(self.presets_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}
    
    def _save_presets(self, presets: Dict[str, Any]):
        """Save presets to file."""
        try:
            with open(self.presets_file, 'w') as f:
                json.dump(presets, f, indent=2)
        except IOError as e:
            print(f"Warning: Could not save presets: {e}")
    
    def _get_timestamp(self) -> str:
        """Get current timestamp string."""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def _count_lines(self, filepath: str) -> int:
        """Count lines in a file."""
        try:
            with open(filepath, 'r') as f:
                return sum(1 for _ in f)
        except IOError:
            return 0