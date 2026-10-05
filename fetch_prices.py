import json, time, datetime, urllib.request, http.cookiejar
BASE = 'https://mis.twse.com.tw/stock/'
H = {'User-Agent': 'Mozilla/5.0', 'Referer': BASE + 'index.jsp'}
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
get = lambda u: op.open(urllib.request.Request(u, headers=H), timeout=30).read().decode('utf-8')

def num(x):
    try:
        v = float(x)
        return v if v > 0 else None
    except (TypeError, ValueError):
        return None

codes = [l.split('#')[0].strip().upper().split('.')[0] for l in open('codes.txt', encoding='utf-8')]
codes = [c for c in dict.fromkeys(codes) if c]
try:
    old = json.load(open('prices.json', encoding='utf-8'))
except Exception:
    old = {}
prices, index, date = dict(old.get('prices', {})), old.get('index', 0), old.get('date', '')

get(BASE + 'index.jsp')  # session cookie
chs = ['tse_t00.tw'] + [f'{m}_{c}.tw' for c in codes for m in ('tse', 'otc')]
got = 0
for i in range(0, len(chs), 20):
    url = BASE + 'api/getStockInfo.jsp?json=1&delay=0&ex_ch=' + '|'.join(chs[i:i+20]) + '&_=' + str(int(time.time() * 1000))
    try:
        arr = json.loads(get(url)).get('msgArray', [])
    except Exception as e:
        print('batch failed:', e)
        continue
    for m in arr:
        # last trade, else best bid, else previous close
        p = num(m.get('z')) or num((m.get('b') or '').split('_')[0]) or num(m.get('y'))
        if not p:
            continue
        got += 1
        d = m.get('d', '')
        if len(d) == 8:
            date = f'{d[:4]}-{d[4:6]}-{d[6:]}'
        if m.get('c') == 't00':
            index = p
        else:
            prices[m.get('c')] = p
    time.sleep(1)

if not got:
    raise SystemExit('No prices received from TWSE')
now = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
json.dump({'updated': now.strftime('%Y-%m-%d %H:%M') + ' TST', 'date': date, 'index': index, 'prices': prices},
          open('prices.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('Updated', got, 'quotes;', len(prices), 'stocks; index', index)
