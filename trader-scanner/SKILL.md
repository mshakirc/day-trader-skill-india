---
name: trader-scanner
description: >-
  Chart Scanner. Scans thousands of charts for setups: opening-range
  breakouts, flags, oversold bounces. Builds the list of Nifty 500 NSE
  stocks (India edition),
  runs a pre-market scan of daily closes (20-day closing-high breakout, bull
  flag, reclaimed the 20-day average, oversold, oversold bounce) and an
  intraday opening-range breakout scan on 5-minute bars, then writes
  trader/watchlist.json for trader-news and trader-entry. Free Yahoo data,
  bar by bar. Use when the user says "scan the market", "find me setups",
  "what is breaking out", "opening range breakouts", "scan for bull flags",
  "oversold stocks", "pre-market scan", "build my watchlist", "what should I
  look at today", or at the start of a trading day before /trader-news.
argument-hint: "[universe | daily | orb] [--at HH:MM]"
---

> **India (NSE) edition.** This copy is patched for Indian stocks: IST clock, NSE session 9:15 AM to 3:30 PM, NSE 2026 holidays, prices in ₹. Use plain NSE symbols (RELIANCE, TCS, M&M, BAJAJ-AUTO); the scripts add `.NS` for Yahoo. Times you type (--now, --at, entry times) are IST. The scanner's universe is the Nifty 500.

# trader-scanner

The Chart Scanner is the first step of a day trade. It reads thousands of
free charts and lists the ones that match a rule. That is all it does. A scan
is a list of charts that match a rule, not a list of stocks to buy, and a
setup on a chart is not a prediction. Most people who day trade lose money;
the scanner does not change that. It only saves you from flipping through
500 charts by hand.

`${CLAUDE_SKILL_DIR}` below is this skill's folder (where this SKILL.md lives).

```bash
python3 "${CLAUDE_SKILL_DIR}/scan.py" universe                       # Nifty 500 -> trader/universe.txt
python3 "${CLAUDE_SKILL_DIR}/scan.py" daily                          # before the open -> trader/watchlist.json
python3 "${CLAUDE_SKILL_DIR}/scan.py" daily --symbols RELIANCE,TCS,INFY  # or --watchlist FILE, --limit 200
python3 "${CLAUDE_SKILL_DIR}/scan.py" orb                            # after 9:35 AM IST -> trader/watchlist.json
python3 "${CLAUDE_SKILL_DIR}/scan.py" orb --at 09:45                 # cut the clock at 9:45 AM IST
python3 "${CLAUDE_SKILL_DIR}/scan.py" orb --watchlist trader/watchlist.json --json
```

Flags: `--min-price 5` (rupees) and `--min-volume` (daily 500,000 shares, orb 0),
`--or-minutes 15`, `--max-confirm 200` (orb stage 2),
`--now "2026-11-13 09:45"` (India time, IST) to pin the clock, `--offline PATH`
to read saved Yahoo files, `--no-write`, `--show N`, `--json`. Exit code 0
when the scan found something, 1 when it found nothing or could not run (the
reason is one plain line).

## What it reads and writes

| file | what |
| --- | --- |
| `trader/universe.txt` | written by `universe`: one NSE symbol a line. If it is missing, `daily` and `orb` use the bundled `nifty500.txt` |
| `trader/watchlist.json` | written by `daily` and `orb`: `mode`, `as_of`, `universe`, `scanned`, `failed`, `hits[]`. trader-news and trader-entry read `hits[].symbol` |
| `trader/config.json` | read by `orb`: `no_entries_after` (15:00 IST) |

## The universe

The Nifty 500: the 500 NSE stocks in `nifty500.txt` next to this file (from
niftyindices.com, read 2026-11-07). `universe` copies it to
`trader/universe.txt`. Symbols are plain NSE symbols (RELIANCE, M&M,
BAJAJ-AUTO); the scripts add `.NS` when they ask Yahoo. To scan a different
list, pass `--universe FILE`, `--symbols` or `--watchlist`.

## The daily scan (before the open)

Yahoo's spark endpoint returns closes for 20 symbols a request, so the Nifty
500 takes 25 requests, under a minute. Liquidity comes from the spark meta:
last price at least `--min-price` (₹5) and last session's volume at least
`--min-volume` (500,000 shares). Run it before 9:15 or after 15:30 IST: during
the session the volume is the day's so far, and today's daily bar is left out
until the close.

The setups are computed from daily closes only (spark has no highs or lows):

| setup | the rule on closes |
| --- | --- |
| `breakout_20d` | the last close is above every close of the 20 sessions before it |
| `bull_flag` | up more than 10 % over the 10 sessions before the last 5, then the last 5 closes inside a 5 % range |
| `reclaim_ma20` | the close before was under its 20-day average, the last close is above it |
| `oversold` | RSI 14 (Wilder) under 30 |
| `oversold_bounce` | RSI 14 was under 30 yesterday and today closed up |

