#!/usr/bin/env python3
"""
Fraud Detection Query Library for Financial Trading Data

This script implements various fraud detection patterns using Elasticsearch queries
to identify suspicious trading activities, account behaviors, and potential market manipulation.
"""

import os
import sys
import json
import time
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Any, Tuple

# Add scripts directory to path for imports
scripts_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scripts')
sys.path.insert(0, scripts_dir)

from common_utils import create_elasticsearch_client

class FraudDetectionSystem:
    def __init__(self):
        self.es_client = create_elasticsearch_client()
        self.results = {
            'volume_anomalies': [],
            'price_manipulation': [],
            'behavior_anomalies': [],
            'coordination_patterns': [],
            'summary_stats': {}
        }
    
    def detect_unusual_trading_volume(self, days_back=30, volume_threshold=3.0):
        """
        Detect accounts with abnormally high trading volumes compared to their risk profile.
        
        Args:
            days_back: Number of days to analyze
            volume_threshold: Multiple above normal considered suspicious (e.g., 3.0 = 300% of normal)
        """
        print(f"\n🔍 FRAUD DETECTION: Unusual Trading Volume")
        print(f"Analyzing last {days_back} days, threshold: {volume_threshold}x normal volume")
        print("="*60)
        
        # First, get account risk profiles and calculate expected volumes
        start_date = (datetime.now() - timedelta(days=days_back)).isoformat()
        
        # Query for high-volume trading accounts
        volume_query = {
            "size": 0,
            "query": {
                "bool": {
                    "must": [
                        {"term": {"order_status": "executed"}},
                        {"range": {"execution_timestamp": {"gte": start_date}}}
                    ]
                }
            },
            "aggs": {
                "accounts": {
                    "terms": {
                        "field": "account_id",
                        "size": 100,
                        "order": {"total_volume": "desc"}
                    },
                    "aggs": {
                        "total_volume": {
                            "sum": {"field": "quantity"}
                        },
                        "trade_count": {
                            "value_count": {"field": "trade_id"}
                        },
                        "avg_trade_size": {
                            "avg": {"field": "quantity"}
                        },
                        "total_value": {
                            "sum": {"field": "trade_cost"}
                        },
                        "unique_symbols": {
                            "cardinality": {"field": "symbol"}
                        }
                    }
                }
            }
        }
        
        try:
            volume_response = self.es_client.search(index='financial_trades', body=volume_query)
            high_volume_accounts = volume_response['aggregations']['accounts']['buckets']
            
            print(f"📊 Found {len(high_volume_accounts)} accounts with trading activity")
            
            # Now cross-reference with account risk profiles
            suspicious_accounts = []
            
            for account_data in high_volume_accounts[:20]:  # Top 20 volume accounts
                account_id = account_data['key']
                total_volume = account_data['total_volume']['value']
                trade_count = account_data['trade_count']['value']
                avg_trade_size = account_data['avg_trade_size']['value']
                total_value = account_data['total_value']['value']
                unique_symbols = account_data['unique_symbols']['value']
                
                # Get account details
                account_query = {
                    "query": {"term": {"account_id": account_id}},
                    "size": 1
                }
                
                account_response = self.es_client.search(index='financial_accounts', body=account_query)
                
                if account_response['hits']['hits']:
                    account_info = account_response['hits']['hits'][0]['_source']
                    risk_profile = account_info.get('risk_profile', 'Unknown')
                    portfolio_value = account_info.get('total_portfolio_value', 0)
                    
                    # Calculate risk-adjusted suspicion score
                    risk_multipliers = {
                        'Conservative': 1.0, 'Very Low': 1.0, 'Low': 1.2,
                        'Medium': 1.5, 'Moderate': 1.5, 'Growth': 2.0,
                        'High': 2.5, 'Very High': 3.0
                    }
                    
                    expected_multiplier = risk_multipliers.get(risk_profile, 1.5)
                    volume_ratio = total_volume / (portfolio_value * expected_multiplier / 100000)  # Normalize
                    
                    suspicion_score = min(100, volume_ratio * 10)  # Cap at 100
                    
                    if volume_ratio > volume_threshold:
                        suspicious_accounts.append({
                            'account_id': account_id,
                            'risk_profile': risk_profile,
                            'portfolio_value': portfolio_value,
                            'total_volume': total_volume,
                            'trade_count': trade_count,
                            'avg_trade_size': avg_trade_size,
                            'total_value': total_value,
                            'unique_symbols': unique_symbols,
                            'volume_ratio': volume_ratio,
                            'suspicion_score': suspicion_score
                        })
            
            # Sort by suspicion score
            suspicious_accounts.sort(key=lambda x: x['suspicion_score'], reverse=True)
            
            # Display results
            print(f"🚨 Found {len(suspicious_accounts)} accounts with suspicious volume patterns:")
            
            for i, account in enumerate(suspicious_accounts[:10], 1):
                print(f"\n{i}. Account: {account['account_id']}")
                print(f"   📊 Risk Profile: {account['risk_profile']}")
                print(f"   💰 Portfolio Value: ${account['portfolio_value']:,.2f}")
                print(f"   📈 Volume: {account['total_volume']:,.0f} shares ({account['trade_count']} trades)")
                print(f"   💸 Total Value: ${account['total_value']:,.2f}")
                print(f"   🎯 Symbols Traded: {account['unique_symbols']}")
                print(f"   ⚠️  Suspicion Score: {account['suspicion_score']:.1f}/100")
            
            self.results['volume_anomalies'] = suspicious_accounts
            
        except Exception as e:
            print(f"❌ Error in volume anomaly detection: {e}")
    
    def detect_price_manipulation_patterns(self, time_window_minutes=60):
        """
        Detect potential price manipulation through rapid buy/sell sequences.
        
        Args:
            time_window_minutes: Time window to look for offsetting trades
        """
        print(f"\n🎭 FRAUD DETECTION: Price Manipulation Patterns")
        print(f"Looking for offsetting trades within {time_window_minutes} minute windows")
        print("="*60)
        
        # Query for accounts with rapid buy/sell patterns on same symbols
        manipulation_query = {
            "size": 0,
            "query": {
                "bool": {
                    "must": [
                        {"term": {"order_status": "executed"}},
                        {"range": {"execution_timestamp": {"gte": "now-7d"}}}
                    ]
                }
            },
            "aggs": {
                "accounts": {
                    "terms": {
                        "field": "account_id",
                        "size": 50
                    },
                    "aggs": {
                        "symbols": {
                            "terms": {
                                "field": "symbol",
                                "size": 20
                            },
                            "aggs": {
                                "trades": {
                                    "top_hits": {
                                        "sort": [{"execution_timestamp": {"order": "asc"}}],
                                        "size": 100,
                                        "_source": ["trade_type", "quantity", "execution_price", "execution_timestamp", "trade_cost"]
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        
        try:
            manipulation_response = self.es_client.search(index='financial_trades', body=manipulation_query)
            accounts = manipulation_response['aggregations']['accounts']['buckets']
            
            suspicious_patterns = []
            
            for account_bucket in accounts:
                account_id = account_bucket['key']
                
                for symbol_bucket in account_bucket['symbols']['buckets']:
                    symbol = symbol_bucket['key']
                    trades = symbol_bucket['trades']['hits']['hits']
                    
                    if len(trades) < 4:  # Need at least 4 trades for pattern
                        continue
                    
                    # Analyze for pump-and-dump or wash trading patterns
                    trade_data = []
                    for hit in trades:
                        source = hit['_source']
                        trade_data.append({
                            'type': source['trade_type'],
                            'quantity': source['quantity'],
                            'price': source['execution_price'],
                            'timestamp': datetime.fromisoformat(source['execution_timestamp'].replace('Z', '+00:00')),
                            'cost': source['trade_cost']
                        })
                    
                    # Look for rapid offsetting patterns
                    pattern_score = 0
                    offsetting_pairs = []
                    
                    for i in range(len(trade_data) - 1):
                        for j in range(i + 1, len(trade_data)):
                            trade1, trade2 = trade_data[i], trade_data[j]
                            time_diff = abs((trade2['timestamp'] - trade1['timestamp']).total_seconds() / 60)
                            
                            if time_diff <= time_window_minutes:
                                # Check for offsetting trades (buy followed by sell, or vice versa)
                                if ((trade1['type'] == 'buy' and trade2['type'] == 'sell') or 
                                    (trade1['type'] == 'sell' and trade2['type'] == 'buy') or
                                    (trade1['type'] == 'short' and trade2['type'] == 'cover')):
                                    
                                    quantity_similarity = min(trade1['quantity'], trade2['quantity']) / max(trade1['quantity'], trade2['quantity'])
                                    
                                    if quantity_similarity > 0.8:  # Similar quantities
                                        pattern_score += 10 * quantity_similarity
                                        offsetting_pairs.append({
                                            'trade1': trade1,
                                            'trade2': trade2,
                                            'time_diff_minutes': time_diff,
                                            'quantity_similarity': quantity_similarity
                                        })
                    
                    if pattern_score > 15:  # Threshold for suspicious activity
                        suspicious_patterns.append({
                            'account_id': account_id,
                            'symbol': symbol,
                            'total_trades': len(trade_data),
                            'pattern_score': pattern_score,
                            'offsetting_pairs': len(offsetting_pairs),
                            'sample_pairs': offsetting_pairs[:3]  # Show first 3 pairs
                        })
            
            # Sort by pattern score
            suspicious_patterns.sort(key=lambda x: x['pattern_score'], reverse=True)
            
            print(f"🚨 Found {len(suspicious_patterns)} accounts with potential manipulation patterns:")
            
            for i, pattern in enumerate(suspicious_patterns[:10], 1):
                print(f"\n{i}. Account: {pattern['account_id']} | Symbol: {pattern['symbol']}")
                print(f"   📊 Total Trades: {pattern['total_trades']}")
                print(f"   🎯 Offsetting Pairs: {pattern['offsetting_pairs']}")
                print(f"   ⚠️  Pattern Score: {pattern['pattern_score']:.1f}")
                
                for j, pair in enumerate(pattern['sample_pairs'], 1):
                    trade1, trade2 = pair['trade1'], pair['trade2']
                    print(f"   📅 Pair {j}: {trade1['type']} {trade1['quantity']:,.0f} → {trade2['type']} {trade2['quantity']:,.0f} "
                          f"({pair['time_diff_minutes']:.1f}min gap)")
            
            self.results['price_manipulation'] = suspicious_patterns
            
        except Exception as e:
            print(f"❌ Error in price manipulation detection: {e}")
    
    def detect_account_behavior_anomalies(self):
        """
        Detect accounts with unusual behavior patterns compared to their profile.
        """
        print(f"\n👤 FRAUD DETECTION: Account Behavior Anomalies")
        print("Analyzing account behavior vs risk profile mismatches")
        print("="*60)
        
        # Query for accounts and their recent trading patterns
        behavior_query = {
            "size": 0,
            "query": {
                "bool": {
                    "must": [
                        {"term": {"order_status": "executed"}},
                        {"range": {"execution_timestamp": {"gte": "now-30d"}}}
                    ]
                }
            },
            "aggs": {
                "accounts": {
                    "terms": {
                        "field": "account_id",
                        "size": 100
                    },
                    "aggs": {
                        "trade_types": {
                            "terms": {"field": "trade_type"}
                        },
                        "order_types": {
                            "terms": {"field": "order_type"}
                        },
                        "avg_trade_value": {
                            "avg": {"field": "trade_cost"}
                        },
                        "total_value": {
                            "sum": {"field": "trade_cost"}
                        },
                        "trade_count": {
                            "value_count": {"field": "trade_id"}
                        },
                        "unique_symbols": {
                            "cardinality": {"field": "symbol"}
                        },
                        "trading_hours": {
                            "date_histogram": {
                                "field": "execution_timestamp",
                                "calendar_interval": "hour",
                                "min_doc_count": 1
                            }
                        }
                    }
                }
            }
        }
        
        try:
            behavior_response = self.es_client.search(index='financial_trades', body=behavior_query)
            trading_accounts = behavior_response['aggregations']['accounts']['buckets']
            
            anomalous_accounts = []
            
            for account_bucket in trading_accounts:
                account_id = account_bucket['key']
                
                # Get account profile
                account_query = {
                    "query": {"term": {"account_id": account_id}},
                    "size": 1
                }
                
                account_response = self.es_client.search(index='financial_accounts', body=account_query)
                
                if not account_response['hits']['hits']:
                    continue
                
                account_info = account_response['hits']['hits'][0]['_source']
                risk_profile = account_info.get('risk_profile', 'Unknown')
                state = account_info.get('state', 'Unknown')
                portfolio_value = account_info.get('total_portfolio_value', 0)
                
                # Analyze trading patterns
                trade_types = {bucket['key']: bucket['doc_count'] for bucket in account_bucket['trade_types']['buckets']}
                order_types = {bucket['key']: bucket['doc_count'] for bucket in account_bucket['order_types']['buckets']}
                avg_trade_value = account_bucket['avg_trade_value']['value'] or 0
                total_value = account_bucket['total_value']['value']
                trade_count = account_bucket['trade_count']['value']
                unique_symbols = account_bucket['unique_symbols']['value']
                
                # Calculate anomaly scores
                anomaly_score = 0
                anomalies = []
                
                # Check for risk profile mismatches
                conservative_profiles = ['Conservative', 'Very Low', 'Low']
                aggressive_profiles = ['High', 'Very High', 'Growth']
                
                if risk_profile in conservative_profiles:
                    # Conservative accounts shouldn't have high short/cover activity
                    short_ratio = (trade_types.get('short', 0) + trade_types.get('cover', 0)) / max(trade_count, 1)
                    if short_ratio > 0.2:  # More than 20% short trades
                        anomaly_score += 15
                        anomalies.append(f"High short activity ({short_ratio:.1%}) for conservative profile")
                    
                    # Shouldn't have very high trade values relative to portfolio
                    if avg_trade_value > portfolio_value * 0.1:  # More than 10% of portfolio per trade
                        anomaly_score += 20
                        anomalies.append(f"Large trades (${avg_trade_value:,.0f} avg) vs portfolio (${portfolio_value:,.0f})")
                
                # Check for unusual diversification
                if unique_symbols > 50 and trade_count < 100:  # High symbol diversity, low trade count
                    anomaly_score += 10
                    anomalies.append(f"Unusual diversification: {unique_symbols} symbols in {trade_count} trades")
                
                # Check for extreme trade frequency
                daily_avg_trades = trade_count / 30  # Assuming 30-day window
                if daily_avg_trades > 20:  # More than 20 trades per day average
                    anomaly_score += 15
                    anomalies.append(f"High frequency trading: {daily_avg_trades:.1f} trades/day average")
                
                if anomaly_score > 20:
                    anomalous_accounts.append({
                        'account_id': account_id,
                        'risk_profile': risk_profile,
                        'state': state,
                        'portfolio_value': portfolio_value,
                        'trade_count': trade_count,
                        'avg_trade_value': avg_trade_value,
                        'unique_symbols': unique_symbols,
                        'trade_types': trade_types,
                        'anomaly_score': anomaly_score,
                        'anomalies': anomalies
                    })
            
            # Sort by anomaly score
            anomalous_accounts.sort(key=lambda x: x['anomaly_score'], reverse=True)
            
            print(f"🚨 Found {len(anomalous_accounts)} accounts with behavioral anomalies:")
            
            for i, account in enumerate(anomalous_accounts[:10], 1):
                print(f"\n{i}. Account: {account['account_id']} ({account['state']})")
                print(f"   📊 Risk Profile: {account['risk_profile']}")
                print(f"   💰 Portfolio: ${account['portfolio_value']:,.2f}")
                print(f"   📈 Activity: {account['trade_count']} trades, {account['unique_symbols']} symbols")
                print(f"   💸 Avg Trade: ${account['avg_trade_value']:,.2f}")
                print(f"   ⚠️  Anomaly Score: {account['anomaly_score']:.1f}")
                for anomaly in account['anomalies']:
                    print(f"      🔍 {anomaly}")
            
            self.results['behavior_anomalies'] = anomalous_accounts
            
        except Exception as e:
            print(f"❌ Error in behavior anomaly detection: {e}")
    
    def detect_cross_account_coordination(self, time_window_minutes=30, min_accounts=3):
        """
        Detect coordinated trading patterns across multiple accounts.
        
        Args:
            time_window_minutes: Time window for coordinated activity
            min_accounts: Minimum number of accounts for coordination pattern
        """
        print(f"\n🤝 FRAUD DETECTION: Cross-Account Coordination")
        print(f"Looking for {min_accounts}+ accounts trading within {time_window_minutes} minute windows")
        print("="*60)
        
        # Query for trades grouped by symbol and time windows
        coordination_query = {
            "size": 0,
            "query": {
                "bool": {
                    "must": [
                        {"term": {"order_status": "executed"}},
                        {"range": {"execution_timestamp": {"gte": "now-7d"}}}
                    ]
                }
            },
            "aggs": {
                "symbols": {
                    "terms": {
                        "field": "symbol",
                        "size": 50
                    },
                    "aggs": {
                        "time_buckets": {
                            "date_histogram": {
                                "field": "execution_timestamp",
                                "fixed_interval": f"{time_window_minutes}m",
                                "min_doc_count": min_accounts
                            },
                            "aggs": {
                                "accounts": {
                                    "terms": {
                                        "field": "account_id",
                                        "size": 20
                                    },
                                    "aggs": {
                                        "trade_details": {
                                            "top_hits": {
                                                "size": 10,
                                                "_source": ["trade_type", "quantity", "execution_price", "trade_cost"]
                                            }
                                        }
                                    }
                                },
                                "unique_accounts": {
                                    "cardinality": {"field": "account_id"}
                                },
                                "total_volume": {
                                    "sum": {"field": "quantity"}
                                },
                                "total_value": {
                                    "sum": {"field": "trade_cost"}
                                }
                            }
                        }
                    }
                }
            }
        }
        
        try:
            coordination_response = self.es_client.search(index='financial_trades', body=coordination_query)
            symbols = coordination_response['aggregations']['symbols']['buckets']
            
            coordination_patterns = []
            
            for symbol_bucket in symbols:
                symbol = symbol_bucket['key']
                time_buckets = symbol_bucket['time_buckets']['buckets']
                
                for time_bucket in time_buckets:
                    account_count = time_bucket['unique_accounts']['value']
                    
                    if account_count >= min_accounts:
                        accounts = time_bucket['accounts']['buckets']
                        total_volume = time_bucket['total_volume']['value']
                        total_value = time_bucket['total_value']['value']
                        timestamp = time_bucket['key_as_string']
                        
                        # Calculate coordination score based on synchronization
                        account_details = []
                        trade_types = defaultdict(int)
                        
                        for account_bucket in accounts:
                            account_id = account_bucket['key']
                            trades = account_bucket['trade_details']['hits']['hits']
                            
                            for trade_hit in trades:
                                trade = trade_hit['_source']
                                trade_types[trade['trade_type']] += 1
                                account_details.append({
                                    'account_id': account_id,
                                    'trade_type': trade['trade_type'],
                                    'quantity': trade['quantity'],
                                    'price': trade['execution_price']
                                })
                        
                        # Score based on coordination indicators
                        coordination_score = 0
                        
                        # High score if many accounts trade same direction
                        max_same_direction = max(trade_types.values()) if trade_types else 0
                        if max_same_direction >= min_accounts:
                            coordination_score += 25
                        
                        # Higher score for more accounts
                        coordination_score += account_count * 2
                        
                        # Higher score for larger volumes
                        if total_volume > 10000:
                            coordination_score += 15
                        
                        if coordination_score > 20:
                            coordination_patterns.append({
                                'symbol': symbol,
                                'timestamp': timestamp,
                                'account_count': account_count,
                                'total_volume': total_volume,
                                'total_value': total_value,
                                'trade_types': dict(trade_types),
                                'coordination_score': coordination_score,
                                'account_details': account_details[:10]  # Limit details
                            })
            
            # Sort by coordination score
            coordination_patterns.sort(key=lambda x: x['coordination_score'], reverse=True)
            
            print(f"🚨 Found {len(coordination_patterns)} potential coordination patterns:")
            
            for i, pattern in enumerate(coordination_patterns[:10], 1):
                print(f"\n{i}. Symbol: {pattern['symbol']} | Time: {pattern['timestamp']}")
                print(f"   👥 Accounts Involved: {pattern['account_count']}")
                print(f"   📊 Total Volume: {pattern['total_volume']:,.0f} shares")
                print(f"   💸 Total Value: ${pattern['total_value']:,.2f}")
                print(f"   📈 Trade Types: {pattern['trade_types']}")
                print(f"   ⚠️  Coordination Score: {pattern['coordination_score']:.1f}")
                
                # Show sample accounts
                sample_accounts = list(set(detail['account_id'] for detail in pattern['account_details'][:5]))
                print(f"   🎯 Sample Accounts: {', '.join(sample_accounts)}")
            
            self.results['coordination_patterns'] = coordination_patterns
            
        except Exception as e:
            print(f"❌ Error in coordination detection: {e}")
    
    def run_fraud_detection_suite(self):
        """
        Run the complete fraud detection analysis.
        """
        print("🕵️  COMPREHENSIVE FRAUD DETECTION ANALYSIS")
        print("="*60)
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        overall_start = time.time()
        
        # Run all detection methods
        self.detect_unusual_trading_volume(days_back=30, volume_threshold=2.5)
        self.detect_price_manipulation_patterns(time_window_minutes=120)
        self.detect_account_behavior_anomalies()
        self.detect_cross_account_coordination(time_window_minutes=30, min_accounts=4)
        
        # Generate summary statistics
        overall_time = time.time() - overall_start
        
        total_volume_alerts = len(self.results['volume_anomalies'])
        total_manipulation_alerts = len(self.results['price_manipulation'])
        total_behavior_alerts = len(self.results['behavior_anomalies'])
        total_coordination_alerts = len(self.results['coordination_patterns'])
        
        self.results['summary_stats'] = {
            'analysis_time_seconds': overall_time,
            'total_alerts': total_volume_alerts + total_manipulation_alerts + total_behavior_alerts + total_coordination_alerts,
            'volume_anomaly_alerts': total_volume_alerts,
            'price_manipulation_alerts': total_manipulation_alerts,
            'behavior_anomaly_alerts': total_behavior_alerts,
            'coordination_alerts': total_coordination_alerts
        }
        
        print(f"\n{'='*60}")
        print("📊 FRAUD DETECTION SUMMARY")
        print(f"⏱️  Analysis Time: {overall_time:.2f} seconds")
        print(f"🚨 Total Alerts: {self.results['summary_stats']['total_alerts']}")
        print(f"   📊 Volume Anomalies: {total_volume_alerts}")
        print(f"   🎭 Price Manipulation: {total_manipulation_alerts}")
        print(f"   👤 Behavior Anomalies: {total_behavior_alerts}")
        print(f"   🤝 Coordination Patterns: {total_coordination_alerts}")
        print(f"{'='*60}")
        
        return self.results

def main():
    """
    Run fraud detection analysis.
    """
    try:
        detector = FraudDetectionSystem()
        results = detector.run_fraud_detection_suite()
        
        # Save results
        results_file = 'fraud_detection_results.json'
        with open(results_file, 'w') as f:
            # Convert datetime objects to strings for JSON serialization
            import json
            json_results = json.loads(json.dumps(results, default=str))
            json.dump(json_results, f, indent=2)
        print(f"\n💾 Results saved to {results_file}")
        
        return results
        
    except Exception as e:
        print(f"❌ Error running fraud detection: {e}")
        return None

if __name__ == "__main__":
    main()