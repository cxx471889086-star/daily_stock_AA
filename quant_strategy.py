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

def call_deepseek(stocks, api_key):
    """调用 DeepSeek 分析"""
    valid = [s for s in stocks if 'error' not in s]
    if not valid:
        return None
    
    context = "\n".join([
        f"{s['code']} {s.get('name','?')}: "
        f"信号={s.get('signal','?')}, "
        f"现价={s.get('price',0):.2f}, "
        f"涨跌幅={s.get('change',0):+.2f}%, "
        f"振幅={s.get('amplitude',0):.2f}%, "
        f"成交额={s.get('amount',0)/1e8:.2f}亿"
        for s in valid
    ])
    
    prompt = f"""你是 A 股量化交易分析师。根据以下实时数据，给出简洁交易策略：

{context}

输出格式（每项≤30字）：
🎯 **大盘情绪**：涨/跌/震荡
⭐ **重点关注**：最值得交易的1只+理由
⚠️ **风险提示**：当前主要风险
💡 **操作建议**：建仓/加仓/减仓/观望"""
    
    payload = json.dumps({
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "你是经验丰富的 A 股量化交易分析师，简洁直接。"},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 600,
        "temperature": 0.3
    }).encode('utf-8')
    
    req = urllib.request.Request(
        'https://api.deepseek.com/v1/chat/completions',
        data=payload,
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}'
        }
    )
    resp = urllib.request.urlopen(req, timeout=30)
    result = json.loads(resp.read().decode('utf-8'))
    return result['choices'][0]['message']['content']

def build_text(stocks, time_str, ai_advice=None):
    valid = [s for s in stocks if 'error' not in s]
    errors = [s for s in stocks if 'error' in s]
    buy_count = sum(1 for s in valid if s.get('signal') == 'BUY')
    hold_count = len(valid) - buy_count
    avg_change = sum(s.get('change', 0) for s in valid) / len(valid) if valid else 0
    avg_icon = '📈' if avg_change >= 0 else '📉'

    lines = []
    lines.append(f'📊 量化信号 · {time_str}')
    lines.append('')
    lines.append(f'🟢 BUY: {buy_count} | ⚪ HOLD: {hold_count}')
    lines.append(f'{avg_icon} 平均涨跌: {avg_change:+.2f}%')
    lines.append('')

    for s in valid:
        emoji = '🟢' if s.get('signal') == 'BUY' else '⚪'
        amount_yi = s.get('amount', 0) / 1e8
        lines.append('─────────────────────')
        lines.append(f"{emoji} {s['code']} {s.get('name', '?')}")
        lines.append(f"   {s.get('signal', '?')} · 现价 {s.get('price', 0):.2f} ({s.get('change', 0):+.2f}%)")
        lines.append(f"   振幅 {s.get('amplitude', 0):.2f}% · 成交额 {amount_yi:.2f}亿")

    if errors:
        lines.append('─────────────────────')
        lines.append('⚠️ 错误股票:')
        for s in errors:
            lines.append(f"  - {s['code']}: {s['error']}")

    if ai_advice:
        lines.append('─────────────────────')
        lines.append('🤖 DeepSeek 策略:')
        lines.append(ai_advice)

    lines.append('─────────────────────')
    lines.append(f'更新于 {time_str} · 每 10 分钟自动推送')

    return '\n'.join(lines)

def send(webhook, text):
    data = json.dumps({'msg_type': 'text', 'content': {'text': text}}).encode('utf-8')
    req = urllib.request.Request(webhook, data=data, headers={'Content-Type': 'application/json'})
    resp = urllib.request.urlopen(req, timeout=15)
    return resp.status, resp.read().decode()

if __name__ == '__main__':
    raw = sys.argv[1] if len(sys.argv) > 1 else '600519'
    webhook = sys.argv[2] if len(sys.argv) > 2 else ''
    deepseek_key = sys.argv[3] if len(sys.argv) > 3 else ''

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

    ai_advice = None
    if deepseek_key:
        try:
            print('Calling DeepSeek...')
            ai_advice = call_deepseek(results, deepseek_key)
        except Exception as e:
            print(f'DeepSeek error: {e}')
            ai_advice = None

    text = build_text(results, time_str, ai_advice)
    print(text)

    if webhook:
        status, resp = send(webhook, text)
        print(f'\nFeishu status: {status}')
        print(f'Response: {resp}')
