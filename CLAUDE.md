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
├── update_es_timestamps.py        # ⚡ Fast ES timestamp updater (10x faster)
├── load_all_data.py              # 🚀 Fast data loader (bypasses control.py)
├── load_specific_indices.py       # 🎯 Selective data loader
├── load_demo_subset.py           # 🎭 Demo subset loader (5K holdings)
├── load_fresh_data.py            # 🆕 Recent data loader
├── quick_reload.py               # 🔄 Quick reload (delete + load)
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
│   ├── index_manager.py          # 🗄️ Elasticsearch index management
│   └── timestamp_updater.py      # 🕐 Timestamp update operations
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
- **🕐 Timestamp Management** (`lib/timestamp_updater.py`): Updates document timestamps in Elasticsearch or data files to current time with optional offsets
- **📈 Generation Scripts**:
  - `generate_holdings_accounts.py`: Creates accounts, holdings, and asset details
  - `generate_reports_and_news_new.py`: Generates news articles and financial reports
  - `trigger_bad_news_event.py`: Creates controlled negative market events for demos

## Development Commands

### 🚀 Fast Loading Scripts (Recommended for Google Colab)

**NEW: Optimized loading scripts that are 10-15x faster than control.py:**

```bash
# Load all data in ~20 seconds (instead of several minutes)
python3 load_all_data.py

# Load specific indices only
python3 load_specific_indices.py --holdings --news
python3 load_specific_indices.py --all

# Quick reload for demos (delete + reload)
python3 quick_reload.py --news --reports

# Load demo subset (5K holdings, <5 seconds)
python3 load_demo_subset.py

# Load only recently generated files
python3 load_fresh_data.py --hours 2
```

**Why these are faster:**
- Bypass TaskExecutor overhead that slows control.py in Colab
- Direct ES connection without subprocess management
- Optimal settings pre-configured (24 workers, 1000 batch)
- Real-time progress with batch timestamps
- Timestamps always updated to current time

### ⚡ Fast Timestamp Updates

**NEW: Direct ES timestamp updater - 10x faster than control.py method:**

```bash
# Update all ES document timestamps to current time
python3 update_es_timestamps.py

# Set timestamps to 24 hours ago for historical demos
python3 update_es_timestamps.py --offset -24

# Set timestamps to 3 hours in the future
python3 update_es_timestamps.py --offset 3

# Update specific indices only
python3 update_es_timestamps.py --indices accounts holdings
python3 update_es_timestamps.py --indices news reports

# Dry run to preview changes without updating
python3 update_es_timestamps.py --dry-run --offset -168
```

**Performance Benefits:**
- **10x Faster**: ~100k docs/sec vs ~10k docs/sec with control.py
- **In-Place Updates**: Uses ES update_by_query API - no data reloading
- **Memory Efficient**: Processes documents in ES without downloading
- **Conflict Handling**: Continues on version conflicts
- **Real-time Progress**: Live progress tracking with docs/sec rates

**Timestamp Fields Updated:**
- `financial_accounts`: `last_updated`
- `financial_holdings`: `last_updated`, `purchase_date`
- `financial_asset_details`: `last_updated`, `current_price.last_updated`
- `financial_news`: `last_updated`, `published_date`
- `financial_reports`: `last_updated`, `published_date`

**Use Cases:**
- **Demo Preparation**: Make historical data appear current instantly
- **Time Simulation**: Create realistic time sequences for testing
- **Data Refresh**: Keep datasets current without regenerating content
- **Performance Testing**: Quick timestamp updates for load testing

### Operations Without Gemini API Key

Many operations can be performed without a Gemini API key:

**Available without Gemini key:**
- Fast loading scripts (all `load_*.py` scripts above)
- `control.py --status` - Check system status (informational only, not required)
- `control.py --check-indices` - Check Elasticsearch index status
- `control.py --custom --elasticsearch` - Load existing data to ES (slower, use load_all_data.py instead)
- `control.py --update-timestamps` - Update ES document timestamps
- `control.py --update-files` - Update data file timestamps
- Interactive index management (option 5 in menu)
- Configuration management (option 6 in menu)
- Viewing existing data files

