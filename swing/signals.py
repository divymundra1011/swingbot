import numpy as np, pandas as pd
from . import config as cf

def build(df):
    P = lambda col: df.pivot(index="date", columns="sym", values=col)
    O,H,L,C,Craw = P("oa"),P("ha"),P("la"),P("ca"),P("c")
    V,T,D = P("vol"),P("turn"),P("deliv")
    tr = pd.concat([(H-L).stack(), (H-C.shift()).abs().stack(), (L-C.shift()).abs().stack()], axis=1).max(axis=1).unstack()
    ATR = tr.rolling(14).mean(); S200 = C.rolling(200).mean()
    VOLR = V / V.rolling(20).mean().shift(1)
    T60 = T.rolling(60).mean(); rank = T60.rank(axis=1, ascending=False)
    liquid = (T60 > cf.MIN_TURNOVER_LAKH) & (Craw > cf.MIN_PRICE) & (C.rolling(200).count() == 200)
    bucket = pd.DataFrame(np.select([rank<=100, rank<=250, rank<=500],[0,1,2],3), index=C.index, columns=C.columns)
    r3 = C / C.shift(3) - 1
    return dict(O=O,H=H,L=L,C=C,Craw=Craw,V=V,T=T,D=D,ATR=ATR,S200=S200,VOLR=VOLR,T60=T60,bucket=bucket,r3=r3,liquid=liquid)

def strategy_dip(X):
    """Sharp 3-day drop (8-25%) on >2x volume with delivery >40%."""
    return X["liquid"] & (X["r3"] < -0.08) & (X["r3"] > -0.25) & (X["VOLR"] > 2) & (X["D"] > 40)

def make_calls(X, equity, cash, open_risk, held):
    last = X["C"].index[-1]
    sig = strategy_dip(X).loc[last]; syms = list(sig[sig].index)
    calls = []
    for s in syms:
        cl = float(X["Craw"].at[last, s]); at = float(X["ATR"].at[last, s] * cl / X["C"].at[last, s]); risk = cf.ATR_STOP * at
        if not np.isfinite(risk) or risk / cl < 0.01 or s in held: continue
        b = int(X["bucket"].at[last, s])
        calls.append(dict(sym=s, tier=cf.TIER_NAMES[b], b=b, close=round(cl,2), drop3d=round(float(X["r3"].at[last,s])*100,1),
            vol_x=round(float(X["VOLR"].at[last,s]),1), deliv=round(float(X["D"].at[last,s])),
            entry_lo=round(cl*0.995,2), entry_hi=round(cl*1.015,2), stop=round(cl-risk,2), target=round(cl+cf.REWARD_R*risk,2), risk_pct=round(risk/cl*100,1)))
    calls.sort(key=lambda x: x["drop3d"])
    for x in calls:
        size = min(equity*cf.RISK_PER_TRADE/(x["risk_pct"]/100), equity*cf.TIER_CAP[x["b"]], cash)
        qty = int(size // x["close"]); amt = qty * x["close"]; ramt = qty * (x["close"] - x["stop"])
        ok = qty > 0 and amt >= cf.MIN_POSITION and open_risk + ramt <= equity*cf.OPEN_RISK_CAP
        x.update(qty=qty, size=round(amt), risk_amt=round(ramt), take=bool(ok))
        if ok: cash -= amt; open_risk += ramt
    return calls, str(last.date())
