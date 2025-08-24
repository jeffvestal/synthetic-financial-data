"""
Central symbol and asset configuration for Portfolio-Pilot-AI synthetic data generation.

This module contains all stock, ETF, and bond definitions used across the data generation scripts.
Update symbols here to affect all scripts that use them.

Usage:
    from symbols_config import STOCK_SYMBOLS_AND_INFO, ETF_SYMBOLS_AND_INFO, BOND_TYPES
    from symbols_config import get_all_asset_symbols, get_asset_info
"""

# --- Stock Symbols and Information ---
# Major US stocks from NASDAQ 100 and S&P 500
STOCK_SYMBOLS_AND_INFO = {
    # Technology Sector
    'AAPL': {'name': 'Apple Inc.', 'sector': 'Technology', 'indices': ['NASDAQ 100', 'S&P 500']},
    'MSFT': {'name': 'Microsoft Corp.', 'sector': 'Technology', 'indices': ['NASDAQ 100', 'S&P 500']},
    'GOOGL': {'name': 'Alphabet Inc. (Class A)', 'sector': 'Communication Services',
              'indices': ['NASDAQ 100', 'S&P 500']},
    'AMZN': {'name': 'Amazon.com Inc.', 'sector': 'Consumer Discretionary', 'indices': ['NASDAQ 100', 'S&P 500']},
    'NVDA': {'name': 'NVIDIA Corp.', 'sector': 'Technology', 'indices': ['NASDAQ 100', 'S&P 500']},
    'META': {'name': 'Meta Platforms Inc.', 'sector': 'Communication Services', 'indices': ['NASDAQ 100', 'S&P 500']},
    'TSLA': {'name': 'Tesla Inc.', 'sector': 'Consumer Discretionary', 'indices': ['NASDAQ 100', 'S&P 500']},
    'AVGO': {'name': 'Broadcom Inc.', 'sector': 'Information Technology', 'indices': ['NASDAQ 100', 'S&P 500']},
    'ADBE': {'name': 'Adobe Inc.', 'sector': 'Technology', 'indices': ['NASDAQ 100', 'S&P 500']},
    'CSCO': {'name': 'Cisco Systems Inc.', 'sector': 'Technology', 'indices': ['NASDAQ 100', 'S&P 500']},
    'INTC': {'name': 'Intel Corp.', 'sector': 'Technology', 'indices': ['NASDAQ 100', 'S&P 500']},
    'QCOM': {'name': 'Qualcomm Inc.', 'sector': 'Technology', 'indices': ['NASDAQ 100', 'S&P 500']},
    'TXN': {'name': 'Texas Instruments Inc.', 'sector': 'Technology', 'indices': ['NASDAQ 100', 'S&P 500']},
    'INTU': {'name': 'Intuit Inc.', 'sector': 'Technology', 'indices': ['NASDAQ 100', 'S&P 500']},
    'ADSK': {'name': 'Autodesk Inc.', 'sector': 'Technology', 'indices': ['NASDAQ 100', 'S&P 500']},
    'CDNS': {'name': 'Cadence Design Systems Inc.', 'sector': 'Technology', 'indices': ['NASDAQ 100', 'S&P 500']},
    'LRCX': {'name': 'Lam Research Corp.', 'sector': 'Technology', 'indices': ['NASDAQ 100', 'S&P 500']},
    'SNPS': {'name': 'Synopsys Inc.', 'sector': 'Technology', 'indices': ['NASDAQ 100', 'S&P 500']},
    'WDAY': {'name': 'Workday Inc.', 'sector': 'Technology', 'indices': ['NASDAQ 100', 'S&P 500']},
    'CRM': {'name': 'Salesforce Inc.', 'sector': 'Technology', 'indices': ['S&P 500', 'DJIA']},
    'IBM': {'name': 'International Business Machines Corp.', 'sector': 'Technology', 'indices': ['S&P 500', 'DJIA']},
    'ACN': {'name': 'Accenture Plc (Class A)', 'sector': 'Information Technology', 'indices': ['S&P 500']},

    # Communication Services
    'CMCSA': {'name': 'Comcast Corp.', 'sector': 'Communication Services', 'indices': ['NASDAQ 100', 'S&P 500']},
    'TMUS': {'name': 'T-Mobile US Inc.', 'sector': 'Communication Services', 'indices': ['NASDAQ 100', 'S&P 500']},
    'CHTR': {'name': 'Charter Communications Inc.', 'sector': 'Communication Services',
             'indices': ['NASDAQ 100', 'S&P 500']},
    'EA': {'name': 'Electronic Arts Inc.', 'sector': 'Communication Services', 'indices': ['NASDAQ 100', 'S&P 500']},
    'DIS': {'name': 'The Walt Disney Co.', 'sector': 'Communication Services', 'indices': ['S&P 500']},
    'T': {'name': 'AT&T Inc.', 'sector': 'Communication Services', 'indices': ['S&P 500']},

    # Healthcare
    'AMGN': {'name': 'Amgen Inc.', 'sector': 'Healthcare', 'indices': ['NASDAQ 100', 'S&P 500']},
    'ISRG': {'name': 'Intuitive Surgical Inc.', 'sector': 'Healthcare', 'indices': ['NASDAQ 100', 'S&P 500']},
    'MRNA': {'name': 'Moderna Inc.', 'sector': 'Healthcare', 'indices': ['NASDAQ 100', 'S&P 500']},
    'UNH': {'name': 'UnitedHealth Group Inc.', 'sector': 'Healthcare', 'indices': ['S&P 500', 'DJIA']},
    'LLY': {'name': 'Eli Lilly and Co.', 'sector': 'Healthcare', 'indices': ['S&P 500']},
    'PFE': {'name': 'Pfizer Inc.', 'sector': 'Healthcare', 'indices': ['S&P 500']},
    'DHR': {'name': 'Danaher Corp.', 'sector': 'Healthcare', 'indices': ['S&P 500']},
    'SYK': {'name': 'Stryker Corp.', 'sector': 'Healthcare', 'indices': ['S&P 500']},
    'CVS': {'name': 'CVS Health Corp.', 'sector': 'Healthcare', 'indices': ['S&P 500']},
    'ELV': {'name': 'Elevance Health Inc.', 'sector': 'Healthcare', 'indices': ['S&P 500']},
    'BAX': {'name': 'Baxter International Inc.', 'sector': 'Healthcare', 'indices': ['S&P 500']},
    'BDX': {'name': 'Becton, Dickinson and Co.', 'sector': 'Healthcare', 'indices': ['S&P 500']},
    'JNJ': {'name': 'Johnson & Johnson', 'sector': 'Healthcare', 'indices': ['S&P 500', 'DJIA']},

    # Consumer Staples
    'PEP': {'name': 'PepsiCo Inc.', 'sector': 'Consumer Staples', 'indices': ['NASDAQ 100', 'S&P 500']},
    'COST': {'name': 'Costco Wholesale Corp.', 'sector': 'Consumer Staples', 'indices': ['NASDAQ 100', 'S&P 500']},
    'MDLZ': {'name': 'Mondelez International Inc.', 'sector': 'Consumer Staples', 'indices': ['NASDAQ 100', 'S&P 500']},
    'WMT': {'name': 'Walmart Inc.', 'sector': 'Consumer Staples', 'indices': ['S&P 500', 'DJIA']},
    'PG': {'name': 'Procter & Gamble Co.', 'sector': 'Consumer Staples', 'indices': ['S&P 500', 'DJIA']},
    'KO': {'name': 'Coca-Cola Co.', 'sector': 'Consumer Staples', 'indices': ['S&P 500', 'DJIA']},
    'PM': {'name': 'Philip Morris International Inc.', 'sector': 'Consumer Staples', 'indices': ['S&P 500']},
    'MO': {'name': 'Altria Group Inc.', 'sector': 'Consumer Staples', 'indices': ['S&P 500']},
    'CL': {'name': 'Colgate-Palmolive Co.', 'sector': 'Consumer Staples', 'indices': ['S&P 500']},
    'WBA': {'name': 'Walgreens Boots Alliance Inc.', 'sector': 'Consumer Staples', 'indices': ['S&P 500']},

    # Consumer Discretionary
    'SBUX': {'name': 'Starbucks Corp.', 'sector': 'Consumer Discretionary', 'indices': ['NASDAQ 100', 'S&P 500']},
    'BKNG': {'name': 'Booking Holdings Inc.', 'sector': 'Consumer Discretionary', 'indices': ['NASDAQ 100', 'S&P 500']},
    'ROST': {'name': 'Ross Stores Inc.', 'sector': 'Consumer Discretionary', 'indices': ['NASDAQ 100', 'S&P 500']},
    'HD': {'name': 'Home Depot Inc.', 'sector': 'Consumer Discretionary', 'indices': ['S&P 500', 'DJIA']},
    'NKE': {'name': 'NIKE Inc. (Class B)', 'sector': 'Consumer Discretionary', 'indices': ['S&P 500', 'DJIA']},
    'MCD': {'name': 'McDonald\'s Corp.', 'sector': 'Consumer Discretionary', 'indices': ['S&P 500', 'DJIA']},
    'GM': {'name': 'General Motors Co.', 'sector': 'Consumer Discretionary', 'indices': ['S&P 500']},
    'LVS': {'name': 'Las Vegas Sands Corp.', 'sector': 'Consumer Discretionary', 'indices': ['S&P 500']},

    # Financials
    'PYPL': {'name': 'PayPal Holdings Inc.', 'sector': 'Financials', 'indices': ['NASDAQ 100', 'S&P 500']},
    'FISV': {'name': 'Fiserv Inc.', 'sector': 'Financials', 'indices': ['NASDAQ 100', 'S&P 500']},
    'JPM': {'name': 'JPMorgan Chase & Co.', 'sector': 'Financials', 'indices': ['S&P 500', 'DJIA']},
    'BRK.B': {'name': 'Berkshire Hathaway Inc. (Class B)', 'sector': 'Financials', 'indices': ['S&P 500']},
    'V': {'name': 'Visa Inc. (Class A)', 'sector': 'Financials', 'indices': ['S&P 500', 'DJIA']},
    'BAC': {'name': 'Bank of America Corp.', 'sector': 'Financials', 'indices': ['S&P 500']},
    'GS': {'name': 'Goldman Sachs Group Inc.', 'sector': 'Financials', 'indices': ['S&P 500', 'DJIA']},
    'TRV': {'name': 'The Travelers Cos. Inc.', 'sector': 'Financials', 'indices': ['S&P 500', 'DJIA']},
    'AIG': {'name': 'American International Group Inc.', 'sector': 'Financials', 'indices': ['S&P 500']},
    'USB': {'name': 'U.S. Bancorp', 'sector': 'Financials', 'indices': ['S&P 500']},
    'SCHW': {'name': 'Charles Schwab Corp.', 'sector': 'Financials', 'indices': ['S&P 500']},
    'WFC': {'name': 'Wells Fargo & Co.', 'sector': 'Financials', 'indices': ['S&P 500']},
    'CB': {'name': 'Chubb Ltd.', 'sector': 'Financials', 'indices': ['S&P 500']},
    'MET': {'name': 'MetLife Inc.', 'sector': 'Financials', 'indices': ['S&P 500']},
    'PNC': {'name': 'PNC Financial Services Group Inc.', 'sector': 'Financials', 'indices': ['S&P 500']},
    'PRU': {'name': 'Prudential Financial Inc.', 'sector': 'Financials', 'indices': ['S&P 500']},
    'MS': {'name': 'Morgan Stanley', 'sector': 'Financials', 'indices': ['S&P 500']},

    # Energy
    'XOM': {'name': 'Exxon Mobil Corp.', 'sector': 'Energy', 'indices': ['S&P 500', 'DJIA']},
    'CVX': {'name': 'Chevron Corp.', 'sector': 'Energy', 'indices': ['S&P 500', 'DJIA']},
    'COP': {'name': 'ConocoPhillips', 'sector': 'Energy', 'indices': ['S&P 500']},
    'SLB': {'name': 'Schlumberger Ltd.', 'sector': 'Energy', 'indices': ['S&P 500']},
    'EOG': {'name': 'EOG Resources Inc.', 'sector': 'Energy', 'indices': ['S&P 500']},

    # Industrials
    'HON': {'name': 'Honeywell International Inc.', 'sector': 'Industrials', 'indices': ['S&P 500', 'DJIA']},
    'BA': {'name': 'The Boeing Co.', 'sector': 'Industrials', 'indices': ['S&P 500', 'DJIA']},
    'CAT': {'name': 'Caterpillar Inc.', 'sector': 'Industrials', 'indices': ['S&P 500', 'DJIA']},
    'MMM': {'name': '3M Co.', 'sector': 'Industrials', 'indices': ['S&P 500', 'DJIA']},
    'UPS': {'name': 'United Parcel Service Inc. (Class B)', 'sector': 'Industrials', 'indices': ['S&P 500']},
    'DE': {'name': 'Deere & Co.', 'sector': 'Industrials', 'indices': ['S&P 500']},
    'RTX': {'name': 'RTX Corp.', 'sector': 'Industrials', 'indices': ['S&P 500']},
    'LMT': {'name': 'Lockheed Martin Corp.', 'sector': 'Industrials', 'indices': ['S&P 500']},
    'ITW': {'name': 'Illinois Tool Works Inc.', 'sector': 'Industrials', 'indices': ['S&P 500']},
    'GE': {'name': 'General Electric Co.', 'sector': 'Industrials', 'indices': ['S&P 500']},
    'UNP': {'name': 'Union Pacific Corp.', 'sector': 'Industrials', 'indices': ['S&P 500']},

    # Utilities
    'EXC': {'name': 'Exelon Corp.', 'sector': 'Utilities', 'indices': ['NASDAQ 100', 'S&P 500']},
    'DUK': {'name': 'Duke Energy Corp.', 'sector': 'Utilities', 'indices': ['S&P 500']},
    'SO': {'name': 'The Southern Co.', 'sector': 'Utilities', 'indices': ['S&P 500']},
    'XEL': {'name': 'Xcel Energy Inc.', 'sector': 'Utilities', 'indices': ['S&P 500']},
    'AEP': {'name': 'American Electric Power Co. Inc.', 'sector': 'Utilities', 'indices': ['S&P 500']},
    'PCG': {'name': 'PG&E Corp.', 'sector': 'Utilities', 'indices': ['S&P 500']},
    'NEE': {'name': 'NextEra Energy Inc.', 'sector': 'Utilities', 'indices': ['S&P 500']},
    'ETR': {'name': 'Entergy Corp.', 'sector': 'Utilities', 'indices': ['S&P 500']},

    # Materials
    'FCX': {'name': 'Freeport-McMoRan Inc.', 'sector': 'Materials', 'indices': ['S&P 500']},
    'DOW': {'name': 'Dow Inc.', 'sector': 'Materials', 'indices': ['S&P 500']},

    # Real Estate
    'SPG': {'name': 'Simon Property Group Inc.', 'sector': 'Real Estate', 'indices': ['S&P 500']},
}

