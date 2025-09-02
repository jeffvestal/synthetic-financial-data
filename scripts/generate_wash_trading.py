#!/usr/bin/env python3
"""
Wash Trading Scenario Generator

This script generates realistic wash trading patterns by creating circular trades
between accounts to artificially inflate volume without changing net positions.

Key patterns generated:
- Circular trading between 2-4 accounts
- Minimal price spreads (±0.1-0.3%) to avoid losses
- High frequency trading with artificial volume inflation
- Mixed with cancelled orders for realism
- Same symbols traded back and forth repeatedly
"""

import os
import sys
import json
import random
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
from collections import defaultdict

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import FILE_PATHS, GENERATION_SETTINGS, ES_CONFIG, FIELD_NAMES
from symbols_config import ALL_ASSET_INFO, get_asset_info
from common_utils import (
    create_elasticsearch_client,
    ingest_data_to_es,
    clear_file_if_exists,
    get_current_timestamp,
    log_with_timestamp
)

# Configuration
WASH_TRADING_CONFIG = {
    'accounts_per_ring': (2, 4),  # Number of accounts in wash trading ring
    'trades_per_session': (20, 60),  # Trades in a wash trading session
    'session_duration_hours': (2, 8),  # Duration of wash trading activity
    'price_spread': (0.001, 0.003),  # Price spread between trades (0.1-0.3%)
    'cancellation_rate': 0.20,  # 20% of orders cancelled
    'volume_per_trade': (100, 2000),  # Share quantities per trade
    'sessions_per_scenario': (1, 3),  # Number of sessions per scenario
    'time_between_sessions': (1, 48),  # Hours between sessions
    'symbols_per_scenario': (1, 2),  # Symbols manipulated per scenario
    'account_relationship_types': [
        'same_state',  # Accounts from same state (geographic clustering)
        'similar_names',  # Similar account holder names (family/shell companies)
        'sequential_ids',  # Sequential account IDs (batch created accounts)
        'mixed'  # Mixed relationships for cover
    ]
}

def load_accounts() -> List[Dict[str, Any]]:
    """Load account data for wash trading scenarios."""
    accounts = []
    account_file = FILE_PATHS.get('generated_accounts')
    
    if not os.path.exists(account_file):
        raise FileNotFoundError(f"Account file not found: {account_file}")
    
    with open(account_file, 'r') as f:
        for line in f:
            try:
                account = json.loads(line.strip())
                accounts.append(account)
            except json.JSONDecodeError:
                continue
    
    log_with_timestamp(f"Loaded {len(accounts)} accounts for wash trading scenarios")
    return accounts

def load_asset_prices() -> Dict[str, float]:
    """Load current asset prices."""
    asset_prices = {}
    asset_file = FILE_PATHS.get('generated_asset_details')
    
    if not os.path.exists(asset_file):
        log_with_timestamp("WARNING: Asset details file not found. Using default prices.")
        for symbol in list(ALL_ASSET_INFO.keys())[:50]:
            asset_prices[symbol] = round(random.uniform(50, 500), 2)
        return asset_prices
    
    with open(asset_file, 'r') as f:
        for line in f:
            try:
                asset = json.loads(line.strip())
                symbol = asset.get('symbol')
                current_price = asset.get('current_price', {}).get('price')
                if symbol and current_price:
                    asset_prices[symbol] = float(current_price)
            except json.JSONDecodeError:
                continue
    
    return asset_prices

