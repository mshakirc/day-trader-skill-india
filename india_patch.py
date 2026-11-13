#!/usr/bin/env python3
"""India (NSE) patch for Jake Schincariol's day-trader-skill (MIT).
Re-runnable on a fresh clone: python3 india_patch.py
Changes: IST clock (UTC+5:30, no DST), NSE session 9:15-15:30, NSE 2026 holidays,
Yahoo symbols as NAME.NS (BAJAJ-AUTO.NS, M&M.NS), NSE-style tickers allowed,
Nifty 500 as the scanner universe, user-facing text ET->IST, NYSE->NSE."""
import os, re, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
FILES = ["trader-scanner/scan.py", "trader-timemachine/timemachine.py", "trader-entry/entry.py",
         "trader-exit/exit.py", "trader-risk/check.py", "trader-alerts/alerts.py", "trader-budget/size.py"]

NSE_HOLIDAYS = '''NYSE_HOLIDAYS = {  # NSE equity trading holidays 2026 (source: NSE list via cleartax.in, Feb 2026). Add 2027 when NSE publishes it.
    "2026-01-15": "Maharashtra municipal elections",
    "2026-01-26": "Republic Day",
    "2026-03-03": "Holi",
    "2026-03-26": "Shri Ram Navami",
    "2026-03-31": "Shri Mahavir Jayanti",
    "2026-04-03": "Good Friday",
    "2026-04-14": "Dr. Baba Saheb Ambedkar Jayanti",
    "2026-05-01": "Maharashtra Day",
    "2026-05-28": "Bakri Id",
    "2026-06-26": "Muharram",
    "2026-09-14": "Ganesh Chaturthi",
    "2026-10-02": "Mahatma Gandhi Jayanti",
    "2026-10-20": "Dussehra",
    "2026-11-10": "Diwali Balipratipada",
    "2026-11-24": "Prakash Gurpurb Sri Guru Nanak Dev",
    "2026-12-25": "Christmas",
}'''

HELPERS = '''
import urllib.parse as _up


def _ysym(s):
    """Our ticker -> Yahoo's NSE ticker: TCS -> TCS.NS. .NS/.BO and ^indices pass through."""
    s = str(s).strip().upper()
    if not s or s.startswith("^") or s.endswith((".NS", ".BO")):
        return s
    return s + ".NS"


def _q(s):
    return _up.quote(s, safe=".-^")
'''

IST_OFFSET = '''def eastern_offset(utc):
    """India patch: hours from UTC for India (IST), always +5:30, no daylight time."""
    return 5.5
'''
IST_TO_UTC = '''def eastern_to_utc(local):
    """India patch: IST wall clock -> naive UTC."""
    return local - datetime.timedelta(hours=5.5)
'''


def sub(pat, rep, text, flags=re.S, count=0, need=True, name=""):
    new, n = re.subn(pat, rep, text, count=count, flags=flags)
    if need and n == 0:
        print("  ! no match:", name or pat[:60])
    return new


