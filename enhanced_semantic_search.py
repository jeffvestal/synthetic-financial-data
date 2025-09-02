#!/usr/bin/env python3
"""
Enhanced Semantic Search Testing with Hybrid Approaches
Tests optimized semantic search with boosting, hybrid queries, and advanced patterns.
"""

import os
import sys
import json
import time
from datetime import datetime

# Add scripts directory to path for imports
scripts_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scripts')
sys.path.insert(0, scripts_dir)

from common_utils import create_elasticsearch_client

class EnhancedSemanticSearch:
    def __init__(self):
        self.es_client = create_elasticsearch_client()
        self.results = {
            'optimized_queries': [],
            'hybrid_search': [],
            'domain_validation': [],
            'performance_comparison': []
        }
    
    def _enhanced_semantic_search(self, index_name, query, boost_semantic=2.0, boost_title=1.5):
        """Enhanced semantic search with field boosting."""
        search_query = {
            "size": 10,
            "query": {
                "bool": {
                    "should": [
                        {
                            "semantic": {
                                "field": "title.semantic_text",
                                "query": query,
                                "boost": boost_title * boost_semantic
                            }
                        },
                        {
                            "semantic": {
                                "field": "content.semantic_text", 
                                "query": query,
                                "boost": boost_semantic
                            }
                        }
                    ],
                    "minimum_should_match": 1
                }
            }
        }
        
        try:
            response = self.es_client.search(index=index_name, body=search_query)
            return response['hits']['hits']
        except Exception as e:
            print(f"Error in enhanced semantic search: {e}")
            return []
    
    def _hybrid_search(self, index_name, query, semantic_boost=2.0, keyword_boost=1.0):
        """Hybrid search combining semantic and traditional keyword search."""
        search_query = {
            "size": 10,
            "query": {
                "bool": {
                    "should": [
                        # Semantic search component
                        {
                            "bool": {
                                "should": [
                                    {
                                        "semantic": {
                                            "field": "title.semantic_text",
                                            "query": query,
                                            "boost": semantic_boost * 1.5
                                        }
                                    },
                                    {
                                        "semantic": {
                                            "field": "content.semantic_text",
                                            "query": query,
                                            "boost": semantic_boost
                                        }
                                    }
                                ]
                            }
                        },
                        # Traditional keyword search component
                        {
                            "multi_match": {
                                "query": query,
                                "fields": ["title^2", "content"],
                                "type": "best_fields",
                                "boost": keyword_boost
                            }
                        }
                    ]
                }
            }
        }
        
        try:
            response = self.es_client.search(index=index_name, body=search_query)
            return response['hits']['hits']
        except Exception as e:
            print(f"Error in hybrid search: {e}")
            return []
    
    def test_optimized_queries(self):
        """Test optimized semantic queries with boosting."""
        print("\n" + "="*60)
        print("🚀 ENHANCED SEMANTIC SEARCH: Optimized Queries")
        print("="*60)
        
        test_cases = [
            {
                'name': 'Environmental Legal Issues (High Precision)',
                'query': 'environmental lawsuit disposal practices regulatory compliance',
                'expected_symbols': ['VXUS', 'ISRG'],
                'boost_semantic': 3.0,
                'boost_title': 2.0
            },
            {
                'name': 'Financial Risk Management (Balanced)',
                'query': 'supply chain risk insurance volatility business interruption',
                'expected_symbols': ['AIG'],
                'boost_semantic': 2.0,
                'boost_title': 1.5
            },
            {
                'name': 'Corporate Legal Challenges (Comprehensive)',
                'query': 'patent invalidation pharmaceutical drug court ruling intellectual property',
                'expected_symbols': ['JNJ'],
                'boost_semantic': 2.5,
                'boost_title': 2.0
            }
        ]
        
        for test_case in test_cases:
            print(f"\n🔸 Test: {test_case['name']}")
            print(f"   Query: '{test_case['query']}'")
            print(f"   Boost Settings: Semantic={test_case['boost_semantic']}, Title={test_case['boost_title']}")
            
            # Test enhanced semantic search on both indices
            news_results = self._enhanced_semantic_search(
                'financial_news', 
                test_case['query'],
                test_case['boost_semantic'],
                test_case['boost_title']
            )
            reports_results = self._enhanced_semantic_search(
                'financial_reports', 
                test_case['query'],
                test_case['boost_semantic'], 
                test_case['boost_title']
            )
            
            # Analyze results
            all_results = news_results + reports_results
            all_results.sort(key=lambda x: x['_score'], reverse=True)
            
            found_symbols = set()
            for result in all_results[:5]:  # Top 5 results
                score = result['_score']
                source = result['_source']
                symbol = source.get('primary_symbol') or source.get('company_symbol', 'N/A')
                title = source.get('title', '')[:70] + '...'
                
                found_symbols.add(symbol)
                print(f"   📊 [{score:.2f}] {symbol}: {title}")
            
            # Check success
            expected_found = any(sym in found_symbols for sym in test_case['expected_symbols'])
            status = "✅ PASS" if expected_found else "❌ FAIL"
            print(f"   {status} - Expected symbols found: {expected_found}")
            
            self.results['optimized_queries'].append({
                'test': test_case['name'],
                'query': test_case['query'],
                'expected': test_case['expected_symbols'],
                'found': list(found_symbols),
                'passed': expected_found,
                'boost_settings': {
                    'semantic': test_case['boost_semantic'],
                    'title': test_case['boost_title']
                }
            })
    
    def test_hybrid_search(self):
        """Test hybrid semantic + keyword search approach."""
        print("\n" + "="*60)
        print("🔀 HYBRID SEARCH: Semantic + Traditional")
        print("="*60)
        
        queries = [
            'corporate leadership succession planning communication services',
            'balance sheet debt restructuring consumer staples financial optimization',
            'renewable energy clean technology utilities sector transformation'
        ]
        
        for query in queries:
            print(f"\n🔍 Query: '{query}'")
            
            start_time = time.time()
            
            # Test on financial_news
            hybrid_results = self._hybrid_search('financial_news', query, semantic_boost=2.0, keyword_boost=1.2)
            semantic_results = self._enhanced_semantic_search('financial_news', query, boost_semantic=2.0, boost_title=1.5)
            
            hybrid_time = time.time() - start_time
            
            print(f"   ⚡ Hybrid search time: {hybrid_time*1000:.1f}ms")
            print(f"   📊 Hybrid results: {len(hybrid_results)}, Semantic-only: {len(semantic_results)}")
            
            # Show top hybrid results
            print("   🔀 Top Hybrid Results:")
            for i, result in enumerate(hybrid_results[:3], 1):
                score = result['_score']
                source = result['_source']
                symbol = source.get('primary_symbol', 'N/A')
                title = source.get('title', '')[:60] + '...'
                print(f"      {i}. [{score:.2f}] {symbol}: {title}")
            
            self.results['hybrid_search'].append({
                'query': query,
                'hybrid_count': len(hybrid_results),
                'semantic_count': len(semantic_results),
                'response_time': hybrid_time,
                'top_hybrid_symbols': [r['_source'].get('primary_symbol', 'N/A') for r in hybrid_results[:3]]
            })
    
    def test_financial_domain_validation(self):
        """Test semantic understanding across different financial domains."""
        print("\n" + "="*60)
        print("🏦 FINANCIAL DOMAIN VALIDATION")
        print("="*60)
        
        domain_tests = [
            {
                'domain': 'Risk Management',
                'queries': [
                    'operational risk supply chain disruption mitigation strategies',
                    'credit risk assessment financial exposure management',
                    'market volatility portfolio optimization defensive positioning'
                ]
            },
            {
                'domain': 'Corporate Finance', 
                'queries': [
                    'capital structure optimization debt equity balance',
                    'merger acquisition due diligence valuation analysis',
                    'dividend policy shareholder return capital allocation'
                ]
            },
            {
                'domain': 'Regulatory Compliance',
                'queries': [
                    'environmental compliance sustainability reporting requirements',
                    'financial disclosure transparency regulatory filing updates',
                    'intellectual property protection patent litigation defense'
                ]
            }
        ]
        
        for domain in domain_tests:
            print(f"\n🏢 Domain: {domain['domain']}")
            domain_results = []
            
            for query in domain['queries']:
                print(f"\n   🔍 Testing: '{query[:50]}...'")
                
                # Test across both indices
                news_hits = self._enhanced_semantic_search('financial_news', query)
                reports_hits = self._enhanced_semantic_search('financial_reports', query)
                
                total_hits = len(news_hits) + len(reports_hits)
                all_results = news_hits + reports_hits
                all_results.sort(key=lambda x: x['_score'], reverse=True)
                
                # Show top result
                if all_results:
                    top_result = all_results[0]
                    score = top_result['_score']
                    symbol = top_result['_source'].get('primary_symbol', 'N/A')
                    title = top_result['_source'].get('title', '')[:50] + '...'
                    print(f"      ⭐ Best: [{score:.2f}] {symbol}: {title}")
                
                domain_results.append({
                    'query': query,
                    'total_hits': total_hits,
                    'top_score': all_results[0]['_score'] if all_results else 0,
                    'top_symbol': all_results[0]['_source'].get('primary_symbol', 'N/A') if all_results else 'N/A'
                })
            
            # Domain summary
            avg_hits = sum(r['total_hits'] for r in domain_results) / len(domain_results)
            avg_score = sum(r['top_score'] for r in domain_results) / len(domain_results)
            print(f"\n   📈 Domain Summary: Avg {avg_hits:.1f} hits, Avg score {avg_score:.2f}")
            
            self.results['domain_validation'].append({
                'domain': domain['domain'],
                'queries_tested': len(domain['queries']),
                'avg_hits': avg_hits,
                'avg_score': avg_score,
                'results': domain_results
            })
    
    def run_all_tests(self):
        """Run all enhanced semantic search tests."""
        print("🚀 ENHANCED SEMANTIC SEARCH TESTING")
        print("="*60)
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        overall_start = time.time()
        
        # Run all test phases
        self.test_optimized_queries()
        self.test_hybrid_search()
        self.test_financial_domain_validation()
        
        # Final summary
        overall_time = time.time() - overall_start
        print(f"\n{'='*60}")
        print("📊 ENHANCED TESTING COMPLETE")
        print(f"⏱️  Total time: {overall_time:.2f} seconds")
        
        # Performance summary
        optimized_passed = sum(1 for r in self.results['optimized_queries'] if r['passed'])
        total_optimized = len(self.results['optimized_queries'])
        
        print(f"✅ Optimized queries: {optimized_passed}/{total_optimized} passed")
        print(f"🔀 Hybrid tests: {len(self.results['hybrid_search'])} completed")
        print(f"🏦 Domain tests: {len(self.results['domain_validation'])} domains validated")
        print(f"{'='*60}")
        
        return self.results

def main():
    """Run enhanced semantic search tests."""
    try:
        tester = EnhancedSemanticSearch()
        results = tester.run_all_tests()
        
        # Save results
        results_file = 'enhanced_semantic_search_results.json'
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n💾 Results saved to {results_file}")
        
        return results
        
    except Exception as e:
        print(f"❌ Error running enhanced tests: {e}")
        return None

if __name__ == "__main__":
    main()