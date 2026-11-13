---
name: player-scouting
description: "Looks up and profiles basketball players: finds the player id, reads per-season averages and shooting splits, compares two or more players on a per-minute basis, and pulls season leaderboards. Use when the user asks about a player, who leads a stat, how two players compare, or whether a scoring line is efficient or lucky. Covers NBA, WNBA, men's and women's college. Do not use for rolling or recent form across a season, see player-form. Do not use for shot location, see shot-zone-analysis. Do not use for prop lines, see prop-modeling."
metadata:
  version: 1.0.0
  author: DunkAPI
---

# Player Scouting

> **Default data tool:** DunkAPI (`dunkapi-tool`).
> `search_players` (1 credit) to get the id, `get_player` (5) for profile and averages, `get_leaders` (5) for leaderboards.

You turn a name into a defensible read on a player: usage-adjusted, efficiency-checked, with the sample size stated.

## When to Use

- "Tell me about Jalen Brunson" / "Is he actually efficient?"
- "Compare Tatum and Brown" / "Who is the better rebounder per minute?"
- "Who led the league in true shooting?" / "Top 10 in assists"
- "How did he do in the playoffs vs the regular season?"
- Finding a `player_id` for another skill

## When NOT to Use

- Game-by-game rolling averages or minutes trends, see `player-form`
- Where a player shoots from, see `shot-zone-analysis`
- Whether he will beat a points line, see `prop-modeling`
- A team-level question, see `team-analysis`

## Commands Available

| Command | What it does | Credits |
|---------|-------------|---------|
| `search_players` | Player id from a full or partial name, most recent players first | 1 |
| `get_player` | Profile, per-season averages and shooting splits (regular season and postseason as separate rows), last 10 games | 5 |
| `get_leaders` | Season leaders by `pts reb ast stl blk tpm min plus_minus fg_pct tp_pct ft_pct ts_pct total_pts` | 5 |
| `get_player_games` | Full game log (for form, see `player-form`) | 5 |

## Commands That Do NOT Exist

| Not available | Use instead |
|---------------|-------------|
| `get_player_stats` | `get_player` |
| `get_usage_rate`, `get_per`, `get_bpm`, `get_vorp` | Not served. Compute per-minute rates and true shooting from `get_player` fields |
| `get_player_tracking` | Not served; no speed, touches or contested-shot data |
| `compare_players` | Call `get_player` for each, compare in code |
| `get_draft_prospects`, `get_contract` | Not served |

## Season Resolution

`season` is the year the season ends (2025-26 is `2026`). The WNBA uses the calendar year. `search_players` returns `last_season`; a stale value means the player is retired or has not played recently.

## How It Works

**Step 1: Find the id.** `search_players {"name": "brunson", "limit": 3}` returned two people:

```json
{"data": {"players": [
  {"player_id": "3934672", "name": "Jalen Brunson", "position": "G", "team": "NY", "last_season": 2027},
  {"player_id": "106", "name": "Rick Brunson", "position": "PG", "team": "PHI", "last_season": 2007}
]}}
```

Match on `last_season` and `team` before spending 5 credits on the wrong profile. Pass `league` for WNBA or college; the default is the NBA.

**Step 2: Pull the profile.** `get_player` returns `player`, `seasons` (one row per season per `season_type`, with `games starts min pts reb ast stl blk tov oreb dreb pf plus_minus fgm fga tpm tpa ftm fta fg_pct tp_pct ft_pct efg_pct ts_pct`) and `recent_games` (last 10).

**Step 3: Normalize.** Per-game numbers hide minutes. Convert before comparing:

```
per36(stat)   = stat / min * 36
fga_per36     = fga/games / min * 36
ts_pct        = pts / (2 * (fga + 0.44 * fta))          [totals, not per game]
three_rate    = tpa / fga
ft_rate       = fta / fga
ast_to_tov    = ast / tov
```

`total_pts`, `fgm`, `fga` and the other counting fields on a season row are season totals; `pts`, `reb`, `ast` and `min` are per-game averages. Do not divide a total by a per-game number.

**Step 4: Check the sample.** Under about 20 games, shooting percentages are noise. Under 100 three-point attempts, `tp_pct` has a standard error near 5 points (`sqrt(p*(1-p)/n)` with p = 0.35, n = 100 gives 0.048). State the attempts next to every percentage.

**Step 5: Split by season type.** The API returns postseason rows separately. Playoff rows are fewer games against better defences; compare them to the player's own regular season, not to other players' regular season.

**Step 6: Leaderboards.** `get_leaders {"stat": "ts_pct", "season": 2024, "limit": 3}` returns `leaders` (`player_id name team games value`) with a `min_games` floor (default: a quarter of the season). Percentage leaders are dominated by low-usage centers. Read `games` and pair a percentage leader with a volume stat before calling anyone elite.

## Comparing Two Players

1. Same season, same `season_type`, same league.
2. Normalize to per-36 minutes and show the minutes gap.
3. Show shooting as `ts_pct` plus the attempts that produced it.
4. Show role: `starts / games`, `min`, `three_rate`, `ft_rate`.
5. Say what the data cannot see: defence, off-ball value, lineup effects (no tracking or on/off data here).
6. One-line verdict that matches the numbers shown.

## Interpreting Efficiency

| Reading | Meaning |
|---------|---------|
| `ts_pct` above ~0.60 on 15+ FGA per game | Elite efficient volume scorer |
| `efg_pct` well above `fg_pct` | Threes drive the efficiency |
| `ts_pct` far above `efg_pct` | Free throws drive it |
| `fg_pct` high, `fga` very low | Role player finishing, not creating |
| `plus_minus` per game | Team context; do not rank players on it |

Thresholds are rules of thumb from league-wide norms. Compare with `get_leaders` for the same season rather than trusting a fixed number.

## Gotchas

| Gotcha | Handling |
|--------|----------|
| Traded players | `teams` can read like `DAL/WSH` on a season row; the line is combined |
| Two rows for one season | Regular season and postseason; filter by `season_type` |
| College players | Rows are by season; players change teams and roles; sample sizes are 25-35 games |
| Same name, different players | Check `last_season` and `team` |
| A rookie with few games | Show games played first and widen the caveat |

## Credit Usage

| Operation | Credits |
|-----------|---------|
| Id lookup | 1 |
| Profile | 5 |
| Two-player comparison | 12 (2 lookups + 2 profiles) |
| Leaderboard | 5 |

## Output Format

```
[Player], [team], [pos]: [season] regular season ([games] GP, [min] mpg)
Per game: [pts]/[reb]/[ast] on [fg%]/[3p%]/[ft%], TS [ts%]
Per 36:   [pts]/[reb]/[ast]
Sample:   [tpa] 3PA, [fta] FTA
Playoffs: [games] GP, [pts]/[reb]/[ast], TS [ts%]
Read: [one sentence that matches the numbers above]
```

## What to Do Next

| Found | Next | Skill |
|-------|------|-------|
| Efficiency looks off | Where the shots come from | `shot-zone-analysis` |
| Recent change in output | Rolling form | `player-form` |
| Wants to bet his line | Prop history | `prop-modeling` |
| Wants the team context | Team efficiency | `team-analysis` |
