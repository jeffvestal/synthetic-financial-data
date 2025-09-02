"""
Shared pytest fixtures and configuration for the Synthetic Financial Data Generator test suite.

This module provides common fixtures, mock objects, and test utilities used across
all test modules in the suite.
"""

import os
import sys
import tempfile
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from unittest.mock import Mock, MagicMock
import pytest

# Add project directories to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "scripts"))
sys.path.insert(0, str(project_root / "lib"))

# Import project modules after path setup
try:
    from scripts.common_utils import create_elasticsearch_client
    from lib.config_manager import ConfigManager
    from lib.index_manager import IndexManager
except ImportError as e:
    # Handle import errors gracefully for CI environments
    print(f"Warning: Could not import project modules: {e}")


# ============================================================================
# ENVIRONMENT AND CONFIGURATION FIXTURES
# ============================================================================

@pytest.fixture
def temp_env_file():
    """Create a temporary .env file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
        f.write("# Test environment file\n")
        f.write("GEMINI_API_KEY=test_gemini_key_123\n")
        f.write("ES_API_KEY=test_es_key_456\n")
        f.write("ES_ENDPOINT_URL=https://test-elasticsearch:443\n")
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    os.unlink(temp_path)


@pytest.fixture
def temp_project_dir():
    """Create a temporary project directory structure for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create directory structure
        (temp_path / "scripts").mkdir()
        (temp_path / "lib").mkdir()
        (temp_path / "generated_data").mkdir()
        (temp_path / "elasticsearch").mkdir()
        (temp_path / "prompts").mkdir()
        
        # Create basic config files
        with open(temp_path / "requirements.txt", "w") as f:
            f.write("elasticsearch>=8.0.0\n")
        
        yield temp_path


@pytest.fixture
def mock_environment():
    """Mock environment variables for testing."""
    original_env = os.environ.copy()
    
    # Set test environment variables
    test_env = {
        'GEMINI_API_KEY': 'test_gemini_key',
        'ES_API_KEY': 'test_es_key', 
        'ES_ENDPOINT_URL': 'https://test-es:443',
        'UPDATE_TIMESTAMPS_ON_LOAD': 'false',
        'ES_BULK_BATCH_SIZE': '100',
        'PARALLEL_BULK_WORKERS': '1'
    }
    
    for key, value in test_env.items():
        os.environ[key] = value
    
    yield test_env
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


# ============================================================================
# ELASTICSEARCH MOCKING FIXTURES  
# ============================================================================

@pytest.fixture
def mock_elasticsearch_client():
    """Create a comprehensive mock Elasticsearch client."""
    mock_client = Mock()
    
    # Mock cluster info
    mock_client.info.return_value = {
        'version': {'number': '8.9.0'},
        'tagline': 'You Know, for Search'
    }
    
    # Mock index operations
    mock_client.indices = Mock()
    mock_client.indices.exists.return_value = True
    mock_client.indices.create.return_value = {'acknowledged': True}
    mock_client.indices.delete.return_value = {'acknowledged': True}
    mock_client.indices.get_mapping.return_value = {
        'financial_accounts': {
            'mappings': {
                'properties': {
                    'account_id': {'type': 'keyword'},
                    'first_name': {'type': 'keyword'},
                    'last_name': {'type': 'keyword'},
                    'total_portfolio_value': {'type': 'float'}
                }
            }
        }
    }
    
    # Mock search operations
    mock_client.search.return_value = {
        'hits': {
            'total': {'value': 100},
            'hits': [
                {
                    '_index': 'financial_accounts',
                    '_id': 'ACC00001',
                    '_score': 1.0,
                    '_source': {
                        'account_id': 'ACC00001',
                        'first_name': 'John',
                        'last_name': 'Doe',
                        'total_portfolio_value': 100000.0
                    }
                }
            ]
        }
    }
    
    # Mock bulk operations
    mock_client.bulk.return_value = {
        'took': 5,
        'errors': False,
        'items': []
    }
    
    # Mock count operations  
    mock_client.count.return_value = {'count': 1000}
    
    return mock_client


