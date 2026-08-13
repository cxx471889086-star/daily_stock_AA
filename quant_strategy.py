"""
双均线 + 量价共振策略
"""
import yfinance as yf
import pandas as pd

def get_stock_data(symbol):
    """获取A股数据"""
    if symbol.startswith('6'):
        symbol_yf = f"{symbol}.SS"
    else:
        symbol_yf = f"{symbol}.SZ"
    df = yf.download(symbol_yf, period="3mo", progress=False)
    return df

def calc_signals(df):
    """计算买卖信号"""
    df['ma5'] = df['Close'].rolling(5).mean()
    df['ma20'] = df['Close'].rolling(20).mean()
    df['vol_ma5'] = df['Volume'].rolling(5).mean()
    
    current = df.iloc[-1]
    prev = df.iloc[-2]
    
    # 金叉
    golden_cross = (current['ma5'] > current['ma20']) and (prev['ma5'] <= prev['ma20'])
    # 放量
    volume_ok = current['Volume'] > current['vol_ma5'] * 1.5
    # 站稳20日线
    above_ma20 = current['Close'] > current['ma20']
    
    if golden_cross and volume_ok and above_ma20:
        return "🟢 买入", "金叉+放量+站稳20日线"
    elif current['Close'] < current['ma20']:
        return "🔴 卖出", "跌破20日均线"
    else:
        return "🟡 观望", "无明确信号"

def analyze(symbol):
    """分析单只股票"""
    try:
        df = get_stock_data(symbol)
        if df.empty:
            return f"❌ {symbol}: 无数据"
        signal, reason = calc_signals(df)
        price = round(df.iloc[-1]['Close'], 2)
        return f"{signal} {symbol} | 现价:{price} | {reason}"
    except Exception as e:
        return f"❌ {symbol}: {str(e)}"

if __name__ == "__main__":
    import sys
    stocks = sys.argv[1].split(",") if len(sys.argv) > 1 else ["600519"]
    for s in stocks:
        print(analyze(s.strip()))

