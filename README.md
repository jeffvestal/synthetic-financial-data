# Synthetic Financial Data Generator 🏦

Generate realistic financial datasets with trading activity, market events, and **fraud scenarios** for Elasticsearch analysis training. Create accounts, holdings, trades, news, reports, and sophisticated fraud patterns with AI-generated content.

![Header Image](synthetic-financial-data-header.png "Synthetic Financial Data Generator")

## 🎯 What Is This?

A comprehensive Python toolkit that creates realistic synthetic financial data for testing, demos, fraud detection training, and development:

### 🏢 **Core Financial Data**
- **7,000+ Accounts**: Customer portfolios with risk profiles and geographic distribution
- **Holdings**: Stock/ETF/bond positions with purchase history and current valuations
- **262,000+ Trades**: Realistic trading activity with proper pricing and timing patterns
- **Asset Details**: Current prices, sectors, and metadata for 100+ financial instruments

### 📰 **Market Intelligence** 
- **550+ News Articles**: AI-generated market news with sentiment analysis and entity extraction
- **120+ Financial Reports**: Company reports, earnings summaries, and analyst notes
- **Market Events**: Realistic market crashes, volatility spikes, and targeted bad news scenarios

### 🕵️ **Fraud Detection Training** (NEW)
- **Insider Trading Scenarios**: Pre-announcement coordinated trading patterns
- **Wash Trading Rings**: Circular trading between related accounts to inflate volume
- **Pump & Dump Schemes**: Multi-phase coordinated price manipulation
- **Investigation Framework**: Complete guide with Elasticsearch queries for analysts

All content uses Google's Gemini AI for realistic language and automatically ingests into Elasticsearch with proper index mappings and semantic search capabilities.

## 🚀 Quick Start

Get running in 30 seconds:

### 1. Install & Setup
```bash
git clone https://github.com/yourusername/synthetic-financial-data.git
cd synthetic-financial-data
pip install -r requirements.txt

# Set Elasticsearch credentials
export ES_ENDPOINT_URL="your-elasticsearch-endpoint"
export ES_API_KEY="your-elasticsearch-api-key"

# Optional: Set Gemini API key for generating new data
export GEMINI_API_KEY="your-gemini-api-key"  
```

### 2. Interactive Control Panel (Recommended)
```bash
# Launch interactive menu system with live progress dashboard
python3 control.py
```

**Interactive Options:**
- **🚀 Quick Start**: Generate all data with defaults (7K accounts, 550+ articles, 262K+ trades)
- **⚙️ Custom Generation**: Configure specific data volumes and types
- **💥 Trigger Events**: Market crashes, bad news, or fraud scenarios
- **🗄️ Manage Indices**: Elasticsearch index management
- **📊 Check Status**: System status and data statistics

### 3. Alternative: Load Existing Data Only
```bash
# Load all pre-generated data (no AI key required)
python3 load_fresh_data.py

# Or use the streamlined loader
python3 load_all_data.py
```

**That's it!** You now have realistic financial data with trading activity and fraud scenarios in Elasticsearch, ready for analysis training and demos.

## 💡 Common Use Cases

### 📊 Data Loading (No AI Key Needed)
Load pre-generated data files into Elasticsearch:

```bash
# Interactive mode - recommended
python3 control.py
# Select: 🚀 Quick Start or 🗄️ Manage Indices

# Command line mode
python3 load_fresh_data.py                    # Load recent data files
python3 load_all_data.py                      # Load all existing data

# Direct script execution  
python3 scripts/generate_holdings_accounts.py  # Just accounts & holdings
```

### 🤖 Generate New Data (Requires Gemini API Key)
Create fresh synthetic data with AI-generated content:

```bash
# Set API key
export GEMINI_API_KEY="your_key_here"

# Interactive generation (recommended)
python3 control.py
# Select: ⚙️ Custom Generation

# Command line generation
python3 control.py --quick-start                              # Full dataset
python3 control.py --custom --accounts --num-accounts 1000    # Custom volumes
```

### 🎭 Market Events & Scenarios
Create realistic market scenarios for demos and training:

#### Traditional Market Events
```bash
# Interactive mode
python3 control.py → 💥 Trigger Events

# Command line mode
python3 control.py --trigger-event market_crash    # Broad market selloff
python3 control.py --trigger-event bad_news        # Targeted company events
python3 control.py --trigger-event volatility      # Market volatility spike
```

#### 🕵️ Fraud Scenarios (NEW)
Generate sophisticated fraud patterns for analyst training:

```bash
# Interactive mode
python3 control.py → 💥 Trigger Events → Select fraud scenario

# Command line mode  
python3 control.py --trigger-event insider_trading    # Pre-announcement trading
python3 control.py --trigger-event wash_trading       # Circular trading rings
python3 control.py --trigger-event pump_and_dump      # Price manipulation

# Direct script execution with custom parameters
python3 scripts/generate_insider_trading.py --num-scenarios 5 --elasticsearch
python3 scripts/generate_wash_trading.py --num-scenarios 3 --elasticsearch  
python3 scripts/generate_pump_and_dump.py --num-scenarios 2 --elasticsearch
```

**Fraud Scenarios Include:**
- **Insider Trading**: 5-15 accounts coordinate trades 12-48 hours before news announcements
- **Wash Trading**: 2-4 related accounts circular trade with minimal price spreads
- **Pump & Dump**: 8-20 accounts execute multi-phase price manipulation over 5-10 days

#### Bad News Event
Target specific companies with negative events:
```bash  
python3 control.py --trigger-event bad_news
```
**What it creates:**
- 5 negative news articles about Tesla (TSLA)
- 2 negative reports about Freeport-McMoRan (FCX)
- Company-specific issues: recalls, production problems, regulatory issues

#### Volatility Spike
Create market uncertainty and mixed sentiment:
```bash
python3 control.py --trigger-event volatility
```
**What it creates:**
- Articles about VIX and volatility instruments (UVXY, SVXY)
- Mixed positive/negative sentiment patterns
- Geopolitical tensions and uncertain economic data themes
- Trading opportunity focused content

**Perfect for:**
- Live demos showing "breaking news" impact
- Testing dashboards with different sentiment scenarios  
- Simulating market stress conditions
- Creating realistic time-sequenced events

### ⏰ Timestamp Management for Demos
```bash
# Make old data appear fresh
python3 update_es_timestamps.py

# Time-sequence data (news yesterday, reports today)
python3 update_es_timestamps.py --indices news --offset -24
python3 update_es_timestamps.py --indices reports --offset 0
```

### 📓 Jupyter Notebook / Google Colab
```python
# Set credentials
import os
os.environ['ES_ENDPOINT_URL'] = 'https://localhost:9200'  
os.environ['ES_API_KEY'] = 'your_elasticsearch_key'

# Load data (works without Gemini key)
!python3 load_all_data.py

# Generate new data (requires Gemini key)
os.environ['GEMINI_API_KEY'] = 'your_gemini_key'
!python3 control.py --quick-start --non-interactive
```

## ✨ What Else Can It Do?

### Data Types
- **7,000+ Accounts**: Personal info, portfolios, risk profiles
- **70K-175K Holdings**: Stock/ETF/bond positions with realistic values
- **100+ Assets**: Current prices, sectors, index memberships  
- **500+ News Articles**: AI-generated market news with sentiment
- **100+ Reports**: Earnings summaries and analyst notes

### Smart Features
- **10-15x Faster Loading**: Direct scripts bypass control.py overhead
- **Real-time Progress**: Live docs/sec rates and progress bars  
- **Semantic Search Ready**: ELSER-compatible field mappings
- **Market Event Simulation**: Create realistic breaking news scenarios - market crashes, company scandals, volatility spikes
- **Timestamp Management**: Make historical data appear current
- **Index Management**: Auto-create, validate, recreate Elasticsearch indices

### Generation Control
```bash
# Interactive control panel
python3 control.py

# Menu options:
# 1. Quick Start - Generate everything 
# 2. Custom Generation - Pick data types and volumes
# 3. Trigger Events - Market crashes, bad news, volatility
# 4. Check Status - System health and data statistics  
# 5. Manage Indices - Elasticsearch index operations
# 6. Configure Settings - API keys, presets, advanced options
```

### Performance
- **Direct Loading**: ~20 seconds for full dataset
- **Control.py Loading**: Several minutes (use for configuration only)
- **Timestamp Updates**: ~100K docs/sec using in-place ES updates
- **Optimized Settings**: 24 workers, 1000 batch size pre-configured

## ⚙️ Setup & Configuration

### API Keys
```bash
# Required for generating new data
export GEMINI_API_KEY="your_google_gemini_key"

# Required for Elasticsearch operations  
export ES_ENDPOINT_URL="https://localhost:9200"
export ES_API_KEY="your_elasticsearch_key" 

# Or create .env file
echo "GEMINI_API_KEY=your_key" >> .env
echo "ES_API_KEY=your_es_key" >> .env
```

