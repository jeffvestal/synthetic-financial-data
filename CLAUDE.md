# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

The Synthetic Financial Data Generator is a comprehensive Python toolkit for creating realistic financial datasets for testing, demos, and development. It generates:

- **Customer Accounts**: 7,000+ realistic accounts with portfolio information, risk profiles, and geographic distribution
- **Holdings**: Stock, ETF, and bond positions with purchase history and current valuations  
- **Asset Details**: Current prices, sectors, and metadata for 100+ financial instruments
- **News Articles**: 500+ AI-generated market news with sentiment analysis and entity extraction
- **Financial Reports**: 100+ company reports, earnings summaries, and analyst notes

All content is generated using Google's Gemini AI for realistic language and can be automatically ingested into Elasticsearch with proper index mappings for semantic search capabilities.

## Directory Structure

```
synthetic-financial-data/
├── control.py                     # 🎮 Main interactive control script
├── requirements.txt               # Python dependencies
├── README.md                     # Comprehensive documentation
├── .gitignore                    # Git ignore rules (protects secrets & large files)
├── scripts/                      # 🔧 Core generation scripts
│   ├── config.py                 # Centralized configuration
│   ├── generate_holdings_accounts.py
│   ├── generate_reports_and_news_new.py
│   ├── trigger_bad_news_event.py
│   ├── common_utils.py           # Shared utilities with ES integration
│   ├── symbol_manager.py         # Symbol management and filtering
│   └── symbols_config.py         # Stock/ETF/Bond definitions (100+ symbols)
├── lib/                          # 📚 Control script libraries  
│   ├── menu_system.py            # Interactive menus with Rich UI
│   ├── config_manager.py         # Configuration and presets management
│   ├── task_executor.py          # Task execution with live progress
│   └── index_manager.py          # 🗄️ Elasticsearch index management
├── elasticsearch/                # 🔍 Elasticsearch configuration
│   └── index_mappings.json       # Complete index mappings for all 5 indices
├── prompts/                      # 🤖 AI prompt templates for content generation
│   ├── general_market_news.txt   # General market news template
│   ├── specific_news.txt         # Company-specific news template  
│   ├── specific_report.txt       # Company report template
│   └── thematic_sector_report.txt # Thematic industry report template
└── generated_data/               # 📊 Output directory (ignored by git for large files)
    ├── generated_accounts.jsonl
    ├── generated_holdings.jsonl
    ├── generated_asset_details.jsonl
    ├── generated_news.jsonl
    ├── generated_reports.jsonl
    ├── generated_controlled_news.jsonl
    └── generated_controlled_reports.jsonl
```

## Key Architecture

### Data Flow
1. **Interactive Control** (`control.py`): Main entry point with task-based menus and live progress dashboard
2. **Configuration Management** (`lib/config_manager.py`): Handles settings, presets, and environment validation  
3. **Symbol Configuration** (`symbols_config.py`): Defines 100+ financial symbols with sectors and metadata
4. **Index Management** (`lib/index_manager.py`): Automatically creates Elasticsearch indices with proper mappings
5. **AI Content Generation**: Uses Gemini API with custom prompts to create realistic financial content
6. **Data Storage**: Saves to JSONL files and optionally ingests to Elasticsearch with semantic search support

### Core Components

- **🎮 Interactive Control Script** (`control.py`): Main interface with 8 menu options including Quick Start, Custom Generation, Index Management
- **🗄️ Index Management System** (`lib/index_manager.py`): Comprehensive ES index management with status checking, creation, deletion, and mapping validation
- **🔧 Configuration Hub** (`scripts/config.py`): Centralized settings with file paths, API configuration, and generation parameters
- **📊 Task Executor** (`lib/task_executor.py`): Advanced execution engine with live progress dashboard and concurrent task monitoring  
- **🤖 AI Integration** (`common_utils.py`): Gemini API integration with retry logic and error handling
- **💾 Symbol Management** (`symbol_manager.py`): Advanced symbol filtering by sector, index membership, and random selection
- **📈 Generation Scripts**:
  - `generate_holdings_accounts.py`: Creates accounts, holdings, and asset details
  - `generate_reports_and_news_new.py`: Generates news articles and financial reports
  - `trigger_bad_news_event.py`: Creates controlled negative market events for demos

## Development Commands

### Interactive Control Script (Recommended)

Use the interactive control script for a user-friendly experience:

```bash
# Install dependencies first
pip3 install -r requirements.txt

# Run interactive mode
python3 control.py

# Non-interactive examples
python3 control.py --quick-start                    # Generate all with defaults
python3 control.py --custom --accounts --num-accounts 100  # Custom generation
python3 control.py --trigger-event bad_news         # Trigger bad news event
python3 control.py --status                         # Show system status
python3 control.py --help                          # Show all options
```

**Interactive Menu Options:**
1. **🚀 Quick Start** - Generate all data with defaults (7K accounts, 500+ articles)
2. **⚙️ Custom Generation** - Configure specific generation options with custom volumes
3. **💥 Trigger Events** - Create controlled market events (bad news, market crash, volatility)
4. **📊 Check Status** - View system status, environment validation, and data statistics
5. **🗄️ Manage Indices** - Elasticsearch index management (create, delete, status, recreate)
6. **🔧 Configure Settings** - Manage configuration and presets (view, edit, save, load)
7. **🔍 Dry Run Mode** - Preview execution plan without actually running
8. **🚪 Exit** - Exit the application

**Advanced Features:**
- **Live Progress Dashboard**: Real-time status with multiple concurrent progress bars and task monitoring
- **Automatic Index Creation**: All Elasticsearch indices created with proper mappings before data ingestion
- **Configuration Presets**: Built-in presets (Small Demo: 100 accounts, Full Dataset: 7K accounts, Test Mode: 10 accounts)
- **Environment Validation**: Comprehensive checks for API keys, file paths, and system requirements
- **Error Handling**: Graceful error recovery with detailed error messages and retry logic
- **Batch Operations**: Queue multiple tasks and execute them concurrently with status tracking

