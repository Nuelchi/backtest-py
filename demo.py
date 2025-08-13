"""
Demo script to test the Event-Driven Backtesting Platform.
"""

import asyncio
import pandas as pd
from datetime import datetime, timedelta
import numpy as np

from backend.engine.backtest_engine import BacktestEngine
from backend.strategies.moving_average_crossover import MovingAverageCrossover


def generate_sample_data(symbol: str = "AAPL", days: int = 100) -> pd.DataFrame:
    """Generate sample OHLCV data for testing."""
    np.random.seed(42)  # For reproducible results
    
    # Generate dates
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    
    # Generate price data with some trend and volatility
    base_price = 150.0
    prices = [base_price]
    
    for i in range(1, len(dates)):
        # Add some trend and random walk
        change = np.random.normal(0, 1.5) + 0.1  # Slight upward trend
        new_price = prices[-1] + change
        prices.append(max(new_price, 10))  # Ensure price doesn't go negative
    
    # Generate OHLCV data
    data = []
    for i, (date, close) in enumerate(zip(dates, prices)):
        # Generate realistic OHLC from close price
        volatility = np.random.uniform(0.5, 2.0)
        high = close + np.random.uniform(0, volatility)
        low = close - np.random.uniform(0, volatility)
        open_price = np.random.uniform(low, high)
        
        # Ensure OHLC relationship
        high = max(high, open_price, close)
        low = min(low, open_price, close)
        
        # Generate volume
        volume = np.random.randint(1000000, 5000000)
        
        data.append({
            'Open': open_price,
            'High': high,
            'Low': low,
            'Close': close,
            'Volume': volume
        })
    
    df = pd.DataFrame(data, index=dates)
    return df


async def run_demo():
    """Run a demo backtest."""
    print("🚀 Event-Driven Backtesting Platform Demo")
    print("=" * 50)
    
    # Generate sample data
    print("📊 Generating sample data...")
    data = generate_sample_data("AAPL", days=100)
    print(f"Generated {len(data)} days of data")
    print(f"Date range: {data.index[0].date()} to {data.index[-1].date()}")
    print(f"Price range: ${data['Low'].min():.2f} - ${data['High'].max():.2f}")
    print()
    
    # Create strategy
    print("🧠 Creating Moving Average Crossover strategy...")
    strategy = MovingAverageCrossover(
        fast_period=10,
        slow_period=20,
        symbol="AAPL"
    )
    
    # Create backtest engine
    print("⚙️ Initializing backtest engine...")
    engine = BacktestEngine(
        initial_capital=100000.0,
        commission=0.001
    )
    
    # Set strategy
    engine.set_strategy(strategy)
    
    # Run backtest
    print("🏃 Running backtest...")
    print("Processing bars:", end=" ")
    
    async def progress_callback(state):
        if state.get('bar'):
            print(".", end="", flush=True)
    
    engine.set_update_callback(progress_callback)
    
    await engine.run_backtest(data, delay=0.01)  # Fast simulation for demo
    
    print("\n✅ Backtest completed!")
    print()
    
    # Get results
    results = engine.get_performance_summary()
    
    # Display results
    print("📈 Performance Summary")
    print("=" * 30)
    print(f"Total Return: {results['total_return']*100:.2f}%")
    print(f"Annual Return: {results['annual_return']*100:.2f}%")
    print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
    print(f"Max Drawdown: {results['max_drawdown']*100:.2f}%")
    print(f"Total Trades: {results['total_trades']}")
    print(f"Win Rate: {results['win_rate']*100:.1f}%")
    print(f"Final Equity: ${results['final_equity']:,.2f}")
    print()
    
    # Show some trades
    if results['trades']:
        print("💼 Recent Trades")
        print("=" * 20)
        for trade in results['trades'][-5:]:  # Last 5 trades
            timestamp = trade['timestamp']
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            print(f"{timestamp.strftime('%Y-%m-%d %H:%M')} | "
                  f"{trade['side'].upper()} {trade['quantity']} @ ${trade['price']:.2f} | "
                  f"${trade['price'] * trade['quantity']:,.2f}")
    
    print()
    print("🎉 Demo completed! Open http://localhost:8000 to use the web interface.")


if __name__ == "__main__":
    asyncio.run(run_demo()) 