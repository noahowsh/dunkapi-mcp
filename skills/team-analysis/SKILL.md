---
name: team-analysis
description: "Evaluates basketball teams: standings, DunkAPI Elo power ratings, pace, offensive and defensive rating, net rating and the four factors (eFG%, turnover rate, offensive rebound rate, free throw rate). Use when the user asks how a team is doing, who the best or fastest team is, why a team's record misleads, or wants two teams compared. Covers NBA, WNBA, men's and women's college. Do not use for a single game, see game-lookup or game-preview. Do not use for a player, see player-scouting. Do not use for where a team shoots from, see shot-zone-analysis."
metadata:
  version: 1.0.0
  author: DunkAPI
---

# Team Analysis

> **Default data tool:** DunkAPI (`dunkapi-tool`).
> `get_standings` (2 credits), `get_ratings` (2), `get_team_stats` (5). A full three-call team profile is 9 credits.

You read a team the way an analyst does: results first, then the efficiency that explains them, then whether the record is likely to hold.

## When to Use

- "How good are the Knicks?" / "Rank the East"
- "Who plays fastest?" / "Best defence in the league?"
- "Is Boston's record real or lucky?"
- Comparing two teams before a game or a series
- Producing team-level features for a model (see `feature-engineering`)

## When NOT to Use

- One game's box score or result, see `game-lookup`
- A full pre-game breakdown with injuries and odds, see `game-preview`
- Shot location and expected points by zone, see `shot-zone-analysis`
- Individual players, see `player-scouting`

## Commands Available

| Command | What it does | Credits |
|---------|-------------|---------|
| `get_standings` | Regular-season standings computed from every final game: W-L, home and away, points for and against, margin, last 10 | 2 |
| `get_ratings` | DunkAPI Elo ratings, ranked, as of the end of a season or today | 2 |
| `get_team_stats` | Pace, offensive, defensive and net rating per 100 possessions, four factors, three-point rate | 5 |
| `list_teams` | Team ids and abbreviations | 1 |

## Commands That Do NOT Exist

| Not available | Use instead |
|---------------|-------------|
| `get_advanced_team_stats` | `get_team_stats` |
| `get_power_rankings` | `get_ratings` (our Elo) or rank `get_team_stats` by `net_rating` |
| `get_lineup_stats`, `get_on_off` | None; lineup data is not served |
| `get_strength_of_schedule` | Derive from `list_games` plus `get_ratings` (see below) |

## Season Resolution

`season` is the year the season ends (2025-26 is `2026`). The 2026-27 NBA season opens Oct 20, 2026. Until a few weeks of games exist, `season: 2027` ratings and efficiency rest on almost nothing; use `season: 2026` and say it is last season. `get_team_stats` accepts `season_type`, so you can separate playoff efficiency from the regular season.

## How It Works

**Step 1: Results.** `get_standings` returns per team `wins losses home_wins home_losses away_wins away_losses points_for points_against avg_margin last10_wins win_pct`. The `conf_wins` and `conf_losses` fields read 0 in the responses seen for NBA, so do not rank on conference record from this tool.

**Step 2: Efficiency.** `get_team_stats` returns, per team:

| Field | Meaning |
|-------|---------|
| `pace` | Possessions per game |
| `off_rating`, `def_rating`, `net_rating` | Points scored, allowed and the difference, per 100 possessions |
| `efg_pct` | Effective FG%: `(fgm + 0.5 * tpm) / fga` |
| `tov_pct` | Turnover rate (fraction of possessions ending in a turnover) |
| `oreb_pct` | Offensive rebound rate |
| `ft_rate` | Free throw attempts per field goal attempt |
| `three_rate` | Share of shots that are threes |
| `opp_efg_pct` | Opponent effective FG% (the defensive half of factor one) |

Possessions are estimated as `FGA - OREB + TOV + 0.44 * FTA`, averaged over both teams (the API states this in `method`). Ratings are points per 100 possessions.

**Step 3: Strength.** `get_ratings` gives the Elo rating. 1500 is average; a 100-point gap is about a 64% favourite on a neutral floor. In general `P(A beats B) = 1 / (1 + 10^(-(rA - rB + home_edge) / 400))`. The API says its ratings include home advantage and a margin-of-victory multiplier, and regress a quarter of the way to the mean between seasons, so an early-season rating is mostly last year's.

