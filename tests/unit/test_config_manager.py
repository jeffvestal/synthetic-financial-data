"""
Unit Tests for Configuration Manager

Tests the configuration management functionality including settings validation,
preset management, and environment variable handling.
"""

import pytest
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

# Test the actual config manager
from lib.config_manager import ConfigManager


@pytest.mark.unit
class TestConfigManager:
    """Test ConfigManager functionality."""

    @pytest.fixture
    def config_manager(self, mock_environment):
        """Create ConfigManager instance with mocked environment."""
        return ConfigManager()

    def test_config_manager_initialization(self, config_manager):
        """Test ConfigManager initialization."""
        assert isinstance(config_manager, ConfigManager)
        assert hasattr(config_manager, 'current_config')

    def test_load_default_config(self, config_manager):
        """Test loading default configuration."""
        with patch.object(config_manager, '_load_config_from_file') as mock_load:
            mock_load.return_value = {}
            
            config = config_manager.load_default_config()
            
            assert isinstance(config, dict)
            # Should have basic required keys
            expected_keys = ['generate_accounts', 'generate_news', 'generate_reports', 'ingest_elasticsearch']
            for key in expected_keys:
                assert key in config

    def test_validate_config_valid(self, config_manager):
        """Test configuration validation with valid config."""
        valid_config = {
            'generate_accounts': True,
            'generate_news': True,
            'generate_reports': False,
            'ingest_elasticsearch': True,
            'num_accounts': 1000,
            'num_news': 100,
            'num_reports': 50
        }
        
        is_valid, errors = config_manager.validate_config(valid_config)
        
        assert is_valid is True
        assert len(errors) == 0

    def test_validate_config_invalid_types(self, config_manager):
        """Test configuration validation with invalid types."""
        invalid_config = {
            'generate_accounts': 'yes',  # Should be boolean
            'generate_news': True,
            'num_accounts': 'many',      # Should be integer
            'num_news': -10             # Should be positive
        }
        
        is_valid, errors = config_manager.validate_config(invalid_config)
        
        assert is_valid is False
        assert len(errors) > 0

    def test_validate_config_missing_required(self, config_manager):
        """Test configuration validation with missing required fields."""
        incomplete_config = {
            'generate_accounts': True,
            # Missing other required fields
        }
        
        is_valid, errors = config_manager.validate_config(incomplete_config)
        
        assert is_valid is False
        assert len(errors) > 0

    @pytest.mark.parametrize("preset_name,expected_accounts", [
        ('small_demo', 100),
        ('full_dataset', 7000),
        ('test_mode', 10)
    ])
    def test_get_preset_config(self, config_manager, preset_name, expected_accounts):
        """Test loading preset configurations."""
        preset_config = config_manager.get_preset_config(preset_name)
        
        assert isinstance(preset_config, dict)
        if 'num_accounts' in preset_config:
            assert preset_config['num_accounts'] == expected_accounts

    def test_get_preset_config_invalid_preset(self, config_manager):
        """Test loading invalid preset name."""
        preset_config = config_manager.get_preset_config('invalid_preset')
        
        # Should return empty dict or None for invalid preset
        assert preset_config in [None, {}]

    def test_save_config_to_file(self, config_manager, tmp_path):
        """Test saving configuration to file."""
        test_config = {
            'generate_accounts': True,
            'num_accounts': 500,
            'test_setting': 'test_value'
        }
        
        config_file = tmp_path / 'test_config.json'
        
        result = config_manager.save_config_to_file(test_config, str(config_file))
        
        assert result is True
        assert config_file.exists()
        
        # Verify file content
        with open(config_file, 'r') as f:
            saved_config = json.load(f)
        
        assert saved_config == test_config

    def test_save_config_to_file_error(self, config_manager):
        """Test saving configuration with file write error."""
        test_config = {'test': 'value'}
        invalid_path = '/invalid/path/config.json'
        
        result = config_manager.save_config_to_file(test_config, invalid_path)
        
        assert result is False

    def test_load_config_from_file(self, config_manager, tmp_path):
        """Test loading configuration from file."""
        test_config = {
            'generate_accounts': False,
            'num_accounts': 200,
            'custom_setting': 'custom_value'
        }
        
        config_file = tmp_path / 'test_config.json'
        with open(config_file, 'w') as f:
            json.dump(test_config, f)
        
        loaded_config = config_manager._load_config_from_file(str(config_file))
        
        assert loaded_config == test_config

    def test_load_config_from_file_missing(self, config_manager):
        """Test loading configuration from missing file."""
        missing_file = '/tmp/missing_config.json'
        
        loaded_config = config_manager._load_config_from_file(missing_file)
        
        assert loaded_config == {}

    def test_load_config_from_file_invalid_json(self, config_manager, tmp_path):
        """Test loading configuration from invalid JSON file."""
        config_file = tmp_path / 'invalid_config.json'
        with open(config_file, 'w') as f:
            f.write('invalid json content {')
        
        loaded_config = config_manager._load_config_from_file(str(config_file))
        
        assert loaded_config == {}

    def test_merge_configs(self, config_manager):
        """Test configuration merging."""
        base_config = {
            'generate_accounts': True,
            'num_accounts': 1000,
            'generate_news': True,
            'num_news': 100
        }
        
        override_config = {
            'num_accounts': 2000,  # Override
            'generate_reports': True,  # New key
            'custom_setting': 'value'  # New key
        }
        
        merged = config_manager.merge_configs(base_config, override_config)
        
        assert merged['generate_accounts'] is True  # From base
        assert merged['num_accounts'] == 2000      # Overridden
        assert merged['generate_news'] is True     # From base
        assert merged['generate_reports'] is True  # New from override
        assert merged['custom_setting'] == 'value'  # New from override

    def test_get_environment_config(self, config_manager):
        """Test extracting configuration from environment variables."""
        with patch.dict(os.environ, {
            'GEMINI_API_KEY': 'test_gemini_key',
            'ES_API_KEY': 'test_es_key',
            'ES_ENDPOINT_URL': 'https://test-es:443',
            'UPDATE_TIMESTAMPS_ON_LOAD': 'true',
            'ES_BULK_BATCH_SIZE': '500',
            'PARALLEL_BULK_WORKERS': '4'
        }):
            env_config = config_manager.get_environment_config()
            
            assert isinstance(env_config, dict)
            assert 'gemini_api_key' in env_config or 'GEMINI_API_KEY' in env_config
            assert 'es_api_key' in env_config or 'ES_API_KEY' in env_config

    def test_validate_api_keys(self, config_manager):
        """Test API key validation."""
        # Test with valid keys
        with patch.dict(os.environ, {
            'GEMINI_API_KEY': 'AIzaSyExample123',
            'ES_API_KEY': 'es_key_123'
        }):
            validation = config_manager.validate_api_keys()
            
            assert isinstance(validation, dict)
            assert 'gemini' in validation
            assert 'elasticsearch' in validation

    def test_validate_api_keys_missing(self, config_manager):
        """Test API key validation with missing keys."""
        with patch.dict(os.environ, {}, clear=True):
            validation = config_manager.validate_api_keys()
            
            assert isinstance(validation, dict)
            # Should indicate missing keys
            for service in validation.values():
                assert service.get('valid') is False

    def test_get_current_config(self, config_manager):
        """Test getting current configuration."""
        current_config = config_manager.get_current_config()
        
        assert isinstance(current_config, dict)
        # Should contain basic configuration keys
        assert len(current_config) > 0

    def test_update_current_config(self, config_manager):
        """Test updating current configuration."""
        updates = {
            'num_accounts': 500,
            'new_setting': 'new_value'
        }
        
        original_config = config_manager.get_current_config().copy()
        config_manager.update_current_config(updates)
        updated_config = config_manager.get_current_config()
        
        assert updated_config['num_accounts'] == 500
        assert updated_config['new_setting'] == 'new_value'
        
        # Other settings should be preserved
        for key, value in original_config.items():
            if key not in updates:
                assert updated_config[key] == value

    def test_reset_to_defaults(self, config_manager):
        """Test resetting configuration to defaults."""
        # Make some changes
        config_manager.update_current_config({'custom_setting': 'custom_value'})
        
        # Reset to defaults
        config_manager.reset_to_defaults()
        
        current_config = config_manager.get_current_config()
        
        # Should not contain custom setting
        assert 'custom_setting' not in current_config
        
        # Should contain default settings
        assert 'generate_accounts' in current_config

    def test_export_config(self, config_manager, tmp_path):
        """Test configuration export."""
        config_manager.update_current_config({
            'export_test': True,
            'export_value': 42
        })
        
        export_file = tmp_path / 'exported_config.json'
        
        result = config_manager.export_config(str(export_file))
        
        assert result is True
        assert export_file.exists()
        
        # Verify exported content
        with open(export_file, 'r') as f:
            exported_config = json.load(f)
        
        assert exported_config['export_test'] is True
        assert exported_config['export_value'] == 42

    def test_import_config(self, config_manager, tmp_path):
        """Test configuration import."""
        import_config = {
            'imported_setting': True,
            'imported_value': 'test_import',
            'num_accounts': 999
        }
        
        import_file = tmp_path / 'import_config.json'
        with open(import_file, 'w') as f:
            json.dump(import_config, f)
        
        result = config_manager.import_config(str(import_file))
        
        assert result is True
        
        current_config = config_manager.get_current_config()
        assert current_config['imported_setting'] is True
        assert current_config['imported_value'] == 'test_import'
        assert current_config['num_accounts'] == 999

    def test_import_config_with_validation(self, config_manager, tmp_path):
        """Test configuration import with validation."""
        invalid_config = {
            'num_accounts': 'invalid_number',  # Invalid type
            'generate_accounts': 'maybe'       # Invalid boolean
        }
        
        import_file = tmp_path / 'invalid_config.json'
        with open(import_file, 'w') as f:
            json.dump(invalid_config, f)
        
        result = config_manager.import_config(str(import_file), validate=True)
        
        # Should fail validation
        assert result is False

    def test_config_history_tracking(self, config_manager):
        """Test configuration history tracking."""
        # Make several changes
        config_manager.update_current_config({'step1': 'value1'})
        config_manager.update_current_config({'step2': 'value2'})
        config_manager.update_current_config({'step3': 'value3'})
        
        # Check if history is tracked (if implemented)
        if hasattr(config_manager, 'get_config_history'):
            history = config_manager.get_config_history()
            assert isinstance(history, list)
            assert len(history) >= 3

    def test_config_backup_restore(self, config_manager):
        """Test configuration backup and restore functionality."""
        # Set initial config
        initial_config = {'backup_test': 'initial_value'}
        config_manager.update_current_config(initial_config)
        
        # Create backup (if method exists)
        if hasattr(config_manager, 'backup_config'):
            backup_id = config_manager.backup_config('test_backup')
            assert backup_id is not None
            
            # Change config
            config_manager.update_current_config({'backup_test': 'changed_value'})
            
            # Restore backup
            result = config_manager.restore_config(backup_id)
            assert result is True
            
            # Verify restoration
            current_config = config_manager.get_current_config()
            assert current_config['backup_test'] == 'initial_value'


