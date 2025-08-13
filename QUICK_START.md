# 🚀 Quick Start Guide

## Get Up and Running in 5 Minutes

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Test the Platform
```bash
python3 demo.py
```
This will run a quick demo with sample data to verify everything works.

### 3. Start the Web Server
```bash
python3 main.py
```

### 4. Open Your Browser
Navigate to: **http://localhost:8000**

## 🎮 Using the Platform

### Step 1: Configure Your Backtest
- **Symbol**: Choose from AAPL, GOOGL, MSFT, AMZN, TSLA, SPY
- **Strategy**: Select Moving Average Crossover, RSI, or Bollinger Bands
- **Date Range**: Set start and end dates
- **Capital**: Enter initial investment amount
- **Commission**: Set trading fees (default 0.1%)

### Step 2: Customize Strategy Parameters
Each strategy has configurable parameters:
- **MA Crossover**: Fast period (10), Slow period (20)
- **RSI**: Period (14), Oversold (30), Overbought (70)
- **Bollinger Bands**: Period (20), Standard deviation (2.0)

### Step 3: Run the Backtest
1. Click **"Start Backtest"**
2. Watch the real-time simulation
3. Observe trades executing on the chart
4. Monitor performance metrics in real-time

### Step 4: Analyze Results
- **Total Return**: Overall performance
- **Sharpe Ratio**: Risk-adjusted returns
- **Max Drawdown**: Largest peak-to-trough decline
- **Win Rate**: Percentage of profitable trades
- **Trade History**: Detailed list of all trades

## 🔧 Troubleshooting

### Common Issues

**Port already in use:**
```bash
# Kill existing process
lsof -ti:8000 | xargs kill -9
# Or use different port
python3 main.py --port 8001
```

**Data not loading:**
- Check internet connection (needed for Yahoo Finance)
- Try different symbols or date ranges
- Use the demo script for offline testing

**Charts not displaying:**
- Ensure JavaScript is enabled
- Check browser console for errors
- Try refreshing the page

## 📚 Next Steps

1. **Try Different Strategies**: Experiment with RSI and Bollinger Bands
2. **Adjust Parameters**: Fine-tune strategy settings
3. **Test Different Symbols**: Compare performance across stocks
4. **Extend the Platform**: Add your own strategies
5. **Learn More**: Study the code to understand event-driven backtesting

## 🎯 What You'll See

- **Real-time chart updates** as the backtest runs
- **Trade markers** showing buy/sell points
- **Performance metrics** updating live
- **Trade history** with timestamps and prices
- **Progress bar** showing completion status

## 🚀 Advanced Features

- **WebSocket real-time updates** for instant feedback
- **Professional TradingView charts** with zoom and pan
- **Multiple timeframe support** (daily data)
- **Commission and slippage simulation**
- **Realistic order execution** (market orders)

Enjoy exploring the world of event-driven backtesting! 🎉 