**Requires Gemini key:**
- `control.py --quick-start` - Generate new data
- `control.py --custom --accounts` - Generate accounts
- `control.py --custom --news` - Generate news
- `control.py --custom --reports` - Generate reports  
- `control.py --trigger-event` - Trigger market events
- Any operation that creates new synthetic content

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
python3 control.py --trigger-event market_crash     # Trigger market crash scenario
python3 control.py --trigger-event volatility       # Trigger volatility spike
python3 control.py --status                         # Show full system status
python3 control.py --check-indices                  # Check ES index status only
python3 control.py --update-timestamps              # Update ES timestamps to now
python3 control.py --update-timestamps --timestamp-offset -24  # Set timestamps to 24 hours ago
python3 control.py --update-files --timestamp-offset 168       # Update file timestamps to 1 week in future
python3 control.py --custom --elasticsearch --update-timestamps-on-load  # Update timestamps during loading
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
- **Live Progress Dashboard**: Real-time progress tracking with script output parsing and concurrent task monitoring
- **Interactive Configuration Editing**: Full in-app configuration management with validation and real-time updates
- **Elasticsearch Connection Testing**: Live connectivity validation with cluster health and version information
- **Multiple Event Types**: Three distinct market event scenarios (bad news, market crash, volatility) with different content patterns
- **Automatic Index Creation**: All Elasticsearch indices created with proper mappings before data ingestion
- **Configuration Presets**: Built-in presets (Small Demo: 100 accounts, Full Dataset: 7K accounts, Test Mode: 10 accounts)
- **Environment Validation**: Comprehensive checks for API keys, file paths, and system requirements
- **Error Handling**: Graceful error recovery with detailed error messages and retry logic
- **Batch Operations**: Queue multiple tasks and execute them concurrently with status tracking

### Jupyter Notebook Integration

For programmatic usage in Jupyter notebooks or automated workflows:

**Data Loading Only (No AI Key Required):**
```python
import os
os.environ['ES_ENDPOINT_URL'] = 'https://localhost:9200'
os.environ['ES_API_KEY'] = 'your_elasticsearch_api_key_here'

# Check if Elasticsearch indices are properly setup
!python3 control.py --check-indices

# Load existing data files to Elasticsearch
!python3 control.py --custom --elasticsearch
```

**Full Generation with AI (Requires Gemini API Key):**
```python
import os
os.environ['GEMINI_API_KEY'] = 'your_gemini_api_key_here' 
os.environ['ES_ENDPOINT_URL'] = 'https://localhost:9200'
os.environ['ES_API_KEY'] = 'your_elasticsearch_api_key_here'

# Generate complete dataset
!python3 control.py --quick-start

# Or custom generation
!python3 control.py --custom --accounts --news --num-accounts 1000

# Trigger market events
!python3 control.py --trigger-event market_crash
```

### Direct Script Execution

Scripts can also be run directly from the repository root:

```bash
# Generate accounts and holdings
python3 scripts/generate_holdings_accounts.py

# Generate news and reports
python3 scripts/generate_reports_and_news_new.py

# Trigger controlled market events
python3 scripts/trigger_bad_news_event.py --event-type bad_news      # Targeted negative news
python3 scripts/trigger_bad_news_event.py --event-type market_crash  # Broad market crash
python3 scripts/trigger_bad_news_event.py --event-type volatility    # Market volatility spike

# List available Gemini models
python3 scripts/list_models.py
```

### Environment Setup

Environment variables can be set in `.env` file or exported directly:

**API Key Requirements by Use Case:**

| Use Case | GEMINI_API_KEY | ES_API_KEY | ES_ENDPOINT_URL |
|----------|----------------|------------|-----------------|
| Generate new data | ✅ Required | Optional | Optional |
| Load existing data to ES | ❌ Not needed | ✅ Required | ✅ Required |
| Check local data files | ❌ Not needed | ❌ Not needed | ❌ Not needed |
| Update ES timestamps | ❌ Not needed | ✅ Required | ✅ Required |
| Update file timestamps | ❌ Not needed | ❌ Not needed | ❌ Not needed |
| Trigger market events | ✅ Required | Optional | Optional |

