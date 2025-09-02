# Testing Framework Documentation

This document describes the comprehensive testing framework for the Synthetic Financial Data Generator, including setup, usage, and contribution guidelines.

## 🧪 Test Framework Overview

The testing framework uses **pytest** with a structured approach to ensure code quality, reliability, and maintainability:

- **Unit Tests**: Fast, isolated tests for individual components
- **Integration Tests**: Tests for component interactions and external dependencies  
- **Functional Tests**: End-to-end system tests with real-world scenarios
- **Performance Tests**: Benchmarking and performance validation
- **Code Quality**: Formatting, linting, and security checks

## 🚀 Quick Start

### 1. Install Testing Dependencies

```bash
# Install test dependencies
pip install -r requirements-test.txt

# Or use the automated setup
python3 setup.py  # Select 'n' when prompted for credentials
```

### 2. Run Tests

```bash
# Quick test run (unit tests only)
python run_tests.py --unit

# Full test suite (no external dependencies)
python run_tests.py --all

# Include external dependencies (Elasticsearch, Gemini API)
python run_tests.py --all --external

# With coverage reporting
python run_tests.py --unit --coverage
```

## 📁 Test Structure

```
tests/
├── conftest.py                    # Shared fixtures and configuration
├── unit/                          # Unit tests (fast, no external deps)
│   ├── test_setup.py              # setup.py functionality
│   ├── test_config_manager.py     # Configuration management
│   ├── test_index_manager.py      # Elasticsearch index operations
│   └── test_common_utils.py       # Utility functions
├── integration/                   # Integration tests (real dependencies)
│   ├── test_data_generation_workflow.py  # End-to-end workflows
│   └── test_elasticsearch_integration.py # ES connectivity
├── functional/                    # Functional/system tests
│   ├── test_semantic_search.py    # Semantic search capabilities
│   ├── test_timestamp_update.py   # Timestamp management
│   └── test_serverless_compatibility.py  # Serverless ES support
└── fixtures/                      # Test data and mock responses
    ├── sample_data.json           # Sample financial data
    ├── mock_elasticsearch.py      # ES mock responses
    └── mock_gemini.py             # Gemini API mocks
```

## 🏃‍♂️ Running Tests

### Using the Test Runner Script

The `run_tests.py` script provides convenient commands for different testing scenarios:

```bash
# Unit tests (fastest)
python run_tests.py --unit

# Integration tests
python run_tests.py --integration

# Functional tests  
python run_tests.py --functional

# All tests
python run_tests.py --all

# Code quality checks
python run_tests.py --quality

# Security checks
python run_tests.py --security

# Specific test file
python run_tests.py --specific tests/unit/test_setup.py
```

### Using pytest Directly

```bash
# Run all unit tests
pytest tests/unit/ -v -m unit

# Run tests with coverage
pytest tests/unit/ -v --cov=scripts --cov=lib --cov=setup --cov-report=html

# Run specific test category
pytest tests/ -v -m "elasticsearch"
pytest tests/ -v -m "fraud"
pytest tests/ -v -m "slow"

# Run tests with external dependencies
pytest tests/integration/ -v -m "integration and elasticsearch"
pytest tests/functional/ -v -m "functional and gemini"

# Run tests excluding external dependencies
pytest tests/ -v -m "not elasticsearch and not gemini"
```

## 🏷️ Test Markers

Tests are organized using pytest markers:

- `@pytest.mark.unit` - Unit tests (fast, isolated)
- `@pytest.mark.integration` - Integration tests  
- `@pytest.mark.functional` - Functional/system tests
- `@pytest.mark.elasticsearch` - Requires Elasticsearch connection
- `@pytest.mark.gemini` - Requires Gemini API key
- `@pytest.mark.slow` - Tests that take >5 seconds
- `@pytest.mark.fraud` - Fraud scenario related tests

## 🔧 Test Configuration

### pytest.ini

Key configuration settings:

```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --cov=scripts
    --cov=lib  
    --cov=setup
    --cov-report=html:htmlcov
    --cov-report=term-missing
    --strict-markers
    -v
markers =
    unit: Unit tests (fast, no external dependencies)
    integration: Integration tests (real dependencies)
    functional: Functional tests (full system)
    elasticsearch: Tests requiring Elasticsearch connection
    gemini: Tests requiring Gemini API
    slow: Tests that take >5 seconds
    fraud: Tests related to fraud scenario generation
```

### Environment Variables for Testing

```bash
# Required for integration tests
export ES_ENDPOINT_URL="https://localhost:9200"
export ES_API_KEY="your_elasticsearch_api_key"

# Optional for Gemini API tests
export GEMINI_API_KEY="your_gemini_api_key"

# Test-specific settings
export UPDATE_TIMESTAMPS_ON_LOAD="false"
export ES_BULK_BATCH_SIZE="100"
export PARALLEL_BULK_WORKERS="1"
```

## 🧪 Writing Tests

### Unit Test Example

```python
"""Example unit test for a utility function."""
import pytest
from unittest.mock import Mock, patch

@pytest.mark.unit
class TestConfigManager:
    """Test ConfigManager functionality."""
    
    def test_validate_config_valid(self, config_manager):
        """Test configuration validation with valid config."""
        valid_config = {
            'generate_accounts': True,
            'num_accounts': 1000,
            'ingest_elasticsearch': True
        }
        
        is_valid, errors = config_manager.validate_config(valid_config)
        
        assert is_valid is True
        assert len(errors) == 0
    
    @pytest.mark.parametrize("config,expected_valid", [
        ({'generate_accounts': True, 'num_accounts': 100}, True),
        ({'generate_accounts': 'yes', 'num_accounts': 100}, False),
        ({'generate_accounts': True, 'num_accounts': -10}, False)
    ])
    def test_config_validation_cases(self, config_manager, config, expected_valid):
        """Test various configuration validation scenarios."""
        is_valid, errors = config_manager.validate_config(config)
        assert is_valid == expected_valid
```

### Integration Test Example

```python
"""Example integration test."""
import pytest

@pytest.mark.integration
@pytest.mark.elasticsearch
class TestElasticsearchIntegration:
    """Test integration with Elasticsearch."""
    
    @pytest.fixture(autouse=True)
    def setup_es_client(self):
        """Set up real Elasticsearch client."""
        try:
            from scripts.common_utils import create_elasticsearch_client
            self.es_client = create_elasticsearch_client()
            self.es_client.info()  # Test connection
            self.has_real_es = True
        except Exception:
            self.has_real_es = False
            pytest.skip("Elasticsearch not available")
    
    def test_real_index_creation(self):
        """Test creating indices in real Elasticsearch."""
        if not self.has_real_es:
            pytest.skip("No ES connection")
            
        from lib.index_manager import IndexManager
        manager = IndexManager(self.es_client)
        
        # Test index creation
        success = manager.create_index('test_index')
        assert success is True
```

### Mock Usage Examples

```python
"""Examples of using mocks in tests."""
from unittest.mock import Mock, patch, MagicMock

# Mock Elasticsearch client
@pytest.fixture
def mock_elasticsearch_client():
    mock_client = Mock()
    mock_client.info.return_value = {'version': {'number': '8.9.0'}}
    mock_client.indices.exists.return_value = True
    mock_client.search.return_value = {
        'hits': {'total': {'value': 100}, 'hits': []}
    }
    return mock_client

# Mock external API calls
def test_with_api_mock():
    with patch('scripts.common_utils.create_elasticsearch_client') as mock_create:
        mock_client = Mock()
        mock_create.return_value = mock_client
        
        # Your test code here
        result = some_function_that_uses_es()
        assert result is not None
```

## 🔍 Test Fixtures

### Shared Fixtures (conftest.py)

Key fixtures available to all tests:

