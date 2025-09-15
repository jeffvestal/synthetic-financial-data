#!/usr/bin/env python3
"""
Generate realistic trade activity based on actual holdings positions.

This script creates trade histories that explain how accounts acquired their current positions,
plus additional historical activity for positions they previously held but sold off.

Key Features:
- Every current holding has corresponding acquisition trades
- Generates historical "sold-off" positions with complete trade cycles  
- Maintains realistic trade patterns and timing
- Connects trade activity to actual portfolio positions

Usage:
    python3 scripts/generate_holdings_based_trades.py
"""

import json
import random
import uuid
import os
import sys
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Tuple, Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import FILE_PATHS, GENERATION_SETTINGS
from symbols_config import ALL_ASSET_INFO
from common_utils import (
    clear_file_if_exists,
    get_current_timestamp, 
    log_with_timestamp
)

# Trade configuration
TRADE_CONFIG = GENERATION_SETTINGS.get('trades', {})
TIME_WINDOW_START = datetime.fromisoformat(TRADE_CONFIG.get('time_window_start', '2025-06-01'))
TIME_WINDOW_END = datetime.fromisoformat(TRADE_CONFIG.get('time_window_end', '2025-08-28'))

# Trade generation probabilities
HOLDING_ACQUISITION_PATTERNS = {
    'single_buy': 0.70,      # 70% - Single trade for full quantity
    'multiple_buys': 0.20,   # 20% - Multiple partial buys
    'complex_history': 0.10  # 10% - Buy/sell activity with net = current quantity
}

SOLD_POSITION_PATTERNS = {
    'simple_flip': 0.40,     # Buy all, sell all
    'accumulate_sell': 0.30, # Multiple buys, single sell
    'trading_activity': 0.30 # Multiple buy/sell cycles ending in full sale
}

# Order types and statuses (from original script)
ORDER_TYPES = ['market', 'limit', 'stop']
ORDER_STATUSES = ['executed', 'cancelled', 'failed']
CANCELLATION_RATE = TRADE_CONFIG.get('cancellation_rate', 0.07)

def generate_trade_id(timestamp: datetime) -> str:
    """Generate unique trade ID."""
    date_str = timestamp.strftime('%Y%m%d')
    random_hex = uuid.uuid4().hex[:8] 
    return f"TRD-{date_str}-{random_hex}"

def calculate_realistic_price(
    base_price: float,
    quantity: int,
    trade_type: str,
    order_type: str,
    date: datetime
) -> float:
    """Calculate realistic execution price with spread, slippage, and historical variation."""
    
    # Add some historical price variation (prices change over time)
    days_ago = (TIME_WINDOW_END - date).days
    if days_ago > 0:
        # Simulate price evolution over time (small daily variations)
        daily_variation = random.uniform(-0.005, 0.005)  # ±0.5% daily variation
        price_variation = 1 + (daily_variation * days_ago * 0.1)  # Compounded but dampened
        historical_price = base_price * price_variation
    else:
        historical_price = base_price
    
    # Apply bid/ask spread
    spread = TRADE_CONFIG.get('bid_ask_spread', 0.005)
    if trade_type in ['buy', 'cover']:
        price = historical_price * (1 + spread/2)  # Pay ask
    else:
        price = historical_price * (1 - spread/2)  # Receive bid
    
    # Add slippage for large orders
    large_order_threshold = TRADE_CONFIG.get('large_order_threshold', 1000)
    if quantity > large_order_threshold and order_type == 'market':
        slippage_min, slippage_max = TRADE_CONFIG.get('slippage_range', (0.001, 0.003))
        slippage = random.uniform(slippage_min, slippage_max)
        if trade_type in ['buy', 'cover']:
            price *= (1 + slippage)
        else:
            price *= (1 - slippage)
    
    # Limit orders get slight price improvement
    if order_type == 'limit':
        improvement = random.uniform(0, spread/4)
        if trade_type in ['buy', 'cover']:
            price *= (1 - improvement)
        else:
            price *= (1 + improvement)
    
    return round(price, 2)

def generate_random_timestamp(start: datetime, end: datetime) -> datetime:
    """Generate random timestamp within range."""
    time_range = (end - start).total_seconds()
    random_seconds = random.uniform(0, time_range)
    return start + timedelta(seconds=random_seconds)

