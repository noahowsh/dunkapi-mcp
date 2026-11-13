---
name: shot-zone-analysis
description: "Analyzes basketball shot profiles by zone using DunkAPI shot data: attempts, makes and points per shot in restricted area, paint, midrange, corner three and above-the-break three, compared with expected points per shot to separate shot quality from shot making. Also covers team defence by zone, clutch shots and drawing a shot chart from x/y. Use when the user asks where a player or team shoots, whether a hot shooter is lucky, which defence gives up the worst shots, or wants expected points. Do not use for season box-score averages, see player-scouting. Do not use for team pace and ratings, see team-analysis."
metadata:
  version: 1.0.0
  author: DunkAPI
---

# Shot Zone Analysis

> **Default data tool:** DunkAPI (`dunkapi-tool`).
> `get_shot_chart` (10 credits) for zone summaries, `get_plays` (10) for individual shots with game context.

The question is rarely "what is his FG%". It is: where do the shots come from, what is each shot worth on average, and is the result above or below what those shots usually produce.

## When to Use

- "Where does Brunson score from?" / "Does he live in the midrange?"
- "Is his shooting sustainable?" (shot quality versus shot making)
- "Which team allows the most corner threes?" (defence by zone)
- "Show his clutch shots" / "Every shot he took in the 4th"
- "Draw me a shot chart"

## When NOT to Use

- Season averages and per-36 rates, see `player-scouting`
- Team pace, ratings and four factors, see `team-analysis`
- Game-by-game minutes and scoring trend, see `player-form`

## Commands Available

| Command | What it does | Credits |
|---------|-------------|---------|
| `get_shot_chart` | Zone table (`attempts made pct points_per_shot expected_points_per_shot`) and a `share` of attempts for a player, a team, a team's opponents (`opponent: true`), or one game. `include_shots: true` adds each shot's x, y, result (up to 3,000). NBA and WNBA only | 10 |
| `get_plays` | Play-by-play with `shot` objects: `made points_attempted x y distance_ft zone expected_points`, plus score and home win probability. Filter by `zone`, `period`, `made`, `clutch`, `shots_only`. All four leagues | 10 |
| `search_players` | Find the player id | 1 |
| `list_teams` | Team abbreviations | 1 |

## Commands That Do NOT Exist

| Not available | Use instead |
|---------------|-------------|
| `get_shot_quality`, `get_xpts` | Fields on `get_shot_chart` and `get_plays` |
| `get_defender_distance`, `get_shot_tracking` | Not served; no contest or tracking data |
| `get_league_shot_averages` | Not served; build a baseline by calling `get_shot_chart` per team |
| College `get_shot_chart` | Not available for `ncaam` or `ncaaw`; use `get_plays` and check the `shot` fields are populated before relying on zones |

## Zones

`restricted_area`, `paint` (non-restricted), `midrange`, `corner_3`, `above_break_3`, `free_throw`. The free throw row has `expected_points_per_shot: null` and no x/y; `share` and `field_goal_attempts` cover field goals only.

Play-by-play covers NBA games back to 2003-04, and the `get_plays` tool description says win probability after each play is available from 2018. Check https://dunkapi.com/docs/atlas for the seasons that carry shot locations before building a multi-year study.

## How It Works

**Step 1: Pull the profile.** `get_shot_chart {"player_id": "3934672", "season": 2026}`.

**Step 2: Read quality and result separately.**

- `expected_points_per_shot` (xPPS) is what the shot is worth on average given where and how it was taken.
- `points_per_shot` (PPS) is what the player actually scored: `pct * 2` or `pct * 3`.
- Shot making = `PPS - xPPS` per zone.
- Points above expected = `sum(attempts * (PPS - xPPS))` over field-goal zones.

The same zone has different xPPS for different players (restricted area read 1.27 for Jayson Tatum in 2024 and 1.132 for Brunson in 2026), so xPPS reflects shot location and type within the zone, not a single zone constant. Compare a player to himself across seasons before comparing across players.

**Step 3: Look at the mix.** `share` sums to 1 over field-goal zones. A profile heavy in the restricted area, corner three and free throws is efficient by construction; one heavy in midrange and long twos needs above-average making to break even.

