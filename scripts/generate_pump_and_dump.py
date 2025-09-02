#!/usr/bin/env python3
"""
Pump and Dump Scenario Generator

This script generates realistic pump and dump manipulation patterns with coordinated
buying (pump), price manipulation, and coordinated selling (dump) phases.

Key patterns generated:
- Phase 1: Coordinated accumulation across multiple accounts (5-7 days)
- Phase 2: Aggressive buying to drive price up 15-40% (2-4 hours)
- Phase 3: Rapid coordinated selling/dumping (1-2 hours)  
- Phase 4: Negative news generation to justify price collapse
- Volume spikes, price manipulation, and coordinated exit strategies
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
PUMP_AND_DUMP_CONFIG = {
    'accounts_per_scheme': (8, 20),  # Number of accounts in coordination
    'accumulation_days': (5, 10),  # Days of gradual accumulation
    'pump_duration_hours': (2, 6),  # Duration of aggressive buying phase
    'dump_duration_hours': (1, 3),  # Duration of rapid selling phase
    'price_pump_target': (0.15, 0.40),  # Price increase target (15-40%)
    'price_dump_impact': (0.25, 0.50),  # Price crash after dump (25-50%)
    'volume_multiplier': {
        'accumulation': (2.0, 4.0),  # Volume during accumulation
        'pump': (8.0, 20.0),  # Volume during pump phase
        'dump': (15.0, 35.0)  # Volume during dump phase
    },
    'account_coordination': {
        'tight': 0.4,    # 40% chance of tight coordination (same timing)
        'loose': 0.4,    # 40% chance of loose coordination (spread timing)
        'mixed': 0.2     # 20% chance of mixed patterns
    },
    'trade_distribution': {
        'accumulation': {'buy': 0.85, 'sell': 0.15},  # Mostly buying
        'pump': {'buy': 0.95, 'sell': 0.05},  # Almost all buying
        'dump': {'buy': 0.05, 'sell': 0.95}   # Almost all selling
    },
    'order_type_bias': {
        'accumulation': {'market': 0.3, 'limit': 0.7},  # More limit orders (stealth)
        'pump': {'market': 0.8, 'limit': 0.2},  # More market orders (speed)
        'dump': {'market': 0.9, 'limit': 0.1}   # Almost all market (urgency)
    }
}

def load_accounts() -> List[Dict[str, Any]]:
    """Load account data for pump and dump scenarios."""
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
    
    log_with_timestamp(f"Loaded {len(accounts)} accounts for pump and dump scenarios")
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

def select_pump_dump_accounts(accounts: List[Dict], num_accounts: int) -> List[Dict]:
    """
    Select accounts for pump and dump scheme.
    Prefer accounts with higher risk profiles and larger portfolios.
    """
    # Score accounts based on suitability for pump and dump
    scored_accounts = []
    
    for account in accounts:
        score = 0
        risk_profile = account.get('risk_profile', 'Medium')
        portfolio_value = account.get('total_portfolio_value', 0)
        
        # Risk profile scoring (higher risk = more suitable)
        risk_scores = {
            'Conservative': 1, 'Very Low': 2, 'Low': 3,
            'Medium': 4, 'Moderate': 5, 'Growth': 7,
            'High': 9, 'Very High': 10
        }
        score += risk_scores.get(risk_profile, 4)
        
        # Portfolio size scoring (larger portfolios = more impact)
        if portfolio_value > 10000000:  # >$10M
            score += 5
        elif portfolio_value > 5000000:  # >$5M
            score += 3
        elif portfolio_value > 1000000:  # >$1M
            score += 1
        
        scored_accounts.append((account, score))
    
    # Sort by score and select top accounts with some randomization
    scored_accounts.sort(key=lambda x: x[1], reverse=True)
    
    # Take top 50% and randomly select from them
    top_half = scored_accounts[:len(scored_accounts)//2]
    selected = random.sample(top_half, min(num_accounts, len(top_half)))
    
    return [acc[0] for acc in selected]

def calculate_price_progression(
    base_price: float,
    accumulation_days: int,
    pump_hours: int,
    dump_hours: int,
    pump_target: float,
    dump_impact: float
) -> Dict[str, List[Tuple[datetime, float]]]:
    """
    Calculate price progression through all phases of pump and dump.
    Returns dict with phase names and (datetime, price) tuples.
    """
    now = datetime.now()
    phases = {}
    
    # Phase 1: Accumulation (gradual price increase)
    accumulation_start = now - timedelta(days=accumulation_days + 2)
    accumulation_prices = []
    
    for day in range(accumulation_days):
        day_time = accumulation_start + timedelta(days=day)
        # Gradual price increase during accumulation (0-5%)
        progress = day / accumulation_days
        price_increase = 0.05 * progress  # Up to 5% increase
        daily_price = base_price * (1 + price_increase + random.uniform(-0.01, 0.01))
        accumulation_prices.append((day_time, round(daily_price, 2)))
    
    phases['accumulation'] = accumulation_prices
    
    # Phase 2: Pump (rapid price increase)
    pump_start = now - timedelta(days=2)
    pump_prices = []
    accumulation_end_price = accumulation_prices[-1][1]
    
    for hour in range(pump_hours):
        hour_time = pump_start + timedelta(hours=hour)
        # Rapid price increase during pump
        progress = hour / pump_hours
        # Non-linear progression (accelerating)
        pump_progress = progress ** 0.7
        price_increase = pump_target * pump_progress
        hourly_price = accumulation_end_price * (1 + price_increase)
        # Add some volatility
        hourly_price *= (1 + random.uniform(-0.02, 0.03))
        pump_prices.append((hour_time, round(hourly_price, 2)))
    
    phases['pump'] = pump_prices
    
    # Phase 3: Dump (rapid price decrease)
    dump_start = pump_start + timedelta(hours=pump_hours)
    dump_prices = []
    pump_peak_price = pump_prices[-1][1]
    
    for hour in range(dump_hours):
        hour_time = dump_start + timedelta(hours=hour)
        # Rapid price decrease during dump
        progress = hour / dump_hours
        # Accelerating decline
        dump_progress = progress ** 0.5
        price_decrease = dump_impact * dump_progress
        hourly_price = pump_peak_price * (1 - price_decrease)
        # Add volatility (more on downside)
        hourly_price *= (1 + random.uniform(-0.05, 0.02))
        dump_prices.append((hour_time, round(max(hourly_price, base_price * 0.5), 2)))
    
    phases['dump'] = dump_prices
    
    return phases

def generate_phase_trades(
    phase_name: str,
    symbol: str,
    accounts: List[Dict],
    phase_times_prices: List[Tuple[datetime, float]],
    coordination_type: str,
    scheme_id: str
) -> List[Dict]:
    """Generate trades for a specific phase of the pump and dump."""
    
    trades = []
    phase_config = PUMP_AND_DUMP_CONFIG
    
    # Get phase-specific settings
    volume_mult_range = phase_config['volume_multiplier'][phase_name]
    trade_dist = phase_config['trade_distribution'][phase_name]
    order_bias = phase_config['order_type_bias'][phase_name]
    
    log_with_timestamp(f"    Generating {phase_name} trades: {len(phase_times_prices)} time points")
    
    for time_point, price in phase_times_prices:
        # Determine how many accounts are active at this time point
        if coordination_type == 'tight':
            # Most accounts trade at same time
            active_accounts = random.sample(accounts, int(len(accounts) * random.uniform(0.7, 0.9)))
        elif coordination_type == 'loose':
            # Fewer accounts trade at same time
            active_accounts = random.sample(accounts, int(len(accounts) * random.uniform(0.3, 0.6)))
        else:  # mixed
            # Variable coordination
            active_accounts = random.sample(accounts, int(len(accounts) * random.uniform(0.4, 0.8)))
        
        for account in active_accounts:
            # Determine number of trades for this account at this time
            if phase_name == 'accumulation':
                num_trades = random.randint(1, 3)
            elif phase_name == 'pump':
                num_trades = random.randint(2, 6)
            elif phase_name == 'dump':
                num_trades = random.randint(3, 8)
            
            for _ in range(num_trades):
                # Random time variation within the time window
                trade_time = time_point + timedelta(
                    minutes=random.randint(-30, 30),
                    seconds=random.randint(0, 59)
                )
                
                # Determine trade type based on phase
                trade_type = random.choices(
                    list(trade_dist.keys()),
                    weights=list(trade_dist.values())
                )[0]
                
                # Determine order type based on phase
                order_type = random.choices(
                    list(order_bias.keys()),
                    weights=list(order_bias.values())
                )[0]
                
                # Calculate quantity based on account size and phase intensity
                portfolio_value = account.get('total_portfolio_value', 1000000)
                base_quantity = max(100, int(portfolio_value * 0.0002))  # 0.02% of portfolio
                
                # Phase-specific quantity multipliers
                phase_multipliers = {'accumulation': 1.0, 'pump': 2.0, 'dump': 3.0}
                volume_multiplier = random.uniform(*volume_mult_range)
                
                quantity = int(base_quantity * phase_multipliers[phase_name] * volume_multiplier)
                quantity = max(1, quantity)
                
                # Price calculation with some variation
                price_variation = random.uniform(-0.005, 0.005)  # ±0.5%
                execution_price = price * (1 + price_variation)
                
                # Order status (most executed, some cancelled for realism)
                order_status = 'executed' if random.random() > 0.05 else 'cancelled'
                
                trade = {
                    'trade_id': f"PUMP-{phase_name.upper()}-{uuid.uuid4().hex[:8]}-{int(trade_time.timestamp())}",
                    'account_id': account['account_id'],
                    'symbol': symbol,
                    'trade_type': trade_type,
                    'order_type': order_type,
                    'order_status': order_status,
                    'quantity': float(quantity),
                    'execution_price': round(execution_price, 2) if order_status == 'executed' else 0,
                    'trade_cost': round(quantity * execution_price, 2) if order_status == 'executed' else 0,
                    'execution_timestamp': trade_time.isoformat(),
                    'last_updated': get_current_timestamp(),
                    'scenario_type': 'pump_and_dump',
                    'scenario_phase': phase_name,
                    'scenario_symbol': symbol,
                    'pump_scheme_id': scheme_id,
                    'coordination_type': coordination_type
                }
                
                trades.append(trade)
    
    return trades

def generate_pump_and_dump_scenario(
    accounts: List[Dict],
    asset_prices: Dict[str, float],
    scenario_start: datetime
) -> Tuple[List[Dict], str]:
    """Generate a complete pump and dump scenario."""
    
    # Configuration for this scenario
    num_accounts = random.randint(*PUMP_AND_DUMP_CONFIG['accounts_per_scheme'])
    accumulation_days = random.randint(*PUMP_AND_DUMP_CONFIG['accumulation_days'])
    pump_hours = random.randint(*PUMP_AND_DUMP_CONFIG['pump_duration_hours'])
    dump_hours = random.randint(*PUMP_AND_DUMP_CONFIG['dump_duration_hours'])
    pump_target = random.uniform(*PUMP_AND_DUMP_CONFIG['price_pump_target'])
    dump_impact = random.uniform(*PUMP_AND_DUMP_CONFIG['price_dump_impact'])
    
    # Select coordination type
    coord_weights = PUMP_AND_DUMP_CONFIG['account_coordination']
    coordination_type = random.choices(
        list(coord_weights.keys()),
        weights=list(coord_weights.values())
    )[0]
    
    # Select accounts and symbol
    scheme_accounts = select_pump_dump_accounts(accounts, num_accounts)
    available_symbols = list(asset_prices.keys())
    target_symbol = random.choice(available_symbols)
    base_price = asset_prices[target_symbol]
    
    # Generate unique scheme ID
    scheme_id = f"SCHEME-{uuid.uuid4().hex[:8]}"
    
    log_with_timestamp(f"Generating pump and dump scenario:")
    log_with_timestamp(f"  Scheme ID: {scheme_id}")
    log_with_timestamp(f"  Target symbol: {target_symbol} (${base_price:.2f})")
    log_with_timestamp(f"  Accounts: {num_accounts} ({coordination_type} coordination)")
    log_with_timestamp(f"  Timeline: {accumulation_days}d accumulation, {pump_hours}h pump, {dump_hours}h dump")
    log_with_timestamp(f"  Price targets: +{pump_target:.1%} pump, -{dump_impact:.1%} dump")
    
    # Calculate price progression through all phases
    price_progression = calculate_price_progression(
        base_price, accumulation_days, pump_hours, dump_hours, pump_target, dump_impact
    )
    
    all_trades = []
    
    # Generate trades for each phase
    for phase_name, phase_prices in price_progression.items():
        log_with_timestamp(f"  Generating {phase_name} phase...")
        
        phase_trades = generate_phase_trades(
            phase_name=phase_name,
            symbol=target_symbol,
            accounts=scheme_accounts,
            phase_times_prices=phase_prices,
            coordination_type=coordination_type,
            scheme_id=scheme_id
        )
        
        all_trades.extend(phase_trades)
        log_with_timestamp(f"    Generated {len(phase_trades)} trades for {phase_name}")
    
    # Sort all trades by timestamp
    all_trades.sort(key=lambda x: x['execution_timestamp'])
    
    log_with_timestamp(f"Generated {len(all_trades)} total trades for pump and dump scenario")
    
    # Return trades and summary for news generation
    scenario_summary = {
        'scheme_id': scheme_id,
        'symbol': target_symbol,
        'accounts': [acc['account_id'] for acc in scheme_accounts],
        'base_price': base_price,
        'pump_target': pump_target,
        'dump_impact': dump_impact,
        'timeline': {
            'accumulation_days': accumulation_days,
            'pump_hours': pump_hours,
            'dump_hours': dump_hours
        }
    }
    
    return all_trades, scenario_summary

def generate_pump_and_dump_scenarios(
    num_scenarios: int = 1,
    output_file: str = None
) -> Tuple[List[Dict], List[Dict]]:
    """Generate multiple pump and dump scenarios."""
    
    if output_file is None:
        output_file = FILE_PATHS.get('generated_controlled_trades')
    
    log_with_timestamp("Starting pump and dump scenario generation")
    
    # Load required data
    accounts = load_accounts()
    asset_prices = load_asset_prices()
    
    all_trades = []
    all_summaries = []
    
    for i in range(num_scenarios):
        log_with_timestamp(f"Generating pump and dump scenario {i + 1}/{num_scenarios}")
        
        # Set timeline - scenarios occur over past month
        scenario_start = datetime.now() - timedelta(days=random.randint(7, 30))
        
        scenario_trades, scenario_summary = generate_pump_and_dump_scenario(
            accounts=accounts,
            asset_prices=asset_prices,
            scenario_start=scenario_start
        )
        
        all_trades.extend(scenario_trades)
        all_summaries.append(scenario_summary)
    
    # Append to existing controlled trades file
    log_with_timestamp(f"Appending {len(all_trades)} pump and dump trades to {output_file}")
    
    with open(output_file, 'a') as f:  # Append mode
        for trade in all_trades:
            f.write(json.dumps(trade) + '\n')
    
    log_with_timestamp(f"Pump and dump scenario generation complete")
    log_with_timestamp(f"Generated {len(all_trades)} trades across {num_scenarios} scenarios")
    
    return all_trades, all_summaries

def ingest_to_elasticsearch(trades: List[Dict]) -> bool:
    """Ingest pump and dump data to Elasticsearch."""
    try:
        es_client = create_elasticsearch_client()
        index_name = ES_CONFIG['indices']['trades']
        
        log_with_timestamp(f"Ingesting {len(trades)} pump and dump trades to Elasticsearch index: {index_name}")
        
        success = ingest_data_to_es(
            es_client=es_client,
            data=trades,
            index_name=index_name,
            id_field='trade_id'
        )
        
        if success:
            log_with_timestamp("Successfully ingested pump and dump data to Elasticsearch")
        else:
            log_with_timestamp("Failed to ingest pump and dump data to Elasticsearch")
        
        return success
        
    except Exception as e:
        log_with_timestamp(f"Error ingesting to Elasticsearch: {e}")
        return False

def main():
    """Main execution function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate pump and dump scenarios')
    parser.add_argument('--num-scenarios', type=int, default=1,
                       help='Number of pump and dump scenarios to generate')
    parser.add_argument('--output-file', type=str,
                       help='Output file path (default: generated_controlled_trades.jsonl)')
    parser.add_argument('--elasticsearch', action='store_true',
                       help='Ingest generated data to Elasticsearch')
    
    args = parser.parse_args()
    
    try:
        # Generate pump and dump scenarios
        trades, summaries = generate_pump_and_dump_scenarios(
            num_scenarios=args.num_scenarios,
            output_file=args.output_file
        )
        
        # Optionally ingest to Elasticsearch
        if args.elasticsearch:
            ingest_to_elasticsearch(trades)
        
        # Summary
        print(f"\n{'='*60}")
        print("PUMP AND DUMP SCENARIO GENERATION COMPLETE")
        print(f"{'='*60}")
        print(f"📊 Scenarios Generated: {args.num_scenarios}")
        print(f"📈 Total Trades: {len(trades)}")
        print(f"💾 Output File: {args.output_file or FILE_PATHS.get('generated_controlled_trades')}")
        if args.elasticsearch:
            print("🔍 Data ingested to Elasticsearch for analysis")
        
        # Show scenario summaries
        for i, summary in enumerate(summaries, 1):
            print(f"\n🎯 Scenario {i}: {summary['symbol']}")
            print(f"   💰 Base Price: ${summary['base_price']:.2f}")
            print(f"   📈 Pump Target: +{summary['pump_target']:.1%}")
            print(f"   📉 Dump Impact: -{summary['dump_impact']:.1%}")
            print(f"   👥 Accounts: {len(summary['accounts'])}")
        
        print(f"{'='*60}")
        
        return True
        
    except Exception as e:
        log_with_timestamp(f"Error in pump and dump generation: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)