def create_trade_record(
    account_id: str,
    symbol: str, 
    trade_type: str,
    quantity: int,
    base_price: float,
    timestamp: datetime,
    order_type: str = 'market'
) -> Dict:
    """Create a complete trade record."""
    
    # Determine if trade is cancelled/failed
    if random.random() < CANCELLATION_RATE:
        if random.random() < 0.7:
            status = 'cancelled'
            reason = random.choice(['user_cancelled', 'exchange_cancelled'])
        else:
            status = 'failed'  
            reason = random.choice(['insufficient_funds', 'account_locked', 'technical_issue'])
        execution_price = 0
        trade_cost = 0
    else:
        status = 'executed'
        reason = 'fully_filled'
        execution_price = calculate_realistic_price(base_price, quantity, trade_type, order_type, timestamp)
        trade_cost = round(quantity * execution_price, 2)
    
    return {
        'trade_id': generate_trade_id(timestamp),
        'account_id': account_id,
        'symbol': symbol,
        'trade_type': trade_type,
        'order_type': order_type,
        'order_status': status,
        'quantity': float(quantity),
        'execution_price': execution_price,
        'trade_cost': trade_cost,
        'execution_timestamp': timestamp.isoformat(),
        'status_reason': reason,
        'last_updated': get_current_timestamp()
    }

def load_account_holdings() -> Dict[str, List[Dict]]:
    """Load all holdings organized by account_id."""
    holdings_by_account = defaultdict(list)
    
    holdings_file = FILE_PATHS.get('generated_holdings')
    if not os.path.exists(holdings_file):
        log_with_timestamp("ERROR: Holdings file not found. Run generate_holdings_accounts.py first.")
        return {}
    
    with open(holdings_file, 'r') as f:
        for line in f:
            try:
                holding = json.loads(line)
                account_id = holding.get('account_id')
                if account_id:
                    holdings_by_account[account_id].append(holding)
            except json.JSONDecodeError:
                continue
    
    return holdings_by_account

def load_account_data() -> Dict[str, Dict]:
    """Load account data organized by account_id."""
    accounts_by_id = {}
    
    accounts_file = FILE_PATHS.get('generated_accounts')
    if not os.path.exists(accounts_file):
        log_with_timestamp("ERROR: Accounts file not found. Run generate_holdings_accounts.py first.")
        return {}
    
    with open(accounts_file, 'r') as f:
        for line in f:
            try:
                account = json.loads(line)
                account_id = account.get('account_id')
                if account_id:
                    accounts_by_id[account_id] = account
            except json.JSONDecodeError:
                continue
    
    return accounts_by_id

def load_asset_prices() -> Dict[str, float]:
    """Load current asset prices."""
    asset_prices = {}
    
    asset_file = FILE_PATHS.get('generated_asset_details')
    if not os.path.exists(asset_file):
        log_with_timestamp("WARNING: Asset details file not found. Using default prices.")
        # Use symbol config as fallback
        for symbol in ALL_ASSET_INFO:
            asset_prices[symbol] = round(random.uniform(50, 500), 2)
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