**Environment Variables:**
- `GEMINI_API_KEY`: Google Gemini API key (only for generating new content)
- `ES_API_KEY`: Elasticsearch API key (only for ES operations)
- `ES_ENDPOINT_URL`: Elasticsearch endpoint (defaults to https://localhost:9200)

**Note:** When running `control.py --status`, missing GEMINI_API_KEY will show a warning but won't prevent loading existing data

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

## Timestamp Management

The system provides comprehensive timestamp management capabilities to keep data current and simulate different time scenarios for demos and testing.

### Timestamp Update Operations

**Update Elasticsearch Documents:**
```bash
# Update all document timestamps to current time
python3 control.py --update-timestamps

# Set timestamps to 24 hours ago  
python3 control.py --update-timestamps --timestamp-offset -24

# Set timestamps to 1 week in the future
python3 control.py --update-timestamps --timestamp-offset 168
```

**Update Data Files Before Loading:**
```bash
# Update file timestamps before loading to ES
python3 control.py --update-files --timestamp-offset -12

# Update timestamps during data loading (in-flight)
python3 control.py --custom --elasticsearch --update-timestamps-on-load

# Load with specific timestamp offset
python3 control.py --custom --elasticsearch --update-timestamps-on-load --timestamp-offset 72
```

**Interactive Management:**
```bash
python3 control.py
# Select option 5: Manage Indices
# Choose timestamp update options from menu
```

### Supported Timestamp Fields

The system automatically identifies and updates the following timestamp fields for each data type:

- **`financial_accounts`**: `last_updated`
- **`financial_holdings`**: `last_updated`, `purchase_date`
- **`financial_asset_details`**: `last_updated`, `current_price.last_updated`
- **`financial_news`**: `last_updated`, `published_date`
- **`financial_reports`**: `last_updated`, `published_date`

### Programming Interface

```python
from lib.timestamp_updater import TimestampUpdater

# Update all ES indices to current time
results = TimestampUpdater.update_all_indices(es_client, offset_hours=0)

# Update specific index with offset
result = TimestampUpdater.update_elasticsearch_index(
    es_client, 'financial_news', offset_hours=-24
)

# Update document timestamps in-flight
updated_doc = TimestampUpdater.update_document_timestamps(
    document, doc_type='news', offset_hours=12
)

# Update JSONL file timestamps
count = TimestampUpdater.update_file_timestamps(
    'generated_data/generated_news.jsonl', 
    doc_type='news', 
    offset_hours=-48
)
```

### Use Cases

**Demo Preparation:**
- Make historical data appear current for live demos
- Create realistic time sequences for storytelling
- Simulate different market timing scenarios

**Testing & Development:**
- Test time-sensitive features with controlled timestamps
- Create data that appears to be generated at different times
- Validate time-based queries and filters

**Data Refresh:**
- Keep synthetic datasets current without regenerating content
- Update existing Elasticsearch indices quickly
- Maintain data freshness for ongoing development

### Performance Notes

- **Bulk Updates**: ES updates use `update_by_query` API for efficient bulk operations
- **Index Refresh**: Indices are refreshed after timestamp updates for immediate query availability
- **Conflict Handling**: Updates proceed even if some documents fail (conflicts='proceed')
- **Memory Efficient**: File updates process line-by-line without loading entire datasets

## 🚀 Performance Optimization

### Understanding Performance Bottlenecks

**Key Discovery**: The primary performance bottleneck is **TaskExecutor subprocess overhead**, not Elasticsearch indexing speed or timestamp operations.

**Performance Comparison:**
- **Direct Scripts**: ~20 seconds total (load_all_data.py)
- **Control.py**: Several minutes (10-15x slower due to subprocess management)
- **Root Cause**: TaskExecutor creates subprocess overhead in environments like Google Colab/Jupyter

### Optimization Strategies

**1. Use Direct Loading Scripts (Recommended)**
```bash
# FAST: Direct connection (20 seconds)
python3 load_all_data.py

# SLOW: Via control.py (several minutes)
python3 control.py --custom --elasticsearch
```

**2. Optimal Elasticsearch Settings**
Based on performance testing, optimal settings are:
- **Batch Size**: 1000 documents per batch
- **Parallel Workers**: 24 workers (for most systems)
- **Connection**: Direct ES client without subprocess overhead

**3. Environment-Specific Optimizations**

**Google Colab/Jupyter:**
- Always use direct scripts (`load_*.py`, `update_es_timestamps.py`)
- Avoid control.py for data operations
- Use `--non-interactive` flag if using control.py

**Local Development:**
- Direct scripts still faster but control.py more manageable
- Interactive features work properly
- Full menu system available

**Production/Automation:**
- Direct scripts for maximum throughput
- Batch operations with optimal worker counts
- Environment variable configuration

### Performance Diagnostic Tools

**1. Indexing Performance Diagnosis:**
```bash
# Identify indexing bottlenecks
python3 diagnose_indexing_performance.py

# Find optimal settings for your environment
python3 find_optimal_settings.py
```

**2. Performance Monitoring:**
- All scripts show real-time docs/sec rates
- Progress bars with ETA estimates
- Memory usage and batch processing stats

**3. Bottleneck Identification:**
- **Timestamp Updates**: 114k+ docs/sec (very fast)
- **Elasticsearch Indexing**: 10-20k docs/sec (moderate)
- **TaskExecutor Overhead**: 10-15x slowdown (major bottleneck)

### Best Practices

**For Maximum Speed:**
1. Use direct loading scripts
2. Configure optimal batch/worker settings
3. Avoid subprocess-heavy operations
4. Use direct ES timestamp updates

**For Development:**
1. Use control.py for exploration and configuration
2. Switch to direct scripts for data operations
3. Profile performance with diagnostic tools
4. Test in target environment (Colab vs local)

**For Demos:**
1. Pre-load data with direct scripts
2. Use timestamp updates for time simulation
3. Keep reload times minimal with subset loading
4. Test performance before live demos

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

## Event System

### Market Event Types

The system supports three distinct market event types for demo and testing purposes:

**1. Bad News Event (`bad_news`)**
- **Target**: Specific companies (TSLA for news, FCX for reports)
- **Sentiment**: Negative
- **Scope**: Targeted, company-specific negative events
- **Content**: Recalls, production issues, regulatory problems
- **Volume**: Standard controlled generation amounts

**2. Market Crash Event (`market_crash`)**
- **Target**: Broad market ETFs (SPY, QQQ) and sector indices
- **Sentiment**: Very negative
- **Scope**: Market-wide systemic crisis
- **Content**: Economic uncertainty, widespread selloffs, sector declines
- **Volume**: Double the standard amounts (more articles and reports)
- **Additional Symbols**: VTI, IWM, XLF, XLE (broad market coverage)

**3. Volatility Event (`volatility`)**
- **Target**: Volatility instruments (VIX, UVXY)
- **Sentiment**: Neutral with mixed volatile sentiment
- **Scope**: Market uncertainty with mixed directional impact
- **Content**: Geopolitical tensions, economic data uncertainty, trading opportunities
- **Volume**: Triple general news (more market commentary)
- **Additional Symbols**: SVXY, VIXY, TVIX (volatility-related instruments)

### Event Configuration

All event configurations are defined in `scripts/config.py` in the `EVENT_CONFIGS` dictionary:

```python
EVENT_CONFIGS = {
    'bad_news': {
        'target_news_symbol': 'TSLA',
        'news_theme': "major recall impacting new vehicle launches",
        'sentiment': "negative"
    },
    'market_crash': {
        'target_news_symbol': 'SPY', 
        'news_theme': "widespread market selloff triggered by economic uncertainty",
        'sentiment': "very negative",
        'market_wide_impact': True
    },
    # ... more configurations
}
```

### Usage Examples

**Interactive Mode:**
```bash
python3 control.py
# Select option 3: Trigger Events
# Choose from bad_news, market_crash, or volatility
```

**Command Line:**
```bash
python3 control.py --trigger-event bad_news
python3 control.py --trigger-event market_crash  
python3 control.py --trigger-event volatility
```

**Direct Script:**
```bash
python3 scripts/trigger_bad_news_event.py --event-type market_crash
```

## Development Patterns

**Adding New Data Types:**
1. Add mapping to `elasticsearch/index_mappings.json`
2. Update `config.py` with new index name and generation settings
3. Create generation function in appropriate script
4. Add UI options to `lib/menu_system.py`
5. **Performance**: Consider adding direct loading script for large datasets

**Modifying Symbols:**
- Edit `scripts/symbols_config.py` to add/remove stocks, ETFs, or bonds
- All scripts automatically use updated symbol definitions

**Custom Prompts:**
- Modify templates in `prompts/` directory
- Changes automatically picked up by generation scripts

**Performance Optimization Patterns:**

**Creating Direct Loading Scripts:**
```python
# Template for direct loading script
import os
import sys
import time
from datetime import datetime

# Set optimal performance settings
BULK_SIZE = 1000
PARALLEL_WORKERS = 24
os.environ['ES_BULK_BATCH_SIZE'] = str(BULK_SIZE)
os.environ['PARALLEL_BULK_WORKERS'] = str(PARALLEL_WORKERS)

# Direct ES connection (bypass TaskExecutor)
from scripts.common_utils import create_elasticsearch_client, ingest_data_to_es

def fast_load():
    es_client = create_elasticsearch_client()
    # Direct ingest without subprocess overhead
    ingest_data_to_es(es_client, filepath, index_name, id_field,
                     batch_size=BULK_SIZE, parallel_bulk_workers=PARALLEL_WORKERS)
```

**When to Use Direct Scripts vs Control.py:**
- **Direct Scripts**: Data loading, timestamp updates, production automation
- **Control.py**: Configuration, exploration, interactive management, new user onboarding
- **Hybrid**: Use control.py for setup, direct scripts for operations

**Performance Testing Pattern:**
```python
# Always measure performance for new operations
start_time = time.time()
# ... perform operation ...
elapsed = time.time() - start_time
docs_per_sec = document_count / elapsed if elapsed > 0 else 0
print(f"✓ {document_count:,} docs in {elapsed:.1f}s ({docs_per_sec:.0f} docs/sec)")
```

**Environment Detection Pattern:**
```python
# Detect notebook environments for optimal UX
def is_notebook():
    try:
        return get_ipython().__class__.__name__ == 'ZMQInteractiveShell'  # Jupyter
    except:
        return 'google.colab' in sys.modules  # Colab

# Adapt behavior based on environment
if is_notebook():
    # Use direct scripts, avoid interactive prompts
    use_non_interactive_mode = True
```

**Bulk Operation Pattern:**
```python
# Process large datasets efficiently
from concurrent.futures import ThreadPoolExecutor
from elasticsearch.helpers import parallel_bulk

def bulk_process(es_client, documents, batch_size=1000, workers=24):
    def doc_generator():
        for doc in documents:
            yield {"_index": index_name, "_source": doc}
    
    for success, info in parallel_bulk(
        es_client, doc_generator(), 
        chunk_size=batch_size, 
        thread_count=workers
    ):
        if not success:
            print(f"Failed: {info}")
```

**Environment Management:**
- Use `.env` file for local development
- Set environment variables in production
- All secrets automatically excluded by `.gitignore`

## 🔧 Troubleshooting

### Performance Issues

#### Slow Data Loading

**Problem**: Data loading takes several minutes instead of seconds

**Diagnosis:**
```bash
# Check if using control.py (slow) vs direct scripts (fast)
python3 control.py --custom --elasticsearch  # SLOW (several minutes)
python3 load_all_data.py                     # FAST (~20 seconds)
```

**Solutions:**
1. **Use Direct Scripts**: Replace control.py with direct loading scripts
2. **Check Environment**: Colab/Jupyter environments have higher subprocess overhead
3. **Optimize Settings**: Use 24 workers and 1000 batch size
4. **Profile Performance**: Run `diagnose_indexing_performance.py`

#### Slow Timestamp Updates

**Problem**: Timestamp updates take minutes to complete

**Solutions:**
```bash
# SLOW: Via control.py (several minutes)
python3 control.py --update-timestamps

# FAST: Direct update (~10 seconds for 100k docs)
python3 update_es_timestamps.py
```

### Elasticsearch Issues

#### Connection Failures

**Problem**: 
```
ERROR: Could not connect to Elasticsearch
```

**Solutions:**
1. **Check Credentials**:
   ```bash
   echo $ES_ENDPOINT_URL
   echo $ES_API_KEY
   ```
2. **Test Connection**:
   ```bash
   python3 control.py --check-indices
   ```
3. **Common Fixes**:
   - Verify Elasticsearch is running
   - Check firewall/network connectivity
   - Validate API key permissions
   - Ensure correct endpoint format (https://...)

#### Index Creation Errors

**Problem**:
```
ERROR: Settings [index.number_of_shards] not available in serverless mode
```

**Solution**: This is handled automatically in newer versions. Update scripts suppress unsupported serverless settings.

**Problem**:
```
ERROR: Index already exists
```

**Solutions:**
```bash
# Check index status
python3 control.py --check-indices

# Recreate indices if needed
python3 control.py
# Select option 5: Manage Indices
# Choose recreate option
```

#### Bulk Indexing Failures

**Problem**: Documents fail to index with version conflicts

**Solutions:**
1. **Check for Concurrent Operations**: Ensure no other processes are writing to indices
2. **Use Conflict Handling**: Scripts automatically use `conflicts='proceed'`
3. **Retry Failed Batches**: Re-run the loading script - it will skip existing docs

### API and Authentication Issues

#### Gemini API Errors

**Problem**:
```
ERROR: GEMINI_API_KEY environment variable not set
```

**Solutions:**
1. **Set API Key**:
   ```bash
   export GEMINI_API_KEY="your_api_key_here"
   # Or add to .env file
   echo "GEMINI_API_KEY=your_api_key_here" >> .env
   ```

2. **Verify Key Validity**:
   ```bash
   python3 scripts/list_models.py
   ```

**Problem**: API quota exceeded or rate limits

**Solutions:**
1. **Check Quota**: Monitor API usage in Google Cloud Console
2. **Reduce Volume**: Use smaller dataset sizes for testing
3. **Retry Logic**: Scripts automatically handle rate limits with exponential backoff

#### SSL/TLS Warnings

**Problem**: SSL warnings cluttering output

**Solution**: Modern scripts automatically suppress these warnings:
```python
import warnings
warnings.filterwarnings('ignore')
import urllib3
urllib3.disable_warnings()
```

### Data Generation Issues

#### Empty or Missing Data Files

**Problem**: Generated files are empty or missing

**Solutions:**
1. **Check File Permissions**: Ensure write permissions to `generated_data/` directory
2. **Verify API Keys**: Most generation requires valid Gemini API key
3. **Check Disk Space**: Ensure sufficient space for large datasets
4. **Review Error Messages**: Run with verbose output to see specific failures

#### Inconsistent Data Volumes

**Problem**: Generated volumes don't match expected counts

**Solutions:**
1. **Check Configuration**: Review settings in `scripts/config.py`
2. **Symbol Availability**: Ensure sufficient symbols defined in `symbols_config.py`
3. **API Limits**: Gemini may have lower limits during high usage periods

### Environment-Specific Issues

#### Google Colab Problems

**Problem**: control.py hangs or fails in Colab

**Solutions:**
1. **Use Non-Interactive Mode**:
   ```bash
   python3 control.py --quick-start --non-interactive
   ```
2. **Use Direct Scripts**: Bypass control.py entirely
3. **Check Resource Limits**: Colab has CPU/memory limitations

#### Jupyter Notebook Issues

**Problem**: Notebook cells hang on interactive prompts

**Solutions:**
1. **Auto-Detection**: System automatically detects notebook environments
2. **Force Non-Interactive**: Use `--non-interactive` flag explicitly
3. **Use Direct Scripts**: Most reliable in notebook environments

### Diagnostic Commands

**System Status Check:**
```bash
python3 control.py --status
```

**Performance Profiling:**
```bash
python3 diagnose_indexing_performance.py
python3 find_optimal_settings.py
```

**Index Health Check:**
```bash
python3 control.py --check-indices
```

**Connection Testing:**
```bash
# Test ES connection
python3 -c "from scripts.common_utils import create_elasticsearch_client; print('✓ Connected' if create_elasticsearch_client() else '✗ Failed')"

# Test Gemini connection  
python3 scripts/list_models.py
```