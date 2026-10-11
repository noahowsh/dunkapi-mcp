#!/usr/bin/env python3
"""NBA player props vs results: how often a player beat his closing line. Usage: python3 nba_player_props.py [name] [--market player_points] [--from-date YYYY-MM-DD] [--to-date YYYY-MM-DD] [--limit 20]. Costs 11 credits (search_players 1 + get_prop_history 10)."""
import json
import os
import sys
import urllib.error
import urllib.request
import argparse

BRAND = "DunkAPI"
KEY_ENV = "DUNKAPI_API_KEY"
BASE_URL = "https://mcp.dunkapi.com/v1"
SIGNUP_URL = "https://dunkapi.com/signup"
LAST_REMAINING = None


class ApiError(Exception):
    pass


def require_key():
    key = os.environ.get(KEY_ENV, "").strip()
    if not key:
        sys.exit(
            f"Set {KEY_ENV} first:\n"
            f"  export {KEY_ENV}=your_key\n"
            f"Get a free key (500 credits every month, no card): {SIGNUP_URL}"
        )
    return key


def call(key, tool, args=None):
    """POST /v1/<tool> with a JSON body and return the parsed response."""
    global LAST_REMAINING
    req = urllib.request.Request(
        f"{BASE_URL}/{tool}",
        data=json.dumps(args or {}).encode(),
        headers={
            "Content-Type": "application/json",
            "x-api-key": key,
            "User-Agent": "dunkapi.com-examples/1.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            LAST_REMAINING = resp.headers.get("X-Credits-Remaining", LAST_REMAINING)
            body = json.load(resp)
            # Every response is wrapped as {"data": ...}.
            return body.get("data", body) if isinstance(body, dict) else body
    except urllib.error.HTTPError as err:
        raise ApiError(describe(err, tool)) from None
    except urllib.error.URLError as err:
        raise ApiError(f"Network error calling {tool}: {err.reason}") from None


def describe(err, tool):
    try:
        body = json.loads(err.read().decode() or "{}")
    except ValueError:
        body = {}
    message = body.get("message") or body.get("error") or err.reason
    if err.code == 401:
        return f"401 unauthorized. Check {KEY_ENV}. {message}"
    if err.code == 402:
        upgrade = body.get("upgrade_url") or SIGNUP_URL
        return f"402 out of credits. {message} Upgrade or wait for the monthly reset: {upgrade}"
    return f"HTTP {err.code} from {tool}: {message}"


def fmt(value, digits=None):
    if value is None:
        return "-"
    if digits is not None and isinstance(value, (int, float)):
        return f"{value:.{digits}f}"
    return str(value)


def pct(value, digits=1):
    return "-" if value is None else f"{value * 100:.{digits}f}%"


def table(headers, rows):
    rows = [["-" if c is None else str(c) for c in r] for r in rows]
    widths = [max([len(h)] + [len(r[i]) for r in rows]) for i, h in enumerate(headers)]
    line = lambda cells: "  ".join(c.ljust(w) for c, w in zip(cells, widths)).rstrip()
    print(line(headers))
    print("  ".join("-" * w for w in widths))
    for r in rows:
        print(line(r))


def finish():
    if LAST_REMAINING is not None:
        print(f"\nCredits remaining: {LAST_REMAINING}")

def main():
    ap = argparse.ArgumentParser(description="NBA prop lines vs results for one player.")
    ap.add_argument("name", nargs="?", default="Jayson Tatum", help="player name (default: Jayson Tatum)")
    ap.add_argument("--market", default="player_points",
                    help="player_points, player_rebounds, player_assists, player_threes, "
                         "player_points_rebounds_assists, player_blocks or player_steals")
    ap.add_argument("--from-date", default="2025-10-01")
    ap.add_argument("--to-date", default="2026-06-30")
    ap.add_argument("--limit", type=int, default=20)
    args = ap.parse_args()
    key = require_key()

    found = call(key, "search_players", {"name": args.name, "limit": 1}).get("players") or []
    if not found:
        sys.exit(f"No player found for {args.name!r}.")
    player = found[0]
    print(f"{player['name']} ({player.get('team')}), player_id {player['player_id']}")

    hist = call(key, "get_prop_history", {
        "player_id": player["player_id"],
        "market": args.market,
        "from_date": args.from_date,
        "to_date": args.to_date,
        "limit": args.limit,
    })
    games = hist.get("games") or []
    if not games:
        sys.exit(f"No {args.market} lines between {args.from_date} and {args.to_date}.")

    print(f"\n{args.market}: closing line (median across books) vs actual {hist.get('stat')}")
    table(
        ["Date", "Open", "Line", "Over", "Under", "Actual", "Result", "Margin"],
        [[g.get("game_date"), fmt(g.get("open_line")), fmt(g.get("line")), fmt(g.get("over_odds")),
          fmt(g.get("under_odds")), fmt(g.get("actual")), g.get("result"), fmt(g.get("margin"))]
         for g in games],
    )
    s = hist.get("summary") or {}
    print(f"\nGraded {s.get('graded')} of {s.get('games')} games: "
          f"{s.get('overs')} over, {s.get('unders')} under, {s.get('pushes')} push. "
          f"Over rate {pct(s.get('over_rate'))}. "
          f"Average line {fmt(s.get('avg_line'), 1)}, average actual {fmt(s.get('avg_actual'), 1)}.")
    if hist.get("truncated"):
        print(f"More games exist. Continue with --from-date {hist.get('next_from_date')}.")
    finish()


if __name__ == "__main__":
    try:
        main()
    except ApiError as err:
        sys.exit(f"Error: {err}")