# --- ETF Symbols and Information ---
# Major US and international ETFs across different asset classes
ETF_SYMBOLS_AND_INFO = {
    # US Broad Market ETFs
    'SPY': {'name': 'SPDR S&P 500 ETF Trust', 'sector': 'Diversified', 'indices': ['S&P 500'], 'country': 'USA'},
    'IVV': {'name': 'iShares Core S&P 500 ETF', 'sector': 'Diversified', 'indices': ['S&P 500'], 'country': 'USA'},
    'VOO': {'name': 'Vanguard S&P 500 ETF', 'sector': 'Diversified', 'indices': ['S&P 500'], 'country': 'USA'},
    'QQQ': {'name': 'Invesco QQQ Trust', 'sector': 'Technology-Focused', 'indices': ['NASDAQ 100'], 'country': 'USA'},
    'VTI': {'name': 'Vanguard Total Stock Market ETF', 'sector': 'Diversified', 'indices': ['Total US Market'],
            'country': 'USA'},
    'DIA': {'name': 'SPDR Dow Jones Industrial Avg ETF', 'sector': 'Diversified', 'indices': ['DJIA'],
            'country': 'USA'},

    # US Sector ETFs
    'XLK': {'name': 'Technology Select Sector SPDR Fund', 'sector': 'Technology', 'indices': ['S&P 500 Sectors'],
            'country': 'USA'},
    'XLF': {'name': 'Financial Select Sector SPDR Fund', 'sector': 'Financials', 'indices': ['S&P 500 Sectors'],
            'country': 'USA'},
    'XLV': {'name': 'Health Care Select Sector SPDR Fund', 'sector': 'Healthcare', 'indices': ['S&P 500 Sectors'],
            'country': 'USA'},
    'XLE': {'name': 'Energy Select Sector SPDR Fund', 'sector': 'Energy', 'indices': ['S&P 500 Sectors'],
            'country': 'USA'},
    'XLI': {'name': 'Industrial Select Sector SPDR Fund', 'sector': 'Industrials', 'indices': ['S&P 500 Sectors'],
            'country': 'USA'},
    'XLP': {'name': 'Consumer Staples Select Sector SPDR Fund', 'sector': 'Consumer Staples',
            'indices': ['S&P 500 Sectors'], 'country': 'USA'},
    'XLY': {'name': 'Consumer Discretionary Select Sector SPDR Fund', 'sector': 'Consumer Discretionary',
            'indices': ['S&P 500 Sectors'], 'country': 'USA'},
    'XLB': {'name': 'Materials Select Sector SPDR Fund', 'sector': 'Materials', 'indices': ['S&P 500 Sectors'],
            'country': 'USA'},
    'XLC': {'name': 'Communication Services Select Sector SPDR Fund', 'sector': 'Communication Services',
            'indices': ['S&P 500 Sectors'], 'country': 'USA'},
    'XLU': {'name': 'Utilities Select Sector SPDR Fund', 'sector': 'Utilities', 'indices': ['S&P 500 Sectors'],
            'country': 'USA'},

    # Specialized US ETFs
    'VGT': {'name': 'Vanguard Information Technology ETF', 'sector': 'Technology', 'indices': ['MSCI US IMI'],
            'country': 'USA'},
    'SMH': {'name': 'VanEck Semiconductor ETF', 'sector': 'Technology', 'indices': ['MVIS US Listed Semiconductor 25'],
            'country': 'USA'},
    'IYR': {'name': 'iShares U.S. Real Estate ETF', 'sector': 'Real Estate', 'indices': ['Dow Jones U.S. Real Estate'],
            'country': 'USA'},
    'VNQ': {'name': 'Vanguard Real Estate ETF', 'sector': 'Real Estate', 'indices': ['MSCI US REIT'], 'country': 'USA'},

    # International ETFs
    'VXUS': {'name': 'Vanguard Total International Stock ETF', 'sector': 'Diversified International',
             'indices': ['FTSE Global All Cap ex US'], 'country': 'Global'},
    'VEA': {'name': 'Vanguard FTSE Developed Markets ETF', 'sector': 'Developed Markets Equity',
            'indices': ['FTSE Developed All Cap ex US'], 'country': 'Global'},
    'IEFA': {'name': 'iShares Core MSCI EAFE ETF', 'sector': 'Developed Markets Equity', 'indices': ['MSCI EAFE'],
             'country': 'Global'},
    'VWO': {'name': 'Vanguard FTSE Emerging Markets ETF', 'sector': 'Emerging Markets Equity',
            'indices': ['FTSE Emerging Markets'], 'country': 'Global'},
    'IEMG': {'name': 'iShares Core MSCI Emerging Markets ETF', 'sector': 'Emerging Markets Equity',
             'indices': ['MSCI Emerging Markets'], 'country': 'Global'},
    'EFA': {'name': 'iShares MSCI EAFE ETF', 'sector': 'Developed Markets Equity', 'indices': ['MSCI EAFE'],
            'country': 'Global'},

    # Single Country ETFs
    'EWJ': {'name': 'iShares MSCI Japan ETF', 'sector': 'Single Country Equity', 'indices': ['MSCI Japan'],
            'country': 'Japan'},
    'FXI': {'name': 'iShares China Large-Cap ETF', 'sector': 'Single Country Equity', 'indices': ['FTSE China 50'],
            'country': 'China'},
    'DAX': {'name': 'iShares Core DAX UCITS ETF (Acc)', 'sector': 'Single Country Equity', 'indices': ['DAX 40'],
            'country': 'Germany'},
    'EWW': {'name': 'iShares MSCI Mexico ETF', 'sector': 'Single Country Equity', 'indices': ['MSCI Mexico'],
            'country': 'Mexico'},
    'EWC': {'name': 'iShares MSCI Canada ETF', 'sector': 'Single Country Equity', 'indices': ['MSCI Canada'],
            'country': 'Canada'},
    'EWG': {'name': 'iShares MSCI Germany ETF', 'sector': 'Single Country Equity', 'indices': ['MSCI Germany'],
            'country': 'Germany'},
    'EWS': {'name': 'iShares MSCI Singapore ETF', 'sector': 'Single Country Equity', 'indices': ['MSCI Singapore'],
            'country': 'Singapore'},
    'EWL': {'name': 'iShares MSCI Switzerland ETF', 'sector': 'Single Country Equity', 'indices': ['MSCI Switzerland'],
            'country': 'Switzerland'},
    'EWP': {'name': 'iShares MSCI Spain Capped ETF', 'sector': 'Single Country Equity', 'indices': ['MSCI Spain'],
            'country': 'Spain'},
    'EWI': {'name': 'iShares MSCI Italy Capped ETF', 'sector': 'Single Country Equity', 'indices': ['MSCI Italy'],
            'country': 'Italy'},
    'EWO': {'name': 'iShares MSCI Austria Capped ETF', 'sector': 'Single Country Equity', 'indices': ['MSCI Austria'],
            'country': 'Austria'},
    'INDA': {'name': 'iShares MSCI India ETF', 'sector': 'Single Country Equity', 'indices': ['MSCI India'],
             'country': 'India'},
    'FLJP': {'name': 'Franklin FTSE Japan ETF', 'sector': 'Single Country Equity', 'indices': ['FTSE Japan'],
             'country': 'Japan'},
    'FLCH': {'name': 'Franklin FTSE China ETF', 'sector': 'Single Country Equity', 'indices': ['FTSE China'],
             'country': 'China'}
}

