# Day Trader Skill: India (NSE) edition

8 Claude skills for day trading NSE stocks: scan the Nifty 500, track the news, time every entry and exit, and replay every outcome before you risk a rupee.

A patched copy of [Jake Schincariol's day-trader-skill](https://github.com/Jakeschincariol/day-trader-skill) (MIT), made for Indian stocks only:

- India time (IST, UTC+5:30, no daylight saving), NSE session 9:15 to 15:30, NSE 2026 holidays.
- Plain NSE symbols (RELIANCE, TCS, M&M, BAJAJ-AUTO). The tools add `.NS` for Yahoo.
- The scanner's universe is the Nifty 500 (`trader-scanner/nifty500.txt`, from niftyindices.com, read 2026-11-07).
- Prices and limits in rupees (₹).
- No order is ever placed by this pack. You place your own orders in your broker's app (Zerodha Kite, Groww, Upstox...).

The US-only skills of the original (trader-analyst on SEC filings, trader-pelosi on US Congress trades, and trader-broker on Alpaca, which cannot trade NSE stocks) are not in this edition.

Free, MIT, no signup, no API key. The tools are plain Python that read free
public data: Yahoo Finance charts and Google News (India edition).

Not financial advice. A scan, a replay or a signal is not a reason to buy anything.

## Install

Paste this into Claude:

```
https://github.com/mshakirc/day-trader-skill-india

install skill
```

Or as a plugin, in Claude Code:

```
/plugin marketplace add mshakirc/day-trader-skill-india
/plugin install day-trader-skill-india@day-trader-skill-india
```

Installed as a plugin, the skills show up as
`/day-trader-skill-india:trader-scanner` and so on. Copy the folders instead if
you want plain `/trader-scanner`:

```bash
git clone https://github.com/mshakirc/day-trader-skill-india.git
cp -r day-trader-skill-india/trader-* ~/.claude/skills/
```

The tools need Python 3.8 or newer. Nothing to pip install.

## The eight

| command | job | what it does |
| --- | --- | --- |
| `/trader-scanner` | Chart Scanner | Scans the Nifty 500 for setups: opening-range breakouts, flags, oversold bounces. |
| `/trader-news` | News Monitor | Tracks the news on every stock you watch and flags what moves it. |
| `/trader-entry` | Entry Timer | Watches a setup bar by bar and tells you the moment to get in. |
| `/trader-exit` | Exit Planner | Sets your stop and your target before you enter, so you know when to get out. |
| `/trader-timemachine` | Time Machine | Replays the trade before you risk a rupee: 10,000 simulated sessions plus every past time the setup fired. |
| `/trader-budget` | Budget Manager | Sizes every position to your budget and your max loss per trade. |
| `/trader-risk` | Risk Manager | Checks every trade against your limits and stops anything over them. |
| `/trader-alerts` | Price Alerts | Rings when a price, a stop or the opening bell hits. |

## How to use it

Everything lands in a `trader/` folder in your project, and each skill reads
what the last one wrote:

```
scanner -> news -> entry -> exit -> timemachine -> budget -> risk -> you place it in your broker's app
alerts: stop, target, flat by 15:25                                (while it is open)
```

An example with real data: TATAELXSI, Friday 13 November 2026.

1. **`/trader-scanner`** before the open: 499 of the Nifty 500 charts came
   back, 126 matched a setup (98 of them 20-day closing-high breakouts). At
   9:45 the opening-range scan found 113 of the 200 most traded charts above
   their 9:15 to 9:30 range. TATAELXSI's range was 3,821.60 to 3,865.10.
2. **`/trader-news`**: the day's TATAELXSI headlines from Google News India,
   in IST, with the move against yesterday's close.
3. **`/trader-entry`**: at 9:43 it said waiting (no entries before 9:45, and
   the 9:40 bar was still forming). At 9:45 it said triggered: the 9:40 bar
   closed at 3,881, 0.41 % over the range high.
4. **`/trader-exit`** set the plan before the entry: stop at the range's
   midpoint, 3,843.35, so 37.65 a share at risk; target two times that risk,
   3,956.30; flat by 15:25 either way.
5. **`/trader-timemachine`** replayed the rest of the day 10,000 times from
   TATAELXSI's own 5-minute bars over the previous 59 sessions (seed 19):
   target first 9.0 %, stop first 50.4 %, still open at 15:30 40.6 %. The
   same rule on those 59 real sessions fired 29 times: 6 targets, 16 stops,
   7 neither. Its verdict: strongly toward the stop.
6. **`/trader-budget`** with ₹1,00,000 and a ₹1,000 max loss per trade: the
   max loss allows 26 shares, but 26 x 3,881 is more than the account, so 25
   shares (₹97,025). Max loss at the stop: ₹941.25.
7. **`/trader-risk`** checks it against your limits: max loss, daily loss,
   trades per day, reward to risk, the entry window, position size and cash.
   PASS, with the numbers. 27 shares would be BLOCKED, with the reasons.
8. **You** decide, and if you take it you place it yourself in your broker's
   app, with the stop-loss.
9. **`/trader-alerts`** rings on the stop, the target and at 15:25 to close
   whatever is still open.

## The tools

All standard-library Python. The data tools read public endpoints and are
polite about it.

```bash
python3 trader-scanner/scan.py daily                                   # pre-market setups, Nifty 500
python3 trader-scanner/scan.py orb --at 09:45                          # opening-range breakouts so far
python3 trader-news/news.py --tickers TATAELXSI --hours 12             # headlines, today's move
python3 trader-entry/entry.py check TATAELXSI                          # waiting / triggered / expired
python3 trader-entry/entry.py watch TATAELXSI --every 30               # bar by bar until it triggers
python3 trader-exit/exit.py plan --write                               # -> trader/plan.json
python3 trader-timemachine/timemachine.py run --write                  # 10,000 replays + the history
python3 trader-budget/size.py --write                                  # -> trader/orders.json
python3 trader-risk/check.py                                           # PASS / BLOCK per order
python3 trader-alerts/alerts.py add --from-plan                        # stop, target, flat by close
python3 trader-alerts/alerts.py check                                  # rings what hit, once
```

Start your rules from `trader-budget/config.example.json` (₹1,00,000 budget,
₹1,000 max loss per trade, ₹3,000 a day, no entries before 9:45 or after
15:00, flat by 15:25). The money keys still end in `_usd` so configs from the
original keep working; they are read as rupees.

## Tests

```bash
python3 -m unittest discover -s tests -v
```

The unit tests come from the US original and run on its US fixtures (TSLA,
New York hours), so many of them fail on this edition: they check US times
and dollar amounts, not bugs. The NSE behaviour was checked by running each
tool live on 13 November 2026 (the numbers above). NSE fixtures and tests are
still to be written.

`india_patch.py` re-applies the first round of India changes (clock, session,
holidays, symbols, ₹) to a fresh clone of the original. The later changes
(removing the US-only skills, the news rewrite, the docs) live only in this
repo.

## Fine print

**Not financial advice.** This is software that reads public data and does
arithmetic. It does not know your situation and it cannot see the future.
SEBI's own studies found that most individual intraday traders in equity
lose money. You can lose money. Decide for yourself, and talk to a
SEBI-registered adviser if you need advice.

**Nothing places an order.** This pack only reads, plans and checks. You place
every order yourself, in your broker's app, after `/trader-risk` passes it.

**The Time Machine is a simulation, not a prediction.** It is built from the
stock's own last 60 days of 5-minute bars. The future can do things those 60
days never did: results, a SEBI order, a circuit, a headline. Treat its odds
as a reality check, never as a promise.

**A stop is a plan, not a guarantee.** In a fast market, across a gap, or when
a stock hits its circuit limit, a stop order can fill well past its price or
not at all. The max loss shown is the loss at the stop price.

**The data is free and unofficial.** Yahoo Finance's chart endpoint is not an
official API: it can lag, change or rate-limit you, and its NSE bars have
gaps (the Time Machine says how many it filled). Check anything that matters
against your broker before you act on it.

**Costs and taxes.** Brokerage, STT, exchange charges, GST and stamp duty are
not in these numbers, and intraday gains are taxed as speculative business
income. Nothing here is tax advice.

## Files

```
trader-scanner/     SKILL.md, scan.py, nifty500.txt
trader-news/        SKILL.md, news.py
trader-entry/       SKILL.md, entry.py
trader-exit/        SKILL.md, exit.py
trader-timemachine/ SKILL.md, timemachine.py
trader-budget/      SKILL.md, size.py, config.example.json, targets.example.json
trader-risk/        SKILL.md, check.py
trader-alerts/      SKILL.md, alerts.py, alerts.example.json
india_patch.py      the first round of India changes, for a fresh clone of the original
tests/              unittest suite from the US original + its fixtures
```

MIT. Original by [Jake Schincariol](https://opusjake.ai). India edition by [Shakir C](https://github.com/mshakirc).