def generate_holding_acquisition_trades(
    account_id: str,
    holding: Dict,
    asset_prices: Dict[str, float]
) -> List[Dict]:
    """
    Generate trade history that explains how the current holding was acquired.
    
    Returns:
        List of trade records that result in the current holding quantity
    """
    trades = []
    symbol = holding['symbol']
    current_quantity = int(holding['quantity'])
    base_price = asset_prices.get(symbol, 100.0)
    
    # Purchase date from holding (when final position was established)
    purchase_date = datetime.fromisoformat(holding['purchase_date'])
    
    # Generate trades in window before purchase date
    trade_start = max(TIME_WINDOW_START, purchase_date - timedelta(days=30))
    trade_end = min(purchase_date, TIME_WINDOW_END)
    
    pattern = random.choices(
        list(HOLDING_ACQUISITION_PATTERNS.keys()),
        weights=list(HOLDING_ACQUISITION_PATTERNS.values())
    )[0]
    
    if pattern == 'single_buy':
        # Single trade for full quantity
        timestamp = generate_random_timestamp(trade_start, trade_end)
        trade = create_trade_record(
            account_id, symbol, 'buy', current_quantity, base_price, timestamp
        )
        trades.append(trade)
        
    elif pattern == 'multiple_buys':
        # Split into 2-4 partial buys
        num_buys = random.randint(2, 4)
        remaining_quantity = current_quantity
        
        for i in range(num_buys):
            if i == num_buys - 1:
                # Last buy gets remaining quantity
                quantity = remaining_quantity
            else:
                # Random portion of remaining
                max_portion = remaining_quantity // (num_buys - i)
                quantity = random.randint(1, max(1, max_portion))
                remaining_quantity -= quantity
            
            timestamp = generate_random_timestamp(trade_start, trade_end)
            trade = create_trade_record(
                account_id, symbol, 'buy', quantity, base_price, timestamp
            )
            trades.append(trade)
    
    else:  # complex_history
        # Generate buy/sell activity with net result = current quantity
        # Start with more buys than needed, then sell some back
        total_bought = int(current_quantity * random.uniform(1.2, 2.0))  # 20-100% more than needed
        quantity_to_sell = total_bought - current_quantity
        
        # Generate buy trades
        buy_trades = random.randint(2, 4)
        remaining_to_buy = total_bought
        
        for i in range(buy_trades):
            if i == buy_trades - 1:
                quantity = remaining_to_buy
            else:
                max_portion = remaining_to_buy // (buy_trades - i)
                quantity = random.randint(1, max(1, max_portion))
                remaining_to_buy -= quantity
            
            timestamp = generate_random_timestamp(trade_start, trade_end)
            trade = create_trade_record(
                account_id, symbol, 'buy', quantity, base_price, timestamp
            )
            trades.append(trade)
        
        # Generate sell trades to get down to current quantity
        if quantity_to_sell > 0:
            sell_trades = random.randint(1, 3)
            remaining_to_sell = quantity_to_sell
            
            for i in range(sell_trades):
                if i == sell_trades - 1:
                    quantity = remaining_to_sell
                else:
                    max_portion = remaining_to_sell // (sell_trades - i) 
                    quantity = random.randint(1, max(1, max_portion))
                    remaining_to_sell -= quantity
                
                # Sell trades happen after some buys
                timestamp = generate_random_timestamp(trade_start, trade_end)
                trade = create_trade_record(
                    account_id, symbol, 'sell', quantity, base_price, timestamp
                )
                trades.append(trade)
    
    return trades