def find_related_accounts(
    accounts: List[Dict], 
    relationship_type: str, 
    num_accounts: int
) -> List[Dict]:
    """
    Find accounts that appear related for wash trading rings.
    Different relationship types create different suspicious patterns.
    """
    if relationship_type == 'same_state':
        # Group by state and find states with enough accounts
        state_groups = defaultdict(list)
        for account in accounts:
            state = account.get('state', 'Unknown')
            state_groups[state].append(account)
        
        # Find states with enough accounts
        viable_states = [state for state, accs in state_groups.items() 
                        if len(accs) >= num_accounts]
        
        if viable_states:
            chosen_state = random.choice(viable_states)
            return random.sample(state_groups[chosen_state], num_accounts)
    
    elif relationship_type == 'similar_names':
        # Group by similar last names (first 3 characters)
        name_groups = defaultdict(list)
        for account in accounts:
            last_name = account.get('last_name', '')
            if len(last_name) >= 3:
                name_prefix = last_name[:3].upper()
                name_groups[name_prefix].append(account)
        
        # Find name groups with enough accounts
        viable_names = [prefix for prefix, accs in name_groups.items() 
                       if len(accs) >= num_accounts]
        
        if viable_names:
            chosen_prefix = random.choice(viable_names)
            return random.sample(name_groups[chosen_prefix], num_accounts)
    
    elif relationship_type == 'sequential_ids':
        # Find accounts with sequential or similar IDs
        accounts_with_numeric = []
        for account in accounts:
            account_id = account.get('account_id', '')
            # Extract numeric portion
            numeric_part = ''.join(filter(str.isdigit, account_id))
            if numeric_part:
                account['_numeric_id'] = int(numeric_part)
                accounts_with_numeric.append(account)
        
        # Sort by numeric ID and find sequential groups
        accounts_with_numeric.sort(key=lambda x: x['_numeric_id'])
        
        for i in range(len(accounts_with_numeric) - num_accounts + 1):
            group = accounts_with_numeric[i:i+num_accounts]
            # Check if IDs are reasonably sequential (within 100 of each other)
            if group[-1]['_numeric_id'] - group[0]['_numeric_id'] <= 100:
                return group
    
    # Fallback: return random accounts
    return random.sample(accounts, min(num_accounts, len(accounts)))

def create_wash_trading_ring(
    accounts: List[Dict],
    relationship_type: str,
    num_accounts: int
) -> List[Dict]:
    """Create a wash trading ring with specified relationship pattern."""
    
    # Find related accounts
    ring_accounts = find_related_accounts(accounts, relationship_type, num_accounts)
    
    # If we couldn't find enough related accounts, fill with random ones
    while len(ring_accounts) < num_accounts:
        remaining = [acc for acc in accounts if acc not in ring_accounts]
        if not remaining:
            break
        ring_accounts.append(random.choice(remaining))
    
    return ring_accounts[:num_accounts]

