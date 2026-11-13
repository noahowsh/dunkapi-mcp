---
name: player-form
description: "Reads a basketball player's recent form from his game log: rolling averages, minutes trend, per-minute rates, rest effects, home and road splits and opponent context, with proper shrinkage so a hot week is not mistaken for a new talent level. Use when the user asks if a player is hot, how his minutes have changed, what his last 10 games say, or needs rolling inputs for a projection. Covers NBA, WNBA, men's and women's college. Do not use for season profile and comparisons, see player-scouting. Do not use for shot location, see shot-zone-analysis. Do not use for prop lines, see prop-modeling."
metadata:
  version: 1.0.0
  author: DunkAPI
---

# Player Form

> **Default data tool:** DunkAPI (`dunkapi-tool`).
> `get_player_games` (5 credits for a season's log, paged by `limit` and `offset`). `get_player` (5) already contains the last 10 games if that is all you need.

Recent form is mostly minutes and role, a little shooting luck, and very little "heat". This skill separates them.

## When to Use

- "Is Tatum hot?" / "What has his minutes done since the trade?"
- "Give me his last 10 and last 20"
- Rolling inputs for a points, rebounds or assists projection
- Checking whether a big night was role-driven or shooting-driven
- Home/road, rest and opponent splits

## When NOT to Use

- Season averages and cross-player comparisons, see `player-scouting`
- Where the shots came from, see `shot-zone-analysis`
- Turning a projection into a bet against a line, see `prop-modeling`

## Commands Available

| Command | What it does | Credits |
|---------|-------------|---------|
| `search_players` | Player id from a name | 1 |
| `get_player_games` | Full game log, newest first: opponent, home, result, minutes, box score line. Filters `season`, `season_type`, `limit`, `offset` | 5 |
| `get_player` | Profile, season rows, last 10 games | 5 |
| `list_games` | Team schedule dates, for rest and team context | 2 |
| `get_game` | One game's full lines (when you need teammates' minutes) | 5 |

## Commands That Do NOT Exist

| Not available | Use instead |
|---------------|-------------|
| `get_player_stats` | `get_player_games` or `get_player` |
| `get_hot_players`, `get_trending` | Compute from the game log |
| `get_player_splits` | Group the log yourself |
| `get_minutes_projection`, `get_lineups` | Not served; model minutes from the log |
| `get_usage_rate` | Not served; use `fga + 0.44 * fta + tov` per minute as a usage proxy |

## Season Resolution

`season` is the year the season ends (2025-26 is `2026`). The default is the latest season. In October of a new season the log holds only preseason games; filter on `season_type` before reading anything into them. In game-log rows `season_type` is returned as a number (3 appeared on postseason games); in `list_games` it is a string. Request the type you want with the string parameter and do not rely on the numeric code for anything else.

## How It Works

**Step 1: Pull the log.** `get_player_games {"player_id": "3934672", "season": 2026, "limit": 100}` returns newest first. Each row: `game_id date season season_type opponent home result starter did_not_play minutes pts fgm fga tpm tpa ftm fta oreb dreb reb ast stl blk tov pf plus_minus`.

```json
{"date": "2026-06-13", "opponent": "SA", "home": false, "result": "W",
 "starter": true, "minutes": 41, "pts": 45, "fgm": 14, "fga": 27,
 "tpm": 4, "tpa": 7, "ftm": 13, "fta": 15, "reb": 3, "ast": 3, "tov": 3}
```

**Step 2: Clean.** Reverse to oldest-first. Drop `did_not_play` rows from rate stats but keep them as a count (availability is itself information). Mark blowouts if you have the score (from `list_games`): minutes in a 25-point game are not minutes in a close one.

**Step 3: Minutes first.** Compute a rolling mean of `minutes` over 5 and 10 games, and the share of games under 30. Most "hot" and "cold" stretches are minutes moving.

**Step 4: Rates.** Per-36 and per-minute rates are steadier than counts:

```python
import pandas as pd
df = pd.DataFrame(rows).sort_values("date")           # oldest first
df = df[~df.did_not_play]
df["pts_per_min"] = df.pts / df.minutes
roll = df[["minutes","pts","reb","ast","tpm"]].rolling(10, min_periods=5).mean()
# a feature for a model must exclude the current game:
feat = df[["minutes","pts"]].shift(1).rolling(10, min_periods=5).mean()
```

`shift(1)` before rolling is the leakage guard: a prediction for game N may only use games before N.

**Step 5: Shrink.** A 10-game points average has a standard error of about `sd / sqrt(10)`. With a per-game sd near 7 for a star scorer, that is about 2.2 points. Blend toward the longer baseline:

```
projection ~ w * rolling10 + (1 - w) * season_mean,   w ~ 0.3 to 0.5
```

Start at 0.3 for scoring and 0.4 for minutes (minutes are stickier). These are starting values; fit `w` on a walk-forward split (see `walk-forward-validation`) instead of trusting them.

**Step 6: Context splits.** Group by `home`, by rest days (difference in `date` between rows), by `opponent`. Splits need 15+ games per bucket to say anything; below that, report the number and call it unproven.

**Step 7: Hot-hand check.** Compare shooting percentage in the last 10 to the season, with attempts. A jump of 8 points of FG% on 130 attempts is within normal variation. A jump in `fga` or `minutes` is real; a jump only in `fg_pct` mostly is not.

### Live example

`get_player_games {"player_id": "3934672", "season": 2026, "limit": 3}` returned his last three games of 2025-26 (all postseason): 45, 36 and 32 points in 41, 44 and 35 minutes. Per minute that is 1.10, 0.82 and 0.91 points. Three games say little; the minute loads (35 to 44) are what stand out, and they are a postseason pattern. A regular-season projection from these rows would overstate his minutes. Filter `season_type: "regular"` for a regular-season baseline and keep playoff rows separate.

For a quick scoring view against a market number, `get_prop_history` (10 credits) returns the same player-game results beside the closing line; its first six rows for the same player, from 2025-10-22, had actual points of 23, 31, 37, 36, 29 and 31 (average 31.2) against an average line of 25.8.

## Interpreting the Output

| Pattern | Likely cause | Action |
|---------|--------------|--------|
| Minutes up 4+ for 5 games | Role change, injury to a teammate | Check `get_injuries` for teammates; raise projection |
| Points up, minutes flat, FGA up | Usage up | Believable |
| Points up, minutes and FGA flat | Shooting luck | Shrink hard |
| Minutes down in blowouts | Garbage time | Control for margin |
| Sudden DNP/low minutes after a game | Injury, rest or discipline | Read the injury report before projecting |
| Two short games then a normal one | Early exit then return | Do not average the short games into the rate |

## Gotchas

| Gotcha | Handling |
|--------|----------|
| Log is newest first | Reverse before rolling |
| Preseason games in the early season | Filter by type |
| Traded players | Team context changes; re-baseline after the move |
| Playoff minutes vs regular season | Separate series |
| `limit` default is 100 | Page with `offset` for longer careers |
| College logs | Fewer games; use a smaller window (5) |

## Credit Usage

| Operation | Credits |
|-----------|---------|
| Id lookup | 1 |
| One season log (up to 100 rows) | 5 |
| Two seasons | 10 |
| Last 10 only | 5 via `get_player` (also returns season rows) |

## Output Format

```
[Player], [team], last 10 vs season
Minutes: [r10] vs [season] ([trend])
Points: [r10] vs [season] | per-36 [x] vs [x]
FGA: [r10] vs [season] | FG% [r10] vs [season] on [n] attempts
Context: [rest/home/road split if 15+ games per bucket]
Verdict: [role change / shooting variance / injury effect], shrunk projection [x]
```

## What to Do Next

| Found | Next | Skill |
|-------|------|-------|
| A projection to compare with a line | Hit-rate and calibration | `prop-modeling` |
| Rolling features for a model | Full feature set | `feature-engineering` |
| Efficiency question | Zone profile | `shot-zone-analysis` |
