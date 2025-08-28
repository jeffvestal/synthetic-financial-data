# Synthetic Financial Data Generator 🏦

Generate realistic financial datasets in seconds. Create accounts, holdings, news articles, and reports with AI-generated content, ready for Elasticsearch.

![Header Image](synthetic-financial-data-header.png "Synthetic Financial Data Generator")

## 🎯 What Is This?

A Python tool that creates realistic synthetic financial data for testing, demos, and development:
- **Accounts**: Customer portfolios with risk profiles  
- **Holdings**: Stock/ETF/bond positions with purchase history
- **News**: AI-generated market articles with sentiment analysis
- **Reports**: Company earnings and analyst notes

All data uses Google's Gemini AI for realistic content and loads into Elasticsearch with semantic search mappings.

## 🚀 Quick Start

Get running in 30 seconds:

### 1. Install
```bash
git clone https://github.com/yourusername/synthetic-financial-data.git
cd synthetic-financial-data
pip install -r requirements.txt
```

### 2. Load Sample Data (20 seconds)
```bash
# Load all existing data - accounts, holdings, news, reports
python3 load_all_data.py
```

### 3. Update Timestamps for Demo
```bash
# Make data appear from 4 hours ago (perfect for demos)
python3 update_es_timestamps.py --offset -4

# Or make it current
python3 update_es_timestamps.py
```

### 4. Optional: Interactive Setup
```bash
# Full control panel with menus and configuration
python3 control.py
```

**That's it!** You now have realistic financial data in Elasticsearch ready for queries, dashboards, and demos.

## 💡 Common Use Cases

### Load Existing Data (No AI Key Needed)
Most common scenario - you have the generated data files and want them in Elasticsearch:

```bash
# Load everything (recommended)
python3 load_all_data.py

# Load specific indices only  
python3 load_specific_indices.py --holdings --news

# Quick demo subset (5K holdings instead of 122K)
python3 load_demo_subset.py

# Reload for clean state (delete + reload)  
python3 quick_reload.py --all
```

### Generate New Data (Requires Gemini API Key)
Set your API key first:
```bash
export GEMINI_API_KEY="your_key_here"
```

Then generate:
```bash
# Generate everything with defaults (7K accounts, 500+ articles)
python3 control.py --quick-start

# Custom generation with specific volumes
python3 control.py --custom --accounts --num-accounts 1000
```

### Demo Scenarios
```bash
# Create market crash scenario
python3 control.py --trigger-event market_crash

# Make old data appear fresh
python3 update_es_timestamps.py

# Time-sequence data (news yesterday, reports today)
python3 update_es_timestamps.py --indices news --offset -24
python3 update_es_timestamps.py --indices reports --offset 0
```

### Jupyter Notebook / Google Colab
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
- **Market Events**: Trigger crashes, volatility, bad news scenarios
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

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines and feel free to submit issues or pull requests.

For support, report issues at: https://github.com/anthropics/claude-code/issues

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.