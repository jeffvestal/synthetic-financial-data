"""
Shared configuration constants for Portfolio-Pilot-AI data generation scripts.

This module centralizes all configuration settings used across the data generation tools.
Update settings here to affect all scripts that use them.

Usage:
    from config import ES_CONFIG, GEMINI_CONFIG, FILE_PATHS, GENERATION_SETTINGS
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- Elasticsearch Configuration ---
ES_CONFIG = {
    'endpoint_url': os.getenv("ES_ENDPOINT_URL", "https://localhost:9200"),
    'api_key': os.getenv("ES_API_KEY"),
    'bulk_batch_size': 100,
    'request_timeout': 60,
    'verify_certs': False,
    
    # Index names
    'indices': {
        'accounts': "financial_accounts",
        'holdings': "financial_holdings", 
        'asset_details': "financial_asset_details",
        'news': "financial_news",
        'reports': "financial_reports"
    },
    
    # Index creation settings
    'auto_create_indices': True,  # Automatically create indices if they don't exist
    'index_settings': {
        'number_of_shards': 1,
        'number_of_replicas': 0
    }
}

# --- Gemini API Configuration ---
GEMINI_CONFIG = {
    'api_key': os.getenv("GEMINI_API_KEY"),
    'model_name': 'gemini-2.5-pro',
    'request_delay_seconds': 0.5,
    'max_retries': 3,
    'response_mime_type': "application/json",
    'safety_settings': {
        'HARM_CATEGORY_HARASSMENT': 'BLOCK_NONE',
        'HARM_CATEGORY_HATE_SPEECH': 'BLOCK_NONE',
        'HARM_CATEGORY_SEXUALLY_EXPLICIT': 'BLOCK_NONE',
        'HARM_CATEGORY_DANGEROUS_CONTENT': 'BLOCK_NONE',
    }
}

# --- File Paths Configuration ---
# Get the base directory (parent of scripts directory)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FILE_PATHS = {
    # Generated data files
    'generated_accounts': os.path.join(BASE_DIR, "generated_data", "generated_accounts.jsonl"),
    'generated_holdings': os.path.join(BASE_DIR, "generated_data", "generated_holdings.jsonl"), 
    'generated_asset_details': os.path.join(BASE_DIR, "generated_data", "generated_asset_details.jsonl"),
    'generated_news': os.path.join(BASE_DIR, "generated_data", "generated_news.jsonl"),
    'generated_reports': os.path.join(BASE_DIR, "generated_data", "generated_reports.jsonl"),
    'generated_controlled_news': os.path.join(BASE_DIR, "generated_data", "generated_controlled_news.jsonl"),
    'generated_controlled_reports': os.path.join(BASE_DIR, "generated_data", "generated_controlled_reports.jsonl"),
    
    # Prompt template files
    'prompts': {
        'general_news': os.path.join(BASE_DIR, "prompts", "general_market_news.txt"),
        'specific_news': os.path.join(BASE_DIR, "prompts", "specific_news.txt"), 
        'specific_report': os.path.join(BASE_DIR, "prompts", "specific_report.txt"),
        'thematic_report': os.path.join(BASE_DIR, "prompts", "thematic_sector_report.txt"),
    },
    
    # Elasticsearch index mappings
    'index_mappings': os.path.join(BASE_DIR, "elasticsearch", "index_mappings.json")
}

# --- Data Generation Settings ---
GENERATION_SETTINGS = {
    # Account and holdings generation
    'accounts': {
        'num_accounts': 7000,
        'min_holdings_per_account': 10,
        'max_holdings_per_account': 25
    },
    
    # News generation (main script)
    'news': {
        'num_specific_per_asset': 1,
        'num_general_articles': 500,
        'num_specific_assets_for_news': 50
    },
    
    # Reports generation (main script)
    'reports': {
        'num_specific_per_asset': 1,
        'num_thematic_reports': 100,
        'num_specific_assets_for_reports': 20
    },
    
    # Controlled generation (trigger script)
    'controlled': {
        'num_specific_news': 5,
        'num_general_news': 4,
        'num_specific_reports': 2,
        'num_thematic_reports': 1
    }
}

# --- Account Generation Constants ---
ACCOUNT_SETTINGS = {
    'types': ['Growth', 'Conservative', 'Income-Focused', 'Balanced', 'Aggressive Growth', 'Retirement'],
    'risk_profiles': ['High', 'Medium', 'Low', 'Very Low'],
    'contact_preferences': ['email', 'app_notification', 'none'],
    'us_states': [
        "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
        "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
        "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
        "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
        "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"
    ]
}

# --- Content Generation Constants ---
CONTENT_SETTINGS = {
    'sentiment_options': ["positive", "negative", "neutral", "mixed"],
    
    'news_event_themes': [
        "strong earnings", "new product launch", "regulatory challenge", "economic slowdown",
        "acquisition rumor", "patent dispute", "CEO change", "supply chain disruption",
        "dividend increase", "stock split announcement", "cybersecurity breach", "environmental lawsuit"
    ],
    
    'general_market_events': [
        "inflation data release", "central bank interest rate decision", "global supply chain disruption",
        "energy prices fluctuation", "consumer spending trends", "employment report surprising figures",
        "geopolitical tensions impacting trade", "housing market slowdown", "manufacturing PMI growth"
    ],
    
    'report_types': [
        "Q1 Earnings Summary", "Q2 Earnings Summary", "Q3 Earnings Summary", "Q4 Earnings Summary",
        "Annual Analyst Report", "Regulatory Filing Update", "Sustainability Report Summary"
    ],
    
    'report_focus_themes': [
        "revenue growth", "new product pipeline", "compliance challenges", "market share shifts",
        "sustainability efforts", "cost-cutting measures", "research & development breakthroughs",
        "debt restructuring", "merger and acquisition impact", "divestiture plans"
    ],
    
    'theme_industries': [
        "impact of AI on enterprise software", "future of renewable energy investment",
        "global supply chain resilience", "consumer spending habits in inflationary environment",
        "rise of fintech innovation", "challenges in global semiconductor production",
        "evolution of healthcare technology", "urban development and real estate trends",
        "future of remote work and its economic impact"
    ]
}

# --- Bad Event Configuration (for trigger script) ---
# --- Event Configurations ---
EVENT_CONFIGS = {
    'bad_news': {
        'target_news_symbol': 'TSLA',
        'news_theme': "major recall impacting new vehicle launches and brand reputation",
        'target_report_symbol': 'FCX',
        'report_focus': "unexpected production shortfall due to severe weather disrupting mining operations", 
        'sentiment': "negative",
        'description': "Targeted negative news for specific companies"
    },
    'market_crash': {
        'target_news_symbol': 'SPY',
        'news_theme': "widespread market selloff triggered by economic uncertainty and inflation concerns",
        'target_report_symbol': 'QQQ',
        'report_focus': "significant technology sector decline amid rising interest rates and regulatory pressure",
        'sentiment': "very negative",
        'description': "Broad market crash scenario affecting multiple sectors",
        'additional_symbols': ['VTI', 'IWM', 'XLF', 'XLE'],  # Additional ETFs affected
        'market_wide_impact': True
    },
    'volatility': {
        'target_news_symbol': 'VIX',
        'news_theme': "extreme market volatility driven by geopolitical tensions and uncertain economic data",
        'target_report_symbol': 'UVXY',
        'report_focus': "heightened volatility expectations creating trading opportunities and risk management challenges",
        'sentiment': "neutral_volatile",
        'description': "High volatility market conditions with mixed sentiment",
        'volatility_symbols': ['SVXY', 'VIXY', 'TVIX'],  # Volatility-related instruments
        'mixed_sentiment': True
    }
}

# Legacy configuration for backward compatibility
BAD_EVENT_CONFIG = EVENT_CONFIGS['bad_news']

# --- Common Field Names ---
FIELD_NAMES = {
    'primary_symbol': "primary_symbol",
    'company_symbol': "company_symbol"
}

# --- Price Generation Settings ---
PRICE_SETTINGS = {
    'stock_price_range': (20, 1500),
    'etf_price_range': (50, 600), 
    'bond_price_range': (85, 115),  # Bonds typically around 100 (par)
    'price_fluctuation_range': (0.98, 1.02)  # Small daily fluctuation
}

# --- Holdings Generation Settings ---
HOLDINGS_SETTINGS = {
    'stock_quantity_range': (5, 200),
    'etf_quantity_range': (1, 50),
    'bond_face_values': [1000, 5000, 10000, 25000, 50000],
    'high_value_threshold': 75000,  # Threshold for marking holdings as high value
    'purchase_date_range_years': 10,  # How far back purchases can go
    'purchase_date_buffer_days': 30   # No purchases in last N days
}

# --- Validation Functions ---
def validate_config(check_gemini=True, check_elasticsearch=True):
    """
    Validate that required configuration values are set.
    
    Args:
        check_gemini: Whether to validate GEMINI_API_KEY (only needed for generation)
        check_elasticsearch: Whether to validate ES_API_KEY (needed for ingestion)
    
    Returns:
        tuple: (bool, list) - (is_valid, list_of_errors)
    """
    errors = []
    
    # Check Elasticsearch if needed
    if check_elasticsearch and not ES_CONFIG['api_key']:
        errors.append("ES_API_KEY environment variable not set")
    
    # Check Gemini only if needed (for generation, not for loading existing data)
    if check_gemini and not GEMINI_CONFIG['api_key']:
        errors.append("GEMINI_API_KEY environment variable not set")
    
    # Check required directories exist for prompt files (only if generating)
    if check_gemini:
        for prompt_name, prompt_file in FILE_PATHS['prompts'].items():
            if not os.path.exists(prompt_file):
                errors.append(f"Prompt file not found: {prompt_file}")
    
    return len(errors) == 0, errors

def get_elasticsearch_client_config():
    """
    Get Elasticsearch client configuration ready for use.
    
    Returns:
        dict: Configuration for Elasticsearch client
    """
    return {
        'hosts': [ES_CONFIG['endpoint_url']],
        'api_key': ES_CONFIG['api_key'],
        'request_timeout': ES_CONFIG['request_timeout'],
        'verify_certs': ES_CONFIG['verify_certs']
    }

def get_gemini_generation_config():
    """
    Get Gemini generation configuration ready for use.
    
    Returns:
        dict: Configuration for Gemini generation
    """
    return {
        'response_mime_type': GEMINI_CONFIG['response_mime_type']
    }

# --- Demo Market Simulation Settings ---
DEMO_CONFIG = {
    'update_interval_seconds': 30,
    'auto_start': True,
    'initial_news_count': 3,
    
    # Price Movement Settings
    'base_volatility': 0.08,  # 8% base daily volatility for demo-friendly swings
    'correlation_strength': 0.3,  # Sector correlation factor
    'price_bounds': {
        'max_daily_change': 0.30,  # ±30% maximum daily change
        'min_price': 1.0,  # Minimum price floor
        'circuit_breaker': 0.20  # Halt trading if >20% move in 30 seconds
    },
    
    # Market Modes
    'volatility_modes': {
        'calm': {'multiplier': 0.5, 'event_frequency': 0.1},      # 50% volatility, rare events
        'active': {'multiplier': 1.0, 'event_frequency': 0.3},     # Normal volatility, regular events  
        'extreme': {'multiplier': 2.0, 'event_frequency': 0.6}     # 200% volatility, frequent events
    },
    'default_mode': 'active',
    
    # News Generation Settings
    'news_triggers': {
        'major_threshold': 0.05,    # ±5% triggers major news
        'minor_threshold': 0.02,    # ±2% triggers minor news  
        'sector_threshold': 0.03,   # ±3% for multiple stocks triggers sector news
        'cooldown_minutes': 10,     # Min time between news for same symbol
        'max_daily_articles': 5     # Max articles per symbol per day
    },
    
    # Event System
    'auto_events': {
        'enabled': True,
        'base_frequency_per_hour': 8,  # 8 events per hour on average
        'event_types': {
            'single_stock': 0.4,    # 40% single company events
            'sector_wide': 0.3,     # 30% sector events  
            'market_wide': 0.2,     # 20% market events
            'volatility_spike': 0.1 # 10% volatility events
        }
    },
    
    # Preset Events
    'preset_events': {
        'market_crash': {
            'price_impact': -0.15,  # -15% across all stocks
            'volatility_multiplier': 3.0,
            'duration_minutes': 30,
            'news_count': 10
        },
        'tech_boom': {
            'sector': 'Technology',
            'price_impact': 0.10,   # +10% for tech stocks
            'volatility_multiplier': 2.0,
            'duration_minutes': 15,
            'news_count': 5
        },
        'volatility_spike': {
            'volatility_multiplier': 4.0,
            'duration_minutes': 20,
            'news_count': 3
        }
    },
    
    # Market Bias Settings
    'market_bias': {
        'bull': 0.02,     # +2% daily drift
        'neutral': 0.0,   # No drift
        'bear': -0.02     # -2% daily drift
    },
    'default_bias': 'neutral',
    
    # WebSocket Settings
    'websocket': {
        'broadcast_interval': 5,  # Broadcast updates every 5 seconds
        'max_connections': 50,
        'heartbeat_interval': 30
    }
}

# --- Debug and Logging Settings ---
DEBUG_SETTINGS = {
    'log_level': 'INFO',
    'log_format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'show_progress_bars': True,
    'verbose_api_calls': False
}