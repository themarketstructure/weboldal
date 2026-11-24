#!/usr/bin/env python3
"""Záróár-frissítés a themarketstructure.hu pozíciótáblájához (GitHub Actions, 2026-11-24).
Az index.html TRADES listájából a nyitott pozíciók belépő árát olvassa (entry: '382,55 $ (átlag)'),
a Yahoo Finance chart API-ból a legutóbbi lezárt NY-i napi záróárat, és átírja a ret és asof mezőket.
Darabszámot, belépőt, célárat NEM módosít (az a vételnél kézzel történik)."""
import json, re, sys, urllib.request, datetime as dt
P = "index.html"
s = open(P, encoding="utf-8").read()
sor = re.compile(r"\{t:'([A-Z.]+)',[^{}]*?entry:'([^']*)'[^{}]*?ret:(-?[\d.]+|null),status:'open',asof:'[^']*'\}")
def zaro(t):
    u = f"https://query1.finance.yahoo.com/v8/finance/chart/{t}?range=7d&interval=1d"
    r = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"})
    j = json.load(urllib.request.urlopen(r, timeout=30))["chart"]["result"][0]
    m = j["meta"]; ts = j["timestamp"]; c = j["indicators"]["quote"][0]["close"]
    # a mai gyertya csak zárás után számít: ha a piac még nyitva (regularMarketTime < a mai zárás), az utolsó előtti
    nap = [(dt.datetime.utcfromtimestamp(a).date(), b) for a, b in zip(ts, c) if b is not None]
    zar = m.get("currentTradingPeriod", {}).get("regular", {}).get("end")
    if zar and m.get("regularMarketTime", 0) < zar and len(nap) > 1: nap = nap[:-1]
    return nap[-1]
valt = []; datumok = set()
def csere(mt):
    t, entry = mt.group(1), mt.group(2)
    num = re.search(r"([\d ]+(?:,\d+)?)", entry.replace(" ", " "))
    if not num: return mt.group(0)
    belepo = float(num.group(1).replace(" ", "").replace(",", "."))
    try: nap, ar = zaro(t)
    except Exception as e: print("hiba", t, e); return mt.group(0)
    datumok.add(nap); ret = round((ar / belepo - 1) * 100, 2)
    valt.append(f"{t} {ar:.2f} {ret:+.2f}%")
    x = re.sub(r"ret:(-?[\d.]+|null),", f"ret:{ret},", mt.group(0))
    return re.sub(r"asof:'[^']*'", f"asof:'{nap.month:02d}.{nap.day:02d}. NY záró, Yahoo Finance'", x)
uj = sor.sub(csere, s)
if len(datumok) > 1: print("FIGYELEM: eltérő dátumok", datumok)
print("\n".join(valt))
if uj != s:
    open(P, "w", encoding="utf-8").write(uj); print("index.html frissítve")
else: print("nincs változás")