# --- Bond Types and Information ---
# Various bond types including government, corporate, and international bonds
BOND_TYPES = [
    # US Government Bonds
    {'symbol': 'US_T_BOND_2YR', 'name': 'US Treasury Note (2 Year)', 'issuer': 'US Treasury',
     'sector': 'Government Bonds', 'country': 'USA'},
    {'symbol': 'US_T_BOND_5YR', 'name': 'US Treasury Note (5 Year)', 'issuer': 'US Treasury',
     'sector': 'Government Bonds', 'country': 'USA'},
    {'symbol': 'US_T_BOND_7YR', 'name': 'US Treasury Note (7 Year)', 'issuer': 'US Treasury',
     'sector': 'Government Bonds', 'country': 'USA'},
    {'symbol': 'US_T_BOND_10YR', 'name': 'US Treasury Note (10 Year)', 'issuer': 'US Treasury',
     'sector': 'Government Bonds', 'country': 'USA'},
    {'symbol': 'US_T_BOND_20YR', 'name': 'US Treasury Bond (20 Year)', 'issuer': 'US Treasury',
     'sector': 'Government Bonds', 'country': 'USA'},
    {'symbol': 'US_T_BOND_30YR', 'name': 'US Treasury Bond (30 Year)', 'issuer': 'US Treasury',
     'sector': 'Government Bonds', 'country': 'USA'},

    # US Inflation-Protected Bonds
    {'symbol': 'US_TIPS_5YR', 'name': 'US TIPS (5 Year)', 'issuer': 'US Treasury',
     'sector': 'Inflation-Protected Bonds', 'country': 'USA'},
    {'symbol': 'US_TIPS_10YR', 'name': 'US TIPS (10 Year)', 'issuer': 'US Treasury',
     'sector': 'Inflation-Protected Bonds', 'country': 'USA'},
    {'symbol': 'US_TIPS_30YR', 'name': 'US TIPS (30 Year)', 'issuer': 'US Treasury',
     'sector': 'Inflation-Protected Bonds', 'country': 'USA'},

    # US Municipal and Corporate Bonds
    {'symbol': 'US_MUNI_BOND', 'name': 'US Municipal Bond (Generic)', 'issuer': 'Various US Municipalities',
     'sector': 'Municipal Bonds', 'country': 'USA'},
    
    # US Corporate Bonds by Sector
    {'symbol': 'CORP_BOND_TECH_A', 'name': 'Tech Corp Bond A', 'issuer': 'Generic Tech Co. A',
     'sector': 'Corporate Bonds', 'country': 'USA'},
    {'symbol': 'CORP_BOND_FIN_B', 'name': 'Financial Corp Bond B', 'issuer': 'Generic Financial Co. B',
     'sector': 'Corporate Bonds', 'country': 'USA'},
    {'symbol': 'CORP_BOND_UTIL_C', 'name': 'Utility Corp Bond C', 'issuer': 'Generic Utility Co. C',
     'sector': 'Corporate Bonds', 'country': 'USA'},
    {'symbol': 'CORP_BOND_CONS_D', 'name': 'Consumer Corp Bond D', 'issuer': 'Generic Consumer Co. D',
     'sector': 'Corporate Bonds', 'country': 'USA'},
    {'symbol': 'CORP_BOND_HEALTH_E', 'name': 'Healthcare Corp Bond E', 'issuer': 'Generic Healthcare Co. E',
     'sector': 'Corporate Bonds', 'country': 'USA'},
    {'symbol': 'CORP_BOND_IND_F', 'name': 'Industrial Corp Bond F', 'issuer': 'Generic Industrial Co. F',
     'sector': 'Corporate Bonds', 'country': 'USA'},
    {'symbol': 'CORP_BOND_COMM_G', 'name': 'Comm Services Corp Bond G', 'issuer': 'Generic Comm Co. G',
     'sector': 'Corporate Bonds', 'country': 'USA'},
    {'symbol': 'CORP_BOND_MAT_H', 'name': 'Materials Corp Bond H', 'issuer': 'Generic Materials Co. H',
     'sector': 'Corporate Bonds', 'country': 'USA'},
    {'symbol': 'CORP_BOND_ENG_I', 'name': 'Energy Corp Bond I', 'issuer': 'Generic Energy Co. I',
     'sector': 'Corporate Bonds', 'country': 'USA'},
    {'symbol': 'CORP_BOND_REAL_J', 'name': 'Real Estate Corp Bond J', 'issuer': 'Generic Real Estate Co. J',
     'sector': 'Corporate Bonds', 'country': 'USA'},

    # International Government Bonds
    {'symbol': 'GER_BUND_5YR', 'name': 'German Bund (5 Year)', 'issuer': 'German Federal Government',
     'sector': 'Government Bonds', 'country': 'Germany'},
    {'symbol': 'GER_BUND_10YR', 'name': 'German Bund (10 Year)', 'issuer': 'German Federal Government',
     'sector': 'Government Bonds', 'country': 'Germany'},
    {'symbol': 'UK_GILT_5YR', 'name': 'UK Gilt (5 Year)', 'issuer': 'UK Government', 'sector': 'Government Bonds',
     'country': 'United Kingdom'},
    {'symbol': 'UK_GILT_10YR', 'name': 'UK Gilt (10 Year)', 'issuer': 'UK Government', 'sector': 'Government Bonds',
     'country': 'United Kingdom'},
    {'symbol': 'JAP_JGB_5YR', 'name': 'Japanese Government Bond (5 Year)', 'issuer': 'Japanese Government',
     'sector': 'Government Bonds', 'country': 'Japan'},
    {'symbol': 'JAP_JGB_10YR', 'name': 'Japanese Government Bond (10 Year)', 'issuer': 'Japanese Government',
     'sector': 'Government Bonds', 'country': 'Japan'},
    {'symbol': 'CAN_GB_5YR', 'name': 'Canadian Government Bond (5 Year)', 'issuer': 'Government of Canada',
     'sector': 'Government Bonds', 'country': 'Canada'},
    {'symbol': 'CAN_GB_10YR', 'name': 'Canadian Government Bond (10 Year)', 'issuer': 'Government of Canada',
     'sector': 'Government Bonds', 'country': 'Canada'},
    {'symbol': 'AUS_GB_5YR', 'name': 'Australian Government Bond (5 Year)', 'issuer': 'Australian Government',
     'sector': 'Government Bonds', 'country': 'Australia'},
    {'symbol': 'AUS_GB_10YR', 'name': 'Australian Government Bond (10 Year)', 'issuer': 'Australian Government',
     'sector': 'Government Bonds', 'country': 'Australia'},

    # International Corporate Bonds
    {'symbol': 'INTL_CORP_EU_A', 'name': 'Eurozone Corp Bond A', 'issuer': 'EuroCo A', 'sector': 'Corporate Bonds',
     'country': 'Germany'},
    {'symbol': 'INTL_CORP_EU_B', 'name': 'Eurozone Corp Bond B', 'issuer': 'EuroCo B', 'sector': 'Corporate Bonds',
     'country': 'France'},
    {'symbol': 'INTL_CORP_ASIA_C', 'name': 'Asia Corp Bond C', 'issuer': 'AsiaCo C', 'sector': 'Corporate Bonds',
     'country': 'Japan'},
    {'symbol': 'INTL_CORP_ASIA_D', 'name': 'Asia Corp Bond D', 'issuer': 'AsiaCo D', 'sector': 'Corporate Bonds',
     'country': 'China'},
    {'symbol': 'INTL_CORP_UK_E', 'name': 'UK Corp Bond E', 'issuer': 'UKCo E', 'sector': 'Corporate Bonds',
     'country': 'United Kingdom'},
    {'symbol': 'INTL_CORP_CAN_F', 'name': 'Canadian Corp Bond F', 'issuer': 'CanadaCo F', 'sector': 'Corporate Bonds',
     'country': 'Canada'},
    {'symbol': 'INTL_CORP_AUS_G', 'name': 'Australian Corp Bond G', 'issuer': 'AustraliaCo G',
     'sector': 'Corporate Bonds', 'country': 'Australia'},

    # Emerging Market Corporate Bonds
    {'symbol': 'INTL_CORP_EM_H', 'name': 'Emerging Market Corp Bond H', 'issuer': 'EMCo H',
     'sector': 'Emerging Market Corporate Bonds', 'country': 'Brazil'},
    {'symbol': 'INTL_CORP_EM_I', 'name': 'Emerging Market Corp Bond I', 'issuer': 'EMCo I',
     'sector': 'Emerging Market Corporate Bonds', 'country': 'India'},
    {'symbol': 'INTL_CORP_EM_J', 'name': 'Emerging Market Corp Bond J', 'issuer': 'EMCo J',
     'sector': 'Emerging Market Corporate Bonds', 'country': 'Mexico'}
]

