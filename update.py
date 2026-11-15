import json, urllib.request, datetime

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"}
SYMS = {"gold": "GC=F", "silver": "SI=F", "copper": "HG=F", "alu": "ALI=F"}

def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)

def yahoo(sym):
    for host in ("query1", "query2"):
        try:
            j = get(f"https://{host}.finance.yahoo.com/v8/finance/chart/{sym}?range=7d&interval=1d")
            res = j["chart"]["result"][0]
            m, q = res["meta"], res["indicators"]["quote"][0]
            price = m.get("regularMarketPrice")
            if not price:
                continue
            closes = [c for c in (q.get("close") or []) if c is not None]
            opens = [o for o in (q.get("open") or []) if o is not None]
            # previous close = the close of the session before the latest one
            prev = closes[-2] if len(closes) > 1 else m.get("chartPreviousClose")
            return {"price": price, "prev": prev,
                    "open": opens[-1] if opens else None,
                    "hi": m.get("regularMarketDayHigh"), "lo": m.get("regularMarketDayLow")}
        except Exception as e:
            print("yahoo fail", sym, host, e)
    return None

def goldapi(sym):
    try:
        p = get(f"https://api.gold-api.com/price/{sym}").get("price")
        return {"price": p, "prev": None, "open": None, "hi": None, "lo": None} if p else None
    except Exception as e:
        print("goldapi fail", sym, e)
        return None

metals = {}
for name, ysym in SYMS.items():
    d = yahoo(ysym)
    if d is None:
        alt = {"gold": "XAU", "silver": "XAG", "copper": "HG"}.get(name)
        d = goldapi(alt) if alt else None
    metals[name] = d or {"price": None}

usdinr = None
try:
    usdinr = get("https://open.er-api.com/v6/latest/USD")["rates"]["INR"]
except Exception as e:
    print("fx fail", e)
if usdinr is None:
    try:
        usdinr = yahoo("INR=X")["price"]
    except Exception:
        pass

if usdinr and any(v.get("price") for v in metals.values()):
    out = {"t": datetime.datetime.now(datetime.timezone.utc).isoformat(), "usdinr": usdinr, "metals": metals}
    json.dump(out, open("data.json", "w"), indent=1)
    print("written", out)
else:
    raise SystemExit("no usable data, keeping old data.json")
