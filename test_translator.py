#!/usr/bin/env python3
"""
Test script for the AI-powered strategy translator.
Tests translation from Pine Script to Python using the same AI service as the sidebar.
"""

import os
import sys
sys.path.append('backend')

from backend.strategies.strategy_translator import translate_to_python

def test_pine_translation():
    """Test Pine Script to Python translation using AI."""
    
    # Sample Pine Script strategy
    pine_code = """
//@version=5
strategy("EMA Crossover Strategy", overlay=true)

// Input parameters
fast_length = input(12, "Fast EMA Length")
slow_length = input(26, "Slow EMA Length")

// Calculate EMAs
fast_ema = ta.ema(close, fast_length)
slow_ema = ta.ema(close, slow_length)

// Entry conditions
long_condition = ta.crossover(fast_ema, slow_ema)
short_condition = ta.crossunder(fast_ema, slow_ema)

// Execute trades
if long_condition
    strategy.entry("Long", strategy.long)

if short_condition
    strategy.entry("Short", strategy.short)

// Plot EMAs
plot(fast_ema, "Fast EMA", color=color.blue)
plot(slow_ema, "Slow EMA", color=color.red)
"""
    
    print("Testing AI-powered Pine Script translation...")
    print("=" * 50)
    print("Input Pine Script:")
    print(pine_code)
    print("\n" + "=" * 50)
    
    try:
        # Set API key if available
        if 'OPENROUTER_API_KEY' not in os.environ:
            print("⚠️  OPENROUTER_API_KEY not set. The translator will try to get it from the frontend endpoint.")
            print("   Set OPENROUTER_API_KEY environment variable for direct API access.")
        
        # Translate using AI
        result, meta = translate_to_python(pine_code, language="pine")
        
        print("✅ Translation successful!")
        print(f"Language: {meta['language']}")
        print(f"Translation method: {meta['via']}")
        print(f"Wrapped: {meta.get('wrapped', False)}")
        print("\nTranslated Python code:")
        print("-" * 30)
        print(result)
        
    except ValueError as e:
        print(f"❌ Translation failed: {e}")
        print("\nThis usually means:")
        print("1. API key is invalid or missing")
        print("2. Network connectivity issues")
        print("3. AI service is down")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_pine_translation() 