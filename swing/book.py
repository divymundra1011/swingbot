import json, os, datetime as dt
from . import config as cf
STATE = "docs/state.json"

def load():
    if os.path.exists(STATE): return json.load(open(STATE))
    return dict(capital=cf.CAPITAL, last_processed=None, pending=dict(date=None, calls=[]), positions=[], history=[], equity_log=[], alerts_sent=[], asof=None, calls=[])

def save(s):
    os.makedirs("docs", exist_ok=True); json.dump(s, open(STATE, "w"), default=str)

def realized(s): return sum(h["pnl"] for h in s["history"])
def cash(s): return s["capital"] + realized(s) - sum(p["entry"]*p["qty"] for p in s["positions"])
def equity_closed(s): return s["capital"] + realized(s)
def open_risk(s): return sum((p["entry"]-p["stop"])*p["qty"] for p in s["positions"])

def _close(s, p, price, day, why):
    pnl = (price - p["entry"]) * p["qty"] - cf.COST_ROUNDTRIP * p["entry"] * p["qty"]
    s["history"].append(dict(sym=p["sym"], entry=p["entry"], exit=round(price,2), qty=p["qty"], pnl=round(pnl,2), opened=p["open_date"], closed=day, why=why))
    s["positions"].remove(p)

def process_day(s, df, day, notes):
    """Apply one trading day (raw prices) to the paper book. Mirrors the backtest rules."""
    d = df[df["date"] == day].set_index("sym")
    pend = s["pending"]
    # 1) pending calls from an earlier day: enter at the open if it is inside the zone
    if pend["date"] and pend["date"] < str(day.date()):
        for c in pend["calls"]:
            if not c.get("take") or c["sym"] not in d.index or any(p["sym"] == c["sym"] for p in s["positions"]): continue
            op = float(d.at[c["sym"], "o"])
            if op > c["entry_hi"]: notes.append(f"Missed {c['sym']}: opened {op} above zone"); continue
            qty = min(c["qty"], int(cash(s) // op))
            if qty <= 0: continue
            risk = c["close"] - c["stop"]
            s["positions"].append(dict(sym=c["sym"], entry=round(op,2), qty=qty, stop=round(op-risk,2), target=round(op+cf.REWARD_R*risk,2), open_date=str(day.date()), days=0, last=round(op,2)))
            notes.append(f"BUY {c['sym']} {qty} @ {op:.2f} (stop {op-risk:.2f}, target {op+cf.REWARD_R*risk:.2f})")
        s["pending"] = dict(date=None, calls=[])
    # 2) manage every open position with the day's high/low/close
    for p in list(s["positions"]):
        if p["sym"] not in d.index: continue
        r = d.loc[p["sym"]]; p["days"] = p.get("days", 0) + 1; p["last"] = round(float(r["c"]),2)
        if r["l"] <= p["stop"]:
            px = min(p["stop"], float(r["o"])); _close(s, p, px, str(day.date()), "stop"); notes.append(f"EXIT {p['sym']} stop @ {px:.2f}")
        elif r["h"] >= p["target"]:
            px = max(p["target"], float(r["o"])) if r["o"] > p["target"] else p["target"]; _close(s, p, px, str(day.date()), "target"); notes.append(f"BOOK {p['sym']} target @ {px:.2f}")
        elif p["days"] >= cf.MAX_HOLD_DAYS:
            _close(s, p, float(r["c"]), str(day.date()), "time"); notes.append(f"EXIT {p['sym']} time limit @ {float(r['c']):.2f}")
    unreal = sum((p["last"] - p["entry"]) * p["qty"] for p in s["positions"])
    s["equity_log"].append([str(day.date()), round(equity_closed(s) + unreal)])
    s["last_processed"] = str(day.date())
