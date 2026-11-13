---
name: trader-budget
description: >-
  Budget Manager. Sizes every position to your budget and your max loss per
  trade. Reads the trade plan from trader-exit (entry, stop, target), finds
  the whole shares that fit inside four limits (max loss per trade, position
  cap, max order, cash after your buffer), says which limit decided it, and
  writes ONE bracket order (entry, stop-loss, take-profit) to
  trader/orders.json as a bracket order you can copy into your broker's app. A stop
  too far away for your max loss is a plain refusal, not a smaller order.
  Nothing is placed. Use when the user says "how many shares", "size this
  trade", "how much should I buy", "I have ₹1 lakh", "I only want to risk ₹1,000
  a trade", "set my rules", "keep 10% in cash", or after /trader-exit writes
  a plan.
argument-hint: "[budget in rupees]"
---

> **India (NSE) edition.** This copy is patched for Indian stocks: IST clock, NSE session 9:15 AM to 3:30 PM, NSE 2026 holidays, prices in ₹. Use plain NSE symbols (RELIANCE, TCS, M&M, BAJAJ-AUTO); the scripts add `.NS` for Yahoo. Times you type (--now, --at, entry times) are IST. The scanner's universe is the Nifty 500.

# trader-budget

The Budget Manager turns a plan ("buy TATAELXSI at 3,881, stop 3,843.35") into an
exact order ("buy 25 shares"), inside rules the user sets once. The stop
decides the size: the further away the stop, the fewer shares. It writes a
proposal only. trader-risk checks it, and the user places it
themselves in their own broker's app. Day trading loses most people money. Sizing to a max loss keeps each
loss small; it does not make a trade win.

`${CLAUDE_SKILL_DIR}` below is this skill's folder (where this SKILL.md lives).

```bash
python3 "${CLAUDE_SKILL_DIR}/size.py"                        # trader/plan.json + trader/config.json
python3 "${CLAUDE_SKILL_DIR}/size.py" --write                # write trader/orders.json
python3 "${CLAUDE_SKILL_DIR}/size.py" --limit --write        # a limit order at the plan's entry
python3 "${CLAUDE_SKILL_DIR}/size.py" --limit 3880 --json    # a limit order at ₹3,880
python3 "${CLAUDE_SKILL_DIR}/size.py" --weights TCS=40,INFY=60 --config split.json   # weights mode, below
```

`--now "2026-11-13 09:50"` pins the clock (India time, IST). A plan for
another day is refused: make a new one with trader-exit.

## What it reads and writes

| file | what |
| --- | --- |
| `trader/config.json` | the rules (start from `config.example.json` in this folder) |
| `trader/plan.json` | the trade: entry, stop, target, setup, flat-by time (trader-exit writes it) |
| `trader/prices.json` | optional: a fresh price above the plan's entry means a bigger risk (trader-alerts writes it) |
| `trader/portfolio.json` | optional: its cash caps the size (you keep it up to date) |
| `trader/orders.json` | the one proposed bracket order it writes with `--write` |

## Step 1: set the rules once

If `trader/config.json` does not exist, copy `config.example.json` into
`trader/config.json` and ask the user for each value in plain words:

- **budget**: how much money this is for. Only money they can afford to lose.
- **cash_buffer_pct**: how much always stays in cash (default 0 in the example config).
- **max_loss_per_trade_usd**: the most one trade may lose if the stop fills at the stop (default ₹1,000).
- **max_position_pct**, **max_order_usd**, **min_order_usd**: the biggest position (100% of the
  budget), the biggest order (₹1,00,000) and the smallest order (₹500).
- The day limits trader-risk enforces: **max_daily_loss_usd** (₹3,000), **max_trades_per_day** (3),
  **min_reward_risk** (1.0), **require_stop** (true), **no_entries_before** / **no_entries_after**
  ("09:45" / "15:00") and **flat_by** ("15:25"), all India time (IST). The NSE closes at 15:30.
- All money is in rupees. The keys still end in `_usd` so old configs keep working.
- **blocked**: tickers they never want to trade.
- Keep **paper** true until they have watched it work on a paper account.

## Step 2: size the trade

```bash
python3 "${CLAUDE_SKILL_DIR}/size.py" --write
```

Whole shares only: NSE cash equities trade in whole shares. The size is
the smallest of four limits:

