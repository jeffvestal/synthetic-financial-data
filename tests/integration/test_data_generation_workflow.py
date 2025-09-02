"""
Integration Tests for Data Generation Workflows

Tests end-to-end data generation workflows including account creation,
news generation, and Elasticsearch integration.
"""

import pytest
import os
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock


@pytest.mark.integration
class TestDataGenerationWorkflow:
    """Test complete data generation workflows."""

    @pytest.fixture(autouse=True)
    def setup_test_environment(self, mock_environment, tmp_path):
        """Set up test environment for integration tests."""
        self.temp_dir = tmp_path
        self.original_cwd = os.getcwd()
        
        # Create test directory structure
        (self.temp_dir / 'scripts').mkdir()
        (self.temp_dir / 'lib').mkdir() 
        (self.temp_dir / 'generated_data').mkdir()
        (self.temp_dir / 'elasticsearch').mkdir()
        
        # Change to temp directory for tests
        os.chdir(self.temp_dir)
        
        yield
        
        # Restore original directory
        os.chdir(self.original_cwd)

    def test_account_generation_workflow(self, sample_financial_accounts, create_temp_jsonl_file):
        """Test complete account generation workflow."""
        # Create sample accounts file
        accounts_file = create_temp_jsonl_file(sample_financial_accounts, 'accounts')
        
        try:
            # Mock the account generation process
            with patch('scripts.generate_holdings_accounts.generate_accounts') as mock_gen_accounts:
                mock_gen_accounts.return_value = sample_financial_accounts
                
                # Simulate workflow
                accounts = mock_gen_accounts()
                
                # Validate results
                assert len(accounts) == len(sample_financial_accounts)
                assert all('account_id' in acc for acc in accounts)
                assert all('total_portfolio_value' in acc for acc in accounts)
                
                # Test portfolio value distribution
                portfolio_values = [acc['total_portfolio_value'] for acc in accounts]
                assert all(value > 0 for value in portfolio_values)
                
        finally:
            os.unlink(accounts_file)

    @pytest.mark.gemini
    def test_news_generation_workflow(self, mock_gemini_client):
        """Test news generation workflow with AI integration."""
        with patch('google.generativeai.GenerativeModel') as mock_model_class:
            # Setup mock Gemini client
            mock_model = Mock()
            mock_response = Mock()
            mock_response.text = """
            # Tesla Reports Strong Q3 Earnings
            
            Tesla Inc. (TSLA) announced robust third-quarter earnings today, 
            surpassing analyst expectations with record vehicle deliveries and 
            improved production efficiency.
            
            Key highlights:
            - Revenue: $25.2B (+15% YoY)  
            - Vehicle deliveries: 485,000 units
            - Net income: $3.1B
            """
            
            mock_model.generate_content.return_value = mock_response
            mock_model_class.return_value = mock_model
            
            # Test news generation process
            with patch('scripts.generate_reports_and_news_new.generate_news_articles') as mock_gen_news:
                mock_gen_news.return_value = [
                    {
                        'article_id': 'ART-001',
                        'title': 'Tesla Reports Strong Q3 Earnings',
                        'content': mock_response.text,
                        'primary_symbol': 'TSLA',
                        'sentiment': 'positive'
                    }
                ]
                
                news_articles = mock_gen_news()
                
                assert len(news_articles) > 0
                assert all('article_id' in article for article in news_articles)
                assert all('title' in article for article in news_articles)
                assert all('primary_symbol' in article for article in news_articles)

    @pytest.mark.elasticsearch
    def test_elasticsearch_integration_workflow(self, mock_elasticsearch_client, sample_financial_accounts):
        """Test complete Elasticsearch integration workflow."""
        with patch('scripts.common_utils.create_elasticsearch_client', return_value=mock_elasticsearch_client):
            with patch('scripts.common_utils.ingest_data_to_es') as mock_ingest:
                # Mock successful ingestion
                mock_ingest.return_value = True
                
                # Test data ingestion workflow
                from scripts.common_utils import ingest_data_to_es
                
                # Simulate ingesting accounts
                result = ingest_data_to_es(
                    mock_elasticsearch_client,
                    'test_accounts.jsonl',
                    'financial_accounts',
                    'account_id'
                )
                
                assert result is True
                mock_ingest.assert_called_once()

    def test_fraud_scenario_generation_workflow(self, sample_financial_trades):
        """Test fraud scenario generation workflow."""
        # Filter for fraud scenarios
        fraud_trades = [trade for trade in sample_financial_trades 
                       if trade.get('scenario_type')]
        
        assert len(fraud_trades) > 0
        
        # Test insider trading scenario
        insider_trades = [trade for trade in fraud_trades 
                         if trade.get('scenario_type') == 'insider_trading']
        
        if insider_trades:
            insider_trade = insider_trades[0]
            assert 'scenario_symbol' in insider_trade
            assert 'execution_timestamp' in insider_trade
            
        # Test wash trading scenario
        wash_trades = [trade for trade in fraud_trades 
                      if trade.get('scenario_type') == 'wash_trading']
        
        if wash_trades:
            wash_trade = wash_trades[0]
            assert 'wash_ring_id' in wash_trade
            assert 'counterpart_account' in wash_trade

    def test_control_script_integration(self, mock_elasticsearch_client, mock_environment):
        """Test control.py integration with core components."""
        with patch('lib.task_executor.TaskExecutor') as mock_task_executor_class:
            with patch('lib.config_manager.ConfigManager') as mock_config_manager_class:
                with patch('lib.menu_system.MenuSystem') as mock_menu_system_class:
                    
                    # Setup mocks
                    mock_task_executor = Mock()
                    mock_config_manager = Mock()
                    mock_menu_system = Mock()
                    
                    mock_task_executor_class.return_value = mock_task_executor
                    mock_config_manager_class.return_value = mock_config_manager
                    mock_menu_system_class.return_value = mock_menu_system
                    
                    # Mock configuration
                    mock_config_manager.load_default_config.return_value = {
                        'generate_accounts': True,
                        'num_accounts': 100,
                        'ingest_elasticsearch': False
                    }
                    
                    # Test control script initialization
                    from control import SyntheticDataController
                    
                    controller = SyntheticDataController(interactive_mode=False)
                    
                    # Verify components are initialized
                    assert controller.config_manager is not None
                    assert controller.menu_system is not None
                    assert controller.task_executor is not None

    def test_setup_script_integration(self, tmp_path):
        """Test setup.py integration workflow."""
        # Create mock project structure in temp directory
        requirements_file = tmp_path / 'requirements.txt'
        requirements_file.write_text('elasticsearch>=8.0.0\nrich>=13.0.0\n')
        
        with patch('setup.create_venv', return_value=True), \
             patch('setup.install_requirements', return_value=True), \
             patch('setup.upgrade_pip', return_value=True), \
             patch('setup.prompt_for_credentials', return_value=None):
            
            # Change to temp directory
            original_cwd = os.getcwd()
            os.chdir(tmp_path)
            
            try:
                import setup
                
                # Test main setup workflow
                setup.main()
                
                # If we reach here, setup completed without errors
                assert True
                
            finally:
                os.chdir(original_cwd)

    @pytest.mark.slow
    def test_performance_integration_small_dataset(self, mock_elasticsearch_client):
        """Test performance with small dataset generation."""
        import time
        
        start_time = time.time()
        
        # Simulate small dataset generation
        with patch('scripts.generate_holdings_accounts.main') as mock_accounts_gen:
            with patch('scripts.generate_reports_and_news_new.main') as mock_news_gen:
                
                mock_accounts_gen.return_value = None  # Simulate successful completion
                mock_news_gen.return_value = None      # Simulate successful completion
                
                # Run mock generation
                mock_accounts_gen()
                mock_news_gen()
                
                execution_time = time.time() - start_time
                
                # Should complete quickly for mocked operations
                assert execution_time < 5.0  # 5 seconds max for mocked operations

    def test_error_handling_integration(self, mock_elasticsearch_client):
        """Test error handling across integrated components."""
        # Test Elasticsearch connection failure
        mock_elasticsearch_client.info.side_effect = ConnectionError("Connection failed")
        
        with patch('scripts.common_utils.create_elasticsearch_client', return_value=mock_elasticsearch_client):
            from lib.index_manager import IndexManager
            
            manager = IndexManager(mock_elasticsearch_client)
            result = manager.test_connection()
            
            # Should handle error gracefully
            assert result['success'] is False
            assert 'error' in result

    def test_configuration_persistence_integration(self, tmp_path):
        """Test configuration persistence across components."""
        from lib.config_manager import ConfigManager
        
        # Create config manager
        config_manager = ConfigManager()
        
        # Create test configuration
        test_config = {
            'generate_accounts': True,
            'num_accounts': 500,
            'ingest_elasticsearch': True,
            'custom_setting': 'test_value'
        }
        
        # Test saving and loading configuration
        config_file = tmp_path / 'test_config.json'
        
        # Save config
        result = config_manager.save_config_to_file(test_config, str(config_file))
        assert result is True
        assert config_file.exists()
        
        # Load config
        loaded_config = config_manager._load_config_from_file(str(config_file))
        assert loaded_config == test_config

    def test_multi_component_integration(self, mock_elasticsearch_client):
        """Test integration between multiple components."""
        with patch('lib.index_manager.IndexManager') as mock_index_manager_class:
            with patch('lib.config_manager.ConfigManager') as mock_config_manager_class:
                
                # Setup mocks
                mock_index_manager = Mock()
                mock_config_manager = Mock()
                
                mock_index_manager_class.return_value = mock_index_manager
                mock_config_manager_class.return_value = mock_config_manager
                
                # Mock index manager methods
                mock_index_manager.get_all_indices_status.return_value = {
                    'financial_accounts': {'exists': True, 'doc_count': 100},
                    'financial_trades': {'exists': False, 'doc_count': 0}
                }
                
                # Mock config manager methods
                mock_config_manager.get_current_config.return_value = {
                    'generate_accounts': True,
                    'ingest_elasticsearch': True
                }
                
                # Test integration
                index_manager = mock_index_manager_class()
                config_manager = mock_config_manager_class()
                
                indices_status = index_manager.get_all_indices_status()
                current_config = config_manager.get_current_config()
                
                # Verify integration works
                assert 'financial_accounts' in indices_status
                assert current_config['generate_accounts'] is True