# --- Derived Data Structures ---
# These are computed from the base data for convenience

# Combined asset information dictionary
ALL_ASSET_INFO = {**STOCK_SYMBOLS_AND_INFO, **ETF_SYMBOLS_AND_INFO}
for bond in BOND_TYPES:
    ALL_ASSET_INFO[bond['symbol']] = bond

# All asset symbols list
ALL_ASSET_SYMBOLS = (
    list(STOCK_SYMBOLS_AND_INFO.keys()) + 
    list(ETF_SYMBOLS_AND_INFO.keys()) + 
    [bond['symbol'] for bond in BOND_TYPES]
)

# --- Utility Functions ---

def get_all_asset_symbols():
    """
    Returns a list of all available asset symbols (stocks, ETFs, bonds).
    
    Returns:
        List[str]: All asset symbols
    """
    return ALL_ASSET_SYMBOLS.copy()

def get_asset_info(symbol):
    """
    Get asset information for a given symbol.
    
    Args:
        symbol (str): Asset symbol to look up
        
    Returns:
        dict or None: Asset information or None if not found
    """
    return ALL_ASSET_INFO.get(symbol)

def get_stock_symbols():
    """Returns list of stock symbols only."""
    return list(STOCK_SYMBOLS_AND_INFO.keys())

def get_etf_symbols():
    """Returns list of ETF symbols only."""
    return list(ETF_SYMBOLS_AND_INFO.keys())

def get_bond_symbols():
    """Returns list of bond symbols only."""
    return [bond['symbol'] for bond in BOND_TYPES]

def get_symbols_by_sector(sector):
    """
    Get all symbols for a specific sector.
    
    Args:
        sector (str): Sector name to filter by
        
    Returns:
        List[str]: Symbols in the specified sector
    """
    symbols = []
    for symbol, info in ALL_ASSET_INFO.items():
        if info.get('sector') == sector:
            symbols.append(symbol)
    return symbols

def validate_symbol(symbol):
    """
    Check if a symbol exists in the configuration.
    
    Args:
        symbol (str): Symbol to validate
        
    Returns:
        bool: True if symbol exists, False otherwise
    """
    return symbol in ALL_ASSET_INFO

def get_all_sectors():
    """
    Get a list of all unique sectors.
    
    Returns:
        List[str]: All unique sector names
    """
    sectors = set()
    for info in ALL_ASSET_INFO.values():
        if 'sector' in info:
            sectors.add(info['sector'])
    return sorted(list(sectors))