def patch(path):
    p = os.path.join(ROOT, path)
    t = open(p, encoding="utf-8").read()
    if "India patch" in t:
        print("skip (already patched):", path)
        return
    print("patching", path)
    t = sub(r"def eastern_offset\(utc\):.*?(?=\n\n\n|\n\ndef )", lambda m: IST_OFFSET.rstrip(), t, name="eastern_offset")
    t = sub(r"def eastern_to_utc\(local\):.*?(?=\n\n\n|\n\ndef )", lambda m: IST_TO_UTC.rstrip(), t, need=False)
    t = sub(r"NYSE_HOLIDAYS = \{.*?\n\}", lambda m: NSE_HOLIDAYS, t, need=False)
    t = sub(r"NYSE_EARLY_CLOSE = \{.*?\n\}", "NYSE_EARLY_CLOSE = {}  # NSE has no scheduled half days", t, need=False)
    t = t.replace("CALENDAR_YEARS = (2026, 2027)", "CALENDAR_YEARS = (2026,)")
    t = t.replace("OPEN = datetime.time(9, 30)", "OPEN = datetime.time(9, 15)")
    t = t.replace("CLOSE = datetime.time(16, 0)", "CLOSE = datetime.time(15, 30)")
    t = t.replace("SESSION_BARS = 78    # 9:30 to 16:00 in 5-minute bars", "SESSION_BARS = 75    # 9:15 to 15:30 in 5-minute bars")
    t = t.replace("OPEN_MIN = 9 * 60 + 30", "OPEN_MIN = 9 * 60 + 15")
    t = t.replace("CLOSE_MIN = 16 * 60", "CLOSE_MIN = 15 * 60 + 30")
    t = t.replace("or_min >= 390", "or_min >= 375")
    t = t.replace('mc.get("until") or "16:00"', 'mc.get("until") or "15:30"')
    t = t.replace('"%s 09:30" % nd.isoformat()', '"%s 09:15" % nd.isoformat()')
    # Yahoo symbols
    t = t.replace('return sym.upper().replace(".", "-")', "return _ysym(sym)")
    t = t.replace('ysym = sym.upper().replace(".", "-")', "ysym = _ysym(sym)")
    t = t.replace('urllib.parse.quote(sym.upper().replace(".", "-"))', "_q(_ysym(sym))")
    t = t.replace('msym != sym.replace(".", "-")', "msym != _ysym(sym)")
    t = t.replace('(host, sym.upper().replace(".", "-"))', "(host, _q(_ysym(sym)))")
    t = t.replace('",".join(to_yahoo(s) for s in symbols)', '",".join(_q(to_yahoo(s)) for s in symbols)')
    t = t.replace('% (to_yahoo(sym), rng, interval)', '% (_q(to_yahoo(sym)), rng, interval)')
    t = t.replace('% (yahoo_symbol(sym), rng, interval)', '% (_q(yahoo_symbol(sym)), rng, interval)')
    # NSE-style tickers: up to 20 chars, digits, & and -, optional .NS/.BO
    t = t.replace('TICKER = re.compile(r"^[A-Z]{1,5}([.\\-][A-Z]{1,2})?$")',
                  'TICKER = re.compile(r"^[A-Z0-9][A-Z0-9&\\-]{0,19}(\\.(NS|BO))?$")')
    t = t.replace('re.match(r"^[A-Z][A-Z0-9.\\-]{0,9}$", sym)', 're.match(r"^[\\^A-Z0-9][A-Z0-9.&\\-]{0,22}$", sym)')
    # user-facing text
    t = t.replace("New York", "India (IST)").replace("NYSE", "NSE").replace("nyse.com", "nseindia.com")
    t = re.sub(r"(?<![A-Za-z_])ET(?![A-Za-z_])", "IST", t)
    t = t.replace("NSE opens at 9:30", "NSE opens at 9:15").replace("9:30 to 16:00", "9:15 to 15:30")
    t = t.replace("9:30 to 4:00", "9:15 to 3:30").replace("from 9:30 to", "from 9:15 to")
    # helpers after the last top-level import
    imports = list(re.finditer(r"^(?:import |from )[^\n]+\n", t, flags=re.M))
    if imports and "_ysym" in t:
        k = imports[-1].end()
        t = t[:k] + HELPERS + t[k:]
    open(p, "w", encoding="utf-8").write(t)


def patch_scanner_universe():
    p = os.path.join(ROOT, "trader-scanner/scan.py")
    t = open(p, encoding="utf-8").read()
    if "NIFTY500_FILE" in t:
        return
    t = t.replace('DEFAULT_UNIVERSE = "trader/universe.txt"',
                  'DEFAULT_UNIVERSE = "trader/universe.txt"\n'
                  'NIFTY500_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "nifty500.txt")')
    t = t.replace('--min-volume (1,000,000)', '--min-volume (500,000)')
    new_universe = '''def cmd_universe(a):
    """India patch: the universe is the Nifty 500 list shipped with this skill."""
    with open(NIFTY500_FILE, encoding="utf-8") as fh:
        kept = [ln.strip() for ln in fh if ln.strip() and not ln.startswith("#")]
    if not a.no_write:
        d = os.path.dirname(a.out)
        if d:
            os.makedirs(d, exist_ok=True)
        with open(a.out, "w", encoding="utf-8") as fh:
            fh.write("\\n".join(kept) + "\\n")
    if a.json:
        print(json.dumps({"count": len(kept), "source": "Nifty 500 (niftyindices.com)",
                          "out": None if a.no_write else a.out}, indent=2))
    else:
        print("Nifty 500 universe: %d NSE stocks." % len(kept))
        if not a.no_write:
            print("Wrote %s (one NSE symbol a line)." % a.out)
    return 0 if kept else 1
'''
    t = re.sub(r"def cmd_universe\(a\):.*?(?=\n\n\ndef )", lambda m: new_universe.rstrip(), t, flags=re.S)
    t = t.replace('''        path = a.universe or DEFAULT_UNIVERSE
        if not os.path.exists(path):''', '''        path = a.universe or DEFAULT_UNIVERSE
        if not a.universe and not os.path.exists(path):
            path = NIFTY500_FILE  # India patch: fall back to the bundled Nifty 500
        if not os.path.exists(path):''')
    open(p, "w", encoding="utf-8").write(t)


if __name__ == "__main__":
    for f in FILES:
        patch(f)
    patch_scanner_universe()
    print("done")


