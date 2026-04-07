#!/usr/bin/env python3
"""
RAPTOR Alert - Fetch ETF data da Yahoo Finance
Eseguito da GitHub Actions ogni ora
Genera data/etf.json con tutti i segnali pre-calcolati
"""

import json
import time
import math
from datetime import datetime
import urllib.request
import urllib.error
import os

# ── Lista ETF ────────────────────────────────────────────────────────────────
TICKERS = [
    {"y":"IAEX.AS","c":"Paesi","t":"IAEX"},{"y":"TOF.AS","c":"ATTIVO","t":"TOF"},
    {"y":"18MN.DE","c":"Lazy","t":"18MN"},{"y":"7USH.DE","c":"BOND","t":"7USH"},
    {"y":"CBUH.DE","c":"ATTIVO","t":"CBUH"},{"y":"CEB1.DE","c":"BOND","t":"CEB1"},
    {"y":"CEB4.DE","c":"NEW AREA","t":"CEB4"},{"y":"DBZB.DE","c":"Lazy","t":"DBZB"},
    {"y":"EUNY.DE","c":"ATTIVO","t":"EUNY"},{"y":"FTGM.DE","c":"ATTIVO","t":"FTGM"},
    {"y":"IBC5.DE","c":"BOND","t":"IBC5"},{"y":"IS04.DE","c":"BOND","t":"IS04"},
    {"y":"IS3C.DE","c":"Lazy","t":"IS3C"},{"y":"IS3N.DE","c":"Lazy","t":"IS3N"},
    {"y":"IUSQ.DE","c":"Lazy","t":"IUSQ"},{"y":"SXR1.DE","c":"Lazy","t":"SXR1"},
    {"y":"SXRT.DE","c":"Lazy","t":"SXRT"},{"y":"SXRW.DE","c":"Lazy","t":"SXRW"},
    {"y":"XDEM.DE","c":"ATTIVO","t":"XDEM"},{"y":"XGIN.DE","c":"Lazy","t":"XGIN"},
    # Aggiungi qui tutti gli altri ticker...
    # Per brevità includi i principali — il file completo va copiato dall'HTML
    {"y":"AIAI.MI","c":"Tematici","t":"AIAI"},{"y":"AGGH.MI","c":"BOND","t":"AGGH"},
    {"y":"ARMI.MI","c":"Tematici","t":"ARMI"},{"y":"BATT.MI","c":"Tematici","t":"BATT"},
    {"y":"BNK.MI","c":"Settoriali","t":"BNK"},{"y":"BOTZ.MI","c":"Tematici","t":"BOTZ"},
    {"y":"BTC.MI","c":"Tematici","t":"BTC"},{"y":"CHIP.MI","c":"ADVICE","t":"CHIP"},
    {"y":"CIBR.MI","c":"ADVICE","t":"CIBR"},{"y":"CLOU.MI","c":"Tematici","t":"CLOU"},
    {"y":"CO2.MI","c":"Materie","t":"CO2"},{"y":"CSSPX.MI","c":"ADVICE","t":"CSSPX"},
    {"y":"CYBR.MI","c":"Settoriali","t":"CYBR"},{"y":"DEFS.MI","c":"Settoriali","t":"DEFS"},
    {"y":"DFNS.MI","c":"Tematici","t":"DFNS"},{"y":"EIMI.MI","c":"ADVICE","t":"EIMI"},
    {"y":"ESPO.MI","c":"Tematici","t":"ESPO"},{"y":"GAS.MI","c":"Materie","t":"GAS"},
    {"y":"GDX.MI","c":"Tematici","t":"GDX"},{"y":"GDXJ.MI","c":"Tematici","t":"GDXJ"},
    {"y":"HEAL.MI","c":"Tematici","t":"HEAL"},{"y":"HTWO.MI","c":"Tematici","t":"HTWO"},
    {"y":"HYGN.MI","c":"Tematici","t":"HYGN"},{"y":"INQQ.MI","c":"Tematici","t":"INQQ"},
    {"y":"LITM.MI","c":"Tematici","t":"LITM"},{"y":"NATO.MI","c":"Settoriali","t":"NATO"},
    {"y":"NCLR.MI","c":"Tematici","t":"NCLR"},{"y":"NGAS.MI","c":"Materie","t":"NGAS"},
    {"y":"NUCL.MI","c":"Tematici","t":"NUCL"},{"y":"PHAG.MI","c":"Materie","t":"PHAG"},
    {"y":"QQQ","c":"top4 usa","t":"QQQ"},{"y":"RBOT.MI","c":"ADVICE","t":"RBOT"},
    {"y":"ROBO.MI","c":"Tematici","t":"ROBO"},{"y":"SMH.MI","c":"Tematici","t":"SMH"},
    {"y":"SOLR.MI","c":"Tematici","t":"SOLR"},{"y":"SPY","c":"top4 usa","t":"SPY"},
    {"y":"SWDA.MI","c":"ADVICE","t":"SWDA"},{"y":"U3O8.MI","c":"Tematici","t":"U3O8"},
    {"y":"URNU.MI","c":"ADVICE","t":"URNU"},{"y":"USTEC.MI","c":"Tematici","t":"USTEC"},
    {"y":"VOLT.MI","c":"Tematici","t":"VOLT"},{"y":"WEB3.MI","c":"Tematici","t":"WEB3"},
    {"y":"XDWD.MI","c":"Benchmark","t":"XDWD"},{"y":"XEON.MI","c":"Liquidità","t":"XEON"},
    {"y":"XSMI.MI","c":"Paesi","t":"XSMI"},{"y":"ZINC.MI","c":"Materie","t":"ZINC"},
    {"y":"ADS.DE","c":"EUROGROW","t":"ADS"},{"y":"AIR.PA","c":"EUROGROW","t":"AIR"},
    {"y":"ASML.SW","c":"EUROGROW","t":"ASML"},{"y":"RHM.DE","c":"EUROGROW","t":"RHM"},
    {"y":"SAP.DE","c":"EUROGROW","t":"SAP"},{"y":"SIE.DE","c":"EUROGROW","t":"SIE"},
    {"y":"RACE.MI","c":"EUROGROW","t":"RACE"},{"y":"UCG.MI","c":"EUROGROW","t":"UCG"},
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json',
}