A closing-high breakout fires more often than an intraday-high one. Hits are
listed most traded first (price times volume).

## The opening-range breakout scan (during the session)

The opening range is the first `--or-minutes` (15) of the session: the 9:15,
9:20 and 9:25 five-minute bars. A hit is the first completed 5-minute bar
to CLOSE above the range high, at that bar's close time.

1. Stage 1, every symbol: spark closes of today's 5-minute bars, 20 a
   request. A chart goes on only if a completed bar after the range closed at
   or above the highest close of the range. That is a necessary condition
   (the range high is at least every range close), so no breakout is lost.
2. Stage 2, each candidate: the v8 chart with real highs and lows, one
   request each. Range high = the highest high of the range bars, range low =
   the lowest low. On a strong morning most charts are candidates, so stage 2
   checks at most `--max-confirm` (200) of them, the most traded first (price
   times volume so far), and prints PARTIAL with the count it skipped.

A chart is usable only when every 5-minute bar from 9:15 to the cutoff is
there; a missing bar means a halt or a thin stock. Null closes are dropped,
a bar off the 5-minute grid (the live tick) is dropped, and a bar counts only
once it is complete (start + 5 minutes). Before the first bar after the range
has closed, on a weekend or NSE holiday, after the close, or after
`no_entries_after` (an expired setup) it prints one plain line and writes
nothing.

## Data and limits

- Yahoo's chart and spark endpoints are free, unofficial and can lag. Bars are
  5-minute bars, bar by bar, never tick by tick. query2 first, query1 on a 429
  or 5xx, one retry after a 5-second wait on a 429.
- Partial results are said as partial: "Fetched 499 of 500 charts (1 failed
  or had no data)". Never round a partial scan up to "the whole market".
- NSE trading holidays for 2026 are in the scripts (NSE list). Add 2027 when
  the NSE publishes it; until then a 2027 date says the holiday list is unknown.

## Steps

1. Before the open: `scan.py daily`. Tell the user the counts (fetched,
   liquid, scanned, hits) and the top few by setup.
2. After 9:35 AM IST (9:45 is a common time): `scan.py orb`. Tell the user how
   many usable charts broke their range and when, and that a later hit is
   closer to the price now.
3. The user picks one chart. Hand it on: `/trader-news TICKER` (what is moving
   it), then `/trader-entry TICKER` (the entry bar by bar). Never pick for them.

## Example: a real NSE day

Friday 2026-11-13, the Nifty 500. `scan.py daily` before the open (closes
through Thu 11-12):

```
Fetched 499 of 500 charts (1 failed or had no data). 301 passed the liquidity filter (₹5+ and 500,000+ shares); 301 scanned.
126 charts matched a setup: 98 20-day closing-high breakout, 27 bull flag, 11 reclaimed the 20-day average, 3 oversold (RSI under 30), 1 oversold bounce.
Most traded first (price x volume):
  HDFCBANK    ₹812.30  RSI  77.9  20-day closing-high breakout
  RELIANCE  ₹1,339.70  RSI  70.8  20-day closing-high breakout
  ...
```

`scan.py orb --at 09:45` the same morning:

```
Opening-range breakout scan, Fri 2026-11-13 9:45 AM IST: 15-minute range (9:15 to 9:30 AM), 5-minute bars, Yahoo.
Fetched 499 of 500 charts (1 failed or had no data); 479 usable; 378 candidates, 200 confirmed with real highs and lows.
PARTIAL: 178 more candidates were not checked (only the 200 most traded are; --max-confirm 0 checks all).
113 of the 200 checked charts closed above their opening-range high by 9:45 AM:
   9:35 AM  AMBER   ₹6,483.00  range 6,045.00 to 6,469.00  +0.22% over
   ...
```

TATAELXSI's range was 3,821.60 to 3,865.10, and its 9:40 bar closed at 3,881
(+0.41 % over the high) at 9:45 AM. If the user picks it, Claude hands it to
`/trader-news TATAELXSI`, then `/trader-entry TATAELXSI`.

## Rules

- Say what was scanned: how many symbols, how many charts came back, how many
  were usable, and the time of the data.
- Say "matched a rule", never "a buy", "a winner" or "a good trade".
- Never print a P&L, a return or a profit figure.
- A hit is stale once the price has moved on. Re-run before acting on it.

## What it never does

It never places, sizes or checks an order, never says which stock to buy,
never calls data real time, and never promises that a setup works.

## Safety

- Education and tooling, not financial advice. A PASS is a rules check, not a recommendation.
- Paper trading by default (`"paper": true`). Going live is the user's own decision, in their own config.
- Nothing in this pack places an order. The user places it themselves in their own broker's app
  (Zerodha Kite, Groww, Upstox...), and only after trader-risk passed that exact order today.
- No options, margin, short selling or leverage unless the config allows it and the user confirms.