def generate_speculative_trades(
    account_id: str,
    risk_profile: str,
    available_symbols: List[str],
    asset_prices: Dict[str, float]
) -> List[Dict]:
    """
    Generate additional speculative/day trading activity.
    
    These trades don't affect current holdings - they're short-term speculation,
    failed trades, day trading, etc.
    
    Returns:
        List of speculative trade records
    """
    trades = []
    
    # Number of speculative trades based on risk profile
    speculative_volumes = {
        'Very Low': (2, 8),
        'Low': (3, 12),
        'Medium': (5, 18),
        'High': (8, 25),
        'Very High': (10, 30),
        'Conservative': (1, 5),
        'Moderate': (4, 15),
        'Growth': (6, 20)
    }
    
    min_trades, max_trades = speculative_volumes.get(risk_profile, (5, 15))
    num_speculative = random.randint(min_trades, max_trades)
    
    for _ in range(num_speculative):
        symbol = random.choice(available_symbols)
        base_price = asset_prices[symbol]
        
        # Types of speculative activity
        activity_type = random.choices(
            ['day_trade', 'failed_speculation', 'short_term_flip', 'swing_trade'],
            weights=[0.3, 0.2, 0.3, 0.2]
        )[0]
        
        if activity_type == 'day_trade':
            # Buy and sell same day, small profit/loss
            trade_date = generate_random_timestamp(TIME_WINDOW_START, TIME_WINDOW_END)
            quantity = random.randint(100, 1000)  # Round lots for day trading
            
            # Buy in morning
            buy_time = trade_date.replace(
                hour=random.randint(9, 11),
                minute=random.randint(0, 59)
            )
            buy_trade = create_trade_record(
                account_id, symbol, 'buy', quantity, base_price, buy_time
            )
            
            # Sell later same day
            sell_time = buy_time + timedelta(
                hours=random.randint(1, 6),
                minutes=random.randint(0, 59)
            )
            # Day trades often at small loss/gain
            day_trade_price = base_price * random.uniform(0.98, 1.03)
            sell_trade = create_trade_record(
                account_id, symbol, 'sell', quantity, day_trade_price, sell_time
            )
            
            trades.extend([buy_trade, sell_trade])
            
        elif activity_type == 'failed_speculation':
            # Single buy that was intended to be held but market moved against them
            # No corresponding sell (they just "gave up" on the position and it's now minimal)
            trade_date = generate_random_timestamp(TIME_WINDOW_START, TIME_WINDOW_END)
            quantity = random.randint(10, 200)  # Small speculative position
            
            trade = create_trade_record(
                account_id, symbol, 'buy', quantity, base_price, trade_date
            )
            trades.append(trade)
            
        elif activity_type == 'short_term_flip':
            # Buy and sell within 1-7 days for quick profit attempt
            buy_date = generate_random_timestamp(TIME_WINDOW_START, TIME_WINDOW_END - timedelta(days=7))
            sell_date = buy_date + timedelta(days=random.randint(1, 7))
            
            quantity = random.randint(25, 500)
            
            buy_trade = create_trade_record(
                account_id, symbol, 'buy', quantity, base_price, buy_date
            )
            
            # Short-term flip price - could be profit or loss
            flip_price = base_price * random.uniform(0.95, 1.08)
            sell_trade = create_trade_record(
                account_id, symbol, 'sell', quantity, flip_price, sell_date
            )
            
            trades.extend([buy_trade, sell_trade])
            
        else:  # swing_trade
            # Hold for 1-4 weeks, then sell
            buy_date = generate_random_timestamp(TIME_WINDOW_START, TIME_WINDOW_END - timedelta(days=28))
            sell_date = buy_date + timedelta(days=random.randint(7, 28))
            
            quantity = random.randint(50, 800)
            
            buy_trade = create_trade_record(
                account_id, symbol, 'buy', quantity, base_price, buy_date
            )
            
            # Swing trade price - wider range of outcomes
            swing_price = base_price * random.uniform(0.90, 1.15)
            sell_trade = create_trade_record(
                account_id, symbol, 'sell', quantity, swing_price, sell_date
            )
            
            trades.extend([buy_trade, sell_trade])
    
    return trades

def generate_sold_position_history(
    account_id: str,
    symbol: str,
    base_price: float
) -> List[Dict]:
    """
    Generate complete trade history for a position that was fully sold off.
    
    Returns:
        List of trade records with net position = 0 (bought and then sold everything)
    """
    trades = []
    
    # Random position size that was fully sold
    position_size = random.randint(50, 1500)
    
    pattern = random.choices(
        list(SOLD_POSITION_PATTERNS.keys()),
        weights=list(SOLD_POSITION_PATTERNS.values())
    )[0]
    
    # Generate timeline for this position
    position_start = generate_random_timestamp(TIME_WINDOW_START, TIME_WINDOW_END - timedelta(days=7))
    position_end = generate_random_timestamp(position_start + timedelta(days=1), TIME_WINDOW_END)
    
    if pattern == 'simple_flip':
        # Buy all, sell all
        buy_timestamp = generate_random_timestamp(position_start, position_start + timedelta(days=1))
        sell_timestamp = generate_random_timestamp(buy_timestamp + timedelta(hours=1), position_end)
        
        buy_trade = create_trade_record(account_id, symbol, 'buy', position_size, base_price, buy_timestamp)
        sell_trade = create_trade_record(account_id, symbol, 'sell', position_size, base_price, sell_timestamp)
        
        trades.extend([buy_trade, sell_trade])
        
    elif pattern == 'accumulate_sell':
        # Multiple buys, single sell
        num_buys = random.randint(2, 4)
        remaining_to_buy = position_size
        
        # Generate buy trades
        for i in range(num_buys):
            if i == num_buys - 1:
                quantity = remaining_to_buy
            else:
                max_portion = remaining_to_buy // (num_buys - i)
                quantity = random.randint(1, max(1, max_portion))
                remaining_to_buy -= quantity
            
            timestamp = generate_random_timestamp(position_start, position_start + timedelta(days=5))
            trade = create_trade_record(account_id, symbol, 'buy', quantity, base_price, timestamp)
            trades.append(trade)
        
        # Single sell of everything
        sell_timestamp = generate_random_timestamp(position_start + timedelta(days=3), position_end)
        sell_trade = create_trade_record(account_id, symbol, 'sell', position_size, base_price, sell_timestamp)
        trades.append(sell_trade)
        
    else:  # trading_activity
        # Multiple buy/sell cycles, ending with net = 0
        total_bought = 0
        total_sold = 0
        
        # Generate 3-6 trades with final net = 0
        num_trades = random.randint(3, 6)
        
        for i in range(num_trades):
            if i == num_trades - 1:
                # Final trade: balance out to net = 0
                if total_bought > total_sold:
                    trade_type = 'sell'
                    quantity = total_bought - total_sold
                else:
                    trade_type = 'buy' 
                    quantity = total_sold - total_bought
            else:
                trade_type = random.choice(['buy', 'sell'])
                quantity = random.randint(25, 500)
            
            timestamp = generate_random_timestamp(position_start, position_end)
            trade = create_trade_record(account_id, symbol, trade_type, quantity, base_price, timestamp)
            trades.append(trade)
            
            if trade_type == 'buy':
                total_bought += quantity
            else:
                total_sold += quantity
    
    return trades

