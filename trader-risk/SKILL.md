---
name: trader-risk
description: >-
  Risk Manager. Checks every trade against your limits and stops anything
  over them, before it can reach the broker. For a day trade: a stop is
  required, the loss at the stop must fit your max loss per trade (measured
  from the higher of the plan's entry and a fresh price), reward:risk must
  meet your minimum, the day's total risk must fit your daily loss limit, no
  more than your trades per day, and no new entries outside your entry
  window or when the market is closed. It also keeps the basics: blocked
  tickers, order size, position cap, cash buffer, margin, short sales,
  options and crypto, malformed or bad bracket orders, duplicates and a daily
  order limit. Getting out is never blocked by a day limit. Prints PASS or
  BLOCK with the reason and records the verdicts, so the user knows which
  exact order passed before placing it in their own broker's app. Use when the user says "check my order", "is this
  safe", "risk check", "does this break my rules", "can I take this trade",
  "how much have I risked today", or before placing any order, always.
argument-hint: "[path to orders.json]"
---

> **India (NSE) edition.** This copy is patched for Indian stocks: IST clock, NSE session 9:15 AM to 3:30 PM, NSE 2026 holidays, prices in ₹. Use plain NSE symbols (RELIANCE, TCS, M&M, BAJAJ-AUTO); the scripts add `.NS` for Yahoo. Times you type (--now, --at, entry times) are IST. The scanner's universe is the Nifty 500.

# trader-risk

The Risk Manager is the gate between a proposal and the broker. Every order
written by trader-budget passes through it. A BLOCK is final for that order:
do not place it. Most people who day trade lose money. These limits
keep each loss and each day's losses small. They do not make a trade win.

`${CLAUDE_SKILL_DIR}` below is this skill's folder (where this SKILL.md lives).

```bash
python3 "${CLAUDE_SKILL_DIR}/check.py"                           # trader/ files; writes trader/state/risk.json
python3 "${CLAUDE_SKILL_DIR}/check.py" --json
python3 "${CLAUDE_SKILL_DIR}/check.py" --no-write                # look without recording
python3 "${CLAUDE_SKILL_DIR}/check.py" --now "2026-11-13 09:50"  # pin the clock (India time, IST)
```

## What it reads and writes

| file | what |
| --- | --- |
| `trader/orders.json` | the proposed orders (trader-budget) |
| `trader/config.json` | the limits (trader-budget ships `config.example.json`) |
| `trader/portfolio.json` | cash and holdings; if missing, a fresh account funded with the budget |
| `trader/prices.json` | a fresh price raises the entry it measures risk from; also values holdings |
| `trader/state/broker.json` | what was placed today: duplicates, trades per day, daily loss, day trades |
| `trader/state/risk.json` | the verdicts it writes, with a fingerprint of each exact order |

## Entries and exits

An **entry** opens or adds to a position: a buy, or a sell that would go
short. An **exit** only reduces what you already hold. Getting out must
always be possible, so an exit is checked for format, asset and short sales
only. Every other rule (day limits, entry window, loss, reward:risk, blocked
list, size, duplicates) turns into a warning for an exit, never a BLOCK.

## The checks

Orders are checked in file order, as if each passed order had filled, so a
batch that is fine order by order but breaks a limit together is caught.

| check | blocks when |
| --- | --- |
| format | no symbol, side not buy or sell, both or neither of qty and notional, a notional order that is not market + day, a limit order with no limit price; a bracket that is not whole shares, not `day` or `gtc`, or misses its stop-loss or take-profit |
| asset | an option symbol while `allow_options` is false; crypto or anything that is not a stock or ETF ticker |
| short | a sell of more than you hold (`allow_short` false) |
| blocked | (entries) the ticker is on the `blocked` list |
| size | (entries) under `min_order_usd` or over `max_order_usd` |
| position | (entries) the stock would be over `max_position_pct` of the account |
| cash | (entries) the buy would leave less than the cash buffer, or need margin |
| stop | (entries) no stop while `require_stop` is true (a bracket `stop_loss_stop_price`, or the order's plan stop); a stop on the wrong side of the entry |
| loss | (entries) qty x (entry minus stop) over `max_loss_per_trade_usd` |
| reward:risk | (entries) (target minus entry) / (entry minus stop) under `min_reward_risk` |
| daily loss | (entries) the max losses at the stops of today's entries, plus this one, over `max_daily_loss_usd` |
| trades | (entries) `max_trades_per_day` entries already placed today |
| window | (entries) before `no_entries_before` or after `no_entries_after`, or the market is closed |
| duplicate | (entries) the same symbol and side twice in one batch, or already placed today |
| daily limit | (entries) `max_orders_per_day` orders already placed today |

How the numbers work:

- **The entry it measures from**: the limit price for a limit order. For a
  market order, the HIGHER of the plan's entry and a fresh price from
  `trader/prices.json` (under 15 minutes old). A plan written at 10:15 cannot
  understate the risk at 10:55 after the price ran up. An older price is not
  used, and it says so.
- **Daily loss** counts the full max loss of every entry placed today, win or
  lose, as the log in `trader/state/broker.json` has it. Three full-size trades use up
  a ₹3,000 day.
- **The window** is India time (IST, UTC+5:30, no daylight saving), worked
  out in the tool, never from the computer's clock zone. Weekends and NSE
  holidays are closed. The NSE session is 9:15 to 15:30.
  Set both `no_entries_*` to null to switch the window off.
- **Money** is in rupees. The config keys still end in `_usd`
  (`max_loss_per_trade_usd` and so on) so old configs keep working; read them
  as ₹. Leave `pdt_guard` false: India has no pattern-day-trader rule.

Warnings do not block, but say them to the user: a LIVE account, a number
sent as a number instead of a string, a stop that lives only in the plan and
not at the broker, a price too old to use.

## Steps

1. If the price may have moved since the plan, refresh it first
   (trader-alerts: `alerts.py quote TATAELXSI --write`).
2. Run `check.py`. Exit code 0 means every order passed, 1 means at least one
   was blocked.
3. Tell the user the result in plain words, order by order: the max loss at
   the stop, reward:risk, and how much of today's limits it uses. For a
   BLOCK, give the reason and the fix (fewer shares, a closer stop from
   trader-exit, wait for the window, or skip the trade). Never change a
   limit yourself.
4. If the order changes in any way, run the check again. Each verdict is
   tied to that exact order, so an edited order is not ready until it passes
   again, and a verdict from yesterday does not count today.

## Example: a real NSE day

The TATAELXSI bracket from trader-budget at 9:50 AM on Friday 2026-11-13,
on a ₹1,00,000 paper account with a ₹1,000 max loss per trade and a ₹3,000
daily loss limit:

```
PASS  #1 buy TATAELXSI 25 shares, entry
          entry 3881.00 (the plan's entry), stop 3843.35, target 3956.30: risk 37.65 a share
          max loss ₹941.25 (limit ₹1,000), reward:risk 2.00 (min 1)
          today before this: 0 of 3 trades, ₹0 of ₹3,000 daily loss

1 passed, 0 blocked at 2026-11-13 09:50 India (IST). Cash after the passed orders: ₹2,975 (paper account).
```

Two more shares and it is blocked, for four reasons:

```
BLOCK #1 buy TATAELXSI 27 shares, entry
          max loss ₹1,016.55 (limit ₹1,000), reward:risk 2.00 (min 1)
        - size: ₹104,787 is over your ₹100,000 max order
        - cash: needs ₹104,787 but only ₹100,000 cash; that would be margin (borrowed money)
        - position: TATAELXSI would be ₹104,787, 104.8% of the ₹100,000 account, over your 100% cap
        - loss: 27 shares x 37.65 risk a share = ₹1,016.55 at the stop, over your ₹1,000 max loss per trade
```

The same 25 shares checked at 9:40 are blocked by the window: "no new entries
before 09:45 India (IST)". A sell that closes the position passes even after
the entry cutoff: it is an exit.

## Rules

- A PASS only means the order is allowed to be shown to the user. It is not a yes.
- Every number comes from the config, the order, the portfolio, the prices or your log of placed orders.
- Free Yahoo prices are unofficial and can lag; the broker's price is the one that fills, and a
  stop can fill worse than its price in a fast market.

## What it never does

It never places an order, never edits an order to make it pass, never
loosens a limit, never blocks a sell that only gets the user out, and never
treats a PASS as the user's yes.

## Safety

- Education and tooling, not financial advice. A PASS is a rules check, not a recommendation.
- Paper trading by default (`"paper": true`). Going live is the user's own decision, in their own config.
- Nothing in this pack places an order. The user places it themselves in their own broker's app
  (Zerodha Kite, Groww, Upstox...), and only after trader-risk passed that exact order today.
- No options, margin, short selling or leverage unless the config allows it and the user confirms.