@pytest.fixture
def mock_index_mappings():
    """Provide sample index mappings for testing."""
    return {
        'financial_accounts': {
            'settings': {
                'number_of_shards': 1,
                'number_of_replicas': 0
            },
            'mappings': {
                'properties': {
                    'account_id': {'type': 'keyword'},
                    'first_name': {'type': 'keyword'},
                    'last_name': {'type': 'keyword'},
                    'account_holder_name': {'type': 'text'},
                    'state': {'type': 'keyword'},
                    'zip_code': {'type': 'keyword'},
                    'total_portfolio_value': {'type': 'float'},
                    'risk_profile': {'type': 'keyword'},
                    'last_updated': {'type': 'date'}
                }
            }
        },
        'financial_trades': {
            'settings': {
                'number_of_shards': 1,
                'number_of_replicas': 0
            },
            'mappings': {
                'properties': {
                    'trade_id': {'type': 'keyword'},
                    'account_id': {'type': 'keyword'},
                    'symbol': {'type': 'keyword'},
                    'trade_type': {'type': 'keyword'},
                    'quantity': {'type': 'float'},
                    'execution_price': {'type': 'float'},
                    'execution_timestamp': {'type': 'date'},
                    'scenario_type': {'type': 'keyword'},
                    'pump_scheme_id': {'type': 'keyword'},
                    'wash_ring_id': {'type': 'keyword'}
                }
            }
        }
    }


# ============================================================================
# GEMINI API MOCKING FIXTURES
# ============================================================================

@pytest.fixture
def mock_gemini_response():
    """Mock Gemini API response for content generation."""
    return {
        'text': """# Company Financial News

**Tesla Inc. (TSLA) Reports Strong Q3 Earnings**

Tesla Inc. reported robust third-quarter earnings today, exceeding analyst expectations with revenue of $23.4 billion, up 9% from the previous quarter. The electric vehicle manufacturer delivered 462,890 vehicles during Q3, marking a significant milestone in production capacity.

Key highlights include:
- Revenue: $23.4B (+9% QoQ)
- Vehicle deliveries: 462,890 units
- Automotive gross margin: 16.9%
- Energy storage deployments: 4.0 GWh

CEO Elon Musk noted that the company is on track to achieve its annual delivery target despite supply chain challenges in the semiconductor industry."""
    }


@pytest.fixture 
def mock_gemini_client():
    """Create a mock Gemini client for testing."""
    mock_client = Mock()
    mock_model = Mock()
    
    # Mock successful generation
    mock_response = Mock()
    mock_response.text = "Generated financial news content..."
    mock_model.generate_content.return_value = mock_response
    
    mock_client.GenerativeModel.return_value = mock_model
    
    return mock_client


# ============================================================================
# SAMPLE DATA FIXTURES
# ============================================================================

@pytest.fixture
def sample_financial_accounts():
    """Sample financial account data for testing."""
    return [
        {
            'account_id': 'ACC00001-TEST',
            'first_name': 'John',
            'last_name': 'Doe',
            'account_holder_name': 'John Doe',
            'state': 'CA',
            'zip_code': '90210',
            'account_type': 'Growth',
            'risk_profile': 'High',
            'total_portfolio_value': 250000.0,
            'last_updated': '2025-01-15T10:00:00'
        },
        {
            'account_id': 'ACC00002-TEST',
            'first_name': 'Jane',
            'last_name': 'Smith',
            'account_holder_name': 'Jane Smith',
            'state': 'NY',
            'zip_code': '10001',
            'account_type': 'Conservative',
            'risk_profile': 'Low',
            'total_portfolio_value': 150000.0,
            'last_updated': '2025-01-15T10:00:00'
        }
    ]