| limit | shares |
| --- | --- |
| max loss | `max_loss_per_trade_usd` / risk a share (entry minus stop) |
| position cap | budget x `max_position_pct` / entry |
| max order | `max_order_usd` / entry |
| cash | (budget minus the cash buffer) / entry, never more than the cash in `trader/portfolio.json` |

The entry it sizes at: the limit price with `--limit`. For a market order, the
plan's entry, or the price in `trader/prices.json` if it is fresh (under 15
minutes old) and higher. A price that ran up since the plan means a bigger
loss at the same stop, so fewer shares. A lower price never shrinks the risk.

It refuses, and writes no order, when: the size is zero shares, the order is
under the minimum, reward:risk is under `min_reward_risk`, the stop is not
below the entry, the target is not above it (the move already happened), the
plan is for another day, the ticker is blocked, or the plan is a short. Say
the reason to the user in one line.

## Step 3: show the user

Show the four limits, which one decided the size, the shares, the rupees
and the max loss at the stop. Say plainly that a stop is an order, not a
promise: in a fast market it can fill below the stop. Then hand over to
`/trader-risk`.

## Example: a real NSE day

TATAELXSI on Friday 2026-11-13. Opening-range breakout: entry 3,881 at 9:45 AM,
stop 3,843.35 (the opening-range midpoint), target 3,956.30 (2R). Risk 37.65 a
share. The example config: ₹1,00,000 budget, no cash buffer, ₹1,000 max loss.

| limit | the math | shares |
| --- | --- | --- |
| max loss | ₹1,000 / 37.65 | 26 |
| position cap | 100% of ₹1,00,000 / 3,881 | **25 (decides it)** |
| max order | ₹1,00,000 / 3,881 | 25 |
| cash | ₹1,00,000 / 3,881 | 25 |

25 shares = ₹97,025. Max loss at the stop: 25 x 37.65 = ₹941.25. The max loss
alone would allow 26, but 26 x 3,881 = ₹1,00,906 is more than the account. It
writes:

```json
{"symbol": "TATAELXSI", "side": "buy", "qty": "25", "type": "market", "time_in_force": "day",
 "order_class": "bracket", "take_profit_limit_price": "3956.30", "stop_loss_stop_price": "3843.35",
 "why": "opening-range breakout on TATAELXSI: 25 shares, bound by your position cap (25 x 37.65 = ₹941.25 at the stop)",
 "plan": {"entry": 3881.0, "stop": 3843.35, "target": 3956.3, "risk_per_share": 37.65, ...}}
```

`why` and `plan` are notes for trader-risk. To place it, the user enters the
same order in their broker's app: a bracket order (or a buy plus a stop-loss
and a target order) for 25 shares. If the stop were so far away that one
share risks more than the max loss, there is no order.

## Weights mode (kept from v1)

`--weights TCS=40,INFY=60` or `--targets FILE` (`targets.example.json`
here, five Nifty 50 stocks with example weights) splits a budget across a
list by weight: the cash buffer comes off the top, weights are renormalised
to 100, any stock over `max_position_pct` is pinned at the cap and its excess
shared out, slices under the minimum order are dropped, and amounts round to
whole rupees so nothing is left idle by accident. With `"fractional": false`
(the example config) it buys whole shares and needs prices (`--prices
trader/prices.json`). These are plain buys with no stop: trader-risk blocks
them while `require_stop` is true and counts each one against
`max_trades_per_day`. Use a separate config (`--config`) for a long-term split.

## Rules

- Proposals only. This skill never places an order.
- Never size money the user has not said is for this. Ask for the budget and the max loss.
- Every number comes from the config, the plan or the prices. Nothing is guessed.
- No projections: never say what a trade will make. A target is a plan, not a forecast.
- Free Yahoo prices are unofficial and can lag. The broker's price is the one that fills.

## What it never does

It never places, approves or schedules an order, never raises a limit on its
own, never shrinks a stop to fit more shares, and never sizes options,
margin or short positions.

## Safety

- Education and tooling, not financial advice. A PASS is a rules check, not a recommendation.
- Paper trading by default (`"paper": true`). Going live is the user's own decision, in their own config.
- Nothing in this pack places an order. The user places it themselves in their own broker's app
  (Zerodha Kite, Groww, Upstox...), and only after trader-risk passed that exact order today.
- No options, margin, short selling or leverage unless the config allows it and the user confirms.
