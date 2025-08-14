"""
Event-driven backtesting engine that simulates real-time trading.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import asyncio
from enum import Enum


class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"


class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"


@dataclass
class Order:
    id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    price: Optional[float] = None
    stop_price: Optional[float] = None
    timestamp: datetime = None
    filled: bool = False
    filled_price: Optional[float] = None
    filled_quantity: float = 0.0


@dataclass
class Trade:
    id: str
    symbol: str
    side: OrderSide
    quantity: float
    price: float
    timestamp: datetime
    order_id: str
    commission: float = 0.0


@dataclass
class Position:
    symbol: str
    quantity: float = 0.0
    avg_price: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0


@dataclass
class Bar:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


class BacktestEngine:
    """
    Event-driven backtesting engine that processes data bar-by-bar
    and simulates realistic trading conditions.
    """
    
    def __init__(self, initial_capital: float = 100000.0, commission: float = 0.001):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.commission = commission
        
        # State tracking
        self.positions: Dict[str, Position] = {}
        self.orders: List[Order] = []
        self.trades: List[Trade] = []
        self.equity_curve: List[Dict] = []
        
        # Strategy callback
        self.strategy_callback: Optional[Callable] = None
        
        # Real-time update callback
        self.update_callback: Optional[Callable] = None
        
        # Current bar data
        self.current_bar: Optional[Bar] = None
        self.current_index: int = 0
        
        # Performance tracking
        self.peak_equity = initial_capital
        self.max_drawdown = 0.0
        self.total_trades = 0
        self.winning_trades = 0
        
    def set_strategy(self, strategy_callback: Callable):
        """Set the strategy function to be called on each bar."""
        self.strategy_callback = strategy_callback
    
    def set_update_callback(self, update_callback: Callable):
        """Set callback for real-time updates during backtesting."""
        self.update_callback = update_callback
    
    def place_order(self, symbol: str, side: OrderSide, quantity: float, 
                   order_type: OrderType = OrderType.MARKET, 
                   price: Optional[float] = None,
                   stop_price: Optional[float] = None) -> str:
        """Place a new order."""
        order_id = f"order_{len(self.orders)}_{datetime.now().timestamp()}"
        
        order = Order(
            id=order_id,
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            stop_price=stop_price,
            timestamp=self.current_bar.timestamp if self.current_bar else datetime.now()
        )
        
        self.orders.append(order)
        return order_id
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel an existing order."""
        for i, order in enumerate(self.orders):
            if order.id == order_id and not order.filled:
                self.orders.pop(i)
                return True
        return False
    
    def get_position(self, symbol: str) -> Position:
        """Get current position for a symbol."""
        return self.positions.get(symbol, Position(symbol=symbol))
    
    def get_equity(self) -> float:
        """Calculate current equity including unrealized P&L."""
        equity = self.capital
        for position in self.positions.values():
            if position.quantity != 0:
                # Calculate unrealized P&L based on current price
                if self.current_bar:
                    current_price = self.current_bar.close
                    position.unrealized_pnl = (current_price - position.avg_price) * position.quantity
                    equity += position.unrealized_pnl
        return equity
    
    def _process_orders(self, bar: Bar):
        """Process pending orders against current bar."""
        orders_to_remove = []
        
        for order in self.orders:
            if order.filled:
                continue
                
            filled = False
            fill_price = 0.0
            
            if order.order_type == OrderType.MARKET:
                # Market orders are filled at current price
                fill_price = bar.close
                filled = True
                
            elif order.order_type == OrderType.LIMIT:
                if order.side == OrderSide.BUY and bar.low <= order.price:
                    fill_price = min(order.price, bar.close)
                    filled = True
                elif order.side == OrderSide.SELL and bar.high >= order.price:
                    fill_price = max(order.price, bar.close)
                    filled = True
                    
            elif order.order_type == OrderType.STOP:
                if order.side == OrderSide.BUY and bar.high >= order.stop_price:
                    fill_price = max(order.stop_price, bar.open)
                    filled = True
                elif order.side == OrderSide.SELL and bar.low <= order.stop_price:
                    fill_price = min(order.stop_price, bar.open)
                    filled = True
            
            if filled:
                self._execute_trade(order, fill_price, bar.timestamp)
                orders_to_remove.append(order)
        
        # Remove filled orders
        for order in orders_to_remove:
            self.orders.remove(order)
    
    def _execute_trade(self, order: Order, fill_price: float, timestamp: datetime):
        """Execute a trade from a filled order."""
        # Calculate commission
        commission = abs(order.quantity * fill_price * self.commission)
        
        # Create trade record
        trade = Trade(
            id=f"trade_{len(self.trades)}_{timestamp.timestamp()}",
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            price=fill_price,
            timestamp=timestamp,
            order_id=order.id,
            commission=commission
        )
        
        self.trades.append(trade)
        
        # Update position
        if order.symbol not in self.positions:
            self.positions[order.symbol] = Position(symbol=order.symbol)
        
        position = self.positions[order.symbol]
        
        if order.side == OrderSide.BUY:
            # Calculate new average price
            total_cost = position.quantity * position.avg_price + order.quantity * fill_price
            position.quantity += order.quantity
            position.avg_price = total_cost / position.quantity if position.quantity > 0 else 0
            
            # Update capital
            self.capital -= (order.quantity * fill_price + commission)
            
        else:  # SELL
            # Calculate realized P&L
            if position.quantity > 0:
                realized_pnl = (fill_price - position.avg_price) * min(order.quantity, position.quantity)
                position.realized_pnl += realized_pnl
                self.capital += realized_pnl
            
            position.quantity -= order.quantity
            if position.quantity <= 0:
                position.quantity = 0
                position.avg_price = 0
            
            # Update capital
            self.capital += (order.quantity * fill_price - commission)
        
        # Mark order as filled
        order.filled = True
        order.filled_price = fill_price
        order.filled_quantity = order.quantity
        
        # Update statistics
        self.total_trades += 1
        if trade.side == OrderSide.SELL and position.realized_pnl > 0:
            self.winning_trades += 1
    
    def _update_performance_metrics(self):
        """Update performance metrics after each bar."""
        equity = self.get_equity()
        
        # Update peak equity and drawdown
        if equity > self.peak_equity:
            self.peak_equity = equity
        
        current_drawdown = (self.peak_equity - equity) / self.peak_equity
        if current_drawdown > self.max_drawdown:
            self.max_drawdown = current_drawdown
        
        # Record equity curve
        self.equity_curve.append({
            'timestamp': self.current_bar.timestamp.isoformat() if hasattr(self.current_bar.timestamp, 'isoformat') else str(self.current_bar.timestamp),
            'equity': float(equity),
            'capital': float(self.capital),
            'drawdown': float(current_drawdown)
        })
    
    async def run_backtest(self, data: pd.DataFrame, delay: float = 0.1):
        """
        Run the backtest on historical data with real-time simulation.
        
        Args:
            data: DataFrame with OHLCV data
            delay: Delay between bars in seconds for real-time simulation
        """
        # Reset state
        self.capital = self.initial_capital
        self.positions.clear()
        self.orders.clear()
        self.trades.clear()
        self.equity_curve.clear()
        self.peak_equity = self.initial_capital
        self.max_drawdown = 0.0
        self.total_trades = 0
        self.winning_trades = 0
        
        # Convert DataFrame to Bar objects
        bars = []
        for _, row in data.iterrows():
            bar = Bar(
                timestamp=row.name if hasattr(row, 'name') else datetime.now(),
                open=row['Open'],
                high=row['High'],
                low=row['Low'],
                close=row['Close'],
                volume=row.get('Volume', 0)
            )
            bars.append(bar)
        
        # Process each bar
        for i, bar in enumerate(bars):
            self.current_bar = bar
            self.current_index = i
            
            # Process pending orders
            self._process_orders(bar)
            
            # Call strategy function
            if self.strategy_callback:
                try:
                    self.strategy_callback(self, bar)
                except Exception as e:
                    print(f"Strategy callback error: {e}")
                    # Continue with backtest even if strategy fails
            
            # Update performance metrics
            self._update_performance_metrics()
            
            # Send real-time update
            if self.update_callback:
                await self.update_callback(self._get_current_state())
            
            # Add delay for real-time simulation
            if delay > 0:
                await asyncio.sleep(delay)
    
    def _get_current_state(self) -> Dict:
        """Get current state for real-time updates."""
        return {
            'timestamp': self.current_bar.timestamp.isoformat() if self.current_bar else None,
            'bar': {
                'open': float(self.current_bar.open),
                'high': float(self.current_bar.high),
                'low': float(self.current_bar.low),
                'close': float(self.current_bar.close),
                'volume': float(self.current_bar.volume)
            } if self.current_bar else None,
            'equity': float(self.get_equity()),
            'capital': float(self.capital),
            'positions': {str(symbol): {
                'quantity': float(pos.quantity),
                'avg_price': float(pos.avg_price),
                'unrealized_pnl': float(pos.unrealized_pnl),
                'realized_pnl': float(pos.realized_pnl)
            } for symbol, pos in self.positions.items()},
            'orders': [{
                'id': str(order.id),
                'symbol': str(order.symbol),
                'side': str(order.side.value),
                'quantity': float(order.quantity),
                'filled': bool(order.filled)
            } for order in self.orders],
            'trades': [{
                'timestamp': trade.timestamp.isoformat() if hasattr(trade.timestamp, 'isoformat') else str(trade.timestamp),
                'symbol': str(trade.symbol),
                'side': str(trade.side.value),
                'quantity': float(trade.quantity),
                'price': float(trade.price),
                'commission': float(trade.commission)
            } for trade in self.trades[-10:]]  # Last 10 trades
        }
    
    def get_performance_summary(self) -> Dict:
        """Get comprehensive performance summary."""
        try:
            if not self.equity_curve:
                return {}
            
            equity_series = pd.Series([e['equity'] for e in self.equity_curve])
            returns = equity_series.pct_change().dropna()
            
            # Calculate metrics with safe conversion
            final_equity = float(equity_series.iloc[-1]) if len(equity_series) > 0 else float(self.initial_capital)
            total_return = float((final_equity - self.initial_capital) / self.initial_capital)
            annual_return = float(total_return * (252 / len(equity_series))) if len(equity_series) > 1 else 0.0
            volatility = float(returns.std() * np.sqrt(252)) if len(returns) > 1 else 0.0
            sharpe_ratio = float(annual_return / volatility if volatility > 0 else 0.0)
            win_rate = float(self.winning_trades / self.total_trades if self.total_trades > 0 else 0.0)
            
            # Safely convert equity curve data
            safe_equity_curve = []
            for e in self.equity_curve:
                try:
                    safe_equity_curve.append({
                        'timestamp': str(e['timestamp']),
                        'equity': float(e['equity']),
                        'capital': float(e['capital']),
                        'drawdown': float(e['drawdown'])
                    })
                except Exception as e:
                    print(f"Error processing equity curve entry: {e}")
                    continue
            
            # Safely convert trades data
            safe_trades = []
            for trade in self.trades:
                try:
                    safe_trades.append({
                        'timestamp': trade.timestamp.isoformat() if hasattr(trade.timestamp, 'isoformat') else str(trade.timestamp),
                        'symbol': str(trade.symbol),
                        'side': str(trade.side.value),
                        'quantity': float(trade.quantity),
                        'price': float(trade.price),
                        'commission': float(trade.commission)
                    })
                except Exception as e:
                    print(f"Error processing trade: {e}")
                    continue
            
            return {
                'total_return': total_return,
                'annual_return': annual_return,
                'volatility': volatility,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': float(self.max_drawdown),
                'total_trades': int(self.total_trades),
                'winning_trades': int(self.winning_trades),
                'win_rate': win_rate,
                'final_equity': final_equity,
                'peak_equity': float(self.peak_equity),
                'equity_curve': safe_equity_curve,
                'trades': safe_trades
            }
        except Exception as e:
            print(f"Error in get_performance_summary: {e}")
            # Return safe fallback data
            return {
                'total_return': 0.0,
                'annual_return': 0.0,
                'volatility': 0.0,
                'sharpe_ratio': 0.0,
                'max_drawdown': 0.0,
                'total_trades': 0,
                'winning_trades': 0,
                'win_rate': 0.0,
                'final_equity': float(self.initial_capital),
                'peak_equity': float(self.initial_capital),
                'equity_curve': [],
                'trades': []
            } 