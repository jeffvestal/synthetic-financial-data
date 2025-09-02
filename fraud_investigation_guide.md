# Fraud Investigation Guide for Elasticsearch Analysts

This guide provides investigation techniques and Elasticsearch queries to discover the fraud scenarios generated in the synthetic financial dataset. The scenarios are designed to be realistic and discoverable through proper analysis techniques.

## Overview of Generated Fraud Scenarios

The system generates three types of fraudulent trading patterns mixed within legitimate trading data:

1. **🕵️ Insider Trading** - Pre-announcement coordinated trading
2. **🔄 Wash Trading** - Circular trading to inflate volume
3. **🎯 Pump & Dump** - Coordinated price manipulation schemes

---

## 1. Insider Trading Investigation

### Pattern Description
- **5-15 accounts** coordinate trades 12-48 hours BEFORE news announcements
- **Volume spikes** of 300-800% above normal trading
- **Timeline correlation** between unusual trading and subsequent news
- **Account clustering** by risk profile (High/Very High accounts more likely)

### Key Investigation Queries

#### A) Find Pre-Announcement Trading Spikes
```elasticsearch
GET /financial_trades/_search
{
  "size": 0,
  "query": {
    "bool": {
      "must": [
        {"term": {"order_status": "executed"}},
        {"range": {"execution_timestamp": {"gte": "2025-07-01", "lte": "2025-08-31"}}}
      ]
    }
  },
  "aggs": {
    "symbols": {
      "terms": {"field": "symbol", "size": 50},
      "aggs": {
        "daily_volume": {
          "date_histogram": {
            "field": "execution_timestamp",
            "calendar_interval": "1d"
          },
          "aggs": {
            "total_volume": {"sum": {"field": "quantity"}},
            "unique_accounts": {"cardinality": {"field": "account_id"}},
            "account_list": {"terms": {"field": "account_id", "size": 20}}
          }
        }
      }
    }
  }
}
```

#### B) Detect Account Coordination Patterns
```elasticsearch
GET /financial_trades/_search
{
  "size": 0,
  "query": {
    "bool": {
      "must": [
        {"term": {"scenario_type": "insider_trading"}},
        {"term": {"order_status": "executed"}}
      ]
    }
  },
  "aggs": {
    "schemes": {
      "terms": {"field": "scenario_symbol"},
      "aggs": {
        "timeline": {
          "date_histogram": {
            "field": "execution_timestamp", 
            "fixed_interval": "1h"
          },
          "aggs": {
            "volume": {"sum": {"field": "quantity"}},
            "accounts": {"cardinality": {"field": "account_id"}},
            "avg_price": {"avg": {"field": "execution_price"}}
          }
        },
        "coordinated_accounts": {
          "terms": {"field": "account_id", "size": 30}
        }
      }
    }
  }
}
```

#### C) Timeline Analysis for Specific Symbol
```elasticsearch
GET /financial_trades/_search
{
  "query": {
    "bool": {
      "must": [
        {"term": {"symbol": "TSLA"}},
        {"range": {"execution_timestamp": {"gte": "2025-07-15", "lte": "2025-07-17"}}}
      ]
    }
  },
  "sort": [{"execution_timestamp": {"order": "asc"}}],
  "size": 100
}
```

### Investigation Checklist
- [ ] Look for symbols with sudden volume spikes (>300% increase)
- [ ] Check if volume increase occurred 12-48 hours before news
- [ ] Identify accounts that traded during suspicious periods
- [ ] Cross-reference account risk profiles (High/Very High clustering)
- [ ] Verify profit-taking trades 1-6 hours after news announcement

---

## 2. Wash Trading Investigation

### Pattern Description
- **2-4 accounts** trade the same symbols back and forth
- **Minimal price spreads** (±0.1-0.3%) to avoid losses  
- **High frequency trading** with artificial volume inflation
- **Account relationships** (same state, similar names, sequential IDs)
- **20% cancellation rate** for realism

### Key Investigation Queries

#### A) Find Circular Trading Patterns
```elasticsearch
GET /financial_trades/_search
{
  "size": 0,
  "query": {
    "bool": {
      "must": [
        {"term": {"scenario_type": "wash_trading"}},
        {"term": {"order_status": "executed"}}
      ]
    }
  },
  "aggs": {
    "wash_rings": {
      "terms": {"field": "wash_ring_id"},
      "aggs": {
        "accounts": {"terms": {"field": "account_id"}},
        "symbols": {"terms": {"field": "symbol"}},
        "total_volume": {"sum": {"field": "quantity"}},
        "total_trades": {"value_count": {"field": "trade_id"}},
        "price_range": {
          "stats": {"field": "execution_price"}
        }
      }
    }
  }
}
```

