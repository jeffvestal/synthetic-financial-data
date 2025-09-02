#!/usr/bin/env python3
"""
Generate realistic trade activity data for financial accounts.

This script creates a comprehensive trading history with realistic price variations,
trade types (buy/sell/short/cover), and order statuses. Trade volume is based on
account risk profiles.

Usage:
    python3 scripts/generate_trades.py
"""

import json
import random
import uuid
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Tuple, Optional
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import FILE_PATHS, GENERATION_SETTINGS
from symbols_config import ALL_ASSET_INFO
from common_utils import (
    clear_file_if_exists,
    get_current_timestamp, 
    log_with_timestamp
)

# Trade type constants
TRADE_TYPES = ['buy', 'sell', 'short', 'cover']
ORDER_TYPES = ['market', 'limit', 'stop']
ORDER_STATUSES = ['executed', 'cancelled']

# Trade generation configuration from config
TRADE_CONFIG = GENERATION_SETTINGS.get('trades', {})
RISK_TRADE_VOLUMES = TRADE_CONFIG.get('risk_trade_volumes', {
    'Conservative': (5, 15),
    'Very Low': (5, 15),
    'Low': (5, 15),
    'Medium': (15, 50),
    'Moderate': (15, 50),
    'Growth': (50, 150),
    'High': (50, 150),
    'Very High': (50, 150)
})

def generate_trade_id(timestamp: datetime) -> str:
    """Generate unique trade ID with timestamp."""
    date_str = timestamp.strftime("%Y%m%d")
    unique_id = str(uuid.uuid4())[:8]
    return f"TRD-{date_str}-{unique_id}"

def calculate_execution_price(
    base_price: float, 
    quantity: float, 
    order_type: str,
    trade_type: str
) -> float:
    """
    Calculate realistic execution price with bid/ask spread and slippage.
    
    Args:
        base_price: Current market price
        quantity: Number of shares
        order_type: market, limit, or stop
        trade_type: buy, sell, short, or cover
        
    Returns:
        Execution price with realistic variations
    """
    # Base bid/ask spread
    spread = TRADE_CONFIG.get('bid_ask_spread', 0.005)
    
    # Determine if this is a large order
    large_order_threshold = TRADE_CONFIG.get('large_order_threshold', 1000)
    is_large_order = quantity > large_order_threshold
    
    # Apply spread based on trade direction
    if trade_type in ['buy', 'cover']:
        # Buyers pay the ask (higher price)
        price = base_price * (1 + spread/2)
    else:  # sell or short
        # Sellers receive the bid (lower price)
        price = base_price * (1 - spread/2)
    
    # Add slippage for large orders
    if is_large_order and order_type == 'market':
        slippage_min, slippage_max = TRADE_CONFIG.get('slippage_range', (0.001, 0.003))
        slippage = random.uniform(slippage_min, slippage_max)
        
        if trade_type in ['buy', 'cover']:
            price *= (1 + slippage)  # Pay more when buying large
        else:
            price *= (1 - slippage)  # Receive less when selling large
    
    # Limit orders might get better prices
    if order_type == 'limit':
        improvement = random.uniform(0, spread/4)
        if trade_type in ['buy', 'cover']:
            price *= (1 - improvement)
        else:
            price *= (1 + improvement)
    
    return round(price, 2)

def generate_trade_pattern(
    num_trades: int,
    symbols: List[str]
) -> List[Dict[str, str]]:
    """
    Generate realistic trade patterns with appropriate trade types.
    
    Returns list of trade patterns with symbol, trade_type, order_type.
    """
    patterns = []
    
    for _ in range(num_trades):
        symbol = random.choice(symbols)
        
        # Determine trade type with realistic distribution
        rand = random.random()
        if rand < 0.45:  # 45% buys
            trade_type = 'buy'
        elif rand < 0.85:  # 40% sells
            trade_type = 'sell'
        elif rand < 0.95:  # 10% shorts
            trade_type = 'short'
        else:  # 5% covers
            trade_type = 'cover'
        
        # Determine order type
        order_rand = random.random()
        if order_rand < 0.70:  # 70% market orders
            order_type = 'market'
        elif order_rand < 0.95:  # 25% limit orders
            order_type = 'limit'
        else:  # 5% stop orders
            order_type = 'stop'
        
        patterns.append({
            'symbol': symbol,
            'trade_type': trade_type,
            'order_type': order_type
        })
    
    return patterns

