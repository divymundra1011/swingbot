# Swing Desk (paper mode)

Scans NSE cash stocks after close, makes long-only calls with entry zone, stop, target and quantity for a Rs 5.5 lakh account,
runs an automatic **paper** book, sends Telegram/email reports, and publishes a dashboard.

**Status: the strategy has NOT passed out-of-sample testing. Paper trade only.**

## One-time setup (about 30 minutes)
1. Make the repo **Public** (free GitHub Pages needs this). It holds code only, no passwords.
2. Upload every file in this folder. If `.github/workflows` is missing after upload, use *Add file > Create new file*, type
   `.github/workflows/daily.yml` as the name, paste the text of `WORKFLOW_daily.yml.txt`, commit. Repeat for `watch.yml`.
3. *Settings > Pages > Build and deployment*: Source = **Deploy from a branch**, Branch = **main**, folder = **/docs**. Save.
   Your dashboard will be at `https://<your-username>.github.io/<repo-name>/`.
4. *Settings > Secrets and variables > Actions > New repository secret*, add:
   - `TELEGRAM_TOKEN`: message **@BotFather** on Telegram, send `/newbot`, follow steps, copy the token.
   - `TELEGRAM_CHAT_ID`: message your new bot "hi", then message **@userinfobot** to read your numeric id.
   - `GMAIL_USER`: your Gmail address.
   - `GMAIL_APP_PASSWORD`: Google Account > Security > 2-Step Verification (turn on) > App passwords > create one.
   - `MAIL_TO` (optional): where to send reports, defaults to GMAIL_USER.
5. *Actions* tab: enable workflows if asked, open **Daily run**, press **Run workflow**. First run takes a few minutes.
   If it fails, open the run, copy the red error text and send it to Claude.

## What runs when
- **Daily run**, 18:00 IST weekdays: downloads NSE data, updates the paper book, makes tomorrow's calls, sends Telegram + email with Excel and PDF.
- **Live watch**, every 15 min in market hours: alerts when a call's price enters its entry zone, or a paper position hits stop or target.
  Live prices come from Yahoo Finance via `yfinance` (free, unofficial, can lag or fail).

## Change settings
Edit `swing/config.py` (capital, risk per trade, stop distance, target, holding days).

## Known limits
- Not yet run on GitHub's servers. NSE may block cloud IPs; if downloads fail, tell Claude.
- Paper book enters at the next open if inside the entry zone; it does not model circuit limits or partial fills.
- No news or fundamentals filter yet.