#### B) Identify Offsetting Trade Pairs
```elasticsearch
GET /financial_trades/_search
{
  "query": {
    "bool": {
      "must": [
        {"exists": {"field": "counterpart_account"}},
        {"term": {"scenario_type": "wash_trading"}}
      ]
    }
  },
  "sort": [{"execution_timestamp": {"order": "asc"}}],
  "size": 50,
  "_source": ["trade_id", "account_id", "counterpart_account", "symbol", "trade_type", "quantity", "execution_price", "execution_timestamp"]
}
```

#### C) Analyze Geographic Account Clustering
```elasticsearch
GET /financial_accounts/_search
{
  "size": 0,
  "aggs": {
    "states": {
      "terms": {"field": "state", "size": 50},
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

### Investigation Checklist
- [ ] Look for accounts trading same symbols with minimal price differences
- [ ] Check for rapid back-and-forth trading between same accounts
- [ ] Verify high trade frequency with low net position changes
- [ ] Investigate account relationships (geographic, name similarity, ID patterns)
- [ ] Calculate volume inflation vs. actual position changes

---

## 3. Pump & Dump Investigation

### Pattern Description
- **8-20 accounts** coordinate across three phases:
  - **Accumulation**: 5-10 days of gradual buying
  - **Pump**: 2-6 hours of aggressive coordinated buying (+15-40% price)
  - **Dump**: 1-3 hours of rapid coordinated selling (-25-50% price)
- **Volume multipliers**: 2-4x (accumulation), 8-20x (pump), 15-35x (dump)
- **Coordination types**: Tight, loose, or mixed timing patterns

### Key Investigation Queries

#### A) Detect Multi-Phase Price Manipulation
```elasticsearch
GET /financial_trades/_search
{
  "size": 0,
  "query": {
    "bool": {
      "must": [
        {"term": {"scenario_type": "pump_and_dump"}},
        {"term": {"order_status": "executed"}}
      ]
    }
  },
  "aggs": {
    "schemes": {
      "terms": {"field": "pump_scheme_id"},
      "aggs": {
        "phases": {
          "terms": {"field": "scenario_phase"},
          "aggs": {
            "volume_by_phase": {"sum": {"field": "quantity"}},
            "trades_by_phase": {"value_count": {"field": "trade_id"}},
            "price_stats": {"stats": {"field": "execution_price"}},
            "timeline": {
              "date_histogram": {
                "field": "execution_timestamp",
                "fixed_interval": "1h"
              },
              "aggs": {
                "hourly_volume": {"sum": {"field": "quantity"}},
                "hourly_accounts": {"cardinality": {"field": "account_id"}}
              }
            }
          }
        },
        "coordinated_accounts": {
          "terms": {"field": "account_id", "size": 25}
        },
        "target_symbol": {
          "terms": {"field": "scenario_symbol", "size": 1}
        }
      }
    }
  }
}
```

#### B) Timeline Analysis of Pump Phase
```elasticsearch
GET /financial_trades/_search
{
  "query": {
    "bool": {
      "must": [
        {"term": {"scenario_phase": "pump"}},
        {"term": {"scenario_type": "pump_and_dump"}}
      ]
    }
  },
  "sort": [{"execution_timestamp": {"order": "asc"}}],
  "size": 100,
  "_source": ["account_id", "symbol", "trade_type", "quantity", "execution_price", "execution_timestamp", "pump_scheme_id"]
}
```

#### C) Cross-Phase Account Analysis
```elasticsearch
GET /financial_trades/_search
{
  "size": 0,
  "query": {
    "term": {"pump_scheme_id": "SCHEME-12345678"}
  },
  "aggs": {
    "account_participation": {
      "terms": {"field": "account_id", "size": 30},
      "aggs": {
        "phases": {
          "terms": {"field": "scenario_phase"},
          "aggs": {
            "trade_types": {"terms": {"field": "trade_type"}},
            "total_volume": {"sum": {"field": "quantity"}},
            "avg_price": {"avg": {"field": "execution_price"}}
          }
        }
      }
    }
  }
}
```

### Investigation Checklist
- [ ] Identify symbols with 15-40% price increases over 2-6 hour periods
- [ ] Look for preceding accumulation period (5-10 days)
- [ ] Check for rapid dump phase following the pump
- [ ] Verify same accounts participated across all phases
- [ ] Calculate coordination timing (tight vs. loose patterns)
- [ ] Cross-reference with any related negative news post-dump

---

## Advanced Investigation Techniques

### 1. Cross-Reference with Account Profiles
```elasticsearch
GET /financial_accounts/_search
{
  "query": {
    "terms": {
      "account_id": ["ACC00001-5074", "ACC00002-3c56", "ACC00003-a87a"]
    }
  },
  "_source": ["account_id", "first_name", "last_name", "state", "zip_code", "risk_profile", "total_portfolio_value"]
}
```

### 2. News Event Correlation
```elasticsearch
GET /financial_news/_search
{
  "query": {
    "bool": {
      "must": [
        {"term": {"primary_symbol": "TSLA"}},
        {"range": {"published_date": {"gte": "2025-07-15", "lte": "2025-07-17"}}}
      ]
    }
  },
  "sort": [{"published_date": {"order": "asc"}}]
}
```

### 3. Volume Anomaly Detection
```elasticsearch
GET /financial_trades/_search
{
  "size": 0,
  "query": {
    "bool": {
      "must": [
        {"range": {"execution_timestamp": {"gte": "2025-07-01", "lte": "2025-08-31"}}},
        {"term": {"order_status": "executed"}}
      ]
    }
  },
  "aggs": {
    "symbols": {
      "terms": {"field": "symbol", "size": 100},
      "aggs": {
        "daily_stats": {
          "date_histogram": {
            "field": "execution_timestamp",
            "calendar_interval": "1d"
          },
          "aggs": {
            "daily_volume": {"sum": {"field": "quantity"}},
            "unique_traders": {"cardinality": {"field": "account_id"}}
          }
        },
        "volume_variance": {
          "extended_stats": {
            "script": {
              "source": "doc['quantity'].value"
            }
          }
        }
      }
    }
  }
}
```

---

## Red Flags & Investigation Priorities

### High Priority Indicators
1. **Volume spikes >500%** within 24-48 hours
2. **>10 accounts** trading same symbol simultaneously  
3. **Price movements >20%** with coordinated trading
4. **Circular trading patterns** with minimal price spreads
5. **Timeline correlation** between trading and news events

### Medium Priority Indicators
1. **Geographic clustering** of trading accounts
2. **Sequential account IDs** trading together
3. **Risk profile mismatches** (conservative accounts doing high-risk trades)
4. **High cancellation rates** in specific trading rings
5. **After-hours trading** coordination

### Investigation Workflow
1. **Start with volume analysis** - identify unusual trading patterns
2. **Timeline analysis** - map trading activity against news events  
3. **Account clustering** - find relationships between coordinating accounts
4. **Cross-reference data** - link trades, accounts, holdings, and news
5. **Pattern validation** - confirm fraudulent intent vs. coincidence

---

## Sample Investigation Scenarios

### Scenario A: TSLA Insider Trading (July 16, 2025)
- **Timeline**: Heavy buying 36 hours before breakthrough announcement
- **Accounts**: 12 high-risk accounts coordinated purchases
- **Volume**: 650% increase from normal trading
- **Outcome**: All accounts sold within 4 hours post-announcement for 18% profit

### Scenario B: Wash Trading Ring (August 2-8, 2025)  
- **Pattern**: 4 accounts in Texas (same zip code area) circular trading
- **Symbols**: AAPL, MSFT with 0.15% average price spreads
- **Frequency**: 347 trades over 6 days, minimal net position changes
- **Red Flags**: Sequential account IDs, geographic clustering

### Scenario C: NVDA Pump & Dump (July 22-29, 2025)
- **Accumulation**: 15 accounts slowly accumulate over 7 days
- **Pump**: 4-hour coordinated buying drives price up 28%
- **Dump**: 90-minute coordinated selling crashes price 42%
- **Cover**: Negative product defect news published 2 hours post-dump

---

## Tools & Queries Quick Reference

### Essential Elasticsearch Aggregations
- `terms`: Group by field values (accounts, symbols, phases)
- `date_histogram`: Time-based analysis (hourly, daily patterns) 
- `cardinality`: Count unique values (unique accounts, symbols)
- `stats/extended_stats`: Statistical analysis (price, volume ranges)
- `range`: Time window filtering (before/after events)

### Key Fields for Investigation
- **Trades**: `account_id`, `symbol`, `trade_type`, `quantity`, `execution_price`, `execution_timestamp`, `scenario_type`, `wash_ring_id`, `pump_scheme_id`
- **Accounts**: `account_id`, `risk_profile`, `state`, `zip_code`, `total_portfolio_value`
- **News**: `primary_symbol`, `published_date`, `sentiment`, `title`

### Performance Tips
- Use `size: 0` for aggregation-only queries
- Filter by date ranges to improve performance
- Use `_source` filtering to return only needed fields
- Combine multiple criteria in `bool` queries for efficiency

---

*This investigation guide is designed for training purposes using synthetic financial data. All scenarios and patterns are artificially generated for educational use in fraud detection training programs.*