"""
Data Manager for fetching and managing historical price data.
"""

import pandas as pd
import yfinance as yf
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import asyncio
import aiofiles
import json
import os


class DataManager:
    """
    Manages historical price data fetching and caching.
    """
    
    def __init__(self, cache_dir: str = "data_cache"):
        self.cache_dir = cache_dir
        self.cache = {}
        
        # Create cache directory if it doesn't exist
        os.makedirs(cache_dir, exist_ok=True)
    
    async def get_historical_data(self, symbol: str, period: str = "1y", 
                                 interval: str = "1d") -> pd.DataFrame:
        """
        Fetch historical data for a symbol.
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL', 'GOOGL')
            period: Data period ('1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max')
            interval: Data interval ('1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h', '1d', '5d', '1wk', '1mo', '3mo')
        
        Returns:
            DataFrame with OHLCV data
        """
        # Check cache first
        cache_key = f"{symbol}_{period}_{interval}"
        cached_data = await self._load_from_cache(cache_key)
        
        if cached_data is not None:
            return cached_data
        
        # Fetch from Yahoo Finance
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period, interval=interval)
            
            if data.empty:
                raise ValueError(f"No data found for symbol {symbol}")
            
            # Ensure proper column names
            data.columns = [col.title() for col in data.columns]
            
            # Cache the data
            await self._save_to_cache(cache_key, data)
            
            return data
            
        except Exception as e:
            raise Exception(f"Error fetching data for {symbol}: {str(e)}")
    
    async def get_data_for_backtest(self, symbol: str, start_date: str, 
                                   end_date: str, interval: str = "1d") -> pd.DataFrame:
        """
        Get data for a specific date range for backtesting.
        
        Args:
            symbol: Stock symbol
            start_date: Start date in 'YYYY-MM-DD' format
            end_date: End date in 'YYYY-MM-DD' format
            interval: Data interval
        
        Returns:
            DataFrame with OHLCV data
        """
        cache_key = f"{symbol}_{start_date}_{end_date}_{interval}"
        cached_data = await self._load_from_cache(cache_key)
        
        if cached_data is not None:
            return cached_data
        
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(start=start_date, end=end_date, interval=interval)
            
            if data.empty:
                raise ValueError(f"No data found for {symbol} from {start_date} to {end_date}")
            
            # Ensure proper column names
            data.columns = [col.title() for col in data.columns]
            
            # Cache the data
            await self._save_to_cache(cache_key, data)
            
            return data
            
        except Exception as e:
            raise Exception(f"Error fetching data for {symbol}: {str(e)}")
    
    async def get_available_symbols(self) -> List[str]:
        """Get a list of popular symbols for testing."""
        return [
            "AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "META", "NVDA", "NFLX",
            "SPY", "QQQ", "IWM", "GLD", "SLV", "USO", "TLT", "VTI"
        ]
    
    async def get_symbol_info(self, symbol: str) -> Dict:
        """Get basic information about a symbol."""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            return {
                'symbol': symbol,
                'name': info.get('longName', symbol),
                'sector': info.get('sector', 'Unknown'),
                'industry': info.get('industry', 'Unknown'),
                'market_cap': info.get('marketCap', 0),
                'current_price': info.get('currentPrice', 0)
            }
        except Exception as e:
            return {
                'symbol': symbol,
                'name': symbol,
                'sector': 'Unknown',
                'industry': 'Unknown',
                'market_cap': 0,
                'current_price': 0
            }
    
    async def _load_from_cache(self, cache_key: str) -> Optional[pd.DataFrame]:
        """Load data from cache."""
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.parquet")
        
        if os.path.exists(cache_file):
            try:
                # Check if cache is less than 24 hours old
                file_time = os.path.getmtime(cache_file)
                if datetime.now().timestamp() - file_time < 86400:  # 24 hours
                    return pd.read_parquet(cache_file)
            except Exception:
                pass
        
        return None
    
    async def _save_to_cache(self, cache_key: str, data: pd.DataFrame):
        """Save data to cache."""
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.parquet")
        
        try:
            data.to_parquet(cache_file)
        except Exception as e:
            print(f"Warning: Could not save to cache: {e}")
    
    def clear_cache(self):
        """Clear all cached data."""
        import shutil
        if os.path.exists(self.cache_dir):
            shutil.rmtree(self.cache_dir)
        os.makedirs(self.cache_dir, exist_ok=True)


# Sample data for testing when internet is not available
SAMPLE_DATA = {
    'AAPL': pd.DataFrame({
        'Open': [150.0, 151.0, 152.0, 149.0, 153.0, 154.0, 155.0, 156.0, 157.0, 158.0],
        'High': [152.0, 153.0, 154.0, 151.0, 155.0, 156.0, 157.0, 158.0, 159.0, 160.0],
        'Low': [149.0, 150.0, 151.0, 148.0, 152.0, 153.0, 154.0, 155.0, 156.0, 157.0],
        'Close': [151.0, 152.0, 153.0, 150.0, 154.0, 155.0, 156.0, 157.0, 158.0, 159.0],
        'Volume': [1000000, 1100000, 1200000, 900000, 1300000, 1400000, 1500000, 1600000, 1700000, 1800000]
    }, index=pd.date_range('2024-01-01', periods=10, freq='D'))
} 