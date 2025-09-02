# Fraud Detection Query Examples & Results

This document demonstrates the fraud detection capabilities implemented for the synthetic financial trading dataset. The system analyzes 262,018+ trade records across 7,000+ accounts to identify suspicious patterns.

## System Overview

The fraud detection system implements four main detection patterns:

1. **🔍 Unusual Trading Volume Detection**
2. **🎭 Price Manipulation Pattern Detection** 
3. **👤 Account Behavior Anomaly Detection**
4. **🤝 Cross-Account Coordination Detection**

## Detection Results Summary

**Latest Analysis Results:**
- **⏱️  Analysis Time**: 12.4 seconds
- **🚨 Total Alerts**: 21 suspicious activities detected
- **📊 Volume Anomalies**: 20 accounts with unusual trading volumes
- **🎭 Price Manipulation**: 0 pump-and-dump patterns detected  
- **👤 Behavior Anomalies**: 0 risk profile violations
- **🤝 Coordination Patterns**: 1 cross-account coordination event

---

## 1. Unusual Trading Volume Detection

### Query Pattern
```json
{
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
      "terms": {"field": "account_id", "size": 100},
      "aggs": {
        "total_volume": {"sum": {"field": "quantity"}},
        "trade_count": {"value_count": {"field": "trade_id"}},
        "total_value": {"sum": {"field": "trade_cost"}}
      }
    }
  }
}
```

### Detection Logic
- Cross-references trading volume with account risk profiles
- Calculates volume ratio: `actual_volume / (portfolio_value * risk_multiplier)`
- Flags accounts exceeding 2.5x expected volume for their risk profile
- Generates suspicion scores (0-100 scale)

### Sample Results
```
Account: ACC06448-5ae4
📊 Risk Profile: High
💰 Portfolio Value: $404,173.31
📈 Volume: 45,903 shares (48 trades)
💸 Total Value: $24,008,888.61
🎯 Symbols Traded: 44
⚠️  Suspicion Score: 100.0/100
```

**Key Indicators:**
- High volume relative to portfolio size
- Excessive diversification (44 different symbols)
- Large average trade values

---

## 2. Price Manipulation Detection

### Query Pattern
```json
{
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
      "terms": {"field": "account_id"},
      "aggs": {
        "symbols": {
          "terms": {"field": "symbol"},
          "aggs": {
            "trades": {
              "top_hits": {
                "sort": [{"execution_timestamp": {"order": "asc"}}],
                "_source": ["trade_type", "quantity", "execution_price", "execution_timestamp"]
              }
            }
          }
        }
      }
    }
  }
}
```

### Detection Logic
- Identifies rapid buy/sell sequences within 120-minute windows
- Detects offsetting trades (buy→sell, sell→buy, short→cover)
- Analyzes quantity similarity between offsetting trades (>80% similarity flagged)
- Calculates pattern scores based on coordination and timing

### Current Status
- **0 manipulation patterns detected** in current dataset
- System designed to catch pump-and-dump schemes, wash trading, and layering

---

## 3. Account Behavior Anomaly Detection

### Query Pattern
```json
{
  "aggs": {
    "accounts": {
      "terms": {"field": "account_id"},
      "aggs": {
        "trade_types": {"terms": {"field": "trade_type"}},
        "avg_trade_value": {"avg": {"field": "trade_cost"}},
        "unique_symbols": {"cardinality": {"field": "symbol"}},
        "trading_hours": {
          "date_histogram": {
            "field": "execution_timestamp",
            "calendar_interval": "hour"
          }
        }
      }
    }
  }
}
```

### Detection Logic
- Compares trading patterns against account risk profiles
- Flags conservative accounts with high short/cover activity (>20%)
- Identifies large trades relative to portfolio size (>10%)
- Detects unusual diversification patterns
- Monitors high-frequency trading patterns (>20 trades/day average)

### Risk Profile Analysis
```python
risk_multipliers = {
    'Conservative': 1.0, 'Very Low': 1.0, 'Low': 1.2,
    'Medium': 1.5, 'Moderate': 1.5, 'Growth': 2.0,
    'High': 2.5, 'Very High': 3.0
}
```

### Current Status
- **0 behavioral anomalies detected** - accounts trading within expected risk parameters

---

## 4. Cross-Account Coordination Detection

### Query Pattern
```json
{
  "aggs": {
    "symbols": {
      "terms": {"field": "symbol"},
      "aggs": {
        "time_buckets": {
          "date_histogram": {
            "field": "execution_timestamp",
            "fixed_interval": "30m",
            "min_doc_count": 4
          },
          "aggs": {
            "unique_accounts": {"cardinality": {"field": "account_id"}},
            "accounts": {"terms": {"field": "account_id"}}
          }
        }
      }
    }
  }
}
```

