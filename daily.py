"""Runs after market close: update data, run the paper book, make new calls, write dashboard + reports, send alerts."""
import os, json, pandas as pd
from swing import config as cf, data, signals, book, reports, notify

def main():
    if not os.environ.get("SKIP_DOWNLOAD"): data.download(cf.HISTORY_WEEKDAYS)
    df = data.load_prices(); days = sorted(df["date"].unique()); last = pd.Timestamp(days[-1])
    s = book.load(); notes = []
    if s["last_processed"] is None:
        s["last_processed"] = str(pd.Timestamp(days[-2]).date())      # fresh start: begin paper book from the latest close
    todo = [pd.Timestamp(d) for d in days if str(pd.Timestamp(d).date()) > s["last_processed"]]
    if not todo: print("No new trading day. Latest:", last.date())
    for d in todo: book.process_day(s, df, d, notes)
    X = signals.build(df[df["date"] >= (last - pd.Timedelta(days=620))])
    held = {p["sym"] for p in s["positions"]}
    calls, asof = signals.make_calls(X, book.equity_closed(s), book.cash(s), book.open_risk(s), held)
    s["calls"], s["asof"] = calls, asof
    s["pending"] = dict(date=asof, calls=calls)
    s["alerts_sent"] = []
    s.setdefault("backtest", json.load(open("docs/backtest.json")) if os.path.exists("docs/backtest.json") else None)
    book.save(s)
    os.makedirs("docs", exist_ok=True)
    reports.excel(s, "docs/report_latest.xlsx"); reports.pdf(s, "docs/report_latest.pdf", notes)
    take = [c for c in calls if c["take"]]
    lines = [f"Swing Desk (PAPER) | close {asof}"] + notes
    lines += [f"CALL {c['sym']} buy {c['entry_lo']}-{c['entry_hi']} qty {c['qty']} stop {c['stop']} target {c['target']}" for c in take] or ["No new calls today."]
    eq = s["equity_log"][-1][1] if s["equity_log"] else s["capital"]
    lines.append(f"Paper account Rs {eq:,.0f} | open {len(s['positions'])}")
    msg = "\n".join(lines); notify.telegram(msg)
    notify.email(f"Swing Desk report {asof}", msg, ["docs/report_latest.xlsx", "docs/report_latest.pdf"])
if __name__ == "__main__": main()
