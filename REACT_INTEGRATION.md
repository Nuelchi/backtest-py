# React Integration Guide

## 🚀 **How to Integrate with Your React App**

### **Option 1: API Integration (Recommended)**

Your React app can call the Python backend APIs directly. This is the cleanest approach.

#### **1. Create API Client**

```javascript
// api/backtestAPI.js
class BacktestAPI {
    constructor(baseURL = 'http://localhost:8000') {
        this.baseURL = baseURL;
        this.websocket = null;
    }

    // Get available strategies
    async getStrategies() {
        const response = await fetch(`${this.baseURL}/api/strategies`);
        return await response.json();
    }

    // Get available symbols
    async getSymbols() {
        const response = await fetch(`${this.baseURL}/api/symbols`);
        return await response.json();
    }

    // Run backtest (non-realtime)
    async runBacktest(config) {
        const response = await fetch(`${this.baseURL}/api/backtest`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config)
        });
        return await response.json();
    }

    // Start realtime backtest with WebSocket
    startRealtimeBacktest(config, callbacks) {
        const wsUrl = this.baseURL.replace('http', 'ws') + '/ws/backtest';
        this.websocket = new WebSocket(wsUrl);

        this.websocket.onopen = () => {
            this.websocket.send(JSON.stringify(config));
        };

        this.websocket.onmessage = (event) => {
            const message = JSON.parse(event.data);
            switch (message.type) {
                case 'start': callbacks.onStart?.(message.data); break;
                case 'update': callbacks.onUpdate?.(message.data); break;
                case 'complete': callbacks.onComplete?.(message.data); break;
                case 'error': callbacks.onError?.(message.data); break;
            }
        };
    }

    stopRealtimeBacktest() {
        if (this.websocket) {
            this.websocket.close();
            this.websocket = null;
        }
    }
}

export default BacktestAPI;
```

#### **2. React Component Example**

```jsx
// components/BacktestChart.jsx
import React, { useState, useEffect, useRef } from 'react';
import BacktestAPI from '../api/backtestAPI';

const BacktestChart = () => {
    const [strategies, setStrategies] = useState({});
    const [symbols, setSymbols] = useState([]);
    const [isRunning, setIsRunning] = useState(false);
    const [results, setResults] = useState(null);
    const chartRef = useRef(null);
    const api = new BacktestAPI();

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        const [strategiesData, symbolsData] = await Promise.all([
            api.getStrategies(),
            api.getSymbols()
        ]);
        setStrategies(strategiesData.strategies);
        setSymbols(symbolsData.symbols);
    };

    const startBacktest = () => {
        const config = {
            symbol: 'AAPL',
            strategy: 'moving_average_crossover',
            start_date: '2023-01-01',
            end_date: '2024-01-01',
            initial_capital: 100000,
            commission: 0.001,
            strategy_params: { fast_period: 10, slow_period: 20 }
        };

        setIsRunning(true);
        api.startRealtimeBacktest(config, {
            onStart: (data) => console.log('Backtest started:', data),
            onUpdate: (data) => updateChart(data),
            onComplete: (data) => {
                setResults(data);
                setIsRunning(false);
            },
            onError: (error) => {
                console.error('Backtest error:', error);
                setIsRunning(false);
            }
        });
    };

    const updateChart = (data) => {
        // Update your chart with real-time data
        if (data.bar && chartRef.current) {
            // Add candlestick data to your chart
            // This depends on your charting library
        }
    };

    return (
        <div>
            <h2>Backtesting Platform</h2>
            <button onClick={startBacktest} disabled={isRunning}>
                {isRunning ? 'Running...' : 'Start Backtest'}
            </button>
            <div ref={chartRef} style={{ height: '400px' }}>
                {/* Your chart component here */}
            </div>
            {results && (
                <div>
                    <h3>Results</h3>
                    <p>Total Return: {(results.total_return * 100).toFixed(2)}%</p>
                    <p>Sharpe Ratio: {results.sharpe_ratio.toFixed(2)}</p>
                    <p>Max Drawdown: {(results.max_drawdown * 100).toFixed(2)}%</p>
                </div>
            )}
        </div>
    );
};

export default BacktestChart;
```

### **Option 2: Embed as iframe**

```jsx
// components/BacktestIframe.jsx
const BacktestIframe = () => {
    return (
        <iframe 
            src="http://localhost:8000"
            width="100%"
            height="800px"
            style={{ border: 'none' }}
            title="Backtesting Platform"
        />
    );
};
```

### **Option 3: Extract Frontend Components**

You can extract the chart and UI components from the current frontend and use them in React.

## 🌐 **Deployment Options**

### **1. Local Development**
- Run Python backend: `python3 main.py`
- Your React app calls `http://localhost:8000`

### **2. Production Deployment**

#### **Backend Deployment (Python)**
```bash
# Deploy to Heroku, Railway, or any Python hosting
pip install -r requirements.txt
python3 main.py
```

#### **Frontend Deployment (React)**
```bash
# Deploy React app to Vercel, Netlify, etc.
npm run build
```

#### **CORS Configuration**
Update the backend to allow your React domain:

```python
# backend/api/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-react-app.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### **3. Docker Deployment**

```dockerfile
# Dockerfile
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python3", "main.py"]
```

## 🔧 **Environment Configuration**

### **React App (.env)**
```env
REACT_APP_BACKTEST_API_URL=http://localhost:8000
REACT_APP_BACKTEST_API_URL_PROD=https://your-backend.herokuapp.com
```

### **Python Backend (.env)**
```env
ALLOWED_ORIGINS=https://your-react-app.vercel.app
PORT=8000
```

## 📊 **Chart Integration**

### **With TradingView Lightweight Charts**
```jsx
import { createChart } from 'lightweight-charts';

const ChartComponent = () => {
    const chartRef = useRef(null);
    const chart = useRef(null);

    useEffect(() => {
        if (chartRef.current) {
            chart.current = createChart(chartRef.current, {
                width: 800,
                height: 400,
                layout: { background: { color: '#1e222d' } }
            });
        }
    }, []);

    const updateChart = (data) => {
        if (chart.current && data.bar) {
            const candleSeries = chart.current.addCandlestickSeries();
            candleSeries.update({
                time: new Date(data.timestamp).getTime() / 1000,
                open: data.bar.open,
                high: data.bar.high,
                low: data.bar.low,
                close: data.bar.close
            });
        }
    };

    return <div ref={chartRef} />;
};
```

## 🎯 **Key Benefits**

1. **Separation of Concerns**: Python handles data processing, React handles UI
2. **Scalability**: Can deploy backend and frontend separately
3. **Flexibility**: Use any React charting library
4. **Real-time Updates**: WebSocket integration for live data
5. **Professional UI**: Leverage React's component ecosystem

## 🚀 **Quick Start**

1. **Start Python Backend**: `python3 main.py`
2. **Create React API Client**: Copy the API client code
3. **Add Chart Component**: Integrate with your preferred charting library
4. **Test Integration**: Run your React app and test the backtesting features

The Python backend will run as a service that your React app can call via HTTP/WebSocket APIs! 