def generate_wash_trading_session(
    symbol: str,
    ring_accounts: List[Dict],
    base_price: float,
    session_start: datetime,
    session_duration_hours: int
) -> List[Dict]:
    """Generate a single wash trading session between ring accounts."""
    
    trades = []
    num_trades = random.randint(*WASH_TRADING_CONFIG['trades_per_session'])
    session_end = session_start + timedelta(hours=session_duration_hours)
    
    log_with_timestamp(f"  Generating wash session: {len(ring_accounts)} accounts, {num_trades} trades")
    log_with_timestamp(f"  Duration: {session_duration_hours} hours, Base price: ${base_price:.2f}")
    
    # Track current "holders" to create realistic circular trading
    # Start with random distribution
    current_positions = {}
    for account in ring_accounts:
        current_positions[account['account_id']] = random.randint(0, 1000)
    
    for trade_num in range(num_trades):
        # Random time within session
        trade_time = session_start + timedelta(
            seconds=random.randint(0, int(session_duration_hours * 3600))
        )
        
        # Select seller (must have position) and buyer
        sellers = [acc_id for acc_id, pos in current_positions.items() if pos > 0]
        if not sellers:
            # Reset positions if everyone is empty
            for acc_id in current_positions:
                current_positions[acc_id] = random.randint(100, 500)
            sellers = list(current_positions.keys())
        
        seller_id = random.choice(sellers)
        
        # Select buyer (different from seller)
        buyers = [acc['account_id'] for acc in ring_accounts if acc['account_id'] != seller_id]
        buyer_id = random.choice(buyers)
        
        # Calculate trade details
        max_quantity = min(current_positions[seller_id], 
                          random.randint(*WASH_TRADING_CONFIG['volume_per_trade']))
        quantity = max(1, max_quantity)
        
        # Price with minimal spread
        price_spread = random.uniform(*WASH_TRADING_CONFIG['price_spread'])
        price_direction = random.choice([-1, 1])
        trade_price = base_price * (1 + (price_direction * price_spread))
        
        # Determine if order is cancelled
        is_cancelled = random.random() < WASH_TRADING_CONFIG['cancellation_rate']
        order_status = 'cancelled' if is_cancelled else 'executed'
        
        # Create matching sell and buy orders
        trade_id_base = f"WASH-{uuid.uuid4().hex[:8]}-{int(trade_time.timestamp())}"
        
        # Sell trade
        sell_trade = {
            'trade_id': f"{trade_id_base}-SELL",
            'account_id': seller_id,
            'symbol': symbol,
            'trade_type': 'sell',
            'order_type': random.choice(['market', 'limit']),
            'order_status': order_status,
            'quantity': float(quantity),
            'execution_price': round(trade_price, 2) if order_status == 'executed' else 0,
            'trade_cost': round(quantity * trade_price, 2) if order_status == 'executed' else 0,
            'execution_timestamp': trade_time.isoformat(),
            'last_updated': get_current_timestamp(),
            'scenario_type': 'wash_trading',
            'scenario_phase': 'circular_trading',
            'wash_ring_id': f"RING-{hash(tuple(sorted([acc['account_id'] for acc in ring_accounts]))) % 10000:04d}",
            'counterpart_account': buyer_id
        }
        
        # Buy trade (matching)
        buy_trade = {
            'trade_id': f"{trade_id_base}-BUY",
            'account_id': buyer_id,
            'symbol': symbol,
            'trade_type': 'buy',
            'order_type': random.choice(['market', 'limit']),
            'order_status': order_status,
            'quantity': float(quantity),
            'execution_price': round(trade_price, 2) if order_status == 'executed' else 0,
            'trade_cost': round(quantity * trade_price, 2) if order_status == 'executed' else 0,
            'execution_timestamp': trade_time.isoformat(),
            'last_updated': get_current_timestamp(),
            'scenario_type': 'wash_trading',
            'scenario_phase': 'circular_trading',
            'wash_ring_id': f"RING-{hash(tuple(sorted([acc['account_id'] for acc in ring_accounts]))) % 10000:04d}",
            'counterpart_account': seller_id
        }
        
        trades.extend([sell_trade, buy_trade])
        
        # Update positions if trade executed
        if order_status == 'executed':
            current_positions[seller_id] -= quantity
            current_positions[buyer_id] = current_positions.get(buyer_id, 0) + quantity
    
    # Sort trades by timestamp
    trades.sort(key=lambda x: x['execution_timestamp'])
    
    return trades

def generate_wash_trading_scenario(
    accounts: List[Dict],
    asset_prices: Dict[str, float],
    scenario_start: datetime
) -> List[Dict]:
    """Generate a complete wash trading scenario."""
    
    # Configuration for this scenario
    num_accounts = random.randint(*WASH_TRADING_CONFIG['accounts_per_ring'])
    num_sessions = random.randint(*WASH_TRADING_CONFIG['sessions_per_scenario'])
    num_symbols = random.randint(*WASH_TRADING_CONFIG['symbols_per_scenario'])
    relationship_type = random.choice(WASH_TRADING_CONFIG['account_relationship_types'])
    
    # Create wash trading ring
    ring_accounts = create_wash_trading_ring(accounts, relationship_type, num_accounts)
    
    # Select symbols for manipulation
    available_symbols = list(asset_prices.keys())
    scenario_symbols = random.sample(available_symbols, min(num_symbols, len(available_symbols)))
    
    log_with_timestamp(f"Generating wash trading scenario:")
    log_with_timestamp(f"  Ring accounts: {num_accounts} ({relationship_type} relationship)")
    log_with_timestamp(f"  Account IDs: {[acc['account_id'] for acc in ring_accounts]}")
    log_with_timestamp(f"  Symbols: {scenario_symbols}")
    log_with_timestamp(f"  Sessions: {num_sessions}")
    
    all_trades = []
    current_time = scenario_start
    
    for session_num in range(num_sessions):
        log_with_timestamp(f"  Session {session_num + 1}/{num_sessions}")
        
        for symbol in scenario_symbols:
            base_price = asset_prices.get(symbol, random.uniform(50, 500))
            session_duration = random.randint(*WASH_TRADING_CONFIG['session_duration_hours'])
            
            session_trades = generate_wash_trading_session(
                symbol=symbol,
                ring_accounts=ring_accounts,
                base_price=base_price,
                session_start=current_time,
                session_duration_hours=session_duration
            )
            
            all_trades.extend(session_trades)
        
        # Time gap before next session
        if session_num < num_sessions - 1:
            gap_hours = random.randint(*WASH_TRADING_CONFIG['time_between_sessions'])
            current_time += timedelta(hours=gap_hours)
    
    log_with_timestamp(f"Generated {len(all_trades)} wash trades")
    return all_trades

