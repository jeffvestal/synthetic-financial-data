#!/usr/bin/env python3
"""
Generate holdings from trade activity data.

This script calculates current portfolio positions by aggregating all executed trades.
Holdings are the net result of all buy, sell, short, and cover transactions.

Formula: Net Position = Σ(buys) - Σ(sells) + Σ(covers) - Σ(shorts)

Usage:
    python3 scripts/generate_holdings.py
    
Note: Must run AFTER generate_trades.py
"""

import json
import os
import sys
from collections import defaultdict
from typing import Dict, DefaultDict
import uuid

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import FILE_PATHS
from common_utils import (
    clear_file_if_exists,
    get_current_timestamp,
    log_with_timestamp
)

def generate_holding_id(account_id: str, symbol: str) -> str:
    """Generate unique holding ID."""
    # Use first 8 chars of UUID for uniqueness
    unique_suffix = str(uuid.uuid4())[:8]
    return f"{account_id}-{symbol}-{unique_suffix}"

def aggregate_positions_from_trades(trades_file: str) -> Dict[str, Dict[str, float]]:
    """
    Read trades and calculate current positions.
    
    Args:
        trades_file: Path to trades JSONL file
        
    Returns:
        Nested dict: {account_id: {symbol: net_quantity}}
    """
    # Use defaultdict for automatic initialization
    positions: DefaultDict[str, DefaultDict[str, float]] = defaultdict(lambda: defaultdict(float))
    
    trades_processed = 0
    cancelled_trades = 0
    
    log_with_timestamp("Reading and aggregating trades...")
    
    with open(trades_file, 'r') as f:
        for line_num, line in enumerate(f, 1):
            try:
                trade = json.loads(line)
                
                # Skip cancelled orders
                if trade.get('order_status') != 'executed':
                    cancelled_trades += 1
                    continue
                
                account_id = trade['account_id']
                symbol = trade['symbol']
                quantity = float(trade['quantity'])
                trade_type = trade['trade_type']
                
                # Apply trade logic based on type
                if trade_type == 'buy':
                    positions[account_id][symbol] += quantity
                elif trade_type == 'sell':
                    positions[account_id][symbol] -= quantity
                elif trade_type == 'short':
                    positions[account_id][symbol] -= quantity  # Short creates negative position
                elif trade_type == 'cover':
                    positions[account_id][symbol] += quantity  # Cover reduces short position
                else:
                    log_with_timestamp(f"WARNING: Unknown trade type '{trade_type}' at line {line_num}")
                
                trades_processed += 1
                
                # Progress update every 10000 trades
                if trades_processed % 10000 == 0:
                    log_with_timestamp(f"  Processed {trades_processed:,} trades...")
                    
            except json.JSONDecodeError as e:
                log_with_timestamp(f"WARNING: Invalid JSON at line {line_num}: {e}")
            except KeyError as e:
                log_with_timestamp(f"WARNING: Missing field at line {line_num}: {e}")
    
    log_with_timestamp(f"Processed {trades_processed:,} executed trades ({cancelled_trades:,} cancelled)")
    
    # Convert defaultdict to regular dict for cleaner output
    return {account: dict(symbols) for account, symbols in positions.items()}

def filter_positions(positions: Dict[str, Dict[str, float]], min_quantity: float = 0.01) -> Dict[str, Dict[str, float]]:
    """
    Filter out zero or near-zero positions.
    
    Args:
        positions: Position data from aggregation
        min_quantity: Minimum absolute quantity to keep (handles rounding errors)
        
    Returns:
        Filtered positions dictionary
    """
    filtered = {}
    removed_count = 0
    
    for account_id, account_positions in positions.items():
        filtered_symbols = {}
        
        for symbol, quantity in account_positions.items():
            # Keep positions above minimum threshold (including negative/short positions)
            if abs(quantity) >= min_quantity:
                # Round to reasonable precision
                filtered_symbols[symbol] = round(quantity, 4)
            else:
                removed_count += 1
        
        # Only include account if they have positions
        if filtered_symbols:
            filtered[account_id] = filtered_symbols
    
    if removed_count > 0:
        log_with_timestamp(f"Filtered out {removed_count} near-zero positions")
    
    return filtered

def generate_holdings_records(positions: Dict[str, Dict[str, float]]) -> list:
    """
    Convert position data to holdings records with simplified schema.
    
    Args:
        positions: Aggregated position data
        
    Returns:
        List of holding dictionaries
    """
    holdings = []
    
    for account_id, account_positions in positions.items():
        for symbol, quantity in account_positions.items():
            holding = {
                'holding_id': generate_holding_id(account_id, symbol),
                'account_id': account_id,
                'symbol': symbol,
                'quantity': quantity,
                'last_updated': get_current_timestamp()
            }
            holdings.append(holding)
    
    return holdings

