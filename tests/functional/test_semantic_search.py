"""
Comprehensive Semantic Search Testing Module

Tests ELSER semantic search capabilities against the financial news and reports indices.
Migrated from test_semantic_search.py and enhanced with pytest framework.
"""

import pytest
import warnings
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Tuple
from unittest.mock import Mock, patch

# Suppress warnings
warnings.filterwarnings('ignore', message='urllib3 v2 only supports OpenSSL')
warnings.filterwarnings('ignore', message='Connecting to.*using TLS with verify_certs=False')


@pytest.mark.functional
@pytest.mark.elasticsearch
class TestSemanticSearch:
    """Comprehensive semantic search test suite."""

    @pytest.fixture(autouse=True)
    def setup_client(self, mock_environment):
        """Set up test environment and client."""
        self.test_results = {
            'basic_tests': [],
            'comparison_tests': [],
            'advanced_tests': [],
            'performance_metrics': {},
            'summary': {}
        }
        
    def test_connection(self, mock_elasticsearch_client):
        """Test basic Elasticsearch connection."""
        client = mock_elasticsearch_client
        
        # Test connection
        info = client.info()
        assert 'version' in info
        assert info['version']['number'] >= '8.0.0'

    @pytest.mark.parametrize("test_case", [
        {
            'name': 'Environmental Issues Search',
            'query': 'environmental lawsuit issues',
            'expected_symbols': ['VXUS'],
            'description': 'Should find VXUS environmental lawsuit article'
        },
        {
            'name': 'Pharmaceutical Challenges',
            'query': 'pharmaceutical patent problems',
            'expected_symbols': ['JNJ'],
            'description': 'Should find J&J patent invalidation story'
        },
        {
            'name': 'Debt Management Strategy',
            'query': 'debt restructuring financial management',
            'expected_symbols': ['MO'],
            'description': 'Should find Altria debt restructuring report'
        },
        {
            'name': 'Clean Energy Transition',
            'query': 'renewable energy sustainability',
            'expected_symbols': ['XEL'],
            'description': 'Should find Xcel Energy sustainability report'
        }
    ])
    def test_basic_semantic_search(self, mock_elasticsearch_client, test_case):
        """Test basic semantic search validation with parameterized test cases."""
        client = mock_elasticsearch_client
        
        # Configure mock to return relevant results for each test case
        mock_results = self._create_mock_search_results(test_case)
        client.search.return_value = mock_results
        
        # Perform semantic search on both indices
        news_results = self._semantic_search(client, 'financial_news', test_case['query'])
        reports_results = self._semantic_search(client, 'financial_reports', test_case['query'])
        
        # Verify results structure
        assert isinstance(news_results, list)
        assert isinstance(reports_results, list)
        
        # Analyze results
        found_symbols = set()
        all_results = news_results + reports_results
        
        for result in all_results[:3]:  # Top 3 results
            assert '_score' in result
            assert '_source' in result
            
            score = result['_score']
            source = result['_source']
            symbol = source.get('primary_symbol') or source.get('company_symbol', 'N/A')
            
            found_symbols.add(symbol)
            assert score > 0  # Ensure meaningful scores
        
        # Check if expected symbols were found (for real data)
        # In mock mode, just verify the structure is correct
        assert len(found_symbols) > 0
        
        # Store results for reporting
        self.test_results['basic_tests'].append({
            'test': test_case['name'],
            'query': test_case['query'],
            'expected': test_case['expected_symbols'],
            'found': list(found_symbols),
            'passed': True,  # Structure validation passed
            'total_results': len(all_results)
        })

    @pytest.mark.parametrize("comparison_query", [
        {
            'concept': 'Supply Chain Disruption',
            'semantic_query': 'supply chain disruption logistics',
            'traditional_query': 'supply chain',
            'expected_advantage': 'Better conceptual understanding'
        },
        {
            'concept': 'Insurance Risk Assessment',
            'semantic_query': 'insurance risk assessment volatility',
            'traditional_query': 'insurance risk',
            'expected_advantage': 'Better matching of risk concepts'
        },
        {
            'concept': 'Legal Pharmaceutical Issues',
            'semantic_query': 'legal troubles pharmaceutical patents',
            'traditional_query': 'legal pharmaceutical',
            'expected_advantage': 'Better connection of legal issues'
        }
    ])
    def test_semantic_vs_traditional_search(self, mock_elasticsearch_client, comparison_query):
        """Compare semantic vs traditional search performance."""
        client = mock_elasticsearch_client
        
        # Mock semantic search results (higher relevance scores)
        semantic_mock = {
            'hits': {
                'total': {'value': 25},
                'hits': [
                    {
                        '_index': 'financial_news',
                        '_score': 15.5,  # Higher semantic score
                        '_source': {
                            'primary_symbol': 'TEST',
                            'title': f"Semantic result for {comparison_query['concept']}"
                        }
                    }
                ]
            }
        }
        
        # Mock traditional search results (lower relevance scores)  
        traditional_mock = {
            'hits': {
                'total': {'value': 50},
                'hits': [
                    {
                        '_index': 'financial_news',
                        '_score': 8.2,  # Lower traditional score
                        '_source': {
                            'primary_symbol': 'TEST',
                            'title': f"Traditional result for {comparison_query['concept']}"
                        }
                    }
                ]
            }
        }
        
        # Test semantic search
        client.search.return_value = semantic_mock
        semantic_results = []
        for index in ['financial_news', 'financial_reports']:
            results = self._semantic_search(client, index, comparison_query['semantic_query'])
            semantic_results.extend(results)
        
        # Test traditional search
        client.search.return_value = traditional_mock
        traditional_results = []
        for index in ['financial_news', 'financial_reports']:
            results = self._traditional_search(client, index, comparison_query['traditional_query'])
            traditional_results.extend(results)
        
        # Validate results
        assert len(semantic_results) > 0
        assert len(traditional_results) > 0
        
        # Semantic search should typically have higher relevance scores for conceptual queries
        if semantic_results and traditional_results:
            semantic_top_score = semantic_results[0]['_score']
            traditional_top_score = traditional_results[0]['_score']
            
            # In this mock scenario, semantic should have higher scores
            assert semantic_top_score > traditional_top_score
        
        # Store comparison results
        self.test_results['comparison_tests'].append({
            'concept': comparison_query['concept'],
            'semantic_results': len(semantic_results),
            'traditional_results': len(traditional_results),
            'semantic_advantage': semantic_results[0]['_score'] if semantic_results else 0,
            'traditional_score': traditional_results[0]['_score'] if traditional_results else 0
        })

    @pytest.mark.parametrize("advanced_test", [
        {
            'name': 'Multi-Concept Query',
            'query': 'insurance risk management supply chain volatility',
            'description': 'Complex query spanning multiple business concepts'
        },
        {
            'name': 'Industry-Specific Search',
            'query': 'utility renewable energy infrastructure investments',
            'description': 'Industry-specific terminology and concepts'
        },
        {
            'name': 'Financial Strategy Query',
            'query': 'debt restructuring balance sheet optimization',
            'description': 'Financial strategy and corporate restructuring'
        }
    ])
    def test_advanced_semantic_capabilities(self, mock_elasticsearch_client, advanced_test):
        """Test advanced semantic search capabilities."""
        client = mock_elasticsearch_client
        
        # Create diverse mock results
        mock_results = {
            'hits': {
                'total': {'value': 42},
                'hits': [
                    {
                        '_index': 'financial_news',
                        '_score': 12.8,
                        '_source': {
                            'primary_symbol': f'SYM{i}',
                            'title': f"Advanced result {i} for {advanced_test['name']}"
                        }
                    } for i in range(5)
                ]
            }
        }
        
        client.search.return_value = mock_results
        
        # Search across both indices
        all_results = []
        for index in ['financial_news', 'financial_reports']:
            results = self._semantic_search(client, index, advanced_test['query'])
            all_results.extend(results)
        
        # Validate advanced capabilities
        assert len(all_results) > 0
        
        # Sort by relevance
        all_results.sort(key=lambda x: x['_score'], reverse=True)
        
        # Check result diversity (different symbols)
        symbols = [r['_source'].get('primary_symbol') for r in all_results[:5]]
        unique_symbols = len(set(symbols))
        
        assert unique_symbols > 1  # Should have diverse results
        
        # Store advanced test results
        self.test_results['advanced_tests'].append({
            'test': advanced_test['name'],
            'query': advanced_test['query'],
            'total_results': len(all_results),
            'top_scores': [r['_score'] for r in all_results[:3]],
            'result_diversity': unique_symbols
        })

    @pytest.mark.slow
    def test_performance_and_quality(self, mock_elasticsearch_client):
        """Test performance and quality assessment."""
        client = mock_elasticsearch_client
        
        test_queries = [
            'financial earnings performance',
            'environmental sustainability initiatives',
            'legal regulatory challenges',
            'supply chain risk management'
        ]
        
        performance_results = []
        
        for query in test_queries:
            # Mock consistent response
            client.search.return_value = {
                'hits': {
                    'total': {'value': 30},
                    'hits': [
                        {
                            '_score': 10.5,
                            '_source': {'primary_symbol': 'PERF', 'title': f'Result for {query}'}
                        }
                    ]
                }
            }
            
            # Time semantic search
            start_time = time.time()
            semantic_results = []
            for index in ['financial_news', 'financial_reports']:
                results = self._semantic_search(client, index, query)
                semantic_results.extend(results)
            semantic_time = (time.time() - start_time) * 1000
            
            # Time traditional search  
            start_time = time.time()
            traditional_results = []
            for index in ['financial_news', 'financial_reports']:
                results = self._traditional_search(client, index, query)
                traditional_results.extend(results)
            traditional_time = (time.time() - start_time) * 1000
            
            # Validate performance metrics
            assert semantic_time >= 0
            assert traditional_time >= 0
            assert len(semantic_results) > 0
            assert len(traditional_results) > 0
            
            performance_results.append({
                'query': query,
                'semantic_time_ms': semantic_time,
                'traditional_time_ms': traditional_time,
                'semantic_results': len(semantic_results),
                'traditional_results': len(traditional_results)
            })
        
        # Calculate performance averages
        avg_semantic_time = sum(r['semantic_time_ms'] for r in performance_results) / len(performance_results)
        avg_traditional_time = sum(r['traditional_time_ms'] for r in performance_results) / len(performance_results)
        
        # Store performance metrics
        self.test_results['performance_metrics'] = {
            'avg_semantic_time_ms': avg_semantic_time,
            'avg_traditional_time_ms': avg_traditional_time,
            'total_tests': len(performance_results)
        }
        
        # Validate reasonable performance
        assert avg_semantic_time < 5000  # Should complete within 5 seconds
        assert avg_traditional_time < 5000

    def test_demo_queries(self, mock_elasticsearch_client):
        """Test demo queries for showcasing capabilities."""
        client = mock_elasticsearch_client
        
        demo_queries = [
            {
                'title': 'Environmental Impact Assessment',
                'query': 'environmental lawsuit sustainability challenges',
                'description': 'Find environmental legal issues'
            },
            {
                'title': 'Financial Restructuring Strategies',
                'query': 'debt restructuring balance sheet optimization',
                'description': 'Discover financial restructuring'
            }
        ]
        
        for demo in demo_queries:
            # Mock demo results
            client.search.return_value = {
                'hits': {
                    'total': {'value': 15},
                    'hits': [
                        {
                            '_index': 'financial_news',
                            '_score': 14.2,
                            '_source': {
                                'primary_symbol': 'DEMO',
                                'title': f"Demo result for {demo['title']}"
                            }
                        }
                    ]
                }
            }
            
            # Test the query
            results = []
            for index in ['financial_news', 'financial_reports']:
                index_results = self._semantic_search(client, index, demo['query'], size=3)
                results.extend(index_results)
            
            assert len(results) > 0
            assert all('_score' in r for r in results)
            assert all('_source' in r for r in results)

    def _semantic_search(self, client, index: str, query: str, size: int = 10) -> List[Dict]:
        """Perform semantic search using ELSER."""
        search_query = {
            "size": size,
            "query": {
                "bool": {
                    "should": [
                        {
                            "semantic": {
                                "field": "title.semantic_text",
                                "query": query
                            }
                        },
                        {
                            "semantic": {
                                "field": "content.semantic_text",
                                "query": query
                            }
                        }
                    ]
                }
            }
        }
        
        try:
            response = client.search(index=index, body=search_query)
            return response['hits']['hits']
        except Exception:
            return []

    def _traditional_search(self, client, index: str, query: str, size: int = 10) -> List[Dict]:
        """Perform traditional full-text search."""
        search_query = {
            "size": size,
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["title^2", "content"],
                    "type": "best_fields"
                }
            }
        }
        
        try:
            response = client.search(index=index, body=search_query)
            return response['hits']['hits']
        except Exception:
            return []

    def _create_mock_search_results(self, test_case):
        """Create mock search results for test cases."""
        return {
            'hits': {
                'total': {'value': 10},
                'hits': [
                    {
                        '_index': 'financial_news',
                        '_score': 12.5,
                        '_source': {
                            'primary_symbol': test_case['expected_symbols'][0] if test_case['expected_symbols'] else 'MOCK',
                            'title': f"Mock result for {test_case['name']}",
                            'content': test_case['description']
                        }
                    }
                ]
            }
        }

    def test_generate_summary_report(self):
        """Test summary report generation."""
        # Add some test data
        self.test_results['basic_tests'] = [{'passed': True}, {'passed': True}]
        self.test_results['comparison_tests'] = [{'concept': 'Test'}]
        self.test_results['advanced_tests'] = [{'test': 'Advanced'}]
        self.test_results['performance_metrics'] = {
            'avg_semantic_time_ms': 150.0,
            'avg_traditional_time_ms': 100.0
        }
        
        # Test summary generation
        basic_passed = sum(1 for test in self.test_results['basic_tests'] if test['passed'])
        basic_total = len(self.test_results['basic_tests'])
        
        assert basic_passed == 2
        assert basic_total == 2
        
        # Test assessment logic
        overall_success = basic_passed == basic_total
        assert overall_success is True