def generate_trades_for_account(
    account: Dict,
    asset_prices: Dict[str, float],
    time_window_start: datetime,
    time_window_end: datetime
) -> List[Dict]:
    """
    Generate all trades for a single account.
    
    Args:
        account: Account data dictionary
        asset_prices: Current prices for all assets
        time_window_start: Start of trading period
        time_window_end: End of trading period
        
    Returns:
        List of trade dictionaries
    """
    trades = []
    
    # Determine number of trades based on risk profile
    risk_profile = account.get('risk_profile', 'Medium')
    min_trades, max_trades = RISK_TRADE_VOLUMES.get(risk_profile, (15, 50))
    num_trades = random.randint(min_trades, max_trades)
    
    # Get available symbols
    available_symbols = list(asset_prices.keys())
    if not available_symbols:
        return trades
    
    # Generate trade patterns
    patterns = generate_trade_pattern(num_trades, available_symbols)
    
    # Generate timestamp for each trade
    time_range = (time_window_end - time_window_start).total_seconds()
    
    for pattern in patterns:
        # Random timestamp within window
        random_seconds = random.uniform(0, time_range)
        execution_timestamp = time_window_start + timedelta(seconds=random_seconds)
        
        # Generate trade details
        symbol = pattern['symbol']
        base_price = asset_prices[symbol]
        
        # Random quantity with some clustering for realistic portfolios
        if random.random() < 0.3:  # 30% chance of round lots
            quantity = random.choice([100, 200, 500, 1000])
        else:
            quantity = random.randint(10, 2000)
        
        # Determine order status
        cancellation_rate = TRADE_CONFIG.get('cancellation_rate', 0.07)
        order_status = 'cancelled' if random.random() < cancellation_rate else 'executed'
        
        # Calculate execution price (only for executed orders)
        if order_status == 'executed':
            execution_price = calculate_execution_price(
                base_price, 
                quantity, 
                pattern['order_type'],
                pattern['trade_type']
            )
            trade_cost = round(quantity * execution_price, 2)
        else:
            # Cancelled orders don't have execution price
            execution_price = 0
            trade_cost = 0
        
        # Create trade record
        trade = {
            'trade_id': generate_trade_id(execution_timestamp),
            'account_id': account['account_id'],
            'symbol': symbol,
            'trade_type': pattern['trade_type'],
            'order_type': pattern['order_type'],
            'order_status': order_status,
            'quantity': float(quantity),
            'execution_price': execution_price,
            'trade_cost': trade_cost,
            'execution_timestamp': execution_timestamp.isoformat(),
            'last_updated': get_current_timestamp()
        }
        
        trades.append(trade)
    
    # Sort trades by timestamp for realistic order
    trades.sort(key=lambda x: x['execution_timestamp'])
    
    return trades

def load_asset_prices() -> Dict[str, float]:
    """Load current prices from asset details file."""
    asset_prices = {}
    
    asset_file = FILE_PATHS.get('generated_asset_details')
    if not os.path.exists(asset_file):
        log_with_timestamp("WARNING: Asset details file not found. Using default prices.")
        # Provide some default prices
        for symbol in list(ALL_ASSET_INFO.keys())[:50]:
            asset_prices[symbol] = round(random.uniform(10, 500), 2)
        return asset_prices
    
    with open(asset_file, 'r') as f:
        for line in f:
            try:
                asset = json.loads(line)
                symbol = asset.get('symbol')
                current_price = asset.get('current_price', {}).get('price')
                if symbol and current_price:
                    asset_prices[symbol] = float(current_price)
            except json.JSONDecodeError:
                continue
    
    return asset_prices

def process_account_batch(
    accounts: List[Dict],
    asset_prices: Dict[str, float],
    time_window_start: datetime,
    time_window_end: datetime,
    output_file: str
) -> int:
    """
    Process a batch of accounts and write trades to file.
    
    Returns:
        Number of trades generated
    """
    total_trades = 0
    
    with open(output_file, 'a') as f:
        for account in accounts:
            trades = generate_trades_for_account(
                account,
                asset_prices,
                time_window_start,
                time_window_end
            )
            
            for trade in trades:
                f.write(json.dumps(trade) + '\n')
                total_trades += 1
    
    return total_trades

def main():
    """Main execution function."""
    log_with_timestamp("=== Starting Trade Generation ===")
    
    # Load configuration
    time_window_start = datetime.fromisoformat(TRADE_CONFIG.get('time_window_start', '2025-06-01'))
    time_window_end = datetime.fromisoformat(TRADE_CONFIG.get('time_window_end', '2025-08-28'))
    batch_size = TRADE_CONFIG.get('batch_size', 1000)
    
    log_with_timestamp(f"Trade window: {time_window_start.date()} to {time_window_end.date()}")
    log_with_timestamp(f"Batch size: {batch_size} accounts")
    
    # Load account data
    accounts_file = FILE_PATHS.get('generated_accounts')
    if not os.path.exists(accounts_file):
        log_with_timestamp("ERROR: Accounts file not found. Run generate_holdings_accounts.py first.")
        return 1
    
    accounts = []
    with open(accounts_file, 'r') as f:
        for line in f:
            try:
                accounts.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    
    log_with_timestamp(f"Loaded {len(accounts)} accounts")
    
    # Load asset prices
    asset_prices = load_asset_prices()
    log_with_timestamp(f"Loaded prices for {len(asset_prices)} assets")
    
    # Clear output file
    output_file = FILE_PATHS.get('generated_trades')
    clear_file_if_exists(output_file)
    
    # Process accounts in batches
    total_trades = 0
    total_accounts = len(accounts)
    
    for i in range(0, total_accounts, batch_size):
        batch_end = min(i + batch_size, total_accounts)
        batch = accounts[i:batch_end]
        
        log_with_timestamp(f"Processing batch {i//batch_size + 1}: accounts {i+1}-{batch_end}")
        
        batch_trades = process_account_batch(
            batch,
            asset_prices,
            time_window_start,
            time_window_end,
            output_file
        )
        
        total_trades += batch_trades
        log_with_timestamp(f"  Generated {batch_trades} trades")
    
    log_with_timestamp(f"=== Trade Generation Complete ===")
    log_with_timestamp(f"Total trades generated: {total_trades}")
    log_with_timestamp(f"Output file: {output_file}")
    log_with_timestamp("")
    log_with_timestamp("Note: To load trades to Elasticsearch, run:")
    log_with_timestamp("  python3 load_all_data.py")
    log_with_timestamp("  or")
    log_with_timestamp("  python3 load_specific_indices.py --trades")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())