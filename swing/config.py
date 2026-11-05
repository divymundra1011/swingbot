"""All tunable settings live here. Change numbers here, not in the code."""
CAPITAL = 550000          # starting paper capital (INR)
RISK_PER_TRADE = 0.015    # 1.5% of equity risked per trade
OPEN_RISK_CAP = 0.06      # total open risk cap (6% of equity)
TIER_CAP = {0: 0.20, 1: 0.20, 2: 0.15, 3: 0.05}   # max position size per liquidity tier
MIN_POSITION = 10000
ATR_STOP = 3.0            # stop = entry - 3 x ATR
REWARD_R = 3.0            # target = entry + 3 x risk
MAX_HOLD_DAYS = 15
MIN_TURNOVER_LAKH = 100   # avg daily turnover > Rs 1 crore
MIN_PRICE = 10
HISTORY_WEEKDAYS = 420    # how much bhavcopy history to load each run
TIER_NAMES = {0: "Top 100 by turnover", 1: "101-250", 2: "251-500", 3: "Below 500"}
COST_ROUNDTRIP = 0.0035
