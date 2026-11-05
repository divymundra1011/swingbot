"""Runs every ~15 min in market hours: live-price zone/stop/target alerts for today's calls and open positions."""
import datetime as dt, pytz
from swing import book, notify

def main():
    now = dt.datetime.now(pytz.timezone("Asia/Kolkata"))
    if now.weekday() > 4 or not (dt.time(9,15) <= now.time() <= dt.time(15,30)): print("Market closed"); return
    s = book.load(); names = sorted({c["sym"] for c in s.get("pending", {}).get("calls", []) if c.get("take")} | {p["sym"] for p in s["positions"]})
    if not names: print("Nothing to watch"); return
    import yfinance as yf
    px = {}
    for n in names:
        try:
            h = yf.Ticker(n + ".NS").history(period="1d", interval="1m")
            if len(h): px[n] = float(h["Close"].iloc[-1])
        except Exception as e: print("price fail", n, e)
    sent = set(s.get("alerts_sent", [])); msgs = []; day = str(now.date())
    for c in s.get("pending", {}).get("calls", []):
        k = f"zone:{c['sym']}:{day}"
        if c.get("take") and c["sym"] in px and c["entry_lo"] <= px[c["sym"]] <= c["entry_hi"] and k not in sent:
            msgs.append(f"BUY ZONE {c['sym']} now {px[c['sym']]:.2f} (zone {c['entry_lo']}-{c['entry_hi']}) qty {c['qty']} stop {c['stop']} target {c['target']}"); sent.add(k)
    for p in s["positions"]:
        if p["sym"] not in px: continue
        p["last"] = round(px[p["sym"]], 2)
        for tag, hit in [("stop", px[p["sym"]] <= p["stop"]), ("target", px[p["sym"]] >= p["target"])]:
            k = f"{tag}:{p['sym']}:{day}"
            if hit and k not in sent: msgs.append(f"{'EXIT (stop hit)' if tag=='stop' else 'BOOK PROFIT (target hit)'} {p['sym']} now {px[p['sym']]:.2f}"); sent.add(k)
    s["alerts_sent"] = sorted(sent); s["live_time"] = now.strftime("%Y-%m-%d %H:%M"); book.save(s)
    if msgs: notify.telegram("Swing Desk live (PAPER)\n" + "\n".join(msgs))
    print("watched", len(names), "alerts", len(msgs))
if __name__ == "__main__": main()