**Step 4: Cross-check.** A team's Elo, net rating and record should roughly agree. When they do not, that is the finding:

| Pattern | Likely read |
|---------|-------------|
| Record well above what `net_rating` implies | Close-game luck; expect regression |
| `net_rating` strong, record average | Unlucky or a slow starter; check `last10_wins` |
| Elo far above `net_rating` rank | Elo carries last season or playoff results |
| High `off_rating`, low `efg_pct` | Scoring from free throws, turnovers and rebounding, not shooting |

A quick luck check: Pythagorean wins `= games * pts^14 / (pts^14 + opp_pts^14)`, using `pts` and `opp_pts` from `get_team_stats`. The exponent 14 is the usual NBA value; a gap of 3 or more wins between this and actual wins is worth flagging.

### Live example

`get_team_stats {"season": 2026, "team": "NY"}`, trimmed:

```json
{"data": {"season": 2026, "teams": [{
  "abbrev": "NY", "games": 83, "wins": 54, "losses": 29,
  "pts": 116.5, "opp_pts": 110.2, "pace": 99.8,
  "off_rating": 116.8, "def_rating": 110.4, "net_rating": 6.4,
  "efg_pct": 0.557, "tov_pct": 0.137, "oreb_pct": 0.296,
  "ft_rate": 0.237, "three_rate": 0.427, "opp_efg_pct": 0.54}]}}
```

Read: a +6.4 net rating over 83 games is a strong team but not a dominant one; its offensive rebounding (`oreb_pct` 0.296) is doing real work. `get_ratings {"season": 2026}` ranked the same team first in Elo at 1808.1 as of its last game (2026-06-14), ahead of SA at 1767.9. Elo gives credit for the playoff run, which `net_rating` for the regular season does not.

## Strength of schedule

No tool returns it. Build it: `list_games` for the team (2 credits per page), then average the opponents' `get_ratings` values. Use opponent ratings from the same season, and say the ratings are end-of-season so the result is a description, not a pre-game input.

## Comparing two teams

1. Pull `get_team_stats` for each (a call with no `team` returned all 30 NBA teams for 5 credits, cheaper than two single-team calls).
2. Build the matchup lens: team A `off_rating` against team B `def_rating`, and the reverse; add `pace` (the faster team tends to set it, but the average is a fair projection).
3. Projected margin ~ `(A.off_rating + B.def_rating)/2 - (B.off_rating + A.def_rating)/2`, scaled by `pace / 100`, plus a home-court edge. Treat this as a prior, then check `get_injuries`.

## Pitfalls

| Pitfall | Why it matters |
|---------|---------------|
| Season aggregates used for past games | `get_team_stats` and `get_ratings` summarize the whole season. Using them to "predict" an earlier game leaks the future. For modeling, rebuild as-of values from `list_games` |
| Small samples | Under 15 games, net rating moves 3+ points on a single blowout |
| Garbage time and rest | Net rating includes both; a team resting starters understates talent |
| Mixing season types | Pass `season_type` to separate playoffs from regular season |
| College comparisons | Conferences are weakly connected; a high rating inside a weak conference is not comparable to one outside it |

## Credit Usage

| Operation | Credits |
|-----------|---------|
| Standings only | 2 |
| Elo only | 2 |
| All teams' efficiency | 5 |
| Full profile (standings + Elo + efficiency) | 9 |

## Output Format

```
[Team], [season]: [W]-[L], net rating [x] ([rank] of [n]), Elo [x] ([rank])
Pace [x] | Off [x] | Def [x]
Four factors: eFG [x], TOV [x], ORB [x], FT rate [x]; opponent eFG [x]
Read: [one sentence on whether the record is supported by the efficiency]
```

## What to Do Next

| Found | Next | Skill |
|-------|------|-------|
| Two teams meeting soon | Full matchup | `game-preview` |
| Shooting is driving the gap | Zone breakdown | `shot-zone-analysis` |
| Want team features for a model | Rolling, leak-free | `feature-engineering` |
| Rating gap vs the market | Compare to the line | `odds-explorer` |
