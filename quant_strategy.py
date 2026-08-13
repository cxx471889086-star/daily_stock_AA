"""
双均线 + 量价共振策略
"""
import yfinance as yf
import sys

def get_data(symbol):
    if symbol.startswith('6'):
        s = f"{symbol}.SS"
    else:
        s = f"{symbol}.SZ"
    df = yf.download(s, period="1mo", progress=False)
    return df

def analyze(symbol):
    try:
        df = get_data(symbol)
        if df.empty:
            return f"{symbol}: no data"
        price = float(df['Close'].iloc[-1])
        ma5 = float(df['Close'].tail(5).mean())
        signal = "BUY" if price > ma5 else "HOLD"
        return f"{symbol}: {signal} (price={price:.2f}, MA5={ma5:.2f})"
    except Exception as e:
        return f"{symbol}: error - {e}"

if __name__ == "__main__":
    stocks = sys.argv[1].split(",") if len(sys.argv) > 1 else ["600519"]
    for s in stocks:
        print(analyze(s.strip()))

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

