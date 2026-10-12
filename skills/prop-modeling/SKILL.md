---
name: prop-modeling
description: "Builds basketball player prop models for points, rebounds, assists, threes, points + rebounds + assists, blocks and steals: projects minutes and per-minute rates from the game log, turns a projection into an over/under probability with a suitable distribution, compares it with devigged prop prices across books, and checks a player's history against his lines. Use when the user asks if a player will go over a number, how often he has hit his line, what a fair prop price is, or how to project a stat line. Props exist for NBA, WNBA and men's college only. Do not use for team-side or total models, see feature-engineering. Do not use for the generic EV and Kelly steps, see edge-detection. Do not use for recent-form description alone, see player-form."
metadata:
  version: 1.0.0
  author: DunkAPI
---

# Prop Modeling

> **Default data tool:** DunkAPI (`dunkapi-tool`).
> `get_prop_history` (10 credits for up to 200 games) shows each game's closing line against what happened. `get_player_props` (10 credits for a whole game, or 10 per game for one player across dates) gives every book's price. `get_player_games` (5) feeds the projection.

A prop is a single player-game outcome with a wide spread. The line already contains minutes, matchup and injuries. The only way to add value is to model one of those better than the market, and to know when you have not.

## When to Use

- "Will Brunson go over 24.5 points?"
- "How often has he hit his points line this season?"
- "Which book has the best price on his rebounds over?"
- "Project his points, rebounds and assists for tonight"
- Checking whether a player's line has been set too high or low historically

## When NOT to Use

- Team sides and totals, see `feature-engineering`, `odds-analysis`
- Staking and CLV mechanics, see `edge-detection`
- Descriptive form with no line involved, see `player-form`
- Women's college basketball: no player props are served for `ncaaw`

## Commands Available

| Command | What it does | Credits |
|---------|-------------|---------|
| `get_prop_history` | One market for one player: per game the closing line (median across books or one `bookmaker`), opening line, prices, `actual`, `result`, `margin`, and a `summary` with `over_rate`. Returns up to 200 games | 10 |
| `get_player_props` | Props by book for a game (`game_id`), or one player across dates (`player_id` + `from_date`, optional `to_date`). `market`, `bookmaker`, `snapshot_type` (`closing` default, or `opening`). `estimate_only` returns the cost without charging | 10 per game |
| `search_players` | Player id | 1 |
| `get_player_games` | Game log for minutes and rates | 5 |
| `get_injuries` | Availability of the player and his teammates | 2 |
| `get_odds` | Game spread and total (blowout risk, pace) | 5 |

Markets: `player_points`, `player_rebounds`, `player_assists`, `player_threes`, `player_points_rebounds_assists`, `player_blocks`, `player_steals`. Leagues: `nba`, `wnba`, `ncaam`.

## Commands That Do NOT Exist

| Not available | Use instead |
|---------------|-------------|
| `get_prop_projections`, `get_dfs_projections` | Build locally |
| `get_alt_lines` | Not served; one line per book per snapshot |
| `get_live_props` | Not served; closing or opening snapshots only |
| `get_lineups`, `get_minutes_projection` | Model minutes from the log |
| Props for `ncaaw` | Not available |

## Coverage

Prop lines run from May 2023 for the NBA and WNBA and from the 2023-24 season for men's college. Prices come from several books (DraftKings, FanDuel, BetMGM, ESPN BET, Pinnacle and others). `get_player_props` returns lowercase bookmaker keys (`draftkings`, `betmgm`, `espnbet`); `get_odds` returns display names. Use the right form per tool.

## How It Works

**Step 1: Establish the base rate from history.** `get_prop_history {"player_id": "3934672", "market": "player_points", "from_date": "2025-10-20", "limit": 6}` returned six games. Trimmed:

```json
{"data": {"games": [
  {"game_date": "2025-10-22", "line": 24.5, "open_line": 24.5, "over_odds": -106, "under_odds": -120, "books": 7, "actual": 23, "result": "under", "margin": -1.5},
  {"game_date": "2025-10-24", "line": 25.5, "actual": 31, "result": "over", "margin": 5.5}
 ],
 "summary": {"games": 6, "graded": 6, "overs": 5, "unders": 1, "pushes": 0, "over_rate": 0.833, "avg_line": 25.8, "avg_actual": 31.2},
 "truncated": true, "next_from_date": "2025-11-03"}}
```

Read it carefully: 5 overs in 6 games is an 83% over rate, but with 6 games the 95% interval runs from about 44% to 97%. It is a story, not evidence. The line moved from 24.5 to 27.5 over those games, so the market was already chasing his scoring. Use the full season (up to 200 games per call) before saying anything.

**Step 2: Project minutes.** Minutes are the biggest driver. From `get_player_games`, take a shrunk rolling mean (see `player-form`), then adjust:

| Factor | Direction |
|--------|-----------|
| Game spread large (blowout risk) | Minutes down for starters; the absolute spread above about 10 is a flag |
| Back-to-back or heavy recent load | Possible rest, check `get_injuries` |
| Teammate out (starter or primary creator) | Minutes and usage up for the next player |
| Foul trouble history | Wider minutes distribution |

**Step 3: Rate per minute.** `rate = stat / minutes` over a window with shrinkage toward a season value. Project `mean = proj_minutes * rate`.

**Step 4: Distribution.** Convert the mean to `P(over line)`.

| Market | Distribution | Notes |
|--------|--------------|-------|
| Points | Normal around the mean, or the empirical distribution of the player's recent games scaled to the projection | Per-game standard deviation of a star scorer is often near 7; estimate it from his own log |
| Rebounds, assists | Negative binomial or normal | Overdispersed relative to Poisson |
| Threes, blocks, steals | Poisson or negative binomial | Low counts; a line of 2.5 means over needs 3 or more |
| Points + rebounds + assists | Sum of components with covariance | Do not add variances as if independent; minutes link them |

Half-point lines remove pushes. Whole-number lines can push; if the line is 25, `P(over) = P(X >= 26)` and `P(push) = P(X = 25)`.

```python
from scipy.stats import norm
p_over = 1 - norm.cdf(line + 0.5 - mean, scale=sd)    # continuity correction for integer outcomes
```

**Step 5: Compare with the market.** Pull prices: `get_player_props {"player_id": "3934672", "from_date": "2025-10-22", "to_date": "2025-10-22", "market": "player_points"}` returned a row per book. The lines differed by book that night (23.5 at Bovada and ESPN BET, 24.5 at BetMGM, BetOnline and DraftKings), with BetMGM at over -125 / under -105. Devig each pair (see `odds-analysis`): BetMGM's fair over probability was 0.520. Only compare prices at the same line, or adjust the probability for the half-point.

**Step 6: Calibrate and shrink.** Your `P(over)` carries error from minutes, sd and rate. Blend toward the market: `p* = 0.5 * p + 0.5 * m` as a start (see `edge-detection`), and check calibration with history from `get_prop_history`: predicted over probabilities versus the realized `result` (see `probability-calibration`).

**Step 7: Decide.** Required: a gap over the vig plus model error. Single-prop edges under 3 points do not survive that. Correlated props (the same game's points and PRA, or a player's over and his team total over) must not be sized independently.

## Cost Control

- `get_player_props` with `estimate_only: true` returns the cost without running it (`{"estimate_only": true, "tool": "get_player_props", "credits": 10}` for one game).
- One player across 40 games with `player_id` and `from_date` is 400 credits; `get_prop_history` is 10 credits for up to 200 games of lines and results, so use it for history and reserve `get_player_props` for current book-by-book prices.
- Pull `bookmaker` filters when you only need one book.
- `snapshot_type: "opening"` against `"closing"` shows how the line moved: closing line value for props is measured against the closing price of the same book.

## Props-specific Pitfalls

| Pitfall | Handling |
|---------|----------|
| Small history windows | Under 30 games, a hit rate is noise |
| Line differs across books | Edge may be a line difference, not a probability difference |
| The posted line is stale | Check `captured_at`; confirm the live price at the book |
| Player ruled out | A void or missing game is not an under; exclude games with `did_not_play` |
| Regular season vs playoffs | Separate samples |
| Overs in a blowout | Starters sit; model with the spread |
| Selection bias | A player who gets props is already a role player with a stable role |
| Treating hit rate as probability | It is a base rate; the line was set knowing the same history |

This skill estimates probabilities. It does not produce picks or promise returns.

## Credit Usage

| Operation | Credits |
|-----------|---------|
| Id lookup | 1 |
| Full season of one market's history | 10 |
| Game log for projection | 5 |
| Every book's prop prices for one game | 10 |
| Four markets for one player's history | 40 |

## Output Format

```
[Player], [market], line [x] ([book]), [date]
History: [n] games, over rate [x]% (95% CI [lo]% to [hi]%), avg line [x] vs avg actual [x]
Projection: minutes [x], rate [x]/min, mean [x], sd [x]
P(over) model [x]% | market fair [x]% | shrunk [x]%
Best price: over [odds] @ [book] / under [odds] @ [book]
Caveats: [injury, blowout risk, small sample]
```

## What to Do Next

| Found | Next | Skill |
|-------|------|-------|
| A projection that disagrees with the line | EV, shrink, stake | `edge-detection` |
| Minutes uncertainty | Role and trend | `player-form` |
| Over rate looks extreme | Test it on history | `backtesting` |