### Detection Logic
- Groups trades by symbol and 30-minute time windows
- Requires minimum 4 accounts for coordination pattern
- Calculates coordination scores based on:
  - Same-direction trading (all buying or selling)
  - Number of accounts involved (2 points per account)
  - Total volume thresholds (15 points for >10,000 shares)
- Minimum score threshold: 20 points

### Sample Detection Result
```
Symbol: CORP_BOND_MAT_H | Time: 2025-08-26T20:30:00.000Z
👥 Accounts Involved: 4
📊 Total Volume: 1,400 shares  
💸 Total Value: $123,646.00
📈 Trade Types: {'sell': 4}
⚠️  Coordination Score: 33.0
🎯 Sample Accounts: ACC01296-e973, ACC00567-a43f, ACC05997-ad57, ACC02591-2eda
```

**Analysis**: Four accounts simultaneously sold the same corporate bond within a 30-minute window, all at nearly identical prices ($88.31-$88.37), suggesting potential coordination.

---

## Advanced Query Examples

### 1. High-Frequency Trading Detection
```elasticsearch
GET /financial_trades/_search
{
  "size": 0,
  "query": {
    "range": {"execution_timestamp": {"gte": "now-1d"}}
  },
  "aggs": {
    "accounts": {
      "terms": {"field": "account_id"},
      "aggs": {
        "trade_count": {"value_count": {"field": "trade_id"}},
        "avg_time_between_trades": {
          "avg": {
            "script": "doc['execution_timestamp'].value.millis"
          }
        }
      }
    }
  }
}
```

### 2. Insider Trading Indicators
```elasticsearch
GET /financial_trades/_search
{
  "size": 0,
  "query": {
    "bool": {
      "must": [
        {"range": {"execution_timestamp": {"gte": "now-1h", "lte": "now"}}},
        {"term": {"order_status": "executed"}}
      ]
    }
  },
  "aggs": {
    "symbols": {
      "terms": {"field": "symbol"},
      "aggs": {
        "volume_spike": {"sum": {"field": "quantity"}},
        "unique_accounts": {"cardinality": {"field": "account_id"}}
      }
    }
  }
}
```

### 3. Geographic Clustering Analysis
```elasticsearch
POST /financial_accounts/_search
{
  "size": 0,
  "aggs": {
    "states": {
      "terms": {"field": "state"},
      "aggs": {
        "zip_codes": {
          "terms": {"field": "zip_code", "size": 20},
          "aggs": {
            "account_count": {"value_count": {"field": "account_id"}}
          }
        }
      }
    }
  }
}
```

---

## Implementation & Usage

### Running the Analysis
```bash
# Set Elasticsearch credentials
export ES_ENDPOINT_URL="your-elasticsearch-endpoint"
export ES_API_KEY="your-api-key"

# Run complete fraud detection suite
python3 fraud_detection_queries.py
```

### Key Files
- **`fraud_detection_queries.py`** - Main detection system
- **`fraud_detection_results.json`** - Latest analysis results
- **`fraud_detection_examples.md`** - This documentation

### Performance Metrics
- **Dataset Size**: 262,018 trade records
- **Analysis Speed**: ~12 seconds for complete suite
- **Memory Usage**: Optimized aggregation queries
- **Scalability**: Designed for millions of records

### Customization Options
```python
# Adjust detection thresholds
detector.detect_unusual_trading_volume(
    days_back=30,           # Analysis window
    volume_threshold=2.5    # Suspicion multiplier
)

detector.detect_price_manipulation_patterns(
    time_window_minutes=120 # Offsetting trade window
)

detector.detect_cross_account_coordination(
    time_window_minutes=30, # Coordination window
    min_accounts=4         # Minimum accounts for pattern
)
```

---

## Regulatory Compliance Applications

### Anti-Money Laundering (AML)
- Volume anomaly detection for structuring identification
- Cross-account pattern detection for layering schemes
- Geographic clustering for suspicious entity networks

### Market Abuse Detection  
- Price manipulation pattern recognition
- Insider trading timeline analysis
- Coordinated trading scheme identification

### Risk Management
- Real-time anomaly alerts
- Account behavior profiling
- Portfolio concentration risk assessment

### Audit & Compliance Reporting
- Automated suspicious activity reporting (SAR)
- Trading pattern documentation
- Regulatory inquiry response preparation

---

*This fraud detection system provides comprehensive coverage of common financial trading fraud patterns while maintaining high performance and scalability for large datasets.*