"""
Moving Average Crossover Strategy

A simple strategy that generates buy/sell signals based on the crossover
of two moving averages.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any
from backend.engine.backtest_engine import BacktestEngine, OrderSide, OrderType, Bar


class MovingAverageCrossover:
    """
    Moving Average Crossover Strategy
    
    Generates buy signals when fast MA crosses above slow MA
    Generates sell signals when fast MA crosses below slow MA
    """
    
    def __init__(self, fast_period: int = 10, slow_period: int = 20, symbol: str = "AAPL"):
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.symbol = symbol
        
        # Strategy state
        self.fast_ma_values = []
        self.slow_ma_values = []
        self.position = 0  # 1 for long, -1 for short, 0 for flat
        
    def calculate_indicators(self, data: pd.DataFrame) -> Dict[str, pd.Series]:
        """Calculate technical indicators for the strategy."""
        close_prices = data['Close']
        
        # Calculate moving averages
        fast_ma = close_prices.rolling(window=self.fast_period).mean()
        slow_ma = close_prices.rolling(window=self.slow_period).mean()
        
        return {
            'fast_ma': fast_ma,
            'slow_ma': slow_ma
        }
    
    def __call__(self, engine: BacktestEngine, bar: Bar):
        """
        Strategy logic called on each bar.
        
        Args:
            engine: The backtesting engine instance
            bar: Current price bar
        """
        # Store current MA values
        self.fast_ma_values.append(bar.close)
        self.slow_ma_values.append(bar.close)
        
        # Need enough data for both MAs
        if len(self.fast_ma_values) < self.slow_period:
            return
        
        # Calculate current MAs
        fast_ma = np.mean(self.fast_ma_values[-self.fast_period:])
        slow_ma = np.mean(self.slow_ma_values[-self.slow_period:])
        
        # Previous MAs (for crossover detection)
        if len(self.fast_ma_values) > self.fast_period:
            prev_fast_ma = np.mean(self.fast_ma_values[-self.fast_period-1:-1])
        else:
            prev_fast_ma = fast_ma
            
        if len(self.slow_ma_values) > self.slow_period:
            prev_slow_ma = np.mean(self.slow_ma_values[-self.slow_period-1:-1])
        else:
            prev_slow_ma = slow_ma
        
        # Check for crossovers
        fast_crossed_above = prev_fast_ma <= prev_slow_ma and fast_ma > slow_ma
        fast_crossed_below = prev_fast_ma >= prev_slow_ma and fast_ma < slow_ma
        
        # Get current position
        position = engine.get_position(self.symbol)
        
        # Trading logic
        if fast_crossed_above and self.position <= 0:
            # Buy signal
            if position.quantity < 0:
                # Close short position first
                engine.place_order(
                    symbol=self.symbol,
                    side=OrderSide.BUY,
                    quantity=abs(position.quantity),
                    order_type=OrderType.MARKET
                )
            
            # Calculate position size (use 95% of available capital)
            available_capital = engine.capital * 0.95
            quantity = int(available_capital / bar.close)
            
            if quantity > 0:
                engine.place_order(
                    symbol=self.symbol,
                    side=OrderSide.BUY,
                    quantity=quantity,
                    order_type=OrderType.MARKET
                )
                self.position = 1
                
        elif fast_crossed_below and self.position >= 0:
            # Sell signal
            if position.quantity > 0:
                # Close long position
                engine.place_order(
                    symbol=self.symbol,
                    side=OrderSide.SELL,
                    quantity=position.quantity,
                    order_type=OrderType.MARKET
                )
                self.position = -1
                
        # Update position tracker
        if position.quantity > 0:
            self.position = 1
        elif position.quantity < 0:
            self.position = -1
        else:
            self.position = 0


class RSIStrategy:
    """
    RSI (Relative Strength Index) Strategy
    
    Generates buy signals when RSI crosses above oversold level
    Generates sell signals when RSI crosses below overbought level
    """
    
    def __init__(self, period: int = 14, oversold: float = 30, overbought: float = 70, symbol: str = "AAPL"):
        self.period = period
        self.oversold = oversold
        self.overbought = overbought
        self.symbol = symbol
        
        # Strategy state
        self.prices = []
        self.position = 0
        
    def calculate_rsi(self, prices: list, period: int) -> float:
        """Calculate RSI for given prices."""
        if len(prices) < period + 1:
            return 50.0  # Neutral RSI
        
        deltas = np.diff(prices[-period-1:])
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains)
        avg_loss = np.mean(losses)
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def __call__(self, engine: BacktestEngine, bar: Bar):
        """Strategy logic called on each bar."""
        self.prices.append(bar.close)
        
        # Need enough data for RSI calculation
        if len(self.prices) < self.period + 1:
            return
        
        # Calculate RSI
        current_rsi = self.calculate_rsi(self.prices, self.period)
        
        # Previous RSI
        if len(self.prices) > self.period + 1:
            prev_rsi = self.calculate_rsi(self.prices[:-1], self.period)
        else:
            prev_rsi = current_rsi
        
        # Get current position
        position = engine.get_position(self.symbol)
        
        # Trading logic
        rsi_crossed_above_oversold = prev_rsi <= self.oversold and current_rsi > self.oversold
        rsi_crossed_below_overbought = prev_rsi >= self.overbought and current_rsi < self.overbought
        
        if rsi_crossed_above_oversold and self.position <= 0:
            # Buy signal
            if position.quantity < 0:
                # Close short position first
                engine.place_order(
                    symbol=self.symbol,
                    side=OrderSide.BUY,
                    quantity=abs(position.quantity),
                    order_type=OrderType.MARKET
                )
            
            # Calculate position size
            available_capital = engine.capital * 0.95
            quantity = int(available_capital / bar.close)
            
            if quantity > 0:
                engine.place_order(
                    symbol=self.symbol,
                    side=OrderSide.BUY,
                    quantity=quantity,
                    order_type=OrderType.MARKET
                )
                self.position = 1
                
        elif rsi_crossed_below_overbought and self.position >= 0:
            # Sell signal
            if position.quantity > 0:
                engine.place_order(
                    symbol=self.symbol,
                    side=OrderSide.SELL,
                    quantity=position.quantity,
                    order_type=OrderType.MARKET
                )
                self.position = -1
        
        # Update position tracker
        if position.quantity > 0:
            self.position = 1
        elif position.quantity < 0:
            self.position = -1
        else:
            self.position = 0


class BollingerBandsStrategy:
    """
    Bollinger Bands Strategy
    
    Generates buy signals when price touches lower band
    Generates sell signals when price touches upper band
    """
    
    def __init__(self, period: int = 20, std_dev: float = 2.0, symbol: str = "AAPL"):
        self.period = period
        self.std_dev = std_dev
        self.symbol = symbol
        
        # Strategy state
        self.prices = []
        self.position = 0
        
    def calculate_bollinger_bands(self, prices: list, period: int, std_dev: float) -> tuple:
        """Calculate Bollinger Bands."""
        if len(prices) < period:
            return None, None, None
        
        recent_prices = prices[-period:]
        sma = np.mean(recent_prices)
        std = np.std(recent_prices)
        
        upper_band = sma + (std_dev * std)
        lower_band = sma - (std_dev * std)
        
        return upper_band, sma, lower_band
    
    def __call__(self, engine: BacktestEngine, bar: Bar):
        """Strategy logic called on each bar."""
        self.prices.append(bar.close)
        
        # Need enough data for Bollinger Bands calculation
        if len(self.prices) < self.period:
            return
        
        # Calculate Bollinger Bands
        upper, middle, lower = self.calculate_bollinger_bands(self.prices, self.period, self.std_dev)
        
        if upper is None:
            return
        
        # Get current position
        position = engine.get_position(self.symbol)
        
        # Trading logic
        price_touches_lower = bar.low <= lower
        price_touches_upper = bar.high >= upper
        
        if price_touches_lower and self.position <= 0:
            # Buy signal
            if position.quantity < 0:
                # Close short position first
                engine.place_order(
                    symbol=self.symbol,
                    side=OrderSide.BUY,
                    quantity=abs(position.quantity),
                    order_type=OrderType.MARKET
                )
            
            # Calculate position size
            available_capital = engine.capital * 0.95
            quantity = int(available_capital / bar.close)
            
            if quantity > 0:
                engine.place_order(
                    symbol=self.symbol,
                    side=OrderSide.BUY,
                    quantity=quantity,
                    order_type=OrderType.MARKET
                )
                self.position = 1
                
        elif price_touches_upper and self.position >= 0:
            # Sell signal
            if position.quantity > 0:
                engine.place_order(
                    symbol=self.symbol,
                    side=OrderSide.SELL,
                    quantity=position.quantity,
                    order_type=OrderType.MARKET
                )
                self.position = -1
        
        # Update position tracker
        if position.quantity > 0:
            self.position = 1
        elif position.quantity < 0:
            self.position = -1
        else:
            self.position = 0 