### What Needs What?
| Task | Gemini Key | ES Key | 
|------|------------|---------|
| Load existing data | ❌ | ✅ |
| Generate new data | ✅ | Optional |
| Update timestamps | ❌ | ✅ |
| Check status | ❌ | ❌ |

### Quick Troubleshooting

**Slow loading?** Use direct scripts instead of control.py:
```bash
# SLOW (several minutes)
python3 control.py --custom --elasticsearch

# FAST (20 seconds)  
python3 load_all_data.py
```

**Connection issues?** Test your setup:
```bash
# Check ES connection
python3 control.py --check-indices

# Check system status
python3 control.py --status
```

**Missing API key?** Many operations work without keys:
```bash
# These work without any API keys
python3 load_all_data.py           # Load existing data
python3 update_es_timestamps.py    # Update timestamps  
python3 control.py --status        # Check status
```

## 🔧 Advanced

<details>
<summary>Click to expand advanced topics</summary>

### Architecture
```
synthetic-financial-data/
├── control.py                 # Interactive control script
├── load_all_data.py          # Fast data loader (recommended)
├── update_es_timestamps.py   # Fast timestamp updater
├── requirements.txt          # Dependencies
├── scripts/                  # Core generation scripts
├── lib/                      # Control panel libraries
├── elasticsearch/            # Index mappings
├── prompts/                  # AI prompt templates
└── generated_data/           # Output files (JSONL)
```

### Performance Optimization
- **TaskExecutor Overhead**: control.py has 10-15x subprocess overhead in Colab/Jupyter
- **Optimal Settings**: 24 workers, 1000 batch size for maximum throughput
- **Direct Scripts**: Always faster than control.py for data operations
- **Bottleneck**: TaskExecutor subprocess management, not Elasticsearch speed

### API Reference
```python
from scripts.common_utils import create_elasticsearch_client, ingest_data_to_es
from lib.index_manager import IndexManager

# Direct data loading
es_client = create_elasticsearch_client()  
ingest_data_to_es(es_client, 'file.jsonl', 'index_name', 'id_field')

# Index management
manager = IndexManager(es_client)
manager.get_index_status('financial_accounts')
```

### Custom Symbol Configuration
Edit `scripts/symbols_config.py`:
```python
STOCK_SYMBOLS_AND_INFO = {
    'AAPL': {'name': 'Apple Inc.', 'sector': 'Technology'},
    'MSFT': {'name': 'Microsoft Corp.', 'sector': 'Technology'},
    # Add your symbols here
}
```

### Elasticsearch Index Mappings
All indices auto-created with proper mappings from `elasticsearch/index_mappings.json`:
- **Semantic search fields** for titles and content
- **Lookup mode** for optimized storage
- **Proper field types** (keyword, text, date, float)

</details>

## 📄 Sample Documents

<details>
<summary>Click to see example documents from each index</summary>

Examples of what each document looks like in the five indices:

### financial_accounts
Customer account with portfolio information:
```json
{
  "account_id": "ACC00000-5506",
  "first_name": "Brian",
  "last_name": "Solomon",
  "account_holder_name": "Brian Solomon",
  "state": "NE",
  "zip_code": "04946",
  "account_type": "Conservative",
  "risk_profile": "Medium",
  "contact_preference": "email",
  "total_portfolio_value": 4912549.57,
  "last_updated": "2025-07-06T20:51:07"
}
```

### financial_holdings
Stock/ETF/Bond position owned by an account:
```json
{
  "holding_id": "ACC00000-5506-H00-2692",
  "account_id": "ACC00000-5506",
  "symbol": "EWO",
  "quantity": 37,
  "purchase_price": 128.95,
  "purchase_date": "2019-10-03T03:48:27",
  "is_high_value": false,
  "last_updated": "2025-07-06T20:51:07"
}
```

### financial_asset_details
Current pricing and metadata for financial instruments:
```json
{
  "symbol": "EWO",
  "asset_name": "iShares MSCI Austria Capped ETF",
  "instrument_type": "ETF",
  "sector": "Single Country Equity",
  "index_membership": ["MSCI Austria"],
  "country_of_origin": "Austria",
  "current_price": {
    "price": 231.41,
    "last_updated": "2025-07-06T20:51:07"
  },
  "previous_closing_price": {
    "price": 234.36,
    "prev_close_date": "2025-07-03T20:51:07"
  },
  "bond_details": null,
  "last_updated": "2025-07-06T20:51:07"
}
```

