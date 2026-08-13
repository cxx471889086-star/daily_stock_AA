import yfinance as yf
import sys

def get_data(symbol):
    if symbol.startswith('6'):
        s = symbol + '.SS'
    else:
        s = symbol + '.SZ'
    df = yf.download(s, period='1mo', progress=False)
    return df

def analyze(symbol):
    try:
        df = get_data(symbol)
        if df is None or len(df) < 5:
            return symbol + ': no data'
        close_col = df['Close']
        price = float(close_col.iloc[-1])
        ma5 = float(close_col.tail(5).mean())
        if price > ma5:
            sig = 'BUY'
        else:
            sig = 'HOLD'
        return symbol + ': ' + sig + ' (price=' + str(round(price, 2)) + ', MA5=' + str(round(ma5, 2)) + ')'
    except Exception as e:
        return symbol + ': error'

if __name__ == '__main__':
    if len(sys.argv) > 1:
        stocks = sys.argv[1].split(',')
    else:
        stocks = ['600519']
    for s in stocks:
        print(analyze(s.strip()))