def validate_positions(positions: Dict[str, Dict[str, float]]) -> None:
    """
    Perform validation checks on calculated positions.
    
    Args:
        positions: Aggregated position data
    """
    total_accounts = len(positions)
    total_positions = sum(len(symbols) for symbols in positions.values())
    
    # Count short positions (negative quantities)
    short_positions = 0
    for account_positions in positions.values():
        for quantity in account_positions.values():
            if quantity < 0:
                short_positions += 1
    
    log_with_timestamp("=== Position Validation ===")
    log_with_timestamp(f"Total accounts with positions: {total_accounts:,}")
    log_with_timestamp(f"Total unique positions: {total_positions:,}")
    log_with_timestamp(f"Short positions (negative qty): {short_positions:,}")
    
    # Calculate average positions per account
    if total_accounts > 0:
        avg_positions = total_positions / total_accounts
        log_with_timestamp(f"Average positions per account: {avg_positions:.1f}")
    
    # Find accounts with most positions (potential data issues)
    if positions:
        max_positions_account = max(positions.items(), key=lambda x: len(x[1]))
        log_with_timestamp(f"Max positions in single account: {len(max_positions_account[1])} (Account: {max_positions_account[0][:15]}...)")
    
    # Check for extremely large positions that might indicate errors
    extreme_positions = []
    for account_id, account_positions in positions.items():
        for symbol, quantity in account_positions.items():
            if abs(quantity) > 100000:  # Flag positions over 100k shares
                extreme_positions.append((account_id, symbol, quantity))
    
    if extreme_positions:
        log_with_timestamp(f"WARNING: Found {len(extreme_positions)} extreme positions (>100k shares)")
        for i, (acc, sym, qty) in enumerate(extreme_positions[:5], 1):
            log_with_timestamp(f"  {i}. Account {acc[:15]}... has {qty:,.0f} shares of {sym}")

def write_holdings_to_file(holdings: list, output_file: str) -> None:
    """
    Write holdings records to JSONL file.
    
    Args:
        holdings: List of holding dictionaries
        output_file: Path to output file
    """
    with open(output_file, 'w') as f:
        for holding in holdings:
            f.write(json.dumps(holding) + '\n')

def main():
    """Main execution function."""
    log_with_timestamp("=== Starting Holdings Calculation from Trades ===")
    
    # Check that trades file exists
    trades_file = FILE_PATHS.get('generated_trades')
    if not os.path.exists(trades_file):
        log_with_timestamp("ERROR: Trades file not found. Run generate_trades.py first.")
        return 1
    
    # Get file size for estimation
    file_size = os.path.getsize(trades_file)
    log_with_timestamp(f"Processing trades file: {trades_file} ({file_size / 1024 / 1024:.1f} MB)")
    
    # Step 1: Aggregate positions from trades
    log_with_timestamp("Step 1: Aggregating positions from trades...")
    positions = aggregate_positions_from_trades(trades_file)
    
    # Step 2: Filter out zero positions
    log_with_timestamp("Step 2: Filtering positions...")
    filtered_positions = filter_positions(positions)
    
    # Step 3: Validate positions
    log_with_timestamp("Step 3: Validating positions...")
    validate_positions(filtered_positions)
    
    # Step 4: Generate holdings records
    log_with_timestamp("Step 4: Generating holdings records...")
    holdings = generate_holdings_records(filtered_positions)
    log_with_timestamp(f"Generated {len(holdings):,} holding records")
    
    # Step 5: Write to file
    output_file = FILE_PATHS.get('generated_holdings')
    log_with_timestamp(f"Step 5: Writing holdings to {output_file}...")
    
    # Clear existing file
    clear_file_if_exists(output_file)
    
    # Write new holdings
    write_holdings_to_file(holdings, output_file)
    
    log_with_timestamp("=== Holdings Calculation Complete ===")
    log_with_timestamp(f"Output file: {output_file}")
    log_with_timestamp(f"Total holdings: {len(holdings):,}")
    
    # Calculate some statistics
    if holdings:
        quantities = [h['quantity'] for h in holdings]
        positive_holdings = [q for q in quantities if q > 0]
        negative_holdings = [q for q in quantities if q < 0]
        
        log_with_timestamp(f"Long positions: {len(positive_holdings):,}")
        log_with_timestamp(f"Short positions: {len(negative_holdings):,}")
        
        if positive_holdings:
            avg_long = sum(positive_holdings) / len(positive_holdings)
            log_with_timestamp(f"Average long position size: {avg_long:.1f} shares")
        
        if negative_holdings:
            avg_short = sum(negative_holdings) / len(negative_holdings)
            log_with_timestamp(f"Average short position size: {avg_short:.1f} shares")
    
    log_with_timestamp("")
    log_with_timestamp("Note: To load holdings to Elasticsearch, run:")
    log_with_timestamp("  python3 load_all_data.py")
    log_with_timestamp("  or")
    log_with_timestamp("  python3 load_specific_indices.py --holdings")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())