def fetch_yahoo(symbol: str) -> dict | None:
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=1y"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        result = data.get("chart", {}).get("result", [None])[0]
        return result
    except Exception as e:
        print(f"  ✗ {symbol}: {e}")
        return None

# ── Indicatori ────────────────────────────────────────────────────────────────
def ema_arr(arr, p):
    k = 2 / (p + 1)
    out = [arr[0]]
    for i in range(1, len(arr)):
        out.append(arr[i] * k + out[-1] * (1 - k))
    return out

def calc_kama(close, n=10, fast=2, slow=30):
    fast_sc, slow_sc = 2/(fast+1), 2/(slow+1)
    out = [None] * len(close)
    if len(close) < n + 1:
        return out
    out[n] = close[n]
    for i in range(n+1, len(close)):
        direction = abs(close[i] - close[i-n])
        noise = sum(abs(close[j] - close[j-1]) for j in range(i-n+1, i+1))
        er = direction / noise if noise else 0
        sc = (er * (fast_sc - slow_sc) + slow_sc) ** 2
        out[i] = out[i-1] + sc * (close[i] - out[i-1])
    return out

def calc_ao(high, low):
    mid = [(h+l)/2 for h,l in zip(high, low)]
    e7 = ema_arr(mid, 7)
    e34 = ema_arr(mid, 34)
    return [a-b for a,b in zip(e7, e34)]

def calc_rsi(close, p=14):
    if len(close) < p + 1:
        return None
    gains = losses = 0
    for i in range(1, p+1):
        d = close[i] - close[i-1]
        if d >= 0: gains += d
        else: losses -= d
    ag, al = gains/p, losses/p
    for i in range(p+1, len(close)):
        d = close[i] - close[i-1]
        if d >= 0: ag = (ag*(p-1)+d)/p
        else: al = (al*(p-1)-d)/p
    return None if al == 0 else round(100 - 100/(1+ag/al), 1)

def calc_er(close, n=10):
    if len(close) < n+1: return 0
    direction = abs(close[-1] - close[-1-n])
    noise = sum(abs(close[i]-close[i-1]) for i in range(len(close)-n, len(close)))
    return direction/noise if noise else 0

def trendycator(close):
    if len(close) < 55: return 'GRIGIO'
    e21 = ema_arr(close, 21)
    e55 = ema_arr(close, 55)
    if e21[-1] > e55[-1] and e21[-1] > e21[-2]: return 'VERDE'
    if e21[-1] < e55[-1] and e21[-1] < e21[-2]: return 'ROSSO'
    return 'GRIGIO'

def calc_baffetti(ao):
    b = 0
    for i in range(len(ao)-1, 0, -1):
        if ao[i] > ao[i-1]: b += 1
        else: break
    return b

def cross_days(close, kama):
    for i in range(len(close)-1, 0, -1):
        if kama[i] is not None and kama[i-1] is not None:
            if close[i] > kama[i] and close[i-1] <= kama[i-1]:
                return len(close)-1-i
    return 999

def entry_date(close, kama, timestamps):
    for i in range(len(close)-1, 0, -1):
        if kama[i] is not None and kama[i-1] is not None:
            if close[i] > kama[i] and close[i-1] <= kama[i-1]:
                d = datetime.fromtimestamp(timestamps[i])
                return d.strftime("%d/%m/%Y")
    return "—"

def sma(arr, p):
    if len(arr) < p: return None
    return sum(arr[-p:]) / p