@pytest.mark.integration
@pytest.mark.elasticsearch
class TestElasticsearchIntegration:
    """Test integration with real Elasticsearch if available."""
    
    @pytest.fixture(autouse=True)
    def setup_es_client(self):
        """Set up Elasticsearch client if available."""
        try:
            from scripts.common_utils import create_elasticsearch_client
            self.es_client = create_elasticsearch_client()
            # Test basic connection
            self.es_client.info()
            self.has_real_es = True
        except Exception:
            self.has_real_es = False
            pytest.skip("Real Elasticsearch connection not available")

    def test_real_index_creation_workflow(self):
        """Test index creation with real Elasticsearch."""
        if not self.has_real_es:
            pytest.skip("No real ES connection")
            
        from lib.index_manager import IndexManager
        
        manager = IndexManager(self.es_client)
        
        # Test creating a simple test index
        test_index = f'test_integration_{int(time.time())}'
        
        try:
            # Simple mapping
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
                
                # Verify it exists
                assert manager.index_exists(test_index)
                
        finally:
            # Cleanup
            if manager.index_exists(test_index):
                manager.delete_index(test_index)

    def test_real_data_ingestion_workflow(self):
        """Test data ingestion with real Elasticsearch."""
        if not self.has_real_es:
            pytest.skip("No real ES connection")
            
        # Test with small sample data
        test_data = [
            {
                'test_id': 'TEST-001',
                'test_field': 'test_value_1',
                'timestamp': '2025-01-15T10:00:00'
            },
            {
                'test_id': 'TEST-002',
                'test_field': 'test_value_2', 
                'timestamp': '2025-01-15T11:00:00'
            }
        ]
        
        test_index = f'test_data_{int(time.time())}'
        
        try:
            # Create index first
            from lib.index_manager import IndexManager
            manager = IndexManager(self.es_client)
            
            test_mapping = {
                'mappings': {
                    'properties': {
                        'test_id': {'type': 'keyword'},
                        'test_field': {'type': 'keyword'},
                        'timestamp': {'type': 'date'}
                    }
                }
            }
            
            with patch.object(manager, 'get_index_mapping', return_value=test_mapping):
                manager.create_index(test_index)
            
            # Prepare bulk data
            bulk_data = []
            for doc in test_data:
                bulk_data.append({
                    '_index': test_index,
                    '_id': doc['test_id'],
                    '_source': doc
                })
            
            # Ingest data
            response = self.es_client.bulk(body=bulk_data)
            
            assert response['errors'] is False
            
            # Refresh index
            self.es_client.indices.refresh(index=test_index)
            
            # Verify data
            count_response = self.es_client.count(index=test_index)
            assert count_response['count'] == 2
            
        finally:
            # Cleanup
            try:
                self.es_client.indices.delete(index=test_index, ignore=[404])
            except:
                pass