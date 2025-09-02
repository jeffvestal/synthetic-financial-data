"""
Unit Tests for setup.py

Tests the enhanced setup.py functionality including virtual environment creation,
dependency installation, and credential configuration.
"""

import pytest
import os
import sys
import tempfile
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch, mock_open, MagicMock
from io import StringIO

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import setup


@pytest.mark.unit
class TestSetupPy:
    """Test setup.py functionality."""

    def test_run_command_success(self):
        """Test successful command execution."""
        with patch('setup.subprocess.run') as mock_run:
            mock_result = Mock()
            mock_result.stdout = "Command output"
            mock_result.stderr = ""
            mock_run.return_value = mock_result
            
            result = setup.run_command("echo test", "Testing command")
            
            assert result is True
            mock_run.assert_called_once_with(
                "echo test", 
                shell=True, 
                check=True, 
                capture_output=True, 
                text=True
            )

    def test_run_command_failure(self):
        """Test command execution failure handling."""
        with patch('setup.subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(
                1, "failing_command", stderr="Error message"
            )
            
            result = setup.run_command("failing_command", "Failing test")
            
            assert result is False

    def test_create_venv_new_environment(self):
        """Test creating new virtual environment."""
        with patch('setup.Path') as mock_path, \
             patch('setup.venv.create') as mock_venv_create:
            
            # Mock venv directory doesn't exist
            mock_venv_path = Mock()
            mock_venv_path.exists.return_value = False
            mock_path.return_value = mock_venv_path
            
            result = setup.create_venv()
            
            assert result is True
            mock_venv_create.assert_called_once_with("venv", with_pip=True)

    def test_create_venv_existing_environment(self):
        """Test handling of existing virtual environment."""
        with patch('setup.Path') as mock_path:
            # Mock venv directory exists
            mock_venv_path = Mock()
            mock_venv_path.exists.return_value = True
            mock_path.return_value = mock_venv_path
            
            result = setup.create_venv()
            
            assert result is True

    def test_create_venv_creation_failure(self):
        """Test virtual environment creation failure."""
        with patch('setup.Path') as mock_path, \
             patch('setup.venv.create') as mock_venv_create:
            
            # Mock venv directory doesn't exist
            mock_venv_path = Mock()
            mock_venv_path.exists.return_value = False
            mock_path.return_value = mock_venv_path
            
            # Mock creation failure
            mock_venv_create.side_effect = Exception("Creation failed")
            
            result = setup.create_venv()
            
            assert result is False

    @pytest.mark.parametrize("platform,expected_command", [
        ("win32", "venv\\Scripts\\activate"),
        ("darwin", "source venv/bin/activate"),
        ("linux", "source venv/bin/activate"),
    ])
    def test_get_activation_command(self, platform, expected_command):
        """Test activation command generation for different platforms."""
        with patch('setup.sys.platform', platform):
            result = setup.get_activation_command()
            assert result == expected_command

    @pytest.mark.parametrize("platform,expected_executable", [
        ("win32", "venv\\Scripts\\python"),
        ("darwin", "venv/bin/python"),
        ("linux", "venv/bin/python"),
    ])
    def test_get_python_executable(self, platform, expected_executable):
        """Test Python executable path generation for different platforms."""
        with patch('setup.sys.platform', platform):
            result = setup.get_python_executable()
            assert result == expected_executable

    def test_install_requirements_success(self):
        """Test successful requirements installation."""
        with patch('setup.get_python_executable', return_value='python'), \
             patch('setup.Path') as mock_path, \
             patch('setup.run_command', return_value=True) as mock_run_command:
            
            # Mock requirements.txt exists
            mock_req_path = Mock()
            mock_req_path.exists.return_value = True
            mock_path.return_value = mock_req_path
            
            result = setup.install_requirements()
            
            assert result is True
            mock_run_command.assert_called_once_with(
                "python -m pip install -r requirements.txt",
                "Installing requirements"
            )

    def test_install_requirements_missing_file(self):
        """Test requirements installation with missing requirements.txt."""
        with patch('setup.Path') as mock_path:
            # Mock requirements.txt doesn't exist
            mock_req_path = Mock()
            mock_req_path.exists.return_value = False
            mock_path.return_value = mock_req_path
            
            result = setup.install_requirements()
            
            assert result is False

    def test_upgrade_pip(self):
        """Test pip upgrade functionality."""
        with patch('setup.get_python_executable', return_value='python'), \
             patch('setup.run_command', return_value=True) as mock_run_command:
            
            result = setup.upgrade_pip()
            
            assert result is True
            mock_run_command.assert_called_once_with(
                "python -m pip install --upgrade pip",
                "Upgrading pip"
            )


