#!/usr/bin/env python3
"""
Comprehensive Semantic Search Testing Script

Tests ELSER semantic search capabilities against the financial news and reports indices.
Compares semantic search performance with traditional keyword search.
"""

import warnings
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Tuple

# Suppress warnings
warnings.filterwarnings('ignore', message='urllib3 v2 only supports OpenSSL')
warnings.filterwarnings('ignore', message='Connecting to.*using TLS with verify_certs=False')

# Add scripts to path
import os
import sys
scripts_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scripts')
sys.path.insert(0, scripts_dir)

from common_utils import create_elasticsearch_client


class SemanticSearchTester:
    """Comprehensive semantic search testing suite."""
    
    def __init__(self):
        self.es_client = None
        self.results = {
            'basic_tests': [],
            'comparison_tests': [],
            'advanced_tests': [],
            'performance_metrics': {},
            'summary': {}
        }
    
    def connect(self):
        """Connect to Elasticsearch."""
        try:
            self.es_client = create_elasticsearch_client()
            print("✅ Connected to Elasticsearch")
            return True
        except Exception as e:
            print(f"❌ Failed to connect: {e}")
            return False
    
    def test_basic_semantic_search(self):
        """Phase 1: Basic semantic search validation."""
        print("\n" + "="*60)
        print("🔍 PHASE 1: Basic Semantic Search Validation")
        print("="*60)
        
        test_cases = [
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
        ]
        
        for test_case in test_cases:
            print(f"\n🔸 Test: {test_case['name']}")
            print(f"   Query: '{test_case['query']}'")
            print(f"   Expected: {test_case['expected_symbols']}")
            
            # Test both news and reports
            news_results = self._semantic_search('financial_news', test_case['query'])
            reports_results = self._semantic_search('financial_reports', test_case['query'])
            
            # Analyze results
            found_symbols = set()
            all_results = news_results + reports_results
            
            for result in all_results[:3]:  # Top 3 results
                score = result['_score']
                source = result['_source']
                symbol = source.get('primary_symbol') or source.get('company_symbol', 'N/A')
                title = source.get('title', '')[:80] + '...'
                
                found_symbols.add(symbol)
                print(f"   📄 [{score:.2f}] {symbol}: {title}")
            
            # Check if expected symbols were found
            expected_found = any(sym in found_symbols for sym in test_case['expected_symbols'])
            status = "✅ PASS" if expected_found else "❌ FAIL"
            print(f"   {status} - Expected symbols found: {expected_found}")
            
            self.results['basic_tests'].append({
                'test': test_case['name'],
                'query': test_case['query'],
                'expected': test_case['expected_symbols'],
                'found': list(found_symbols),
                'passed': expected_found,
                'top_results': [(r['_score'], r['_source'].get('primary_symbol', ''), r['_source'].get('title', '')) for r in all_results[:3]]
            })
    
    def test_semantic_vs_traditional(self):
        """Phase 2: Compare semantic vs traditional search."""
        print("\n" + "="*60)
        print("🆚 PHASE 2: Semantic vs Traditional Search Comparison")
        print("="*60)
        
        comparison_queries = [
            {
                'concept': 'Supply Chain Disruption',
                'semantic_query': 'supply chain disruption logistics',
                'traditional_query': 'supply chain',
                'expected_advantage': 'Better conceptual understanding of disruption context'
            },
            {
                'concept': 'Insurance Risk Assessment', 
                'semantic_query': 'insurance risk assessment volatility',
                'traditional_query': 'insurance risk',
                'expected_advantage': 'Better matching of risk assessment concepts'
            },
            {
                'concept': 'Legal Pharmaceutical Issues',
                'semantic_query': 'legal troubles pharmaceutical patents',
                'traditional_query': 'legal pharmaceutical',
                'expected_advantage': 'Better connection of legal issues to patent problems'
            }
        ]
        
        for query_test in comparison_queries:
            print(f"\n🔸 Comparison: {query_test['concept']}")
            
            # Semantic search
            print(f"   🧠 Semantic: '{query_test['semantic_query']}'")
            semantic_results = []
            for index in ['financial_news', 'financial_reports']:
                results = self._semantic_search(index, query_test['semantic_query'])
                semantic_results.extend(results)
            
            # Traditional search  
            print(f"   🔍 Traditional: '{query_test['traditional_query']}'")
            traditional_results = []
            for index in ['financial_news', 'financial_reports']:
                results = self._traditional_search(index, query_test['traditional_query'])
                traditional_results.extend(results)
            
            # Compare top results
            print(f"   📊 Semantic Top 3:")
            for i, result in enumerate(semantic_results[:3], 1):
                score = result['_score']
                symbol = result['_source'].get('primary_symbol', 'N/A')
                title = result['_source'].get('title', '')[:60] + '...'
                print(f"      {i}. [{score:.2f}] {symbol}: {title}")
            
            print(f"   📊 Traditional Top 3:")
            for i, result in enumerate(traditional_results[:3], 1):
                score = result['_score']
                symbol = result['_source'].get('primary_symbol', 'N/A')
                title = result['_source'].get('title', '')[:60] + '...'
                print(f"      {i}. [{score:.2f}] {symbol}: {title}")
            
            # Store comparison results
            self.results['comparison_tests'].append({
                'concept': query_test['concept'],
                'semantic_query': query_test['semantic_query'],
                'traditional_query': query_test['traditional_query'],
                'semantic_results': len(semantic_results),
                'traditional_results': len(traditional_results),
                'semantic_top_scores': [r['_score'] for r in semantic_results[:3]],
                'traditional_top_scores': [r['_score'] for r in traditional_results[:3]]
            })
    
    def test_advanced_semantic_capabilities(self):
        """Phase 3: Advanced semantic search capabilities."""
        print("\n" + "="*60)
        print("🚀 PHASE 3: Advanced Semantic Capabilities")
        print("="*60)
        
        advanced_tests = [
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
            },
            {
                'name': 'Regulatory Compliance',
                'query': 'regulatory compliance legal challenges patents',
                'description': 'Regulatory and legal business challenges'
            }
        ]
        
        for test in advanced_tests:
            print(f"\n🔸 {test['name']}")
            print(f"   Query: '{test['query']}'")
            print(f"   Focus: {test['description']}")
            
            # Search across both indices
            all_results = []
            for index in ['financial_news', 'financial_reports']:
                results = self._semantic_search(index, test['query'])
                all_results.extend(results)
            
            # Sort by relevance
            all_results.sort(key=lambda x: x['_score'], reverse=True)
            
            print(f"   📄 Top Results:")
            for i, result in enumerate(all_results[:5], 1):
                score = result['_score']
                symbol = result['_source'].get('primary_symbol', 'N/A')
                title = result['_source'].get('title', '')[:70] + '...'
                index_type = 'News' if result['_index'] == 'financial_news' else 'Report'
                print(f"      {i}. [{score:.2f}] {symbol} ({index_type}): {title}")
            
            self.results['advanced_tests'].append({
                'test': test['name'],
                'query': test['query'],
                'total_results': len(all_results),
                'top_scores': [r['_score'] for r in all_results[:5]],
                'result_diversity': len(set(r['_source'].get('primary_symbol', 'N/A') for r in all_results[:5]))
            })
    
    def test_performance_and_quality(self):
        """Phase 4: Performance and quality assessment."""
        print("\n" + "="*60)
        print("⚡ PHASE 4: Performance and Quality Assessment")
        print("="*60)
        
        test_queries = [
            'financial earnings performance',
            'environmental sustainability initiatives',
            'legal regulatory challenges',
            'supply chain risk management'
        ]
        
        performance_results = []
        
        for query in test_queries:
            print(f"\n🔸 Testing: '{query}'")
            
            # Time semantic search
            start_time = time.time()
            semantic_results = []
            for index in ['financial_news', 'financial_reports']:
                results = self._semantic_search(index, query)
                semantic_results.extend(results)
            semantic_time = (time.time() - start_time) * 1000  # Convert to ms
            
            # Time traditional search
            start_time = time.time()
            traditional_results = []
            for index in ['financial_news', 'financial_reports']:
                results = self._traditional_search(index, query)
                traditional_results.extend(results)
            traditional_time = (time.time() - start_time) * 1000  # Convert to ms
            
            print(f"   ⚡ Semantic search: {semantic_time:.1f}ms ({len(semantic_results)} results)")
            print(f"   ⚡ Traditional search: {traditional_time:.1f}ms ({len(traditional_results)} results)")
            print(f"   📊 Top semantic score: {semantic_results[0]['_score']:.3f}" if semantic_results else "   📊 No semantic results")
            print(f"   📊 Top traditional score: {traditional_results[0]['_score']:.3f}" if traditional_results else "   📊 No traditional results")
            
            performance_results.append({
                'query': query,
                'semantic_time_ms': semantic_time,
                'traditional_time_ms': traditional_time,
                'semantic_results': len(semantic_results),
                'traditional_results': len(traditional_results),
                'semantic_top_score': semantic_results[0]['_score'] if semantic_results else 0,
                'traditional_top_score': traditional_results[0]['_score'] if traditional_results else 0
            })
        
        # Calculate averages
        avg_semantic_time = sum(r['semantic_time_ms'] for r in performance_results) / len(performance_results)
        avg_traditional_time = sum(r['traditional_time_ms'] for r in performance_results) / len(performance_results)
        
        print(f"\n📊 PERFORMANCE SUMMARY:")
        print(f"   Average semantic search time: {avg_semantic_time:.1f}ms")
        print(f"   Average traditional search time: {avg_traditional_time:.1f}ms")
        print(f"   Semantic search overhead: {avg_semantic_time - avg_traditional_time:.1f}ms ({((avg_semantic_time/avg_traditional_time)-1)*100:.1f}%)")
        
        self.results['performance_metrics'] = {
            'avg_semantic_time_ms': avg_semantic_time,
            'avg_traditional_time_ms': avg_traditional_time,
            'semantic_overhead_ms': avg_semantic_time - avg_traditional_time,
            'semantic_overhead_percent': ((avg_semantic_time/avg_traditional_time)-1)*100,
            'detailed_results': performance_results
        }
    
    def _semantic_search(self, index: str, query: str, size: int = 10) -> List[Dict]:
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
            response = self.es_client.search(index=index, body=search_query)
            return response['hits']['hits']
        except Exception as e:
            print(f"   ❌ Semantic search error in {index}: {e}")
            return []
    
    def _traditional_search(self, index: str, query: str, size: int = 10) -> List[Dict]:
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
            response = self.es_client.search(index=index, body=search_query)
            return response['hits']['hits']
        except Exception as e:
            print(f"   ❌ Traditional search error in {index}: {e}")
            return []
    
    def create_demo_queries(self):
        """Create impressive demo queries for showcasing."""
        print("\n" + "="*60)
        print("🎪 DEMO QUERIES FOR SHOWCASING")
        print("="*60)
        
        demo_queries = [
            {
                'title': 'Environmental Impact Assessment',
                'query': 'environmental lawsuit sustainability challenges',
                'description': 'Find companies facing environmental legal issues or sustainability challenges'
            },
            {
                'title': 'Financial Restructuring Strategies',
                'query': 'debt restructuring balance sheet optimization financial flexibility',
                'description': 'Discover companies implementing financial restructuring and optimization'
            },
            {
                'title': 'Innovation and Patent Challenges',
                'query': 'patent invalidation intellectual property legal disputes',
                'description': 'Locate companies dealing with patent disputes and IP challenges'
            },
            {
                'title': 'Supply Chain Risk Management',
                'query': 'supply chain disruption logistics risk assessment insurance',
                'description': 'Find articles about supply chain risks and mitigation strategies'
            },
            {
                'title': 'Clean Energy Transition',
                'query': 'renewable energy clean technology sustainability investment',
                'description': 'Discover companies investing in clean energy and sustainability'
            }
        ]
        
        print("\n🎯 Top Demo Queries:")
        for i, demo in enumerate(demo_queries, 1):
            print(f"\n{i}. {demo['title']}")
            print(f"   Query: '{demo['query']}'")
            print(f"   Use case: {demo['description']}")
            
            # Show sample results
            results = []
            for index in ['financial_news', 'financial_reports']:
                index_results = self._semantic_search(index, demo['query'], size=3)
                results.extend(index_results)
            
            results.sort(key=lambda x: x['_score'], reverse=True)
            
            print(f"   Sample results:")
            for j, result in enumerate(results[:3], 1):
                score = result['_score']
                symbol = result['_source'].get('primary_symbol', 'N/A')
                title = result['_source'].get('title', '')[:60] + '...'
                doc_type = 'News' if result['_index'] == 'financial_news' else 'Report'
                print(f"      {j}. [{score:.2f}] {symbol} ({doc_type}): {title}")
    
    def generate_summary_report(self):
        """Generate comprehensive summary report."""
        print("\n" + "="*60)
        print("📋 SEMANTIC SEARCH TEST SUMMARY")
        print("="*60)
        
        # Basic tests summary
        basic_passed = sum(1 for test in self.results['basic_tests'] if test['passed'])
        basic_total = len(self.results['basic_tests'])
        print(f"\n✅ Basic Tests: {basic_passed}/{basic_total} passed ({basic_passed/basic_total*100:.0f}%)")
        
        # Performance summary
        if self.results['performance_metrics']:
            perf = self.results['performance_metrics']
            print(f"⚡ Performance: Semantic {perf['avg_semantic_time_ms']:.1f}ms, Traditional {perf['avg_traditional_time_ms']:.1f}ms")
            print(f"   Overhead: {perf['semantic_overhead_ms']:.1f}ms ({perf['semantic_overhead_percent']:.1f}%)")
        
        # Advanced tests summary
        advanced_total = len(self.results['advanced_tests'])
        print(f"🚀 Advanced Tests: {advanced_total} complex queries tested")
        
        # Overall assessment
        print(f"\n🎯 OVERALL ASSESSMENT:")
        if basic_passed == basic_total:
            print("   ✅ Semantic search is working correctly")
            print("   ✅ ELSER endpoint generating proper embeddings") 
            print("   ✅ Conceptual understanding demonstrated")
            print("   ✅ Ready for production use")
        else:
            print("   ⚠️  Some basic tests failed - investigate issues")
            print("   ⚠️  May need ELSER endpoint or mapping troubleshooting")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        print("   1. Use semantic search for conceptual queries")
        print("   2. Combine with traditional search for exact matches")
        print("   3. Leverage multi-field semantic search (title + content)")
        print("   4. Monitor query performance in production")
        
        return self.results
    
    def run_all_tests(self):
        """Run complete semantic search test suite."""
        print("🧪 SEMANTIC SEARCH COMPREHENSIVE TEST SUITE")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if not self.connect():
            return False
        
        try:
            # Run all test phases
            self.test_basic_semantic_search()
            self.test_semantic_vs_traditional()
            self.test_advanced_semantic_capabilities()
            self.test_performance_and_quality()
            self.create_demo_queries()
            
            # Generate summary
            results = self.generate_summary_report()
            
            print(f"\n🏁 Testing completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            return results
            
        except Exception as e:
            print(f"\n❌ Test suite failed: {e}")
            return False


def main():
    """Run semantic search tests."""
    tester = SemanticSearchTester()
    results = tester.run_all_tests()
    
    if results:
        print("\n💾 Test results available in tester.results")
        return True
    else:
        print("\n❌ Tests failed")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)