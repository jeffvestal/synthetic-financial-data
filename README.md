# Synthetic Financial Data Generator 🏦

A powerful Python toolkit for generating realistic synthetic financial data for testing, demos, and development. Create thousands of accounts, holdings, news articles, and reports with AI-generated content, all ready for ingestion into Elasticsearch.


![Header Image](synthetic-financial-data-header.png "Synthetic Financial Data Generator")

## 📋 Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Data Structure](#data-structure)
- [API Documentation](#api-documentation)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## 🎯 Overview

The Synthetic Financial Data Generator creates realistic financial datasets including:
- **Customer Accounts**: Personal and portfolio information with risk profiles
- **Holdings**: Stock, ETF, and bond positions with purchase history
- **Asset Details**: Current prices, sectors, and metadata for financial instruments
- **News Articles**: AI-generated market news with sentiment analysis
- **Financial Reports**: Company reports, earnings summaries, and analyst notes

All data is generated using Google's Gemini AI for realistic content and can be automatically ingested into Elasticsearch with proper index mappings for semantic search capabilities.

## ✨ Features

### Core Capabilities
- 🤖 **AI-Powered Generation**: Uses Gemini AI to create realistic financial content
- 📊 **Comprehensive Data Types**: Accounts, holdings, assets, news, and reports
- 🔍 **Elasticsearch Integration**: Automatic index creation with semantic search support
- 🎮 **Interactive Control Panel**: User-friendly CLI with live progress tracking
- 📈 **Scalable Generation**: Create datasets from 10 to 10,000+ records
- 🎯 **Controlled Events**: Trigger specific market events for demo scenarios

### Advanced Features
- **Live Progress Dashboard**: Real-time status updates during generation
- **Index Management**: Create, validate, and manage Elasticsearch indices
- **Configuration Presets**: Save and load custom generation settings
- **Batch Operations**: Queue multiple generation tasks
- **Dry Run Mode**: Preview operations before execution
- **Semantic Search Ready**: ELSER-compatible field mappings
- **Timestamp Management**: Update document timestamps to current time or with custom offsets

## 🏗️ Architecture

```
synthetic-financial-data/
├── control.py                 # Main interactive control script
├── requirements.txt           # Python dependencies
├── scripts/                   # Core generation scripts
│   ├── config.py             # Centralized configuration
│   ├── generate_holdings_accounts.py
│   ├── generate_reports_and_news_new.py
│   ├── trigger_bad_news_event.py
│   ├── common_utils.py       # Shared utilities
│   ├── symbol_manager.py     # Symbol management
│   └── symbols_config.py     # Stock/ETF/Bond definitions
├── lib/                      # Control script libraries
│   ├── menu_system.py        # Interactive menus
│   ├── config_manager.py     # Configuration management
│   ├── task_executor.py      # Task execution engine
│   ├── index_manager.py      # Elasticsearch index management
│   └── timestamp_updater.py  # Timestamp update operations
├── elasticsearch/            # Elasticsearch configuration
│   └── index_mappings.json   # Index mappings and settings
├── prompts/                  # AI prompt templates
│   ├── general_market_news.txt
│   ├── specific_news.txt
│   ├── specific_report.txt
│   └── thematic_sector_report.txt
└── generated_data/           # Output directory
    ├── generated_accounts.jsonl
    ├── generated_holdings.jsonl
    ├── generated_asset_details.jsonl
    ├── generated_news.jsonl
    └── generated_reports.jsonl
```

## 🚀 Installation

### Prerequisites
- Python 3.8+
- Elasticsearch 8.0+ (optional, for data ingestion)
- Google Gemini API key

### Option 1: Automated Setup (Recommended)
Use the automated setup script that creates a virtual environment and installs all dependencies:

```bash
git clone https://github.com/yourusername/synthetic-financial-data.git
cd synthetic-financial-data
python3 setup.py
```

The setup script will:
- ✅ Create a virtual environment in `venv/`
- ✅ Upgrade pip to the latest version
- ✅ Install all required dependencies
- ✅ Provide activation instructions

After setup completes, activate the virtual environment:
```bash
# On macOS/Linux
source venv/bin/activate

# On Windows
venv\Scripts\activate
```

### Option 2: Manual Installation

### Step 1: Clone the Repository
```bash
git clone https://github.com/yourusername/synthetic-financial-data.git
cd synthetic-financial-data
```

### Step 2: Create Virtual Environment (Optional but Recommended)
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

Required packages:
- `google-generativeai` - Gemini AI integration
- `elasticsearch` - Elasticsearch client
- `faker` - Synthetic name/address generation
- `python-dotenv` - Environment variable management
- `rich` - Interactive CLI interface
- `tqdm` - Progress bars

### Step 3: Set Environment Variables

Create a `.env` file in the project root based on your use case:

**For Loading Existing Data Only (No Generation):**
```bash
# Elasticsearch credentials (required for data loading)
ES_ENDPOINT_URL=https://localhost:9200
ES_API_KEY=your_elasticsearch_api_key_here

# Gemini API key NOT required for loading existing data
```

**For Generating New Data:**
```bash
# Required for AI content generation
GEMINI_API_KEY=your_gemini_api_key_here

# Optional for Elasticsearch ingestion
ES_ENDPOINT_URL=https://localhost:9200
ES_API_KEY=your_elasticsearch_api_key_here
```

Or export them directly:
```bash
# For data loading only
export ES_ENDPOINT_URL="https://localhost:9200"
export ES_API_KEY="your_elasticsearch_api_key_here"

# For new data generation (add this)
export GEMINI_API_KEY="your_gemini_api_key_here"
```

**📝 API Key Requirements:**
- **GEMINI_API_KEY**: Only needed for generating new data (accounts, news, reports, events)
- **ES_API_KEY**: Only needed for Elasticsearch operations (loading data, managing indices)
- **Neither key**: Required for checking existing local data files

### Step 4: Verify Installation
```bash
python3 control.py --status
```

**Note**: Always remember to activate your virtual environment before working with the project:
```bash
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate     # On Windows
```

## ⚙️ Configuration

### Default Settings
Configuration is centralized in `scripts/config.py`:

```python
# Generation volumes
- 7,000 accounts
- 10-25 holdings per account
- 500+ news articles
- 100+ financial reports

# Elasticsearch settings
- Batch size: 100 documents
- Timeout: 60 seconds
- Auto-create indices: Yes
```

### Custom Configuration
Modify settings in `scripts/config.py` or use the interactive control panel:
```bash
python3 control.py
# Select option 6: Configure Settings
```

### Presets
Built-in presets for common scenarios:
- **Small Demo**: 100 accounts, 50 articles (quick testing)
- **Full Dataset**: 7,000 accounts, 500+ articles (production)
- **Test Mode**: 10 accounts, 5 articles (development)

## 📖 Usage

### What You Can Do Without Gemini API Key

The following operations work without a Gemini API key:
- ✅ Load existing data files to Elasticsearch
- ✅ Check system status and configuration
- ✅ Manage Elasticsearch indices
- ✅ View and analyze existing generated data
- ✅ Check index status with `--check-indices`
- ✅ Update timestamps in Elasticsearch documents
- ✅ Update timestamps in data files before loading

Operations that require Gemini API key:
- ❌ Generate new accounts and holdings
- ❌ Generate new news articles
- ❌ Generate new financial reports
- ❌ Trigger market events (bad news, crash, volatility)

### Interactive Mode (Recommended)

Launch the interactive control panel:
```bash
python3 control.py
```

Menu options:
1. **🚀 Quick Start** - Generate all data with defaults
2. **⚙️ Custom Generation** - Configure specific options
3. **💥 Trigger Events** - Create controlled market events
4. **📊 Check Status** - View system and data status
5. **🗄️ Manage Indices** - Elasticsearch index management
6. **🔧 Configure Settings** - Manage configuration
7. **🔍 Dry Run Mode** - Preview without executing
8. **🚪 Exit** - Exit the application

### Command Line Mode

Quick generation with defaults:
```bash
python3 control.py --quick-start
```

Custom generation:
```bash
# Generate 100 accounts and 50 news articles
python3 control.py --custom --accounts --news \
  --num-accounts 100 --num-news 50

# Trigger a bad news event
python3 control.py --trigger-event bad_news

# Check full system status
python3 control.py --status

# Check only Elasticsearch index status
python3 control.py --check-indices

# Update all ES document timestamps to current time
python3 control.py --update-timestamps

# Update timestamps to 24 hours ago (for historical testing)
python3 control.py --update-timestamps --timestamp-offset -24

# Update timestamps in data files before loading
python3 control.py --update-files --timestamp-offset -12

# Load existing data with timestamps updated to current time
python3 control.py --custom --elasticsearch --update-timestamps-on-load
```

### Jupyter Notebook Usage

For programmatic usage in Jupyter notebooks without interactive prompts:

**Data Loading Only (No AI Key Required):**
```python
# Set Elasticsearch credentials
import os
os.environ['ES_ENDPOINT_URL'] = 'https://localhost:9200'
os.environ['ES_API_KEY'] = 'your_elasticsearch_api_key_here'

# Check if indices are setup
!python3 control.py --check-indices

# Load existing data to Elasticsearch
!python3 control.py --custom --elasticsearch

# Load data with updated timestamps (appears current)
!python3 control.py --custom --elasticsearch --update-timestamps-on-load

# Update existing ES data timestamps to now
!python3 control.py --update-timestamps
```

**Full Data Generation (Requires AI Key):**
```python
# Set all credentials
import os
os.environ['GEMINI_API_KEY'] = 'your_gemini_api_key_here'
os.environ['ES_ENDPOINT_URL'] = 'https://localhost:9200'
os.environ['ES_API_KEY'] = 'your_elasticsearch_api_key_here'

# Generate new data
!python3 control.py --quick-start

# Or trigger specific events
!python3 control.py --trigger-event market_crash
```

### Direct Script Execution

Run individual generation scripts:
```bash
# Generate accounts and holdings
python3 scripts/generate_holdings_accounts.py

# Generate news and reports
python3 scripts/generate_reports_and_news_new.py

# Trigger controlled events with different types
python3 scripts/trigger_bad_news_event.py --event-type bad_news
python3 scripts/trigger_bad_news_event.py --event-type market_crash
python3 scripts/trigger_bad_news_event.py --event-type volatility
```

### Elasticsearch Index Management

The system automatically creates indices with proper mappings before data ingestion.

**Quick Index Status Check:**
```bash
# Check only index status (no other system checks)
python3 control.py --check-indices
```

This command provides a focused view of your Elasticsearch indices:
- ✅ Connection to Elasticsearch cluster
- 📊 Status of all 5 financial indices  
- 📈 Document counts and sizes
- 🔍 Summary statistics

Example output:
```
📊 Index Status Summary
┌─────────────────────────┬────────┬──────────┬──────────┐
│ Index Name              │ Exists │ Documents│ Size     │
├─────────────────────────┼────────┼──────────┼──────────┤
│ financial_accounts      │ ✓      │ 7,000    │ 2.1 MB   │
│ financial_holdings      │ ✓      │ 87,234   │ 15.3 MB  │
│ financial_asset_details │ ✓      │ 127      │ 45 KB    │
│ financial_news          │ ✓      │ 523      │ 890 KB   │
│ financial_reports       │ ✓      │ 108      │ 234 KB   │
└─────────────────────────┴────────┴──────────┴──────────┘

✓ All 5 indices are properly configured
Total: 94,992 documents, 18.5 MB
```

**Full Index Management:**

To manage indices interactively:

```bash
python3 control.py
# Select option 5: Manage Indices
```

Options include:
- Check index status
- Create missing indices
- Recreate all indices
- Delete specific index
- View index mappings

### Timestamp Management

The system provides comprehensive timestamp management to keep your synthetic data current for demos and testing.

**Update Existing Elasticsearch Documents:**
```bash
# Update all document timestamps to current time
python3 control.py --update-timestamps

# Set timestamps to 24 hours ago (useful for historical testing)
python3 control.py --update-timestamps --timestamp-offset -24

# Set timestamps to 1 week in the future
python3 control.py --update-timestamps --timestamp-offset 168
```

**Update Data Files Before Loading:**
```bash
# Update file timestamps before loading to ES
python3 control.py --update-files --timestamp-offset -12

# Load data with timestamps updated during ingestion
python3 control.py --custom --elasticsearch --update-timestamps-on-load

# Load with specific timestamp offset
python3 control.py --custom --elasticsearch --update-timestamps-on-load --timestamp-offset 72
```

**Timestamp Fields Updated by Data Type:**
- **Accounts**: `last_updated`
- **Holdings**: `last_updated`, `purchase_date`
- **Asset Details**: `last_updated`, `current_price.last_updated`
- **News Articles**: `last_updated`, `published_date`
- **Reports**: `last_updated`, `published_date`

**Common Use Cases:**
- **Demo Preparation**: Make old data appear current for presentations
- **Testing**: Create data with specific timestamps for time-based features
- **Development**: Keep synthetic datasets fresh without regenerating content

## 📊 Data Structure

### Account Data
```json
{
  "account_id": "ACC00001-a1b2",
  "account_holder_name": "John Smith",
  "first_name": "John",
  "last_name": "Smith",
  "state": "CA",
  "zip_code": "94105",
  "account_type": "Growth",
  "risk_profile": "Medium",
  "contact_preference": "email",
  "total_portfolio_value": 125000.50,
  "last_updated": "2024-01-15T10:30:00"
}
```

### Holdings Data
```json
{
  "holding_id": "HLD-12345-6789",
  "account_id": "ACC00001-a1b2",
  "symbol": "AAPL",
  "quantity": 50,
  "purchase_price": 150.25,
  "purchase_date": "2023-06-15",
  "is_high_value": true,
  "last_updated": "2024-01-15T10:30:00"
}
```

### News Article
```json
{
  "article_id": "NEWS-abc123",
  "title": "Tech Stocks Rally on Strong Earnings",
  "content": "Technology stocks surged today...",
  "source": "Financial Times",
  "published_date": "2024-01-15T09:00:00",
  "url": "https://example.com/article",
  "entities": ["AAPL", "MSFT", "GOOGL"],
  "sentiment": "positive",
  "company_symbol": "AAPL",
  "primary_symbol": "AAPL",
  "last_updated": "2024-01-15T10:30:00"
}
```

## 🔌 API Documentation

### Core Modules

#### `control.py`
Main entry point for interactive and command-line usage.

```python
# Interactive mode
python3 control.py

# Command-line arguments
--quick-start         # Run with defaults
--custom             # Custom generation
--accounts           # Generate accounts
--news               # Generate news
--reports            # Generate reports
--num-accounts N     # Number of accounts
--num-news N         # Number of news articles
--trigger-event TYPE # Trigger event (bad_news, market_crash, volatility)
--status            # Show full system status
--check-indices     # Show ES index status only
--update-timestamps # Update ES document timestamps to now
--update-files      # Update file timestamps before loading
--update-timestamps-on-load  # Update timestamps during data loading
--timestamp-offset N # Hours offset from now (+ future, - past)
```

#### `lib/index_manager.py`
Manages Elasticsearch indices.

```python
from lib.index_manager import IndexManager, ensure_indices_exist

# Create manager
manager = IndexManager(es_client)

# Ensure indices exist
ensure_indices_exist(es_client, ['financial_accounts', 'financial_holdings'])

# Check if index exists
exists = manager.index_exists('financial_accounts')

# Create index with mapping
manager.create_index('financial_accounts')

# Get index status
status = manager.get_index_status('financial_accounts')
```

#### `scripts/common_utils.py`
Shared utilities for all scripts.

```python
from common_utils import (
    configure_gemini,
    call_gemini_api,
    create_elasticsearch_client,
    ingest_data_to_es
)

# Configure Gemini
model = configure_gemini()

# Call AI API
response = call_gemini_api(prompt, model)

# Create ES client
es_client = create_elasticsearch_client()

# Ingest data (auto-creates index)
ingest_data_to_es(es_client, filepath, index_name, id_field)
```

#### `lib/timestamp_updater.py`
Manages timestamp updates for financial data.

```python
from lib.timestamp_updater import TimestampUpdater

# Update all ES indices to current time
results = TimestampUpdater.update_all_indices(es_client, offset_hours=0)

# Update specific index with 24-hour offset
result = TimestampUpdater.update_elasticsearch_index(
    es_client, 'financial_news', offset_hours=-24
)

# Update document timestamps in-flight (during loading)
updated_doc = TimestampUpdater.update_document_timestamps(
    document, doc_type='news', offset_hours=12
)

# Update JSONL file timestamps
count = TimestampUpdater.update_file_timestamps(
    'generated_data/generated_news.jsonl', 
    doc_type='news', 
    offset_hours=-48
)

# Calculate target timestamp with offset
timestamp = TimestampUpdater.calculate_target_timestamp(offset_hours=-24)
```

## 💡 Examples

### Example 1: Quick Demo Dataset
Generate a small dataset for testing:
```bash
python3 control.py
# Select 2: Custom Generation
# Accounts: 100
# News: 50
# Reports: 20
# Elasticsearch: No
```

### Example 2: Full Production Dataset
Generate complete dataset with Elasticsearch:
```bash
python3 control.py --quick-start
```
This creates:
- 7,000 accounts
- 70,000-175,000 holdings
- 500+ news articles  
- 100+ reports
- All ingested to Elasticsearch

### Example 3: Trigger Market Event
Create a controlled bad news event:
```bash
python3 control.py --trigger-event bad_news
```
Generates:
- 5 negative news articles for TSLA
- 2 negative reports for FCX
- General market volatility articles

### Example 4: Demo Data Freshness
Update existing data to appear current for a live demo:
```bash
# Load existing data with current timestamps
python3 control.py --custom --elasticsearch --update-timestamps-on-load

# Or update already-loaded ES data to appear current
python3 control.py --update-timestamps

# Create a time-sequenced demo (news from yesterday, reports from today)
python3 control.py --update-timestamps --timestamp-offset -24  # News 24h ago
# Then manually update reports to current time via interactive menu
```

### Example 5: Custom Symbol Focus
Modify `scripts/symbols_config.py` to focus on specific stocks:
```python
STOCK_SYMBOLS_AND_INFO = {
    'AAPL': {'name': 'Apple Inc.', 'sector': 'Technology', ...},
    'MSFT': {'name': 'Microsoft Corp.', 'sector': 'Technology', ...},
    # Add your symbols here
}
```

## 🔧 Troubleshooting

### Common Issues

#### 1. Gemini API Key Error
```
ERROR: GEMINI_API_KEY environment variable not set
```
**Solution**: Set the environment variable or add to `.env` file

#### 2. Elasticsearch Connection Failed
```
ERROR: Could not connect to Elasticsearch
```
**Solution**: 
- Verify Elasticsearch is running
- Check ES_ENDPOINT_URL and ES_API_KEY
- Ensure network connectivity

#### 3. Index Creation Failed
```
Error creating index 'financial_accounts': resource_already_exists_exception
```
**Solution**: Index already exists. Use index management to recreate if needed.

#### 4. Import Errors
```
ModuleNotFoundError: No module named 'rich'
```
**Solution**: Install dependencies:
```bash
pip install -r requirements.txt
```

### Debug Mode
Enable verbose logging by modifying `scripts/config.py`:
```python
DEBUG_SETTINGS = {
    'log_level': 'DEBUG',
    'verbose_api_calls': True
}
```

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Development Guidelines
- Follow PEP 8 style guide
- Add docstrings to all functions
- Update tests for new features
- Update documentation as needed

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Google Gemini AI for content generation
- Elasticsearch for data storage and search
- The Python community for excellent libraries

## 📞 Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Check existing documentation in `CLAUDE.md`
- Review troubleshooting section above

---

Built with ❤️ for the financial data community