@pytest.mark.unit
class TestCredentialConfiguration:
    """Test credential configuration functionality."""

    @patch('builtins.input')
    def test_prompt_for_credentials_decline(self, mock_input):
        """Test declining credential configuration."""
        mock_input.return_value = 'n'
        
        with patch('builtins.print') as mock_print:
            result = setup.prompt_for_credentials()
            
            assert result is None
            
            # Verify decline message was printed
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            decline_messages = [msg for msg in print_calls if 'export' in msg]
            assert len(decline_messages) >= 3  # Should show 3 export commands

    @patch('builtins.input')
    def test_prompt_for_credentials_accept_minimal(self, mock_input):
        """Test accepting credential configuration with minimal input."""
        # Mock user inputs: yes to configure, minimal inputs
        mock_input.side_effect = [
            'y',           # Configure credentials
            '',            # Default ES URL
            '',            # Skip ES API key  
            ''             # Skip Gemini key
        ]
        
        with patch('setup.create_env_file') as mock_create_env:
            mock_create_env.return_value = Path('/tmp/test.env')
            
            result = setup.prompt_for_credentials()
            
            expected_credentials = {'ES_ENDPOINT_URL': 'https://localhost:9200'}
            mock_create_env.assert_called_once_with(expected_credentials)

    @patch('builtins.input')
    def test_prompt_for_credentials_accept_full(self, mock_input):
        """Test accepting credential configuration with full input."""
        # Mock user inputs: yes to configure, full inputs
        mock_input.side_effect = [
            'y',                                    # Configure credentials
            'https://my-es-cluster:443',           # Custom ES URL
            'es_api_key_123',                      # ES API key
            'gemini_key_456'                       # Gemini key
        ]
        
        with patch('setup.create_env_file') as mock_create_env:
            mock_create_env.return_value = Path('/tmp/test.env')
            
            result = setup.prompt_for_credentials()
            
            expected_credentials = {
                'ES_ENDPOINT_URL': 'https://my-es-cluster:443',
                'ES_API_KEY': 'es_api_key_123',
                'GEMINI_API_KEY': 'gemini_key_456'
            }
            mock_create_env.assert_called_once_with(expected_credentials)

    @patch('builtins.input')
    def test_prompt_for_credentials_input_validation(self, mock_input):
        """Test input validation for credential prompts."""
        # Test invalid then valid input for yes/no question
        mock_input.side_effect = [
            'maybe',       # Invalid input
            'yes',         # Valid input  
            '',            # Default ES URL
            '',            # Skip other inputs
            ''
        ]
        
        with patch('setup.create_env_file') as mock_create_env:
            mock_create_env.return_value = Path('/tmp/test.env')
            
            result = setup.prompt_for_credentials()
            
            # Should eventually succeed with valid input
            assert result is not None

    def test_create_env_file_success(self, tmp_path):
        """Test successful .env file creation."""
        credentials = {
            'GEMINI_API_KEY': 'test_gemini_key',
            'ES_API_KEY': 'test_es_key',
            'ES_ENDPOINT_URL': 'https://test-es:443'
        }
        
        with patch('setup.Path', return_value=tmp_path / '.env'), \
             patch('setup.test_elasticsearch_connection') as mock_test_conn:
            
            result = setup.create_env_file(credentials)
            
            # Should return path-like object
            assert result is not None

    def test_create_env_file_with_es_connection_test(self):
        """Test .env file creation triggers ES connection test."""
        credentials = {
            'ES_API_KEY': 'test_key',
            'ES_ENDPOINT_URL': 'https://test:443'
        }
        
        with patch('builtins.open', mock_open()) as mock_file, \
             patch('setup.test_elasticsearch_connection') as mock_test:
            
            result = setup.create_env_file(credentials)
            
            mock_test.assert_called_once_with(
                'https://test:443', 
                'test_key'
            )

    def test_create_env_file_without_es_credentials(self):
        """Test .env file creation without ES credentials skips connection test."""
        credentials = {
            'GEMINI_API_KEY': 'test_gemini_key'
        }
        
        with patch('builtins.open', mock_open()) as mock_file, \
             patch('setup.test_elasticsearch_connection') as mock_test:
            
            result = setup.create_env_file(credentials)
            
            mock_test.assert_not_called()

    def test_create_env_file_write_error(self):
        """Test .env file creation with write error."""
        credentials = {'TEST_KEY': 'test_value'}
        
        with patch('builtins.open', side_effect=IOError("Write failed")):
            result = setup.create_env_file(credentials)
            
            assert result is None

    @patch('setup.urllib3.disable_warnings')
    @patch('setup.urllib.request.urlopen')
    def test_test_elasticsearch_connection_success(self, mock_urlopen, mock_disable_warnings):
        """Test successful Elasticsearch connection test."""
        # Mock successful HTTP response
        mock_response = Mock()
        mock_response.status = 200
        mock_urlopen.return_value = mock_response
        
        with patch('builtins.print') as mock_print:
            setup.test_elasticsearch_connection('https://test:443', 'test_key')
            
            # Should print success message
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            success_messages = [msg for msg in print_calls if 'successful' in msg]
            assert len(success_messages) >= 1

    @patch('setup.urllib3.disable_warnings')
    @patch('setup.urllib.request.urlopen')
    def test_test_elasticsearch_connection_failure(self, mock_urlopen, mock_disable_warnings):
        """Test failed Elasticsearch connection test."""
        # Mock connection failure
        mock_urlopen.side_effect = Exception("Connection failed")
        
        with patch('builtins.print') as mock_print:
            setup.test_elasticsearch_connection('https://test:443', 'test_key')
            
            # Should print warning message
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            warning_messages = [msg for msg in print_calls if 'Could not connect' in msg]
            assert len(warning_messages) >= 1