### Direct Script Execution

Scripts can also be run directly from the repository root:

```bash
# Generate accounts and holdings
python3 scripts/generate_holdings_accounts.py

# Generate news and reports
python3 scripts/generate_reports_and_news_new.py

# Trigger a controlled bad news event
python3 scripts/trigger_bad_news_event.py

# List available Gemini models
python3 scripts/list_models.py
```

### Environment Setup

Required environment variables (set in `.env` file or environment):
- `GEMINI_API_KEY`: Google Gemini API key for content generation
- `ES_API_KEY`: Elasticsearch API key (optional, for data ingestion)
- `ES_ENDPOINT_URL`: Elasticsearch endpoint (defaults to https://localhost:9200)

### Python Dependencies

Install dependencies with: `pip3 install -r requirements.txt`

**Core libraries:**
- `google-generativeai`: Gemini API client
- `elasticsearch`: Elasticsearch client
- `faker`: Synthetic data generation
- `tqdm`: Progress bars
- `python-dotenv`: Environment variable management

**Interactive control script:**
- `rich`: Beautiful terminal output and progress bars
- `colorama`: Cross-platform colored output

## Data Structures

### Generated Files (in `generated_data/`)
- `generated_accounts.jsonl`: Financial account records
- `generated_holdings.jsonl`: Account holdings (stocks, ETFs, bonds)
- `generated_asset_details.jsonl`: Asset pricing and metadata
- `generated_news.jsonl`: Market news articles
- `generated_reports.jsonl`: Financial reports
- `generated_controlled_news.jsonl`: Controlled event news
- `generated_controlled_reports.jsonl`: Controlled event reports

### Elasticsearch Indices
Indices are automatically created with proper mappings when data is ingested. All mappings defined in `elasticsearch/index_mappings.json`:

- **`financial_accounts`**: Account information (7,000 records)
  - Personal details, risk profiles, portfolio values
  - Lookup mode for optimized queries
  
- **`financial_holdings`**: Portfolio holdings (70,000-175,000 records)  
  - Stock/ETF/bond positions with quantities and purchase history
  - Links to accounts via account_id
  
- **`financial_asset_details`**: Asset metadata (100+ records)
  - Current/historical prices, sectors, index memberships
  - Semantic search on asset names for intelligent lookup
  
- **`financial_news`**: Market news articles (500+ records)
  - AI-generated content with title/content semantic search
  - Sentiment analysis and entity extraction
  
- **`financial_reports`**: Financial reports (100+ records)
  - Company reports and analyst notes with semantic search
  - Links to specific companies and broader market themes

**Index Features:**
- **Field Types**: Proper mapping (keyword, text, date, float, boolean, object)
- **Semantic Search**: ELSER-compatible fields on titles and content for intelligent search
- **Lookup Mode**: Optimized storage and query performance for large datasets
- **Auto-Creation**: Indices created automatically before data ingestion with error handling

## Index Management

The system includes comprehensive Elasticsearch index management:

**Available Operations:**
- **Status Check**: View health, document counts, and size for all indices
- **Create Missing**: Automatically create indices that don't exist
- **Recreate All**: Delete and recreate all indices (with confirmation)
- **Delete Specific**: Remove individual indices
- **View Mappings**: Display current index mappings and settings

**Access via Control Script:**
```bash
python3 control.py
# Select option 5: Manage Indices
```

**Programmatic Access:**
```python
from lib.index_manager import IndexManager, ensure_indices_exist

# Auto-create indices before data ingestion  
ensure_indices_exist(es_client, ['financial_accounts', 'financial_news'])

# Manual management
manager = IndexManager(es_client)
status = manager.get_index_status('financial_accounts')
manager.recreate_index('financial_news')
```

## Configuration Points

**Key Configuration Files:**

1. **`scripts/config.py`** - Main configuration hub:
   - `GENERATION_SETTINGS`: Volume controls (7K accounts, 500+ articles, 100+ reports)
   - `ES_CONFIG`: Connection settings, batch sizes, index names, auto-creation settings  
   - `GEMINI_CONFIG`: API settings, safety configurations, retry logic
   - `FILE_PATHS`: All file paths including generated data and index mappings
   - `DEMO_CONFIG`: Market simulation parameters and volatility settings

2. **`elasticsearch/index_mappings.json`** - Complete index mappings:
   - All 5 index definitions with settings and field mappings
   - Semantic search field configurations
   - Lookup mode settings for performance

3. **`requirements.txt`** - Python dependencies:
   - Core: `google-generativeai`, `elasticsearch`, `faker`, `python-dotenv`
   - UI: `rich`, `tqdm`, `colorama`

4. **`.env`** - Environment variables (not tracked by git):
   ```bash
   GEMINI_API_KEY=your_key_here
   ES_API_KEY=your_es_key_here  
   ES_ENDPOINT_URL=https://localhost:9200
   ```

## Development Patterns

**Adding New Data Types:**
1. Add mapping to `elasticsearch/index_mappings.json`
2. Update `config.py` with new index name and generation settings
3. Create generation function in appropriate script
4. Add UI options to `lib/menu_system.py`

**Modifying Symbols:**
- Edit `scripts/symbols_config.py` to add/remove stocks, ETFs, or bonds
- All scripts automatically use updated symbol definitions

**Custom Prompts:**
- Modify templates in `prompts/` directory
- Changes automatically picked up by generation scripts

**Environment Management:**
- Use `.env` file for local development
- Set environment variables in production
- All secrets automatically excluded by `.gitignore`