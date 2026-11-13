---
name: trader-alerts
description: >-
  Price Alerts. Rings when a price, a stop or the opening bell hits. Turns
  the trade plan into three alerts in one go (the stop, the target and "flat
  by close" at your flat-by time), plus above / below / stop / target levels,
  percent moves from the previous close, any time of day, and the NSE
  opening bell, each ringing once so you are not spammed. Knows NSE hours
  (9:15 to 15:30 IST) and the 2026 NSE holidays, works out India time
  itself, fetches free delayed quotes (Yahoo chart JSON) one ticker at a
  time, and writes trader/prices.json for sizing and the risk check. Use
  when the user says "alert me when", "tell me if RELIANCE hits", "watch my
  stop", "watch my trade", "remind me to close by 3:25", "is the market
  open", "when does the market open", "get me a price", or right after
  /trader-exit writes a plan.
argument-hint: "[ticker] [price]"
---

> **India (NSE) edition.** This copy is patched for Indian stocks: IST clock, NSE session 9:15 AM to 3:30 PM, NSE 2026 holidays, prices in ₹. Use plain NSE symbols (RELIANCE, TCS, M&M, BAJAJ-AUTO); the scripts add `.NS` for Yahoo. Times you type (--now, --at, entry times) are IST. The scanner's universe is the Nifty 500.

# trader-alerts

Price Alerts watches the numbers so the user does not have to stare at a
chart. An alert is information, never an order: when a stop alert rings,
nothing is sold by this skill. If the user placed a bracket (or stop-loss) order
in their broker's app, that order does the work; the alerts tell the
user what happened and when it is time to be flat.

`${CLAUDE_SKILL_DIR}` below is this skill's folder (where this SKILL.md lives).

```bash
python3 "${CLAUDE_SKILL_DIR}/alerts.py" clock                          # NSE open or closed, next open
python3 "${CLAUDE_SKILL_DIR}/alerts.py" add --from-plan                # stop, target, flat by close from trader/plan.json
python3 "${CLAUDE_SKILL_DIR}/alerts.py" add --opening-bell
python3 "${CLAUDE_SKILL_DIR}/alerts.py" add --symbol TATAELXSI --stop 3843.35
python3 "${CLAUDE_SKILL_DIR}/alerts.py" add --symbol TATAELXSI --target 3956.30
python3 "${CLAUDE_SKILL_DIR}/alerts.py" add --at 15:25 --label "flat by close" --before-close
python3 "${CLAUDE_SKILL_DIR}/alerts.py" add --symbol RELIANCE --pct 3
python3 "${CLAUDE_SKILL_DIR}/alerts.py" check                          # exit 0 = something rang
python3 "${CLAUDE_SKILL_DIR}/alerts.py" quote TATAELXSI --write            # -> trader/prices.json
python3 "${CLAUDE_SKILL_DIR}/alerts.py" quote --holdings --write       # portfolio + plan tickers
python3 "${CLAUDE_SKILL_DIR}/alerts.py" list
python3 "${CLAUDE_SKILL_DIR}/alerts.py" reset tataelxsi-plan-stop
```

`--now "2026-11-13 15:25"` pins the clock (India time, IST); `--offline DIR`
reads saved quote files instead of the network.

## What it reads and writes

| file | what |
| --- | --- |
| `trader/plan.json` | the trade from trader-exit, for `add --from-plan` |
| `trader/alerts.json` | the rules (`alerts.example.json` in this folder) |
| `trader/state/alerts.json` | which rules rang and when, so each rings once |
| `trader/prices.json` | the latest quotes, merged in, for trader-budget and trader-risk |
| `trader/portfolio.json` | the tickers held, for `quote --holdings` |

## Rule types

| type | rings when | rings again |
| --- | --- | --- |
| `above` / `target` | price at or above `price` | after `reset`, or on its own if `"rearm": true` and the price fell back |
| `below` / `stop` | price at or below `price` | same |
| `pct_move` | moved `pct` percent from the previous close (or `ref`), optional `direction` up or down | once per day at most |
| `time` | the India (IST) clock passed `at` ("15:25") on a trading day | once per trading day |
| `opening_bell` | the NSE is open (9:15) | once per trading day |

A rule with `"date"` is watched on that India (IST) date only; `--from-plan`
rules carry the plan's date, so yesterday's stop never rings today. The NSE has
no scheduled half days, so a `time` rule rings at its own time every trading
day.

## Quotes

- `yahoo` (default): `query2.finance.yahoo.com/v8/finance/chart/<TICKER>.NS`,
  an unofficial free JSON endpoint, one request per ticker, half a second
  apart. On a 429 it waits and tries once more; on a 429 or a 5xx after that
  it tries `query1`. It identifies itself as `day-trader-skill/2.0`.
- `stooq` is left over from the US edition and has no NSE quotes. Do not use it.
- Free quotes are unofficial, delayed and can lag. They are fine for alerts
  and for checking a size, not for timing an order. The broker's price is the
  one that fills. Each price in `trader/prices.json` keeps its quote time, and
  trader-risk only uses one under 15 minutes old.
- If Yahoo is down, the user can read the price from their broker's app and
  you write it into `trader/prices.json` as
  `{"as_of": "...Z", "prices": {"TATAELXSI": 3835.00}}`.

## The NSE clock

Regular session 9:15 a.m. to 3:30 p.m. India time (IST, UTC+5:30, no
daylight saving), closed on weekends and on the NSE's 2026 equity trading
holidays: Jan 15, Jan 26, Mar 3 (Holi), Mar 26, Mar 31, Apr 3 (Good Friday),
Apr 14, May 1, May 28, Jun 26, Sep 14, Oct 2, Oct 20 (Dussehra), Nov 10,
Nov 24 (Guru Nanak Jayanti) and Dec 25. For 2027 it says the holiday list is
unknown until it is added. Muhurat trading on Diwali is a special session
and is not modelled.

The clock is worked out in the tool, so it ignores the computer's own zone.

## Steps

1. Right after trader-exit writes the plan, run `add --from-plan`. Confirm
   the three alerts back to the user: the stop, the target and the flat-by time.
2. Run `check` while the trade is open: every few minutes from a Claude
   scheduled task or `/loop`. Each run fetches only the tickers in today's
   rules and rings each alert once. A check reads the latest delayed quote;
   it is not a live feed, and a price can pass a level between two checks.
3. Tell the user what rang in one line each. A stop or target alert means a
   stop-loss or target order may have filled: the user checks their positions
   in their broker's app. "Flat by close" means close anything still open,
   in the broker's app, by the user. Never act for them.

## Example: a real NSE day

TATAELXSI on Friday 2026-11-13: entry 3,881 at 9:45 AM, stop 3,843.35, target
3,956.30, flat by 15:25. `add --from-plan` writes `tataelxsi-plan-stop`,
`tataelxsi-plan-target` and `tataelxsi-flat-by` for that day. A `check` at
15:25:

```
NSE OPEN (2026-11-13 15:25 India (IST), regular session).
ALERT TATAELXSI is ₹3,835.00: at or below your stop ₹3,843.35 (plan stop: opening-range midpoint).
ALERT Flat by close: it is 15:25 India (IST) (set for 15:25), the market closes at 15:30. If TATAELXSI is still open, close it yourself in your broker's app.
```

Each alert rings once. The next trading day the plan's three alerts are no
longer watched; with `add --opening-bell`, the bell rings at 9:15.

## Rules

- An alert is a fact about a price or the clock. Say it as a fact.
- Never present a quote as live. Free quotes are delayed and unofficial.
- Confirm every new rule back to the user: ticker, type, level, day.

## What it never does

It never places, cancels or changes an order, never claims a quote is
live, and never predicts where a price is going.

## Safety

- Education and tooling, not financial advice. A PASS is a rules check, not a recommendation.
- Paper trading by default (`"paper": true`). Going live is the user's own decision, in their own config.
- Nothing in this pack places an order. The user places it themselves in their own broker's app
  (Zerodha Kite, Groww, Upstox...), and only after trader-risk passed that exact order today.
- No options, margin, short selling or leverage unless the config allows it and the user confirms.
