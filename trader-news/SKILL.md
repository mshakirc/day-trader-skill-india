---
name: trader-news
description: >-
  News Monitor. Tracks breaking news on every NSE stock you watch and flags
  what moves it: Google News (India edition) headlines per company and how far
  each stock is from yesterday's close. Shows only what is new since the last
  check, newest first, in India time (IST), tags each item (earnings, analyst,
  deal, legal, regulatory, macro...) and never repeats one. Use when the user
  says "any news on RELIANCE", "why is this moving", "what's the news on my
  watchlist", "morning briefing", "pre-market news", "monitor the news", "did
  anything break", or after /trader-scanner finds setups.
argument-hint: "[tickers]"
---

> **India (NSE) edition.** Use plain NSE symbols (RELIANCE, TCS, M&M, BAJAJ-AUTO); the script adds `.NS` for Yahoo. Times are India time (IST).

# trader-news

A chart can look perfect and still be about to gap on results, a SEBI order
or a block deal. Before a setup becomes a trade, this skill reads the
headlines for every stock on the watchlist and tells you only what is new. It
also prints how far each stock has moved today, so a headline and a move sit
side by side.

Tool in this folder (standard library Python, no keys):

```bash
python3 "${CLAUDE_SKILL_DIR}/news.py"                         # watchlist + plan + portfolio
python3 "${CLAUDE_SKILL_DIR}/news.py" --tickers TATAELXSI M&M --hours 12
python3 "${CLAUDE_SKILL_DIR}/news.py" --json
```

## What it reads and writes

| file / feed | what |
| --- | --- |
| `--tickers`, else `trader/watchlist.json` | the scanner's hits (trader-scanner) |
| `trader/plan.json` | the trade you are planning (trader-exit) |
| `trader/portfolio.json` | what you hold, if you keep one |
| Yahoo Finance chart endpoint | the company name, and the last price against yesterday's close (unofficial, can lag) |
| Google News RSS, India edition | `news.google.com/rss/search?q="Tata Elxsi" when:2d&hl=en-IN&gl=IN&ceid=IN:en`, searched by company name |
| `trader/state/news.json` | what has been shown (kept 30 days) |

Exchange filings (NSE / BSE corporate announcements: results dates, board
meetings, block deals) are not fetched, because the NSE site blocks scripts.
For those, point the user to nseindia.com or bseindia.com.

## The rules

- **Headlines are leads, not facts.** Before telling the user something
  happened, open the story and read it. Quote the source and link it. Never
  summarise a paywalled story you could not read: say so.
- **The exchange filing beats a headline.** If a headline and the company's
  NSE / BSE announcement disagree, the filing is what the company told the
  exchange.
- **Search hits are not all about the stock.** Google News matches the
  company name anywhere in a story, so a sector round-up or a story that
  only mentions the company shows up too. Say which items are really about
  the stock.
- **Say what it touches.** Every item lists the tickers it touches and its
  tags: earnings, analyst, legal, deal, capital, people, risk, halt (including
  upper / lower circuit), regulatory (SEBI, RBI, USFDA), macro (RBI policy,
  CPI, FII flows, Nifty, Sensex).
- **MOVING** marks a stock 3 % or more from yesterday's close (`--move-pct`).
  A move with no headline is worth saying out loud too.
- **No predictions.** Report what was published and how far the price is from
  yesterday's close. Never say what the stock will do next.

## Steps

1. Run the check: `python3 "${CLAUDE_SKILL_DIR}/news.py"`. Exit code 1 means
   nothing new. `--all` shows items already seen, `--json` gives everything
   machine readable, `--dry-run` leaves the state alone.
2. Read the items that matter: anything tagged earnings, halt, legal,
   regulatory or risk, and every MOVING ticker first.
3. Write a short brief, per ticker: what happened, the source and link, the
   move, and one line on why it matters to the setup (for example "results
   are this week: an overnight gap can jump past any stop").
4. If a story changes the picture, say so before `/trader-entry` and
   `/trader-exit`: a results date inside the trade, a SEBI order, a block
   deal. Never act on a headline alone.

During the session: `/loop 15m /trader-news`, or a scheduled task each
morning before 9:15 IST.

## Example: a real NSE day

Friday 2026-11-13, `news.py --tickers TATAELXSI M&M` after the close:

```
M&M        ₹3,333.00 -1.94% vs yesterday's close ₹3,399.00 at 15:28 IST
TATAELXSI  ₹3,835.00 -0.70% vs yesterday's close ₹3,862.00 at 15:28 IST

  2026-11-13 13:42 IST  M&M         Veloxx media  Mahindra & Mahindra Appoints Shuchi Suri as Chief Sales and Marketing Officer – Automotive
      tags: people  https://news.google.com/rss/articles/...
  2026-11-13 07:30 IST  TATAELXSI   ad-hoc-news.d Tata Elxsi stock: Aesculap center underscores healthcare niche
  2026-11-13 06:27 IST  M&M         Simply Wall S Mahindra & Mahindra's (NSE:M&M) Earnings Are Weaker Than They Seem
      tags: earnings
```

The same check also listed two JSW Motors stories under TATAELXSI, because
they mention Tata Elxsi in passing. The brief says so instead of treating
them as Tata Elxsi news. When a ticker has no news, say so rather than
padding the brief.

## What it never does

- Never invents or embellishes a story, a quote or a number.
- Never trades on news, and never tells the user to buy or sell because of a
  headline.
- Never hammers a server: one request per feed per ticker, with a pause
  between calls.

## Safety

Education and tooling, not financial advice. This skill only reads and
reports. Nothing in this pack places an order: the user places any order
themselves in their own broker's app, after `/trader-risk` passes it.