def generate_wash_trading_scenarios(
    num_scenarios: int = 2,
    output_file: str = None
) -> List[Dict]:
    """Generate multiple wash trading scenarios."""
    
    if output_file is None:
        output_file = FILE_PATHS.get('generated_controlled_trades')
    
    log_with_timestamp("Starting wash trading scenario generation")
    
    # Load required data
    accounts = load_accounts()
    asset_prices = load_asset_prices()
    
    all_trades = []
    
    for i in range(num_scenarios):
        log_with_timestamp(f"Generating wash trading scenario {i + 1}/{num_scenarios}")
        
        # Set timeline - scenarios occur over past month
        scenario_start = datetime.now() - timedelta(days=random.randint(1, 30))
        
        scenario_trades = generate_wash_trading_scenario(
            accounts=accounts,
            asset_prices=asset_prices,
            scenario_start=scenario_start
        )
        
        all_trades.extend(scenario_trades)
    
    # Append to existing controlled trades file (don't overwrite insider trading data)
    log_with_timestamp(f"Appending {len(all_trades)} wash trading trades to {output_file}")
    
    with open(output_file, 'a') as f:  # Append mode
        for trade in all_trades:
            f.write(json.dumps(trade) + '\n')
    
    log_with_timestamp(f"Wash trading scenario generation complete")
    log_with_timestamp(f"Generated {len(all_trades)} trades across {num_scenarios} scenarios")
    
    return all_trades

def ingest_to_elasticsearch(trades: List[Dict]) -> bool:
    """Ingest wash trading data to Elasticsearch."""
    try:
        es_client = create_elasticsearch_client()
        index_name = ES_CONFIG['indices']['trades']
        
        log_with_timestamp(f"Ingesting {len(trades)} wash trades to Elasticsearch index: {index_name}")
        
        success = ingest_data_to_es(
            es_client=es_client,
            data=trades,
            index_name=index_name,
            id_field='trade_id'
        )
        
        if success:
            log_with_timestamp("Successfully ingested wash trading data to Elasticsearch")
        else:
            log_with_timestamp("Failed to ingest wash trading data to Elasticsearch")
        
        return success
        
    except Exception as e:
        log_with_timestamp(f"Error ingesting to Elasticsearch: {e}")
        return False

def main():
    """Main execution function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate wash trading scenarios')
    parser.add_argument('--num-scenarios', type=int, default=2,
                       help='Number of wash trading scenarios to generate')
    parser.add_argument('--output-file', type=str,
                       help='Output file path (default: generated_controlled_trades.jsonl)')
    parser.add_argument('--elasticsearch', action='store_true',
                       help='Ingest generated data to Elasticsearch')
    
    args = parser.parse_args()
    
    try:
        # Generate wash trading scenarios
        trades = generate_wash_trading_scenarios(
            num_scenarios=args.num_scenarios,
            output_file=args.output_file
        )
        
        # Optionally ingest to Elasticsearch
        if args.elasticsearch:
            ingest_to_elasticsearch(trades)
        
        # Summary
        print(f"\n{'='*60}")
        print("WASH TRADING SCENARIO GENERATION COMPLETE")
        print(f"{'='*60}")
        print(f"📊 Scenarios Generated: {args.num_scenarios}")
        print(f"📈 Total Trades: {len(trades)}")
        print(f"💾 Output File: {args.output_file or FILE_PATHS.get('generated_controlled_trades')}")
        if args.elasticsearch:
            print("🔍 Data ingested to Elasticsearch for analysis")
        print(f"{'='*60}")
        
        return True
        
    except Exception as e:
        log_with_timestamp(f"Error in wash trading generation: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)