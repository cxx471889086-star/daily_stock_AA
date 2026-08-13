"""
简单回测：测试策略在历史数据上的表现
"""
import pandas as pd
import yfinance as yf
from quant_strategy import QuantStrategy

def get_data(symbol, period="1y"):
    """获取股票数据"""
    # 沪市加 .SS，深市加 .SZ
    if symbol.startswith('6'):
        symbol = f"{symbol}.SS"
    else:
        symbol = f"{symbol}.SZ"
    df = yf.download(symbol, period=period, progress=False)
    return df

def backtest(symbol, initial_cash=100000):
    """回测单只股票"""
    df = get_data(symbol)
    if df.empty:
        return None
    
    strategy = QuantStrategy()
    df = strategy.calc_indicators(df)
    
    position = 0  # 0=空仓, 1=持仓
    entry_price = 0
    cash = initial_cash
    shares = 0
    trades = []
    
    for i in range(20, len(df)):
        current = df.iloc[i]
        current_df = df.iloc[:i+1]
        
        if position == 0:
            should_buy, reason = strategy.should_buy(current_df)
            if should_buy:
                shares = int(cash * 0.95 / current['close'] / 100) * 100
                if shares > 0:
                    entry_price = current['close']
                    position = 1
                    trades.append({
                        'date': df.index[i],
                        'action': 'BUY',
                        'price': current['close'],
                        'reason': reason
                    })
        else:
            should_sell, reason = strategy.should_sell(current_df, entry_price)
            if should_sell:
                cash = shares * current['close']
                trades.append({
                    'date': df.index[i],
                    'action': 'SELL',
                    'price': current['close'],
                    'reason': reason,
                    'return': (current['close'] - entry_price) / entry_price * 100
                })
                position = 0
                shares = 0
    
    # 计算最终收益
    if position == 1:
        final_value = shares * df.iloc[-1]['close']
    else:
        final_value = cash
    
    total_return = (final_value - initial_cash) / initial_cash * 100
    
    return {
        'symbol': symbol,
        'initial_cash': initial_cash,
        'final_value': round(final_value, 2),
        'total_return': round(total_return, 2),
        'trades': trades
    }

if __name__ == "__main__":
    # 测试自选股
    stocks = ['600519', '300750', '002594']
    for stock in stocks:
        result = backtest(stock)
        if result:
            print(f"\n{stock}:")
            print(f"  总收益: {result['total_return']}%")
            print(f"  交易次数: {len(result['trades'])}")