def main():
    """Main execution function."""
    log_with_timestamp("=== Starting Holdings-Based Trade Generation ===")
    
    # Load data
    log_with_timestamp("Loading account holdings...")
    holdings_by_account = load_account_holdings()
    
    if not holdings_by_account:
        log_with_timestamp("ERROR: No holdings found. Cannot generate trades.")
        return 1
    
    log_with_timestamp(f"Loaded holdings for {len(holdings_by_account)} accounts")
    
    # Load account data for risk profiles
    log_with_timestamp("Loading account data...")
    accounts_by_id = load_account_data()
    log_with_timestamp(f"Loaded data for {len(accounts_by_id)} accounts")
    
    # Load asset prices
    asset_prices = load_asset_prices()
    log_with_timestamp(f"Loaded prices for {len(asset_prices)} assets")
    
    # Clear output file
    output_file = FILE_PATHS.get('generated_trades', 'generated_data/financial_trades.jsonl')
    clear_file_if_exists(output_file)
    
    total_trades = 0
    all_symbols = list(asset_prices.keys())
    
    with open(output_file, 'w') as f:
        for account_id, holdings in holdings_by_account.items():
            account_trades = []
            
            # Phase 1: Generate trades for current holdings
            for holding in holdings:
                holding_trades = generate_holding_acquisition_trades(
                    account_id, holding, asset_prices
                )
                account_trades.extend(holding_trades)
            
            # Phase 2: Generate sold-off position histories (2-5 per account)
            num_sold_positions = random.randint(2, 5)
            current_symbols = {h['symbol'] for h in holdings}
            
            for _ in range(num_sold_positions):
                # Pick symbol not currently held
                available_symbols = [s for s in all_symbols if s not in current_symbols]
                if available_symbols:
                    symbol = random.choice(available_symbols)
                    base_price = asset_prices[symbol]
                    
                    sold_trades = generate_sold_position_history(account_id, symbol, base_price)
                    account_trades.extend(sold_trades)
            
            # Phase 3: Generate additional speculative trading activity
            account_data = accounts_by_id.get(account_id, {})
            risk_profile = account_data.get('risk_profile', 'Medium')
            
            # Use all available symbols for speculation (including current holdings)
            speculative_trades = generate_speculative_trades(
                account_id, risk_profile, all_symbols, asset_prices
            )
            account_trades.extend(speculative_trades)
            
            # Sort trades by timestamp
            account_trades.sort(key=lambda t: t['execution_timestamp'])
            
            # Write trades to file
            for trade in account_trades:
                f.write(json.dumps(trade) + '\n')
                total_trades += 1
            
            if len(holdings_by_account) <= 10 or len(account_trades) % 100 == 0:
                log_with_timestamp(f"Generated {len(account_trades)} trades for account {account_id}")
    
    log_with_timestamp(f"=== Trade Generation Complete ===")
    log_with_timestamp(f"Total trades generated: {total_trades:,}")
    log_with_timestamp(f"Output file: {output_file}")

if __name__ == "__main__":
    main()