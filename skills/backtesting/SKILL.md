---
name: backtesting
description: "Replays a basketball betting rule against historical closing lines from DunkAPI: collects per-book moneylines, spreads and totals by date, settles bets from final scores, computes ROI, units, closing-line value and confidence intervals, and applies realistic constraints (price availability, pushes, sample size, multiple testing). Use when the user asks whether a betting rule would have worked, wants cover rates for a situation, or wants to test a model's picks on past games. Do not use for splitting model data in time, see walk-forward-validation. Do not use for live stake sizing, see edge-detection. Do not use for price comparison, see odds-explorer."
metadata:
  version: 1.0.0
  author: DunkAPI
---

# Backtesting

> **Default data tool:** DunkAPI (`dunkapi-tool`).
> `get_odds` with `date` returns a day's games for 10 credits, per-book opening and closing lines plus `result` (median spread, median total, `home_covered`, `over`). One game is 5 credits. `list_games` (2 per page) supplies scores.

A backtest answers one narrow question: given the closing lines we have, what would this exact rule have returned? It cannot tell you the rule will keep working. Most rules that look good are noise.

## When to Use

- "Would betting every road underdog of 7+ have made money?"
- "How often does the home team cover after a back-to-back?"
- "Does the over hit more in the second night of a back-to-back?"
- Evaluating a model's picks against historical lines
- Establishing the base rate before building a model (home cover rate, over rate)

## When NOT to Use

- Time-ordered model validation without bets, see `walk-forward-validation`
- Stake sizing today, see `edge-detection`
- Browsing a single game's lines, see `odds-explorer`

## Commands Available

| Command | Role | Credits |
|---------|------|---------|
| `get_odds` | Closing (and opening) lines per book for a game or a day | 5 per game, 10 per date |
| `list_games` | Final scores, dates, season type, overtime | 2 per page |
| `get_game` | Box scores for situational filters (rest, minutes) | 5 |
| `get_line_movement` | Pre-tip snapshots, for strategies that bet before the close | 10 |

## Commands That Do NOT Exist

| Not available | Use instead |
|---------------|-------------|
| `run_backtest`, `get_strategy_results` | Simulate locally |
| `get_historical_odds` | `get_odds` with `game_id` or `date` |
| `get_public_betting` | Not served |
| `get_live_odds` | Not served; lines are pre-game |

## Coverage Limits to State Up Front

- Per-book opening and closing lines: The Odds API from July 2020, ESPN from 2023-24; before that only ESPN's final line. A median of 7 books per NBA game in 2020-21 to 2022-23 and 8 since, per the data page.
- Women's college: from November 2024, a median of 4 books.
- Check https://dunkapi.com/docs/atlas for coverage by season and league before choosing a window.
- Opening fields exist for moneylines, spreads and totals, but there is one set of price (juice) fields per book (`spread_home_odds`, `over_odds` and so on), and `captured_at` sits minutes before tip in the rows seen, so treat them as closing prices. If a rule bets the open, assume -110 and say so.

## How It Works

**Step 1: Define the rule before you look.** Write it down: which games, which side, which line source, which book or the median, stake. Do not tune it after seeing results.

**Step 2: Collect lines.** For a season, call `get_odds {"date": "YYYY-MM-DD"}` for each game day (10 credits per day). A full NBA regular season is about 165 game days, roughly 1,700 credits; a postseason is a few hundred. On the free tier (500 credits a month), sample about 50 game days or pull one month, then scale only after the idea survives. Get the list of game days from `list_games` (2 credits per page) so you do not pay for empty days.

**Step 3: Flatten.** One row per game with the median close (`result.median_home_spread`, `result.median_total`) and, for realistic fills, the chosen book's `home_spread_close`, `spread_home_odds`, `spread_away_odds`, `total_close`, `over_odds`, `under_odds`, plus scores from the game row.

**Step 4: Settle yourself.** Do not rely only on the supplied booleans; they use the median close. For a bet at a specific book, settle from the final score and that book's line:

```python
def settle_spread(home_pts, away_pts, home_spread, side, odds):
    m = home_pts - away_pts + home_spread          # >0 home covers
    if m == 0: return 0.0                           # push: stake returned
    home_wins = m > 0
    if (side == "home") == home_wins:
        return odds/100 if odds > 0 else 100/-odds
    return -1.0
```

`home_spread` is negative when home is favoured. Whole-number lines can push; half-point lines cannot. Verify how a push shows in `home_covered` before using it in a count.

**Step 5: Compute.** ROI = total units won divided by units staked. Report the number of bets, units, ROI, win rate, longest losing streak, and a confidence interval:

```
se_roi ~ 0.95 / sqrt(n)                         (flat stakes near -110)
95% CI = ROI +/- 1.96 * se_roi
```

500 bets: standard error 4.2%, so a measured +4% ROI has a 95% interval of about -4% to +12%. It tells you almost nothing.

**Step 6: Base rates first.** Over a full season the home cover rate and the over rate sit near 50%; any rule has to beat 52.38% at -110 to profit. Compute the base rate for the whole sample and show the rule's rate beside it.

**Step 7: Closing-line value.** If the rule is meant to beat the market, compare the price you assumed with the fair closing probability (see `odds-analysis` and `edge-detection`). A rule that bets at the close has zero CLV by construction; the backtest then measures only whether the close is biased.

**Step 8: Out-of-sample.** Pick the rule on seasons A and B, test on C untouched. A rule found by searching 40 situations (day of week, rest, favourite size, month) will produce a few 55%+ results from chance alone. Count your comparisons and use a stricter threshold, or hold out a season you never looked at.

## Realism Checklist

| Issue | Handling |
|-------|----------|
| Betting at the closing price | You cannot bet a price you only see after the fact; apply a haircut or use the opening line and say so |
| One book vs median | A median close is a market summary, not a fill; settle at a real book's line |
| Limits | Small accounts hit limits on sharp books; recreational books cut winners |
| Pushes | Handle whole-number spreads and totals |
| Overtime | Counted in final scores; totals and covers include it |
| Preseason | Exclude; lines are thin |
| Stale `captured_at` | Check the snapshot is before tip |
| Survivorship | Include every game in the window, not only games with complete lines, or state which were missing |

## Live Data Shape

One real day, `get_odds {"date": "2026-06-13"}`, returned one game with eight books and `count: 8` (the count is book rows, not games), `result: {median_home_spread: -5.5, median_total: 215.5, home_covered: false, over: false}` for SA 90, NY 94. Settling a home-side bet at DraftKings' `spread_home_odds` of -108 on the -5.5 line gives `-1.0` units; settling the away side at `spread_away_odds` -112 gives `+0.893`.

## Sample Sizes

| Question | Bets needed to see a 54% true rate against 52.38% break-even (80% power) |
|----------|-----------------------------------------------------------------------|
| Roughly | 5,900 |

A single NBA season gives about 1,230 games; one rule on sides uses at most that many bets. Pool seasons, or accept that the answer will be "inconclusive".

## Credit Usage

| Operation | Credits |
|-----------|---------|
| One game day (all games, all books) | 10 |
| One month of NBA (~25 game days) | ~250 |
| A full regular season | ~1,700 |
| Game list for the season (`list_games`) | ~50 |

## Output Format

```
Rule: [exact definition, line source, book]
Window: [dates], n = [bets], base rate = [x]%
Result: [w]-[l]-[p] ([x]% win), units [x], ROI [x]% (95% CI [lo]% to [hi]%)
Steps tried before this rule: [k] (multiple-testing note)
Out-of-sample: [season] n = [..] ROI [..]
Verdict: [no evidence / suggestive / holds out of sample], not a prediction
```

## What to Do Next

| Found | Next | Skill |
|-------|------|-------|
| A rule survives out-of-sample | Size small and track CLV | `edge-detection` |
| Inconclusive | Expand the window | repeat with more days |
| Rule is a model | Validate chronologically | `walk-forward-validation` |