### financial_news
AI-generated market news article:
```json
{
  "article_id": "54ab5cd2-e605-417c-97d1-b178db4d23f2",
  "title": "Vanguard's VXUS ETF Rallies as Major Holding Cleared",
  "content": "Vanguard's Total International Stock ETF (VXUS) experienced a notable uptick...",
  "source": "Bloomberg",
  "published_date": "2025-07-14T06:04:22",
  "url": "http://fakenews.com/article/8c65ff41",
  "entities": ["VXUS", "Vanguard Total International Stock ETF"],
  "sentiment": "positive",
  "primary_symbol": "VXUS",
  "last_updated": "2025-07-14T06:04:36"
}
```

### financial_reports
Company earnings report or analyst note:
```json
{
  "report_id": "e91d6e8e-8c23-4bc5-97be-a38e0d2d462d",
  "title": "Altria Group (MO) Q4 Earnings Summary",
  "content": "Altria Group Inc.'s Q4 summary highlighted significant strategic initiatives...",
  "company_symbol": "MO",
  "report_type": "Q4 Earnings Summary",
  "report_date": "2025-07-14T08:06:28",
  "author": "AI Financial Insights",
  "url": "http://fakereports.com/company/MO/03dd827e",
  "entities": ["Altria Group Inc.", "Consumer Staples"],
  "sentiment": "neutral",
  "primary_symbol": "MO",
  "last_updated": "2025-07-14T08:06:45"
}
```

### financial_trades (NEW)
Realistic trading activity with fraud scenario support:
```json
{
  "trade_id": "TRD-20250604-ecc5e298",
  "account_id": "ACC00000-5506",
  "symbol": "BAC",
  "trade_type": "buy",
  "order_type": "market", 
  "order_status": "executed",
  "quantity": 1978.0,
  "execution_price": 178.01,
  "trade_cost": 352103.78,
  "execution_timestamp": "2025-06-04T11:15:43",
  "last_updated": "2025-09-02T13:01:37",
  "scenario_type": "insider_trading",     // Only for fraud scenarios
  "pump_scheme_id": "SCHEME-12345678"     // Links related fraud trades
}
```

</details>

## 🕵️ Fraud Investigation Training

The system generates realistic fraud scenarios mixed with legitimate trading data for analyst training:

### Investigation Resources
- **📋 [Fraud Investigation Guide](fraud_investigation_guide.md)** - Complete investigation techniques and Elasticsearch queries
- **🔍 [Example Queries](semantic_search_examples.md)** - Semantic search examples for finding fraud patterns
- **📊 Generated Scenarios** - Pre-built fraud patterns ready for discovery

### Sample Investigation Queries

#### Find Insider Trading Patterns
```elasticsearch
GET /financial_trades/_search
{
  "query": {
    "bool": {
      "must": [
        {"term": {"scenario_type": "insider_trading"}},
        {"range": {"execution_timestamp": {"gte": "2025-07-01"}}}
      ]
    }
  },
  "aggs": {
    "insider_schemes": {
      "terms": {"field": "scenario_symbol"},
      "aggs": {
        "coordinated_accounts": {"cardinality": {"field": "account_id"}},
        "timeline": {
          "date_histogram": {
            "field": "execution_timestamp",
            "fixed_interval": "1h"
          }
        }
      }
    }
  }
}
```

#### Detect Wash Trading Rings
```elasticsearch
GET /financial_trades/_search
{
  "query": {"exists": {"field": "wash_ring_id"}},
  "aggs": {
    "wash_rings": {
      "terms": {"field": "wash_ring_id"},
      "aggs": {
        "participants": {"terms": {"field": "account_id"}},
        "symbols": {"terms": {"field": "symbol"}},
        "trade_pairs": {
          "terms": {"field": "counterpart_account", "size": 10}
        }
      }
    }
  }
}
```

### Investigation Training Scenarios
1. **🕵️ Insider Trading**: Find accounts that traded TSLA 36 hours before breakthrough announcement
2. **🔄 Wash Trading**: Discover 4 Texas accounts circular trading AAPL with 0.15% spreads
3. **🎯 Pump & Dump**: Trace NVDA price manipulation from accumulation through dump phases

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines and feel free to submit issues or pull requests.

For support, report issues at: https://github.com/anthropics/claude-code/issues

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.