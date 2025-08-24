# Synthetic Financial Data Generator 🏦

A powerful Python toolkit for generating realistic synthetic financial data for testing, demos, and development. Create thousands of accounts, holdings, news articles, and reports with AI-generated content, all ready for ingestion into Elasticsearch.

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
│   └── index_manager.py      # Elasticsearch index management
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
Create a `.env` file in the project root:
```bash
# Required for content generation
GEMINI_API_KEY=your_gemini_api_key_here

# Optional for Elasticsearch ingestion
ES_ENDPOINT_URL=https://localhost:9200
ES_API_KEY=your_elasticsearch_api_key_here
```

Or export them directly:
```bash
export GEMINI_API_KEY="your_gemini_api_key_here"
export ES_ENDPOINT_URL="https://localhost:9200"
export ES_API_KEY="your_elasticsearch_api_key_here"
```

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

# Check system status
python3 control.py --status
```

### Direct Script Execution

Run individual generation scripts:
```bash
# Generate accounts and holdings
python3 scripts/generate_holdings_accounts.py

# Generate news and reports
python3 scripts/generate_reports_and_news_new.py

# Trigger controlled events
python3 scripts/trigger_bad_news_event.py
```

### Elasticsearch Index Management

The system automatically creates indices with proper mappings before data ingestion. To manage indices manually:

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
--status            # Show status only
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

### Example 4: Custom Symbol Focus
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