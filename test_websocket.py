#!/usr/bin/env python3
"""
Test WebSocket backtest with custom Python strategy
"""

import asyncio
import websockets
import json

async def test_websocket_backtest():
    uri = "ws://localhost:8001/ws/backtest"
    
    async with websockets.connect(uri) as websocket:
        print("🔄 Connected to WebSocket")
        
        # Test data for custom Python strategy
        test_data = {
            "symbol": "AAPL",
            "timeframe": "4h",
            "strategy": "custom_python",
            "start_date": "2024-01-01",
            "end_date": "2024-01-31",
            "initial_capital": 100000,
            "commission": 0.001,
            "strategy_params": {
                "python_code": """from backend.engine.backtest_engine import OrderSide, OrderType

class Strategy:
    def __init__(self):
        self.prices = []
        self.ma_period = 20
    
    def __call__(self, engine, bar):
        self.prices.append(bar.close)
        
        if len(self.prices) >= self.ma_period:
            ma = sum(self.prices[-self.ma_period:]) / self.ma_period
            
            if bar.close > ma:
                position = engine.get_position("AAPL").quantity
                if position <= 0:
                    engine.place_order("AAPL", OrderSide.BUY, 1, OrderType.MARKET)
                    print(f"BUY order placed at {bar.close}")
            elif bar.close < ma:
                position = engine.get_position("AAPL").quantity
                if position > 0:
                    engine.place_order("AAPL", OrderSide.SELL, 1, OrderType.MARKET)
                    print(f"SELL order placed at {bar.close}")"""
            }
        }
        
        print("📤 Sending backtest request...")
        await websocket.send(json.dumps(test_data))
        
        # Listen for responses
        try:
            while True:
                response = await websocket.recv()
                data = json.loads(response)
                print(f"📥 Received: {data['type']}")
                
                if data['type'] == 'start':
                    print(f"✅ Backtest started: {data['data']}")
                elif data['type'] == 'update':
                    print(f"📊 Update: Bar {data['data'].get('bar_index', 'N/A')}, Price: {data['data'].get('bar', {}).get('close', 'N/A')}")
                elif data['type'] == 'complete':
                    print(f"🏁 Backtest completed: {data['data']}")
                    break
                elif data['type'] == 'error':
                    print(f"❌ Error: {data['data']}")
                    break
                    
        except websockets.exceptions.ConnectionClosed:
            print("🔌 WebSocket connection closed")

if __name__ == "__main__":
    print("🚀 Testing WebSocket backtest with custom Python strategy...")
    asyncio.run(test_websocket_backtest()) 