@pytest.mark.unit  
class TestNextStepsGeneration:
    """Test next steps generation functionality."""

    def test_get_enhanced_next_steps_with_env(self):
        """Test next steps generation when .env was created."""
        with patch('setup.get_activation_command', return_value='source venv/bin/activate'):
            steps = setup.get_enhanced_next_steps(env_created=True)
            
            assert isinstance(steps, list)
            assert len(steps) > 0
            
            # Should include verification and quick start steps
            steps_text = ' '.join(steps)
            assert 'python3 control.py --status' in steps_text
            assert 'python3 control.py --quick-start' in steps_text
            assert 'source venv/bin/activate' in steps_text

    def test_get_enhanced_next_steps_without_env(self):
        """Test next steps generation when no .env was created."""
        with patch('setup.get_activation_command', return_value='source venv/bin/activate'):
            steps = setup.get_enhanced_next_steps(env_created=False)
            
            assert isinstance(steps, list)
            assert len(steps) > 0
            
            # Should include credential configuration steps
            steps_text = ' '.join(steps)
            assert 'Configure credentials' in steps_text
            assert 'python3 control.py --status' in steps_text
            assert 'source venv/bin/activate' in steps_text

    def test_print_success_message_with_env(self):
        """Test success message printing with env created."""
        with patch('setup.get_enhanced_next_steps') as mock_get_steps, \
             patch('builtins.print') as mock_print:
            
            mock_get_steps.return_value = ['Step 1', 'Step 2', 'Step 3']
            
            setup.print_success_message(env_created=True)
            
            mock_get_steps.assert_called_once_with(True)
            
            # Should print success header and steps
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            success_messages = [msg for msg in print_calls if 'Setup completed' in msg]
            assert len(success_messages) >= 1

    def test_print_success_message_without_env(self):
        """Test success message printing without env created."""
        with patch('setup.get_enhanced_next_steps') as mock_get_steps, \
             patch('builtins.print') as mock_print:
            
            mock_get_steps.return_value = ['Step 1', 'Step 2']
            
            setup.print_success_message(env_created=False)
            
            mock_get_steps.assert_called_once_with(False)