@pytest.mark.unit
class TestConfigValidation:
    """Test configuration validation functionality."""

    @pytest.fixture
    def config_manager(self):
        return ConfigManager()

    @pytest.mark.parametrize("config,expected_valid", [
        # Valid configurations
        ({
            'generate_accounts': True,
            'generate_news': False,
            'num_accounts': 100,
            'ingest_elasticsearch': True
        }, True),
        
        # Invalid type configurations
        ({
            'generate_accounts': 'yes',  # Should be boolean
            'num_accounts': 100
        }, False),
        
        # Invalid range configurations
        ({
            'generate_accounts': True,
            'num_accounts': -10  # Should be positive
        }, False),
        
        # Missing required configurations
        ({
            'generate_accounts': True
            # Missing other required fields
        }, False)
    ])
    def test_config_validation_cases(self, config_manager, config, expected_valid):
        """Test various configuration validation scenarios."""
        is_valid, errors = config_manager.validate_config(config)
        
        assert is_valid == expected_valid
        if not expected_valid:
            assert len(errors) > 0

    def test_validation_error_messages(self, config_manager):
        """Test that validation errors provide helpful messages."""
        invalid_config = {
            'generate_accounts': 'invalid',
            'num_accounts': -5,
            'num_news': 'not_a_number'
        }
        
        is_valid, errors = config_manager.validate_config(invalid_config)
        
        assert is_valid is False
        assert len(errors) >= 3
        
        # Check that error messages are descriptive
        error_text = ' '.join(errors)
        assert 'boolean' in error_text.lower() or 'true' in error_text.lower()
        assert 'positive' in error_text.lower() or 'greater' in error_text.lower()
        assert 'number' in error_text.lower() or 'integer' in error_text.lower()


