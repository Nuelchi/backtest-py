#!/usr/bin/env python3
"""
Test the AI translation with the Pine Script to see what Python code it generates.
"""

from backend.strategies.strategy_translator import translate_to_python

# The Pine Script that should generate trades
pine_script = '''//@version=5
strategy("Moving Average Crossover Strategy", overlay=true)

// === Strategy Inputs ===
fastLength = input.int(9, title="Fast MA Length", minval=1)
slowLength = input.int(21, title="Slow MA Length", minval=1)
riskPercentage = input.float(1.0, title="Risk Percentage per Trade", step=0.1, minval=0.1, maxval=10.0)
fixedSL = input.float(50, title="Fixed Stop Loss (pips)", step=1, minval=1, maxval=1000)
fixedTP = input.float(100, title="Fixed Take Profit (pips)", step=1, minval=1, maxval=1000)

// === Moving Averages ===
fastMA = ta.ema(close, fastLength)
slowMA = ta.ema(close, slowLength)

// === Entry Conditions ===
bullishCrossover = ta.crossover(fastMA, slowMA)
bearishCrossover = ta.crossunder(fastMA, slowMA)

// === Risk Management ===
pip = syminfo.mintick * 10
riskAmount = strategy.equity * (riskPercentage / 100)

// === Position Sizing ===
sl = close - fixedSL * pip
tp = close + fixedTP * pip
distance = math.abs(close - sl)
qty = riskAmount / distance

// === Strategy Execution ===
if (bullishCrossover)
    strategy.entry("Buy", strategy.long, qty=qty)
    strategy.exit("Take Profit/Stop Loss", from_entry="Buy", stop=sl, limit=tp)

if (bearishCrossover)
    strategy.entry("Sell", strategy.short, qty=qty)
    strategy.exit("Take Profit/Stop Loss", from_entry="Sell", stop=close + fixedSL * pip, limit=close - fixedTP * pip)

// === Visual Signals ===
plotshape(series=bullishCrossover, location=location.belowbar, color=color.green, style=shape.triangleup, size=size.small)
plotshape(series=bearishCrossover, location=location.abovebar, color=color.red, style=shape.triangledown, size=size.small)

// === Alerts ===
alertcondition(bullishCrossover, title="Bullish Crossover", message="Fast MA crossed above Slow MA")
alertcondition(bearishCrossover, title="Bearish Crossover", message="Fast MA crossed below Slow MA")

// === Performance Expectations ===
// This strategy aims for a 2:1 risk-reward ratio with a 60-70% win rate.
// Adjust the risk percentage and stop loss/take profit levels to suit your risk tolerance.'''

def test_translation():
    """Test the AI translation with the Pine Script."""
    print("Testing AI translation with Pine Script...")
    print("=" * 60)
    
    try:
        # Try to translate the Pine Script
        result = translate_to_python(pine_script)
        
        if result[0]:  # Success
            print("✅ Translation successful!")
            print("\nGenerated Python code:")
            print("=" * 60)
            print(result[0])
            print("=" * 60)
            
            # Test if the generated code can be executed
            print("\nTesting if generated code can be executed...")
            try:
                # Create a test namespace
                test_namespace = {}
                test_namespace['SYMBOL'] = 'AAPL'
                
                # Execute the generated code
                exec(result[0], test_namespace)
                
                # Check if Strategy class was created
                if 'Strategy' in test_namespace:
                    print("✅ Generated code executed successfully!")
                    print("✅ Strategy class created!")
                    
                    # Test creating an instance
                    strategy_instance = test_namespace['Strategy']()
                    print("✅ Strategy instance created!")
                    
                    # Check if it has the required method
                    if hasattr(strategy_instance, '__call__'):
                        print("✅ Strategy has __call__ method!")
                    else:
                        print("❌ Strategy missing __call__ method!")
                        
                else:
                    print("❌ Strategy class not found in generated code!")
                    
            except Exception as e:
                print(f"❌ Error executing generated code: {e}")
                import traceback
                traceback.print_exc()
                
        else:
            print("❌ Translation failed!")
            print(f"Error: {result[1]}")
            
    except Exception as e:
        print(f"❌ Error during translation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_translation() 