@pytest.mark.unit
class TestMainFunction:
    """Test main setup function integration."""

    def test_main_success_flow(self):
        """Test successful main execution flow."""
        with patch('setup.sys.version_info', (3, 9, 0)), \
             patch('setup.create_venv', return_value=True), \
             patch('setup.upgrade_pip', return_value=True), \
             patch('setup.install_requirements', return_value=True), \
             patch('setup.prompt_for_credentials', return_value=Path('/tmp/.env')), \
             patch('setup.print_success_message') as mock_print_success:
            
            setup.main()
            
            mock_print_success.assert_called_once_with(True)

    def test_main_python_version_check_failure(self):
        """Test main with insufficient Python version."""
        with patch('setup.sys.version_info', (3, 7, 0)), \
             pytest.raises(SystemExit) as exc_info:
            
            setup.main()
            
            assert exc_info.value.code == 1

    def test_main_venv_creation_failure(self):
        """Test main with virtual environment creation failure."""
        with patch('setup.sys.version_info', (3, 9, 0)), \
             patch('setup.create_venv', return_value=False), \
             pytest.raises(SystemExit) as exc_info:
            
            setup.main()
            
            assert exc_info.value.code == 1

    def test_main_requirements_installation_failure(self):
        """Test main with requirements installation failure."""
        with patch('setup.sys.version_info', (3, 9, 0)), \
             patch('setup.create_venv', return_value=True), \
             patch('setup.upgrade_pip', return_value=True), \
             patch('setup.install_requirements', return_value=False), \
             pytest.raises(SystemExit) as exc_info:
            
            setup.main()
            
            assert exc_info.value.code == 1

    def test_main_credential_configuration_failure(self):
        """Test main with credential configuration failure."""
        with patch('setup.sys.version_info', (3, 9, 0)), \
             patch('setup.create_venv', return_value=True), \
             patch('setup.upgrade_pip', return_value=True), \
             patch('setup.install_requirements', return_value=True), \
             patch('setup.prompt_for_credentials', side_effect=Exception("Config failed")), \
             patch('setup.print_success_message') as mock_print_success:
            
            # Should handle credential error gracefully
            setup.main()
            
            # Should still print success message with env_created=False
            mock_print_success.assert_called_once_with(False)

    def test_main_keyboard_interrupt_handling(self):
        """Test main handles keyboard interrupt during credential setup."""
        with patch('setup.sys.version_info', (3, 9, 0)), \
             patch('setup.create_venv', return_value=True), \
             patch('setup.upgrade_pip', return_value=True), \
             patch('setup.install_requirements', return_value=True), \
             patch('setup.prompt_for_credentials', side_effect=KeyboardInterrupt()), \
             patch('setup.print_success_message') as mock_print_success, \
             patch('builtins.print') as mock_print:
            
            setup.main()
            
            # Should handle interrupt gracefully
            mock_print_success.assert_called_once_with(False)
            
            # Should print interrupt message
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            interrupt_messages = [msg for msg in print_calls if 'interrupted' in msg.lower()]
            assert len(interrupt_messages) >= 1