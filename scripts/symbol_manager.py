"""
Symbol management utilities for Portfolio-Pilot-AI data generation.

This module provides helper functions for working with stock, ETF, and bond symbols,
including validation, filtering, and random selection utilities.

Usage:
    from symbol_manager import SymbolManager
    
    sm = SymbolManager()
    tech_stocks = sm.get_symbols_by_sector('Technology')
    random_symbols = sm.get_random_symbols(10)
"""

import random
from typing import List, Dict, Any, Optional, Set
from symbols_config import (
    STOCK_SYMBOLS_AND_INFO, 
    ETF_SYMBOLS_AND_INFO, 
    BOND_TYPES,
    ALL_ASSET_INFO,
    ALL_ASSET_SYMBOLS,
    get_asset_info,
    validate_symbol
)

class SymbolManager:
    """
    Centralized manager for symbol operations and filtering.
    """
    
    def __init__(self):
        """Initialize the symbol manager."""
        self._stock_symbols = list(STOCK_SYMBOLS_AND_INFO.keys())
        self._etf_symbols = list(ETF_SYMBOLS_AND_INFO.keys())
        self._bond_symbols = [bond['symbol'] for bond in BOND_TYPES]
        self._all_symbols = ALL_ASSET_SYMBOLS.copy()
    
    # --- Basic Symbol Access ---
    
    def get_all_symbols(self) -> List[str]:
        """Get all available symbols."""
        return self._all_symbols.copy()
    
    def get_stock_symbols(self) -> List[str]:
        """Get all stock symbols."""
        return self._stock_symbols.copy()
    
    def get_etf_symbols(self) -> List[str]:
        """Get all ETF symbols."""
        return self._etf_symbols.copy()
    
    def get_bond_symbols(self) -> List[str]:
        """Get all bond symbols."""
        return self._bond_symbols.copy()
    
    def get_stocks_and_etfs(self) -> List[str]:
        """Get combined list of stocks and ETFs (excludes bonds)."""
        return self._stock_symbols + self._etf_symbols
    
    # --- Symbol Information ---
    
    def get_symbol_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get information for a specific symbol.
        
        Args:
            symbol (str): Symbol to look up
            
        Returns:
            dict or None: Symbol information or None if not found
        """
        return get_asset_info(symbol)
    
    def is_valid_symbol(self, symbol: str) -> bool:
        """
        Check if a symbol is valid.
        
        Args:
            symbol (str): Symbol to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        return validate_symbol(symbol)
    
    def get_symbol_type(self, symbol: str) -> Optional[str]:
        """
        Get the type of a symbol (Stock, ETF, or Bond).
        
        Args:
            symbol (str): Symbol to check
            
        Returns:
            str or None: 'Stock', 'ETF', 'Bond', or None if not found
        """
        if symbol in self._stock_symbols:
            return 'Stock'
        elif symbol in self._etf_symbols:
            return 'ETF'
        elif symbol in self._bond_symbols:
            return 'Bond'
        return None
    
    # --- Filtering Functions ---
    
    def get_symbols_by_sector(self, sector: str) -> List[str]:
        """
        Get all symbols in a specific sector.
        
        Args:
            sector (str): Sector name to filter by
            
        Returns:
            List[str]: Symbols in the sector
        """
        symbols = []
        for symbol, info in ALL_ASSET_INFO.items():
            if info.get('sector') == sector:
                symbols.append(symbol)
        return symbols
    
    def get_symbols_by_country(self, country: str) -> List[str]:
        """
        Get all symbols from a specific country.
        
        Args:
            country (str): Country name to filter by
            
        Returns:
            List[str]: Symbols from the country
        """
        symbols = []
        for symbol, info in ALL_ASSET_INFO.items():
            if info.get('country') == country:
                symbols.append(symbol)
        return symbols
    
    def get_symbols_by_index(self, index_name: str) -> List[str]:
        """
        Get all symbols that belong to a specific index.
        
        Args:
            index_name (str): Index name to filter by (e.g., 'S&P 500')
            
        Returns:
            List[str]: Symbols in the index
        """
        symbols = []
        for symbol, info in ALL_ASSET_INFO.items():
            indices = info.get('indices', [])
            if index_name in indices:
                symbols.append(symbol)
        return symbols
    
    def filter_symbols_by_type(self, symbols: List[str], symbol_type: str) -> List[str]:
        """
        Filter a list of symbols by type.
        
        Args:
            symbols (List[str]): Symbols to filter
            symbol_type (str): Type to filter by ('Stock', 'ETF', 'Bond')
            
        Returns:
            List[str]: Filtered symbols
        """
        return [symbol for symbol in symbols if self.get_symbol_type(symbol) == symbol_type]
    
    # --- Random Selection Functions ---
    
    def get_random_symbols(self, count: int, symbol_types: Optional[List[str]] = None) -> List[str]:
        """
        Get a random selection of symbols.
        
        Args:
            count (int): Number of symbols to return
            symbol_types (List[str], optional): Types to include ('Stock', 'ETF', 'Bond')
            
        Returns:
            List[str]: Random symbols
        """
        if symbol_types:
            available_symbols = []
            for symbol_type in symbol_types:
                if symbol_type == 'Stock':
                    available_symbols.extend(self._stock_symbols)
                elif symbol_type == 'ETF':
                    available_symbols.extend(self._etf_symbols)
                elif symbol_type == 'Bond':
                    available_symbols.extend(self._bond_symbols)
        else:
            available_symbols = self._all_symbols
        
        return random.sample(available_symbols, min(count, len(available_symbols)))
    
    def get_random_stocks(self, count: int) -> List[str]:
        """Get random stock symbols."""
        return random.sample(self._stock_symbols, min(count, len(self._stock_symbols)))
    
    def get_random_etfs(self, count: int) -> List[str]:
        """Get random ETF symbols."""
        return random.sample(self._etf_symbols, min(count, len(self._etf_symbols)))
    
    def get_random_bonds(self, count: int) -> List[str]:
        """Get random bond symbols."""
        return random.sample(self._bond_symbols, min(count, len(self._bond_symbols)))
    
    def get_random_stocks_and_etfs(self, count: int) -> List[str]:
        """Get random selection from stocks and ETFs (no bonds)."""
        stocks_and_etfs = self.get_stocks_and_etfs()
        return random.sample(stocks_and_etfs, min(count, len(stocks_and_etfs)))
    
    # --- Analysis Functions ---
    
    def get_all_sectors(self) -> List[str]:
        """Get list of all unique sectors."""
        sectors = set()
        for info in ALL_ASSET_INFO.values():
            if 'sector' in info:
                sectors.add(info['sector'])
        return sorted(list(sectors))
    
    def get_all_countries(self) -> List[str]:
        """Get list of all unique countries."""
        countries = set()
        for info in ALL_ASSET_INFO.values():
            if 'country' in info:
                countries.add(info['country'])
        return sorted(list(countries))
    
    def get_all_indices(self) -> List[str]:
        """Get list of all unique indices."""
        indices = set()
        for info in ALL_ASSET_INFO.values():
            for index in info.get('indices', []):
                indices.add(index)
        return sorted(list(indices))
    
    def get_symbol_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about available symbols.
        
        Returns:
            dict: Statistics including counts by type, sector, etc.
        """
        stats = {
            'total_symbols': len(self._all_symbols),
            'stocks': len(self._stock_symbols),
            'etfs': len(self._etf_symbols),
            'bonds': len(self._bond_symbols),
            'sectors': {},
            'countries': {},
            'indices': {}
        }
        
        # Count by sector
        for symbol, info in ALL_ASSET_INFO.items():
            sector = info.get('sector', 'Unknown')
            stats['sectors'][sector] = stats['sectors'].get(sector, 0) + 1
        
        # Count by country
        for symbol, info in ALL_ASSET_INFO.items():
            country = info.get('country', 'Unknown')
            stats['countries'][country] = stats['countries'].get(country, 0) + 1
        
        # Count by index
        for symbol, info in ALL_ASSET_INFO.items():
            for index in info.get('indices', []):
                stats['indices'][index] = stats['indices'].get(index, 0) + 1
        
        return stats
    
    # --- Validation and Utility Functions ---
    
    def ensure_symbols_exist(self, symbols: List[str]) -> List[str]:
        """
        Filter out any invalid symbols from a list.
        
        Args:
            symbols (List[str]): Symbols to validate
            
        Returns:
            List[str]: Valid symbols only
        """
        return [symbol for symbol in symbols if self.is_valid_symbol(symbol)]
    
    def ensure_target_in_list(self, symbols: List[str], target_symbol: str, max_count: int) -> List[str]:
        """
        Ensure a target symbol is included in a list, replacing one if necessary.
        
        Args:
            symbols (List[str]): Current symbol list
            target_symbol (str): Symbol that must be included
            max_count (int): Maximum symbols allowed
            
        Returns:
            List[str]: Symbol list with target included
        """
        if target_symbol in symbols:
            return symbols
        
        if len(symbols) < max_count:
            return symbols + [target_symbol]
        else:
            # Replace the first symbol with the target
            return [target_symbol] + symbols[1:]
    
    def get_symbol_display_name(self, symbol: str) -> str:
        """
        Get a display-friendly name for a symbol.
        
        Args:
            symbol (str): Symbol to get name for
            
        Returns:
            str: Display name (company name if available, otherwise symbol)
        """
        info = self.get_symbol_info(symbol)
        if info and 'name' in info:
            return f"{symbol} ({info['name']})"
        return symbol


# --- Convenience Functions ---

def create_symbol_manager() -> SymbolManager:
    """Create and return a new SymbolManager instance."""
    return SymbolManager()

def quick_random_selection(count: int, include_bonds: bool = True) -> List[str]:
    """
    Quick function to get random symbols without creating a manager instance.
    
    Args:
        count (int): Number of symbols to return
        include_bonds (bool): Whether to include bonds in selection
        
    Returns:
        List[str]: Random symbols
    """
    sm = SymbolManager()
    if include_bonds:
        return sm.get_random_symbols(count)
    else:
        return sm.get_random_stocks_and_etfs(count)

def validate_symbol_list(symbols: List[str]) -> tuple:
    """
    Validate a list of symbols.
    
    Args:
        symbols (List[str]): Symbols to validate
        
    Returns:
        tuple: (valid_symbols: List[str], invalid_symbols: List[str])
    """
    sm = SymbolManager()
    valid = []
    invalid = []
    
    for symbol in symbols:
        if sm.is_valid_symbol(symbol):
            valid.append(symbol)
        else:
            invalid.append(symbol)
    
    return valid, invalid

def get_sector_breakdown() -> Dict[str, List[str]]:
    """
    Get all symbols organized by sector.
    
    Returns:
        dict: Mapping of sector names to symbol lists
    """
    sm = SymbolManager()
    breakdown = {}
    
    for sector in sm.get_all_sectors():
        breakdown[sector] = sm.get_symbols_by_sector(sector)
    
    return breakdown