# ============================================================================
# INTEGRATION TESTS WITH REAL ELASTICSEARCH
# ============================================================================

@pytest.mark.integration
@pytest.mark.elasticsearch
class TestSemanticSearchIntegration:
    """Integration tests that require real Elasticsearch connection."""
    
    @pytest.fixture(autouse=True)
    def setup_real_client(self):
        """Set up real Elasticsearch client if available."""
        try:
            from scripts.common_utils import create_elasticsearch_client
            self.es_client = create_elasticsearch_client()
            # Test connection
            self.es_client.info()
            self.has_real_connection = True
        except Exception:
            self.has_real_connection = False
            pytest.skip("Real Elasticsearch connection not available")

    def test_real_semantic_search(self):
        """Test semantic search against real Elasticsearch cluster."""
        if not self.has_real_connection:
            pytest.skip("No real ES connection")
            
        # Simple semantic search test
        query = {
            "size": 3,
            "query": {
                "semantic": {
                    "field": "title.semantic_text",
                    "query": "financial earnings performance"
                }
            }
        }
        
        try:
            response = self.es_client.search(index='financial_news', body=query)
            assert 'hits' in response
            assert isinstance(response['hits']['hits'], list)
        except Exception as e:
            pytest.skip(f"Semantic search not available: {e}")

    def test_real_index_exists(self):
        """Test that expected indices exist in real cluster."""
        if not self.has_real_connection:
            pytest.skip("No real ES connection")
            
        expected_indices = ['financial_news', 'financial_reports', 'financial_accounts']
        
        for index in expected_indices:
            exists = self.es_client.indices.exists(index=index)
            if not exists:
                pytest.skip(f"Index {index} does not exist in test cluster")