@pytest.fixture
def sample_financial_trades():
    """Sample trading data including fraud scenarios."""
    return [
        # Normal trade
        {
            'trade_id': 'TRD-20250115-001',
            'account_id': 'ACC00001-TEST',
            'symbol': 'AAPL',
            'trade_type': 'buy',
            'order_type': 'market',
            'order_status': 'executed',
            'quantity': 100.0,
            'execution_price': 150.25,
            'execution_timestamp': '2025-01-15T09:30:00',
            'last_updated': '2025-01-15T09:30:01'
        },
        # Insider trading scenario
        {
            'trade_id': 'TRD-20250115-002',
            'account_id': 'ACC00002-TEST', 
            'symbol': 'TSLA',
            'trade_type': 'buy',
            'order_type': 'market',
            'order_status': 'executed',
            'quantity': 500.0,
            'execution_price': 250.75,
            'execution_timestamp': '2025-01-14T14:30:00',
            'scenario_type': 'insider_trading',
            'scenario_symbol': 'TSLA',
            'last_updated': '2025-01-15T09:30:01'
        },
        # Wash trading scenario
        {
            'trade_id': 'TRD-20250115-003',
            'account_id': 'ACC00001-TEST',
            'symbol': 'MSFT',
            'trade_type': 'buy',
            'order_type': 'limit',
            'order_status': 'executed',
            'quantity': 200.0,
            'execution_price': 375.50,
            'execution_timestamp': '2025-01-15T11:00:00',
            'scenario_type': 'wash_trading',
            'wash_ring_id': 'WASH-RING-001',
            'counterpart_account': 'ACC00002-TEST',
            'last_updated': '2025-01-15T11:00:01'
        }
    ]


@pytest.fixture
def sample_symbols_config():
    """Sample symbol configuration for testing."""
    return {
        'STOCK_SYMBOLS_AND_INFO': {
            'AAPL': {
                'name': 'Apple Inc.',
                'sector': 'Technology',
                'index_membership': ['S&P 500', 'NASDAQ 100'],
                'country_of_origin': 'United States'
            },
            'TSLA': {
                'name': 'Tesla Inc.',
                'sector': 'Automotive',
                'index_membership': ['S&P 500', 'NASDAQ 100'],
                'country_of_origin': 'United States'
            },
            'MSFT': {
                'name': 'Microsoft Corporation',
                'sector': 'Technology',
                'index_membership': ['S&P 500', 'NASDAQ 100'],
                'country_of_origin': 'United States'
            }
        },
        'ETF_SYMBOLS_AND_INFO': {
            'SPY': {
                'name': 'SPDR S&P 500 ETF Trust',
                'sector': 'Broad Market',
                'index_membership': ['S&P 500'],
                'country_of_origin': 'United States'
            }
        },
        'BOND_SYMBOLS_AND_INFO': {
            'TLT': {
                'name': '20+ Year Treasury Bond ETF',
                'sector': 'Government Bonds',
                'index_membership': ['Bond Indices'],
                'country_of_origin': 'United States'
            }
        }
    }


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

@pytest.fixture
def create_temp_jsonl_file():
    """Helper to create temporary JSONL files for testing."""
    def _create_file(data: List[Dict[str, Any]], filename: Optional[str] = None) -> str:
        """Create a temporary JSONL file with the given data."""
        if filename:
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', 
                                                   delete=False, prefix=filename)
        else:
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False)
        
        for item in data:
            temp_file.write(json.dumps(item) + '\n')
        
        temp_file.flush()
        temp_file.close()
        
        return temp_file.name
    
    return _create_file


def pytest_configure(config):
    """Configure pytest with custom settings."""
    # Add custom markers
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests") 
    config.addinivalue_line("markers", "functional: Functional tests")
    config.addinivalue_line("markers", "elasticsearch: Requires Elasticsearch")
    config.addinivalue_line("markers", "gemini: Requires Gemini API")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "fraud: Fraud scenario tests")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Auto-mark tests based on file location
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "functional" in str(item.fspath):
            item.add_marker(pytest.mark.functional)
        
        # Auto-mark tests based on name patterns
        if "elasticsearch" in item.name.lower():
            item.add_marker(pytest.mark.elasticsearch)
        if "gemini" in item.name.lower():
            item.add_marker(pytest.mark.gemini)
        if "fraud" in item.name.lower():
            item.add_marker(pytest.mark.fraud)
        if "slow" in item.name.lower():
            item.add_marker(pytest.mark.slow)