- `mock_elasticsearch_client` - Mock ES client with realistic responses
- `mock_gemini_client` - Mock Gemini API client
- `sample_financial_accounts` - Sample account data
- `sample_financial_trades` - Sample trading data with fraud scenarios
- `sample_symbols_config` - Sample symbol configuration
- `temp_env_file` - Temporary .env file for testing
- `create_temp_jsonl_file` - Helper to create test JSONL files

### Using Fixtures

```python
def test_with_fixtures(mock_elasticsearch_client, sample_financial_accounts):
    """Test using shared fixtures."""
    # mock_elasticsearch_client is pre-configured
    # sample_financial_accounts contains realistic test data
    
    assert len(sample_financial_accounts) > 0
    assert mock_elasticsearch_client.info()['version']
```

## 📊 Coverage Reporting

### Generate Coverage Reports

```bash
# HTML coverage report
pytest tests/unit/ --cov=scripts --cov=lib --cov-report=html
open htmlcov/index.html

# Terminal coverage report
pytest tests/unit/ --cov=scripts --cov=lib --cov-report=term-missing

# XML coverage for CI
pytest tests/unit/ --cov=scripts --cov=lib --cov-report=xml
```

### Coverage Goals

- **Unit Tests**: 90%+ coverage for core business logic
- **Integration Tests**: 80%+ coverage for critical paths  
- **Overall**: 85%+ combined coverage

## 🚦 Continuous Integration

### GitHub Actions

The project includes a comprehensive GitHub Actions workflow (`.github/workflows/test.yml`) that:

- Runs tests on multiple Python versions (3.8, 3.9, 3.10, 3.11)
- Tests across different operating systems (Ubuntu, macOS, Windows)
- Includes code quality checks (Black, isort, flake8, mypy)
- Runs security scans (safety, bandit)
- Tests with multiple Elasticsearch versions
- Generates and uploads coverage reports

### Running CI Tests Locally

```bash
# Simulate CI environment
export CI=true

# Run the same checks as CI
python run_tests.py --all
python run_tests.py --quality
python run_tests.py --security
```

## 🎯 Performance Testing

### Benchmark Tests

```python
"""Example performance test."""
import pytest

@pytest.mark.slow  
def test_large_dataset_performance(benchmark):
    """Benchmark large dataset generation."""
    
    def generate_large_dataset():
        # Your performance-critical code
        return generate_accounts(count=10000)
    
    result = benchmark(generate_large_dataset)
    
    # Assertions about performance
    assert len(result) == 10000
    # benchmark.stats will contain timing information
```

### Running Performance Tests

```bash
# Install benchmark plugin
pip install pytest-benchmark

# Run performance tests
pytest tests/ -v -m "slow" --benchmark-only --benchmark-sort=mean

# Generate benchmark report
pytest tests/ --benchmark-only --benchmark-html=benchmark_report.html
```

## 🔒 Security Testing

### Security Checks

```bash
# Dependency vulnerability scan
safety check

# Security linting
bandit -r scripts/ lib/ setup.py

# Or use the test runner
python run_tests.py --security
```

### Common Security Issues to Test

- API key exposure in logs or files
- SQL injection vulnerabilities (if applicable)
- Unsafe file operations
- Insecure HTTP connections
- Hardcoded secrets

## 🛠️ Development Workflow

### Pre-commit Testing

```bash
# Before committing code
python run_tests.py --unit --quality

# Or set up pre-commit hooks
pip install pre-commit
pre-commit install
```

### Testing New Features

1. **Write tests first** (Test-Driven Development)
2. **Start with unit tests** for individual components
3. **Add integration tests** for component interactions
4. **Include functional tests** for end-to-end workflows
5. **Update documentation** and examples

### Test Categories by Development Phase

- **Development**: Unit tests for immediate feedback
- **Feature Complete**: Integration tests for component interaction
- **Release Candidate**: Full test suite including functional tests
- **Production**: Monitoring and performance tests