@pytest.mark.unit 
class TestPresetManagement:
    """Test configuration preset management."""

    @pytest.fixture
    def config_manager(self):
        return ConfigManager()

    def test_available_presets(self, config_manager):
        """Test getting available presets."""
        presets = config_manager.get_available_presets()
        
        assert isinstance(presets, list)
        assert len(presets) >= 3  # Should have at least small_demo, full_dataset, test_mode
        
        # Check for expected presets
        preset_names = [p['name'] if isinstance(p, dict) else p for p in presets]
        expected_presets = ['small_demo', 'full_dataset', 'test_mode']
        
        for preset in expected_presets:
            assert preset in preset_names

    def test_preset_descriptions(self, config_manager):
        """Test that presets have descriptions."""
        presets = config_manager.get_available_presets()
        
        for preset in presets:
            if isinstance(preset, dict):
                assert 'name' in preset
                assert 'description' in preset
                assert len(preset['description']) > 0

    def test_apply_preset(self, config_manager):
        """Test applying a preset configuration."""
        # Apply small demo preset
        result = config_manager.apply_preset('small_demo')
        
        assert result is True
        
        current_config = config_manager.get_current_config()
        
        # Should have settings appropriate for small demo
        if 'num_accounts' in current_config:
            assert current_config['num_accounts'] <= 1000  # Small number for demo

    def test_apply_invalid_preset(self, config_manager):
        """Test applying invalid preset name."""
        result = config_manager.apply_preset('nonexistent_preset')
        
        assert result is False