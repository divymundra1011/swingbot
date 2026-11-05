import os, glob, time, datetime as dt, requests, numpy as np, pandas as pd
from concurrent.futures import ThreadPoolExecutor
RAW = os.environ.get("RAW_DIR", "raw")
URL = "https://nsearchives.nseindia.com/products/content/sec_bhavdata_full_{d}.csv"
HDR = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)", "Accept": "*/*", "Referer": "https://www.nseindia.com/"}

def _fetch(day):
    f = os.path.join(RAW, day.strftime("%Y%m%d") + ".csv")
    if os.path.exists(f) and os.path.getsize(f) > 10000: return "cached"
    for _ in range(4):
        try:
            r = requests.get(URL.format(d=day.strftime("%d%m%Y")), headers=HDR, timeout=30)
            if r.status_code == 200 and r.content[:6] == b"SYMBOL":
                open(f, "wb").write(r.content); return "ok"
            if r.status_code == 404: return "holiday"
        except Exception: time.sleep(2)
    return "fail"

def download(weekdays):
    os.makedirs(RAW, exist_ok=True)
    end = dt.date.today(); start = end - dt.timedelta(days=int(weekdays * 1.45))
    days = [start + dt.timedelta(n) for n in range((end - start).days + 1)]
    days = [d for d in days if d.weekday() < 5]
    with ThreadPoolExecutor(6) as ex: res = list(ex.map(_fetch, days))
    out = {k: res.count(k) for k in set(res)}
    print("download:", out)
    return out

def load_prices():
    cols = ["SYMBOL","SERIES","DATE1","PREV_CLOSE","OPEN_PRICE","HIGH_PRICE","LOW_PRICE","CLOSE_PRICE","TTL_TRD_QNTY","TURNOVER_LACS","DELIV_PER"]
    dfs = []
    for f in sorted(glob.glob(RAW + "/*.csv")):
        if open(f, "rb").read(6) != b"SYMBOL": continue
        d = pd.read_csv(f, skipinitialspace=True, encoding="latin-1"); d.columns = [c.strip() for c in d.columns]
        d = d[d["SERIES"].str.strip().isin(["EQ", "BE"])][cols]; dfs.append(d)
    df = pd.concat(dfs, ignore_index=True)
    df.columns = ["sym","series","date","prev","o","h","l","c","vol","turn","deliv"]
    df["date"] = pd.to_datetime(df["date"].str.strip(), format="%d-%b-%Y"); df["sym"] = df["sym"].str.strip()
    for k in ["prev","o","h","l","c","vol","turn","deliv"]: df[k] = pd.to_numeric(df[k], errors="coerce")
    df = df.sort_values(["sym","date"]).drop_duplicates(["sym","date"])
    last_c = df.groupby("sym")["c"].shift(1)
    ratio = (df["prev"] / last_c).where(last_c > 0)
    ratio = ratio.where((ratio < 0.97) | (ratio > 1.03), 1.0).fillna(1.0)
    raw = (df["c"] / last_c).where(last_c > 0)
    ratio = ratio.where(~((ratio == 1.0) & (raw < 0.70)), raw)    # NSE prev-close is unadjusted lately; >30% 1-day fall = split/bonus
    f = ratio.groupby(df["sym"]).transform(lambda s: s[::-1].shift(1).fillna(1.0).cumprod()[::-1])
    for k in ["o","h","l","c"]: df[k + "a"] = df[k] * f
    return df
