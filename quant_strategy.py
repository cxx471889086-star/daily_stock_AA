import sys
import re
import urllib.request

def get_data(symbol):
    if symbol.startswith('6'):
        s = 'sh' + symbol
    else:
        s = 'sz' + symbol
    url = 'https://hq.sinajs.cn/list=' + s
    req = urllib.request.Request(url, headers={'Referer': 'https://finance.sina.com.cn'})
    resp = urllib.request.urlopen(req, timeout=10)
    content = resp.read().decode('gbk')
    data = content.split('"')[1].split(',')
    return {
        'name': data[0],
        'open': float(data[1]),
        'prev_close': float(data[2]),
        'price': float(data[3]),
        'high': float(data[4]),
        'low': float(data[5])
    }

def analyze(symbol):
    try:
        d = get_data(symbol)
        if d is None:
            return symbol + ': no data'
        change = (d['price'] - d['prev_close']) / d['prev_close'] * 100
        if d['price'] > d['open']:
            sig = 'BUY'
        else:
            sig = 'HOLD'
        arrow = '+' if change >= 0 else ''
        return symbol + ' ' + d['name'] + ': ' + sig + ' ' + str(d['price']) + ' (' + arrow + str(round(change, 2)) + '%)'
    except Exception as e:
        return symbol + ': ERR ' + str(e)[:80]

if __name__ == '__main__':
    raw = sys.argv[1] if len(sys.argv) > 1 else '600519'
    parts = re.split(r'[\s,;]+', raw)
    seen = set()
    stocks = []
    for p in parts:
        p = p.strip()
        if p and p not in seen:
            seen.add(p)
            stocks.append(p)
    if not stocks:
        stocks = ['600519']
    for s in stocks:
        print(analyze(s))
