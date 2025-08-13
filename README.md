# Event-Driven Backtesting Platform

A TradingView-like backtesting platform with real-time event-driven simulation and interactive charts.

## Features

- **Event-Driven Backtesting Engine**: Real-time simulation of trading strategies
- **Interactive Charts**: TradingView-style charts with real-time updates
- **Trade Summary**: Comprehensive performance metrics and trade analysis
- **Strategy Editor**: Write and test custom trading strategies
- **Real-time Simulation**: Watch trades execute bar-by-bar
- **Multiple Timeframes**: Support for various chart timeframes
- **Performance Metrics**: Sharpe ratio, drawdown, win rate, and more

## Tech Stack

- **Backend**: Python FastAPI
- **Frontend**: React with TradingView Lightweight Charts
- **Real-time**: WebSocket for live updates
- **Data**: Pandas for historical data management
- **Charts**: TradingView Lightweight Charts library

## Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the backend:
```bash
python main.py
```

3. Open your browser to `http://localhost:8000`

## Project Structure

```
backtest-py/
├── backend/
│   ├── engine/           # Event-driven backtesting engine
│   ├── strategies/       # Strategy implementations
│   ├── data/            # Data fetching and management
│   └── api/             # FastAPI endpoints
├── frontend/
│   ├── src/
│   │   ├── components/  # React components
│   │   ├── charts/      # Chart implementations
│   │   └── utils/       # Utility functions
│   └── public/
└── main.py              # Main application entry point
```

## Usage

1. Select a symbol and timeframe
2. Write or select a trading strategy
3. Configure strategy parameters
4. Run the backtest
5. View real-time chart updates and trade execution
6. Analyze performance metrics and trade summary

## License

MIT 