## 🐛 Debugging Tests

### Common Issues and Solutions

**Tests fail with import errors:**
```bash
# Ensure paths are set correctly
export PYTHONPATH="${PYTHONPATH}:$(pwd)/scripts:$(pwd)/lib"

# Or run from project root
cd /path/to/synthetic-financial-data
python run_tests.py --unit
```

**Elasticsearch connection issues:**
```bash
# Check if ES is running
curl http://localhost:9200/_cluster/health

# Run tests without ES dependency
python run_tests.py --unit  # Excludes ES tests
pytest tests/ -v -m "not elasticsearch"
```

**Gemini API rate limits:**
```bash
# Use mocked tests during development
pytest tests/ -v -m "not gemini"

# Or set longer timeout
export GEMINI_REQUEST_TIMEOUT=30
```

### Debugging with pytest

```bash
# Run with detailed output
pytest tests/unit/test_setup.py -v -s

# Stop on first failure
pytest tests/unit/ -x

# Drop into debugger on failure
pytest tests/unit/ --pdb

# Show local variables on failure
pytest tests/unit/ -l

# Run only failed tests from last run
pytest --lf
```

## 📈 Metrics and Reporting

### Test Metrics

Track these metrics over time:
- Test count by category (unit/integration/functional)
- Code coverage percentage
- Test execution time
- Failure rate
- Security scan results

### Generating Reports

```bash
# Comprehensive test report
python run_tests.py --all --coverage > test_report.txt

# JUnit XML for CI integration
pytest tests/ --junitxml=test_results.xml

# Coverage badge data
coverage-badge -o coverage.svg
```

## 🤝 Contributing to Tests

### Guidelines for Test Contributions

1. **Follow naming conventions**: `test_*.py` files, `test_*` functions
2. **Use descriptive test names**: `test_validate_config_with_invalid_types`
3. **Include docstrings**: Explain what the test validates
4. **Use appropriate markers**: `@pytest.mark.unit`, etc.
5. **Mock external dependencies**: Don't rely on external services in unit tests
6. **Test edge cases**: Invalid inputs, boundary conditions, error scenarios
7. **Keep tests isolated**: Each test should be independent

### Test Review Checklist

- [ ] Tests follow naming conventions
- [ ] Appropriate test markers applied  
- [ ] External dependencies properly mocked
- [ ] Edge cases and error conditions tested
- [ ] Tests are independent and can run in any order
- [ ] Test names are descriptive and clear
- [ ] Docstrings explain test purpose
- [ ] No hardcoded values (use fixtures/parameters)

## 🚀 Advanced Testing Techniques

### Parametrized Tests

```python
@pytest.mark.parametrize("input,expected", [
    ("valid_input", True),
    ("invalid_input", False),
    ("edge_case", None)
])
def test_with_parameters(input, expected):
    result = my_function(input)
    assert result == expected
```

### Test Factories

```python
# Use factory-boy for complex test data
import factory

class AccountFactory(factory.Factory):
    class Meta:
        model = dict
    
    account_id = factory.Sequence(lambda n: f"ACC-{n:05d}")
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    total_portfolio_value = factory.Faker('pyfloat', positive=True, max_value=1000000)

# Usage in tests
def test_with_factory():
    account = AccountFactory()
    assert 'account_id' in account
```

### Property-Based Testing

```python
# Use hypothesis for property-based testing
from hypothesis import given, strategies as st

@given(st.integers(min_value=1, max_value=10000))
def test_account_generation_properties(num_accounts):
    """Test that account generation always produces valid results."""
    accounts = generate_accounts(count=num_accounts)
    
    assert len(accounts) == num_accounts
    assert all('account_id' in acc for acc in accounts)
    assert all(acc['total_portfolio_value'] > 0 for acc in accounts)
```

This testing framework ensures the Synthetic Financial Data Generator maintains high quality and reliability while enabling confident development and refactoring.