"""
FastAPI application for the backtesting platform.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import json
import asyncio
from datetime import datetime
import os
from fastapi.encoders import jsonable_encoder

from backend.engine.backtest_engine import BacktestEngine
from backend.data.data_manager import DataManager
from backend.strategies.moving_average_crossover import (
    MovingAverageCrossover, RSIStrategy, BollingerBandsStrategy
)
from backend.api.translate import router as translate_router


app = FastAPI(title="Event-Driven Backtesting Platform", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# Include routers
app.include_router(translate_router)

# Initialize data manager
data_manager = DataManager()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                pass

manager = ConnectionManager()

# Pydantic models
class BacktestRequest(BaseModel):
    symbol: str
    timeframe: str = "1d"
    strategy: str
    start_date: str
    end_date: str
    initial_capital: float = 100000.0
    commission: float = 0.001
    strategy_params: Dict[str, Any] = {}

class StrategyInfo(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Any]

# Available strategies
STRATEGIES = {
    "moving_average_crossover": {
        "name": "Moving Average Crossover",
        "description": "Buy when fast MA crosses above slow MA, sell when it crosses below",
        "parameters": {
            "fast_period": {"type": "int", "default": 10, "min": 1, "max": 50},
            "slow_period": {"type": "int", "default": 20, "min": 5, "max": 200}
        }
    },
    "rsi": {
        "name": "RSI Strategy",
        "description": "Buy when RSI crosses above oversold level, sell when it crosses below overbought",
        "parameters": {
            "period": {"type": "int", "default": 14, "min": 1, "max": 50},
            "oversold": {"type": "float", "default": 30.0, "min": 0, "max": 50},
            "overbought": {"type": "float", "default": 70.0, "min": 50, "max": 100}
        }
    },
    "bollinger_bands": {
        "name": "Bollinger Bands Strategy",
        "description": "Buy when price touches lower band, sell when it touches upper band",
        "parameters": {
            "period": {"type": "int", "default": 20, "min": 5, "max": 100},
            "std_dev": {"type": "float", "default": 2.0, "min": 0.5, "max": 5.0}
        }
    }
}

@app.get("/")
async def get_root():
    """Serve the main HTML page."""
    return FileResponse("frontend/index.html")

@app.get("/backtest")
async def get_backtest():
    """Serve the backtesting interface."""
    return FileResponse("frontend/index.html")

@app.get("/api/strategies")
async def get_strategies():
    """Get available trading strategies."""
    return {"strategies": STRATEGIES}

@app.get("/api/symbols")
async def get_symbols():
    """Get available symbols categorized by asset type."""
    symbols = await data_manager.get_available_symbols()
    return {"symbols": symbols}

@app.get("/api/symbol/{symbol}")
async def get_symbol_info(symbol: str):
    """Get information about a specific symbol."""
    info = await data_manager.get_symbol_info(symbol)
    return info

@app.post("/api/backtest")
async def start_backtest(request: BacktestRequest):
    """Start a new backtest."""
    try:
        # Get historical data
        data = await data_manager.get_data_for_backtest(
            request.symbol, 
            request.start_date, 
            request.end_date,
            request.timeframe
        )
        
        # Create strategy instance
        strategy = None
        if request.strategy == "moving_average_crossover":
            params = request.strategy_params
            strategy = MovingAverageCrossover(
                fast_period=params.get("fast_period", 10),
                slow_period=params.get("slow_period", 20),
                symbol=request.symbol
            )
        elif request.strategy == "rsi":
            params = request.strategy_params
            strategy = RSIStrategy(
                period=params.get("period", 14),
                oversold=params.get("oversold", 30),
                overbought=params.get("overbought", 70),
                symbol=request.symbol
            )
        elif request.strategy == "bollinger_bands":
            params = request.strategy_params
            strategy = BollingerBandsStrategy(
                period=params.get("period", 20),
                std_dev=params.get("std_dev", 2.0),
                symbol=request.symbol
            )
        else:
            raise HTTPException(status_code=400, detail="Unknown strategy")
        
        # Create backtest engine
        engine = BacktestEngine(
            initial_capital=request.initial_capital,
            commission=request.commission
        )
        
        # Set strategy
        engine.set_strategy(strategy)
        
        # Run backtest
        await engine.run_backtest(data, delay=0.05)
        
        # Get performance summary
        try:
            summary = engine.get_performance_summary()
            
            # Ensure all values are JSON serializable
            summary = jsonable_encoder(summary)
            
            return {
                "status": "completed",
                "summary": summary,
                "data_points": len(data)
            }
        except Exception as e:
            print(f"Error serializing performance summary: {e}")
            # Return safe fallback
            return {
                "status": "completed",
                "summary": {
                    "total_return": 0.0,
                    "annual_return": 0.0,
                    "volatility": 0.0,
                    "sharpe_ratio": 0.0,
                    "max_drawdown": 0.0,
                    "total_trades": 0,
                    "winning_trades": 0,
                    "win_rate": 0.0,
                    "final_equity": request.initial_capital,
                    "peak_equity": request.initial_capital,
                    "equity_curve": [],
                    "trades": []
                },
                "data_points": len(data)
            }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/backtest")
async def websocket_backtest(websocket: WebSocket):
    """WebSocket endpoint for real-time backtest updates."""
    await manager.connect(websocket)
    
    try:
        while True:
            # Wait for backtest request
            data = await websocket.receive_text()
            request_data = json.loads(data)
            
            # Start backtest with real-time updates
            await run_realtime_backtest(websocket, request_data)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)

async def run_realtime_backtest(websocket: WebSocket, request_data: Dict):
    """Run backtest with real-time WebSocket updates."""
    try:
        # Get historical data
        data = await data_manager.get_data_for_backtest(
            request_data["symbol"],
            request_data["start_date"],
            request_data["end_date"],
            request_data.get("timeframe", "1d")
        )
        
        # Create strategy
        strategy = None
        if request_data["strategy"] == "moving_average_crossover":
            params = request_data.get("strategy_params", {})
            strategy = MovingAverageCrossover(
                fast_period=params.get("fast_period", 10),
                slow_period=params.get("slow_period", 20),
                symbol=request_data["symbol"]
            )
        elif request_data["strategy"] == "rsi":
            params = request_data.get("strategy_params", {})
            strategy = RSIStrategy(
                period=params.get("period", 14),
                oversold=params.get("oversold", 30),
                overbought=params.get("overbought", 70),
                symbol=request_data["symbol"]
            )
        elif request_data["strategy"] == "bollinger_bands":
            params = request_data.get("strategy_params", {})
            strategy = BollingerBandsStrategy(
                period=params.get("period", 20),
                std_dev=params.get("std_dev", 2.0),
                symbol=request_data["symbol"]
            )
        
        # Create engine
        engine = BacktestEngine(
            initial_capital=request_data.get("initial_capital", 100000.0),
            commission=request_data.get("commission", 0.001)
        )
        
        # Set strategy
        engine.set_strategy(strategy)
        
        # Set update callback
        async def update_callback(state):
            # Ensure JSON serializable
            state = jsonable_encoder(state)
            await websocket.send_text(json.dumps({
                "type": "update",
                "data": state
            }))
        
        engine.set_update_callback(update_callback)
        
        # Send initial data
        await websocket.send_text(json.dumps({
            "type": "start",
            "data": {
                "total_bars": len(data),
                "symbol": request_data["symbol"],
                "strategy": request_data["strategy"]
            }
        }))
        
        # Run backtest
        await engine.run_backtest(data, delay=0.03)
        
        # Send final summary
        try:
            summary = engine.get_performance_summary()
            # Ensure JSON serializable
            summary = jsonable_encoder(summary)
            await websocket.send_text(json.dumps({
                "type": "complete",
                "data": summary
            }))
        except Exception as e:
            print(f"Error serializing WebSocket summary: {e}")
            # Send safe fallback
            await websocket.send_text(json.dumps({
                "type": "complete",
                "data": {
                    "total_return": 0.0,
                    "annual_return": 0.0,
                    "volatility": 0.0,
                    "sharpe_ratio": 0.0,
                    "max_drawdown": 0.0,
                    "total_trades": 0,
                    "winning_trades": 0,
                    "win_rate": 0.0,
                    "final_equity": request_data.get("initial_capital", 100000.0),
                    "peak_equity": request_data.get("initial_capital", 100000.0),
                    "equity_curve": [],
                    "trades": []
                }
            }))
        
    except Exception as e:
        await websocket.send_text(json.dumps({
            "type": "error",
            "data": {"message": str(e)}
        }))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 