def vol_ratio(volume):
    if len(volume) < 21: return 1.0
    avg20 = sum(volume[-21:-1]) / 20
    return round(volume[-1]/avg20, 2) if avg20 else 1.0

# ── Analisi singolo ticker ────────────────────────────────────────────────────
def analyze(info: dict) -> dict:
    base = {"ticker": info["t"], "display": info["t"], "categoria": info["c"],
            "error": None, "score": 0, "tipo": "", "uscita": ""}
    raw = fetch_yahoo(info["y"])
    if not raw:
        return {**base, "error": "fetch failed"}
    try:
        q = raw["indicators"]["quote"][0]
        ts_raw = raw["timestamp"]
        closes_r, highs_r, lows_r, vols_r = q["close"], q["high"], q["low"], q["volume"]
        c, h, l, v, t = [], [], [], [], []
        for i in range(len(ts_raw)):
            if closes_r[i] and highs_r[i] and lows_r[i]:
                c.append(closes_r[i]); h.append(highs_r[i]); l.append(lows_r[i])
                v.append(vols_r[i] or 0); t.append(ts_raw[i])
        if len(c) < 60:
            return {**base, "error": "Dati insuff."}

        kama = calc_kama(c)
        ao = calc_ao(h, l)
        baff = calc_baffetti(ao)
        er = calc_er(c)
        trd = trendycator(c)
        rsi = calc_rsi(c)
        mm20, mm50 = sma(c, 20), sma(c, 50)
        price = c[-1]
        k_now = kama[-1]
        ao_now = ao[-1]
        above_kama = k_now is not None and price > k_now
        pk_pct = round((price - k_now) / k_now * 100, 2) if k_now else 0
        mm_align = bool(mm20 and mm50 and price > mm20 and mm20 > mm50)
        cross = cross_days(c, kama)
        perf_sett = round((price/c[-6]-1)*100, 2) if len(c) >= 6 else 0
        perf_mese = round((price/c[-23]-1)*100, 2) if len(c) >= 23 else 0
        vr = vol_ratio(v)
        edate = entry_date(c, kama, t)

        tipo = ""
        if trd == 'VERDE' and above_kama and er >= 0.50 and baff >= 3 and mm_align: tipo = 'LONG'
        elif above_kama and baff >= 3 and trd in ('VERDE','GRIGIO'): tipo = 'EARLY'
        elif above_kama and baff >= 1 and trd in ('VERDE','GRIGIO'): tipo = 'WATCH'
        elif trd == 'ROSSO' and cross <= 3 and baff >= 3: tipo = 'ROSSO+'

        uscita = ""
        if not above_kama and trd == 'ROSSO': uscita = 'STOP'
        elif not above_kama: uscita = 'USCITA'
        elif above_kama and (ao_now <= 0 or trd == 'GRIGIO'): uscita = 'ATTENZIONE'

        score = (er*30 + min(baff,10)*5 + min(abs(pk_pct),5)*3
                 + max(-10,min(5,perf_sett))*4
                 + max(-20,min(10,perf_mese))*2
                 + (10 if mm_align else 0) + (5 if ao_now > 0 else 0)
                 + (20 if cross<=3 else 12 if cross<=10 else 5 if cross<=20 else 0))
        if trd == 'ROSSO': score *= 0.6
        score = int(max(0, min(200, round(score))))

        return {
            "ticker": info["t"], "display": info["t"], "categoria": info["c"],
            "price": round(price, 4), "kama": round(k_now, 4) if k_now else None,
            "er": round(er, 3), "baff": baff, "trendycator": trd,
            "rsi": rsi, "mmAlign": mm_align, "aoPos": ao_now > 0,
            "pkPct": pk_pct, "perfSett": perf_sett, "perfMese": perf_mese,
            "volRatio": vr, "score": score, "tipo": tipo, "uscita": uscita,
            "entryDate": edate, "cross": cross, "error": None
        }
    except Exception as e:
        return {**base, "error": str(e)}

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print(f"🦅 RAPTOR Alert - Fetch {len(TICKERS)} ETF")
    results = []
    ok, err = 0, 0
    for i, ticker in enumerate(TICKERS):
        print(f"  [{i+1}/{len(TICKERS)}] {ticker['t']}...", end=" ", flush=True)
        r = analyze(ticker)
        results.append(r)
        if r["error"]:
            print(f"✗ {r['error']}")
            err += 1
        else:
            print(f"✓ {r['tipo'] or '—'} score={r['score']}")
            ok += 1
        time.sleep(0.3)  # rate limit gentile

    updated = datetime.now().strftime("%d/%m/%Y %H:%M")
    output = {
        "updated": updated,
        "total": len(results),
        "ok": ok,
        "errors": err,
        "data": results
    }

    os.makedirs("data", exist_ok=True)
    with open("data/etf.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, separators=(',', ':'))

    print(f"\n✅ Completato: {ok} ok, {err} errori → data/etf.json")
    print(f"   Aggiornato: {updated}")

if __name__ == "__main__":
    main()
