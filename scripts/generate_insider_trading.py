#!/usr/bin/env python3
"""
Insider Trading Scenario Generator

This script generates realistic insider trading patterns by creating coordinated
trades before news announcements. The patterns are designed to be discoverable
by Elasticsearch analysts investigating suspicious trading activity.

Key patterns generated:
- Pre-announcement volume spikes (12-48 hours before news)
- Coordinated buying/selling across multiple accounts
- Abnormal trading patterns relative to account risk profiles
- Timeline correlation with subsequent news events
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
INSIDER_TRADING_CONFIG = {
    'accounts_per_scenario': (5, 15),  # Range of accounts involved
    'pre_announcement_hours': (12, 48),  # Hours before news announcement
    'volume_multiplier': (3.0, 8.0),  # Volume increase vs normal trading
    'price_impact': (0.05, 0.15),  # Price movement from insider activity (5-15%)
    'trading_phases': {
        'accumulation': 0.6,  # 60% of trades in early accumulation
        'acceleration': 0.3,   # 30% in acceleration phase  
        'final_push': 0.1     # 10% right before announcement
    },
    'profit_taking_delay': (1, 6),  # Hours after news to start selling
    'account_selection_bias': {
        'High': 0.4,      # 40% chance to select high-risk accounts
        'Very High': 0.3, # 30% chance for very high risk
        'Growth': 0.2,    # 20% chance for growth accounts
        'Medium': 0.1     # 10% chance for others (for cover)
    }
}

def load_accounts() -> List[Dict[str, Any]]:
    """Load account data for insider trading scenario."""
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
    
    log_with_timestamp(f"Loaded {len(accounts)} accounts for insider trading scenarios")
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

def select_insider_accounts(accounts: List[Dict], num_accounts: int) -> List[Dict]:
    """
    Select accounts for insider trading based on risk profile bias.
    Insider trading typically involves accounts that can handle high-risk activity.
    """
    # Group accounts by risk profile
    risk_groups = defaultdict(list)
    for account in accounts:
        risk_profile = account.get('risk_profile', 'Medium')
        risk_groups[risk_profile].append(account)
    
    selected_accounts = []
    remaining = num_accounts
    
    # Select based on bias weights
    for risk_profile, weight in INSIDER_TRADING_CONFIG['account_selection_bias'].items():
        if remaining <= 0:
            break
        
        available_accounts = risk_groups.get(risk_profile, [])
        if not available_accounts:
            continue
        
        # Calculate how many accounts to select from this risk group
        target_count = max(1, int(remaining * weight))
        actual_count = min(target_count, len(available_accounts), remaining)
        
        # Randomly select accounts from this risk group
        selected = random.sample(available_accounts, actual_count)
        selected_accounts.extend(selected)
        remaining -= actual_count
    
    # Fill remaining slots with any available accounts
    while remaining > 0 and len(selected_accounts) < len(accounts):
        remaining_accounts = [acc for acc in accounts if acc not in selected_accounts]
        if not remaining_accounts:
            break
        selected_accounts.append(random.choice(remaining_accounts))
        remaining -= 1
    
    return selected_accounts[:num_accounts]

def calculate_insider_price_progression(
    base_price: float, 
    total_hours: int, 
    price_impact: float
) -> List[Tuple[int, float]]:
    """
    Calculate realistic price progression during insider trading period.
    Returns list of (hour_offset, price) tuples.
    """
    price_points = []
    current_price = base_price
    
    # Generate price progression with some randomness but overall upward trend
    for hour in range(total_hours + 1):
        # Calculate progress through the insider trading period (0.0 to 1.0)
        progress = hour / total_hours
        
        # Base price increase following the timeline
        base_increase = price_impact * progress
        
        # Add some randomness for realism (±2% random walk)
        random_factor = random.uniform(-0.02, 0.02)
        
        # Ensure price doesn't go below starting price early on
        if progress < 0.3:  # First 30% of timeline
            random_factor = max(random_factor, -0.01)
        
        price_change = base_increase + random_factor
        current_price = base_price * (1 + price_change)
        
        price_points.append((hour, round(current_price, 2)))
    
    return price_points

def generate_insider_trading_scenario(
    symbol: str,
    accounts: List[Dict],
    asset_prices: Dict[str, float],
    scenario_start: datetime,
    news_announcement_time: datetime
) -> List[Dict]:
    """Generate insider trading scenario for a specific symbol."""
    
    base_price = asset_prices.get(symbol, random.uniform(50, 500))
    hours_before_news = int((news_announcement_time - scenario_start).total_seconds() / 3600)
    
    # Configuration for this scenario
    num_accounts = random.randint(*INSIDER_TRADING_CONFIG['accounts_per_scenario'])
    volume_multiplier = random.uniform(*INSIDER_TRADING_CONFIG['volume_multiplier'])
    price_impact = random.uniform(*INSIDER_TRADING_CONFIG['price_impact'])
    
    # Select accounts for this scenario
    insider_accounts = select_insider_accounts(accounts, num_accounts)
    
    # Calculate price progression
    price_progression = calculate_insider_price_progression(base_price, hours_before_news, price_impact)
    
    log_with_timestamp(f"Generating insider trading scenario:")
    log_with_timestamp(f"  Symbol: {symbol}")
    log_with_timestamp(f"  Accounts: {num_accounts}")
    log_with_timestamp(f"  Timeline: {hours_before_news} hours")
    log_with_timestamp(f"  Base price: ${base_price:.2f}")
    log_with_timestamp(f"  Expected price impact: {price_impact:.1%}")
    
    trades = []
    trade_phases = INSIDER_TRADING_CONFIG['trading_phases']
    
    for account in insider_accounts:
        account_id = account['account_id']
        portfolio_value = account.get('total_portfolio_value', 1000000)
        risk_profile = account.get('risk_profile', 'Medium')
        
        # Determine total trading activity for this account
        # Higher risk profiles trade more aggressively
        risk_multipliers = {'Conservative': 0.5, 'Low': 0.7, 'Medium': 1.0, 
                          'Growth': 1.5, 'High': 2.0, 'Very High': 3.0}
        account_volume_mult = risk_multipliers.get(risk_profile, 1.0) * volume_multiplier
        
        # Calculate number of trades for this account (spread across timeline)
        base_trades = random.randint(3, 12)
        total_trades = int(base_trades * account_volume_mult)
        
        # Distribute trades across phases
        accumulation_trades = int(total_trades * trade_phases['accumulation'])
        acceleration_trades = int(total_trades * trade_phases['acceleration']) 
        final_trades = total_trades - accumulation_trades - acceleration_trades
        
        # Generate trades for each phase
        phase_trades = [
            ('accumulation', accumulation_trades, 0, int(hours_before_news * 0.6)),
            ('acceleration', acceleration_trades, int(hours_before_news * 0.6), int(hours_before_news * 0.9)),
            ('final_push', final_trades, int(hours_before_news * 0.9), hours_before_news)
        ]
        
        for phase_name, num_trades, start_hour, end_hour in phase_trades:
            for _ in range(num_trades):
                # Random time within phase
                if start_hour == end_hour:
                    trade_hour = start_hour
                else:
                    trade_hour = random.randint(start_hour, min(end_hour, hours_before_news - 1))
                
                trade_time = scenario_start + timedelta(hours=trade_hour, 
                                                      minutes=random.randint(0, 59),
                                                      seconds=random.randint(0, 59))
                
                # Get price at this time (interpolate if needed)
                trade_price = base_price
                for hour, price in price_progression:
                    if hour >= trade_hour:
                        trade_price = price
                        break
                
                # Add some individual trade price variation
                price_variation = random.uniform(-0.005, 0.005)  # ±0.5%
                execution_price = trade_price * (1 + price_variation)
                
                # Calculate quantity based on account size and phase intensity
                phase_intensity = {'accumulation': 0.7, 'acceleration': 1.2, 'final_push': 1.8}
                base_quantity = max(100, int(portfolio_value * 0.0001))  # 0.01% of portfolio
                quantity = int(base_quantity * phase_intensity[phase_name] * random.uniform(0.5, 1.5))
                
                # Almost all insider trades are buys (accumulation)
                trade_type = 'buy' if random.random() < 0.95 else 'sell'  # 95% buys
                
                # Order type bias - insiders often use market orders for speed
                order_type = random.choices(['market', 'limit'], weights=[0.7, 0.3])[0]
                
                trade = {
                    'trade_id': f"INSIDER-{uuid.uuid4().hex[:8]}-{int(trade_time.timestamp())}",
                    'account_id': account_id,
                    'symbol': symbol,
                    'trade_type': trade_type,
                    'order_type': order_type,
                    'order_status': 'executed',
                    'quantity': float(quantity),
                    'execution_price': round(execution_price, 2),
                    'trade_cost': round(quantity * execution_price, 2),
                    'execution_timestamp': trade_time.isoformat(),
                    'last_updated': get_current_timestamp(),
                    'scenario_type': 'insider_trading',
                    'scenario_phase': phase_name,
                    'scenario_symbol': symbol,
                    'news_announcement_time': news_announcement_time.isoformat()
                }
                
                trades.append(trade)
        
        # Generate profit-taking trades AFTER news announcement
        profit_delay_hours = random.randint(*INSIDER_TRADING_CONFIG['profit_taking_delay'])
        profit_start = news_announcement_time + timedelta(hours=profit_delay_hours)
        
        # Sell trades to realize profits (fewer trades, larger quantities)
        num_sell_trades = random.randint(2, 6)
        for i in range(num_sell_trades):
            sell_time = profit_start + timedelta(
                hours=random.randint(0, 12),
                minutes=random.randint(0, 59)
            )
            
            # Price should be higher after positive news
            post_news_price = base_price * (1 + price_impact + random.uniform(0.02, 0.08))
            
            # Larger sell quantities to liquidate positions
            sell_quantity = int(quantity * random.uniform(2, 5))
            
            sell_trade = {
                'trade_id': f"INSIDER-SELL-{uuid.uuid4().hex[:8]}-{int(sell_time.timestamp())}",
                'account_id': account_id,
                'symbol': symbol,
                'trade_type': 'sell',
                'order_type': random.choices(['market', 'limit'], weights=[0.8, 0.2])[0],
                'order_status': 'executed',
                'quantity': float(sell_quantity),
                'execution_price': round(post_news_price, 2),
                'trade_cost': round(sell_quantity * post_news_price, 2),
                'execution_timestamp': sell_time.isoformat(),
                'last_updated': get_current_timestamp(),
                'scenario_type': 'insider_trading',
                'scenario_phase': 'profit_taking',
                'scenario_symbol': symbol,
                'news_announcement_time': news_announcement_time.isoformat()
            }
            
            trades.append(sell_trade)
    
    # Sort trades by timestamp
    trades.sort(key=lambda x: x['execution_timestamp'])
    
    log_with_timestamp(f"Generated {len(trades)} insider trades for {symbol}")
    return trades

def generate_insider_trading_scenarios(
    num_scenarios: int = 3,
    output_file: str = None
) -> List[Dict]:
    """Generate multiple insider trading scenarios."""
    
    if output_file is None:
        output_file = FILE_PATHS.get('generated_controlled_trades')
    
    # Clear output file
    clear_file_if_exists(output_file)
    
    log_with_timestamp("Starting insider trading scenario generation")
    
    # Load required data
    accounts = load_accounts()
    asset_prices = load_asset_prices()
    
    # Select symbols for insider trading scenarios
    available_symbols = list(asset_prices.keys())
    if len(available_symbols) < num_scenarios:
        log_with_timestamp(f"WARNING: Only {len(available_symbols)} symbols available, requested {num_scenarios}")
        num_scenarios = len(available_symbols)
    
    scenario_symbols = random.sample(available_symbols, num_scenarios)
    
    all_trades = []
    
    for i, symbol in enumerate(scenario_symbols, 1):
        log_with_timestamp(f"Generating insider trading scenario {i}/{num_scenarios} for {symbol}")
        
        # Set timeline - scenarios occur over past week
        news_announcement_time = datetime.now() - timedelta(days=random.randint(1, 7))
        hours_before = random.randint(*INSIDER_TRADING_CONFIG['pre_announcement_hours'])
        scenario_start = news_announcement_time - timedelta(hours=hours_before)
        
        scenario_trades = generate_insider_trading_scenario(
            symbol=symbol,
            accounts=accounts,
            asset_prices=asset_prices,
            scenario_start=scenario_start,
            news_announcement_time=news_announcement_time
        )
        
        all_trades.extend(scenario_trades)
    
    # Write all trades to file
    log_with_timestamp(f"Writing {len(all_trades)} insider trading trades to {output_file}")
    
    with open(output_file, 'w') as f:
        for trade in all_trades:
            f.write(json.dumps(trade) + '\n')
    
    log_with_timestamp(f"Insider trading scenario generation complete")
    log_with_timestamp(f"Generated {len(all_trades)} trades across {num_scenarios} scenarios")
    
    return all_trades

def ingest_to_elasticsearch(trades: List[Dict]) -> bool:
    """Ingest insider trading data to Elasticsearch."""
    try:
        es_client = create_elasticsearch_client()
        index_name = ES_CONFIG['indices']['trades']
        
        log_with_timestamp(f"Ingesting {len(trades)} insider trades to Elasticsearch index: {index_name}")
        
        success = ingest_data_to_es(
            es_client=es_client,
            data=trades,
            index_name=index_name,
            id_field='trade_id'
        )
        
        if success:
            log_with_timestamp("Successfully ingested insider trading data to Elasticsearch")
        else:
            log_with_timestamp("Failed to ingest insider trading data to Elasticsearch")
        
        return success
        
    except Exception as e:
        log_with_timestamp(f"Error ingesting to Elasticsearch: {e}")
        return False

def main():
    """Main execution function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate insider trading scenarios')
    parser.add_argument('--num-scenarios', type=int, default=3,
                       help='Number of insider trading scenarios to generate')
    parser.add_argument('--output-file', type=str,
                       help='Output file path (default: generated_controlled_trades.jsonl)')
    parser.add_argument('--elasticsearch', action='store_true',
                       help='Ingest generated data to Elasticsearch')
    
    args = parser.parse_args()
    
    try:
        # Generate insider trading scenarios
        trades = generate_insider_trading_scenarios(
            num_scenarios=args.num_scenarios,
            output_file=args.output_file
        )
        
        # Optionally ingest to Elasticsearch
        if args.elasticsearch:
            ingest_to_elasticsearch(trades)
        
        # Summary
        print(f"\n{'='*60}")
        print("INSIDER TRADING SCENARIO GENERATION COMPLETE")
        print(f"{'='*60}")
        print(f"📊 Scenarios Generated: {args.num_scenarios}")
        print(f"📈 Total Trades: {len(trades)}")
        print(f"💾 Output File: {args.output_file or FILE_PATHS.get('generated_controlled_trades')}")
        if args.elasticsearch:
            print("🔍 Data ingested to Elasticsearch for analysis")
        print(f"{'='*60}")
        
        return True
        
    except Exception as e:
        log_with_timestamp(f"Error in insider trading generation: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)