def patch_currency():
    """Show rupees instead of dollars in printed output."""
    for f in FILES:
        p = os.path.join(ROOT, f)
        t = open(p, encoding="utf-8").read()
        if "# India patch: rupees" in t:
            continue
        t = t.replace("$%", "₹%").replace('"${:,.2f}"', '"₹{:,.2f}"').replace('return "$" + ', 'return "₹" + ')
        t = t.replace('.lstrip("$")', '.lstrip("$₹")')
        t += "\n# India patch: rupees\n"
        open(p, "w", encoding="utf-8").write(t)


if __name__ == "__main__":
    patch_currency()


FULL_SESSIONS = 'def full_sessions(days, before):\n    """Full sessions (all 75 bars) strictly before the plan\'s date, oldest first,\n    and the short ones that were left out (half days, gaps).\n\n    Yahoo\'s NSE feed drops a few 5-minute bars from almost every session (the\n    row comes back with no price). A session missing at most MAX_FILL bars is\n    kept: each gap becomes a flat bar at the last close (the next open for a\n    missing first bar) with volume 0. Returns (full, short, filled)."""\n    full, short, filled = [], [], 0\n    for d in sorted(days):\n        if d >= before:\n            continue\n        s = days[d]\n        missing = SESSION_BARS - len(s)\n        if missing == 0:\n            full.append((d, [s[i] for i in range(SESSION_BARS)]))\n        elif 0 < missing <= MAX_FILL:\n            out, prev = [], None\n            for i in range(SESSION_BARS):\n                if i in s:\n                    prev = s[i]["c"]\n                    out.append(s[i])\n                    continue\n                if prev is None:\n                    prev = s[min(s)]["o"]\n                h, m = divmod(OPEN_MIN + 5 * i, 60)\n                out.append({"date": d, "slot": i, "start": "%02d:%02d" % (h, m),\n                            "o": prev, "h": prev, "l": prev, "c": prev, "v": 0, "filled": True})\n            full.append((d, out))\n            filled += missing\n        else:\n            short.append({"date": d, "bars": len(s)})\n    return full, short, filled\n'


def patch_nse_fixes():
    """Flat-by 15:25 (the US 15:55 is after the NSE 15:30 close) and a Time Machine
    that keeps sessions missing a few bars (Yahoo's NSE feed drops some every day)."""
    for f in FILES + ["trader-broker/ticket.py", "trader-budget/config.example.json"]:
        p = os.path.join(ROOT, f)
        t = open(p, encoding="utf-8").read()
        if "# India patch: nse fixes" in t or "MAX_FILL" in t:
            continue
        t = re.sub(r'(["\s])15:55', r"\g<1>15:25", t)
        if f.endswith("timemachine.py"):
            t = sub(r"def full_sessions\(days, before\):.*?return full, short\n", lambda m: FULL_SESSIONS, t,
                    name="full_sessions")
            t = t.replace("MIN_SESSIONS = 20\n", "MIN_SESSIONS = 20\nMAX_FILL = 6          "
                          "# missing bars a session may have and still count as full (filled flat)\n", 1)
            t = t.replace('sessions, short = full_sessions(days, plan["date"])',
                          'sessions, short, filled = full_sessions(days, plan["date"])')
            t = t.replace('"dropped": dropped, "short_sessions_left_out": short},',
                          '"dropped": dropped, "short_sessions_left_out": short,\n                 "filled_bars": filled},')
            t = t.replace('    if doc["data"]["short_sessions_left_out"]:\n        lines.append("Left out',
                          '    if doc["data"].get("filled_bars"):\n'
                          '        lines.append("Filled %d missing 5-min bar(s) in those sessions with flat bars at the last close (volume 0)."\n'
                          '                     % doc["data"]["filled_bars"])\n'
                          '    if doc["data"]["short_sessions_left_out"]:\n        lines.append("Left out')
        if f.endswith("exit.py"):
            t = t.replace("        if at >= close_dt:\n            if explicit:",
                          "        if at >= close_dt:\n            if s[1] == CLOSE:\n"
                          "                raise PlanError(\"%s %s is at or after the %s close on %s: pick a time before it, like 15:25\"\n"
                          "                                % (\"--flat-by\" if explicit else \"flat_by in the config\", hm(t), ampm(s[1]), day))\n"
                          "            if explicit:", 1)
            t = t.replace("or lose. On a 1:00 p.m. early close it moves up with the close (12:55).",
                          "or lose. It must be before the 15:30 close.")
        if f.endswith(".py"):
            t += "# India patch: nse fixes\n"
        open(p, "w", encoding="utf-8").write(t)


if __name__ == "__main__":
    patch_nse_fixes()