**Step 4: Weigh the sample.** A zone with under 100 attempts has a large standard error; for a 35% three-point shooter on 90 attempts it is about 5 points of percentage. Shot making is noisy and regresses; shot quality is more stable.

### Live example

`get_shot_chart {"player_id": "3934672", "season": 2026}` (Jalen Brunson, 2025-26), trimmed:

| Zone | Attempts | FG% | PPS | xPPS | Above expected per shot |
|------|---------:|----:|----:|-----:|-----------------------:|
| restricted_area | 196 | 0.653 | 1.306 | 1.132 | +0.174 |
| paint | 470 | 0.474 | 0.949 | 0.846 | +0.103 |
| midrange | 302 | 0.507 | 1.013 | 0.808 | +0.205 |
| corner_3 | 90 | 0.411 | 1.233 | 1.147 | +0.086 |
| above_break_3 | 456 | 0.349 | 1.046 | 1.031 | +0.015 |

`field_goal_attempts` 1,514. Summing `attempts * (PPS - xPPS)` gives about +159 points over expected, or +0.105 per shot. Shot mix: `paint` 31.0%, `above_break_3` 30.1%, `midrange` 19.9%, `restricted_area` 12.9%, `corner_3` 5.9%.

Read: his shot quality is ordinary (mean xPPS about 0.95, driven by a low restricted-area share), and the outcome beats it in every zone, most in the midrange (+0.205 per shot on 302 attempts, about +62 points). That is the part least likely to repeat at that size. A forecast should keep the shot mix and shrink the making toward zero, not extrapolate +0.105.

## Defence by Zone

`get_shot_chart {"team": "BOS", "opponent": true, "season": 2026}` returns what opponents took and made against that team. Compare its `share` and xPPS with other teams (30 calls = 300 credits for the league; budget it). Two things to separate:

1. Shot selection allowed (what zones opponents take): a defence, scheme and personnel signal.
2. Shot making allowed (opponent PPS minus xPPS): partly luck, and regresses.

## Clutch and Single-game Shots

`get_plays {"player_id": "3934672", "season": 2026, "clutch": true, "shots_only": true, "limit": 2}` returned a 16-foot step-back midrange make with 164 seconds left in the 4th (xPPS 0.82, home win probability after the play 0.609) and a missed free throw. `clutch` is the last 5 minutes of the 4th quarter (second half for college men) or overtime with the score within 5.

Use `home_win_prob` before and after a play to measure its leverage: `delta = home_win_prob_after - home_win_prob_before`, sign-flipped for the away team. Sum it over a player's shots for a "win probability added from shooting" figure, with a small sample warning: clutch samples are tens of shots per season.

## Drawing a Chart

`include_shots: true` adds every located shot's x, y and result (cap 3,000). x and y are court-grid coordinates (one corner three above came back x=48, y=1). Plot a scatter, color by `made`, and check orientation against a known corner three before trusting the axes. Bin into hexagons for large samples and size by attempts, not by percentage.

## Pitfalls

| Pitfall | Handling |
|---------|----------|
| Treating PPS - xPPS as skill | Small samples; shrink toward zero |
| Mixing regular season and postseason | Pass `season_type` |
| Counting free throws in `share` | They are excluded; add them separately |
| Comparing players' xPPS directly | It varies within a zone; compare to the player's own history and role |
| Two-point zones use `points_attempted` 2, threes 3 | Keep it when computing PPS by hand |
| Large `include_shots` payloads | Ask only when drawing |

## Credit Usage

| Operation | Credits |
|-----------|---------|
| One player or team profile | 10 |
| League defence by zone (30 teams) | 300 |
| 200 individual plays | 10 |

## Output Format

```
[Player/Team], [season], [n] FGA
Zone            FGA   FG%   PPS   xPPS  +/- per shot
restricted_area [n]   [x]   [x]   [x]   [x]
...
Mix: [top 2 zones and share]
Above expected: [points] over [n] shots ([x] per shot)
Read: [what is shot quality, what is shot making, what is likely to repeat]
```

## What to Do Next

| Found | Next | Skill |
|-------|------|-------|
| Player shooting far above expected | Is the minutes/role stable | `player-form` |
| Defence gives up corner threes | Total or spread angle | `odds-explorer` |
| Want quality as a model feature | Leak-free rolling version | `feature-engineering` |
