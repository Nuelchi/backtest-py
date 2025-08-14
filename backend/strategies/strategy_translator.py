#!/usr/bin/env python3
"""
AI-Powered Strategy Translator
Converts Pine Script, MQL4, and MQL5 strategies to Python using GPT-4o via OpenRouter API.
"""

import os
import re
import requests
from typing import Optional, Tuple, Dict, Any

SUPPORTED_LANGS = ("pine", "mql4", "mql5", "python")

def detect_language(code: str) -> str:
    """Detect the programming language of the strategy code."""
    c = code.strip()
    lo = c.lower()
    
    # Strong signals
    if "study(" in lo or "indicator(" in lo or "strategy(" in lo or "//@version" in lo or "ta." in lo:
        return "pine"
    if "#property copyright" in lo or "#property link" in lo or "#property version" in lo or "ordersend" in lo or "mql4" in lo or "mql5" in lo:
        return "mql"
    if "import pandas" in lo or "import numpy" in lo or "class Strategy" in lo or "def __call__" in lo:
        return "python"
    
    # Heuristics for Python
    if "def " in lo or "class " in lo or "import " in lo:
        return "python"
    
    return "pine"  # default bias

def call_llm_translate(code: str, source_lang: str, target: str = "python") -> Optional[str]:
    """
    Call OpenRouter API (GPT-4o) for high-accuracy strategy translation.
    Uses the same AI service as the frontend for consistency.
    """
    try:
        # Get API key from environment or Supabase endpoint
        api_key = os.environ.get("OPENROUTER_API_KEY")
        model = 'openai/gpt-4o'  # Default model
        
        if not api_key:
            # Try to get from the same endpoint the frontend uses
            try:
                response = requests.get(
                    'https://kgfzbkwyepchbysaysky.supabase.co/functions/v1/get-api-key',
                    headers={'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtnZnpia3d5ZXBjaGJ5c2F5c2t5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTI0Nzk5NDAsImV4cCI6MjA2ODA1NTk0MH0.WsMnjZsBPdM5okL4KZXZidX8eiTiGmN-Qc--Y359H6M'}
                )
                if response.status_code == 200:
                    data = response.json()
                    api_key = data.get('apiKey')
                    model = data.get('model', 'openai/gpt-4o')
                else:
                    return None
            except:
                return None
        
        if not api_key:
            return None
            
        # Create the translation prompt with detailed system instructions
        system_prompt = """You are an expert trading strategy translator. Your job is to convert trading strategies from Pine Script, MQL4, or MQL5 to Python for a backtesting engine.

CRITICAL REQUIREMENTS:
1. Create a Python class called 'Strategy' with a '__call__(self, engine, bar)' method
2. The method must implement the EXACT same trading logic as the source code
3. Use engine.place_order() method for all trades
4. Import: from backend.engine.backtest_engine import OrderSide, OrderType
5. Use OrderSide.BUY/SELL and OrderType.MARKET/STOP/LIMIT
6. Access price data via bar.open, bar.high, bar.low, bar.close
7. Get current position via engine.get_position(bar.symbol).quantity
8. Preserve ALL stop-loss, take-profit, and risk management logic
9. Maintain the exact same entry/exit conditions and timing
10. Handle all technical indicators (EMA, SMA, RSI, Bollinger Bands, etc.)
11. Preserve position sizing and risk management rules
12. Return ONLY the Python code, no explanations or markdown

EXAMPLE OUTPUT FORMAT:
```python
from backend.engine.backtest_engine import OrderSide, OrderType

class Strategy:
    def __init__(self):
        self.prices = []
    
    def __call__(self, engine, bar):
        # Strategy logic here
        pass
```"""
        
        user_prompt = f"""Translate this {source_lang.upper()} code to Python:

{code}

Return ONLY the Python code, no explanations."""
        
        # Call OpenRouter API (same as your sidebar AI)
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://trainflow.ai",
            "X-Title": "TrainFlow Strategy Translator"
        }
        
        data = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.1,  # Low temperature for consistent translation
            "max_tokens": 2000
        }
        
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            translated_code = result['choices'][0]['message']['content'].strip()
            
            # Clean up the response to extract just the Python code
            if "```python" in translated_code:
                translated_code = translated_code.split("```python")[1].split("```")[0].strip()
            elif "```" in translated_code:
                translated_code = translated_code.split("```")[1].strip()
            
            return translated_code
        else:
            print(f"OpenRouter API error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"LLM translation error: {e}")
        return None

def translate_to_python(code: str, language: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
    """
    Detect language (if not provided) and translate to Python Strategy using AI only.
    NO rule-based fallback - AI only for maximum accuracy.
    Returns (python_code, meta) or raises ValueError if AI translation fails.
    """
    lang = (language or detect_language(code)).lower()

    # Only use AI translation - no rule-based fallback
    llm_out = call_llm_translate(code, lang)
    if llm_out:
        if "class Strategy" in llm_out and "__call__" in llm_out:
            return llm_out, {"language": "python", "via": "llm"}
        
        # If AI returns function instead of class, wrap it
        wrapper = f"""from backend.engine.backtest_engine import OrderSide, OrderType

{llm_out}

class Strategy:
    def __call__(self, engine, bar):
        return strategy(engine, bar)"""
        return wrapper, {"language": "python", "via": "llm", "wrapped": True}
    
    # If AI translation fails, raise an error - no fallback
    raise ValueError(f"AI translation failed for {lang} code. Please ensure your API key is valid and try again.") 