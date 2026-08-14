import sys
import re
import json
import urllib.request
from datetime import datetime, timezone, timedelta

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
        'low': float(data[5]),
        'volume': int(data[8]),
        'amount': float(data[9])
    }

def analyze(symbol):
    try:
        d = get_data(symbol)
        change = (d['price'] - d['prev_close']) / d['prev_close'] * 100
        amplitude = (d['high'] - d['low']) / d['prev_close'] * 100 if d['prev_close'] > 0 else 0
        d['change'] = change
        d['amplitude'] = amplitude
        d['signal'] = 'BUY' if d['price'] > d['open'] else 'HOLD'
        d['code'] = symbol
        return d
    except Exception as e:
        return {'code': symbol, 'error': str(e)[:80]}

def build_card(stocks, time_str):
    valid = [s for s in stocks if 'error' not in s]
    errors = [s for s in stocks if 'error' in s]
    buy_count = sum(1 for s in valid if s.get('signal') == 'BUY')
    hold_count = len(valid) - buy_count
    avg_change = sum(s.get('change', 0) for s in valid) / len(valid) if valid else 0
    elements = []
    elements.append({"tag": "markdown", "content": f"🟢 **BUY: {buy_count}** | ⚪ **HOLD: {hold_count}** | 平均涨跌: **{avg_change:+.2f}%**"})
    elements.append({"tag": "hr"})
    for s in valid:
        emoji = "🟢" if s.get('signal') == 'BUY' else "⚪"
        amount_yi = s.get('amount', 0) / 1e8
        text = f"{emoji} **{s['code']} {s.get('name', '?')}**\n   **{s.get('signal', '?')}** · 现价 **{s.get('price', 0):.2f}** ({s.get('change', 0):+.2f}%)\n   振幅 {s.get('amplitude', 0):.2f}% · 成交额 {amount_yi:.2f}亿"
        elements.append({"tag": "markdown", "content": text})
        elements.append({"tag": "hr"})
    if errors:
        error_text = "⚠️ **错误股票**\n" + "\n".join([f"- {s['code']}: {s['error']}" for s in errors])
        elements.append({"tag": "markdown", "content": error_text})
        elements.append({"tag": "hr"})
    elements.append({"tag": "markdown", "content": f"<font color='gray'>更新于 {time_str} · 每 10 分钟自动推送</font>"})
    template = "green" if buy_count > hold_count else ("orange" if hold_count > buy_count else "blue")
    return {
        "msg_type": "interactive",
        "card": {
            "schema": "2.0",
            "config": {"compact_width": False},
            "header": {
                "template": template,
                "title": {"tag": "plain_text", "content": f"📊 量化信号 · {time_str}"}
            },
            "body": {"elements": elements}
        }
    }

def send(webhook, card):
    data = json.dumps(card, ensure_ascii=False).encode('utf-8')
    req = urllib.request.Request(webhook, data=data, headers={'Content-Type': 'application/json'})
    resp = urllib.request.urlopen(req, timeout=15)
    return resp.status, resp.read().decode()

if __name__ == '__main__':
    raw = sys.argv[1] if len(sys.argv) > 1 else '600519'
    webhook = sys.argv[2] if len(sys.argv) > 2 else ''
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
    results = [analyze(s) for s in stocks]
    results = [r for r in results if r is not None]
    beijing = timezone(timedelta(hours=8))
    now = datetime.now(beijing)
    time_str = now.strftime('%Y-%m-%d %H:%M')
    card = build_card(results, time_str)
    if webhook:
        status, resp = send(webhook, card)
        print(f'Feishu status: {status}')
        print(f'Response: {resp}')
    else:
        print(json.dumps(card, ensure_ascii=False, indent=2))
