---
name: game-lookup
description: "Finds basketball games and reads results: scores by date, team, range or season, upcoming schedule, and a single game's full box score. Use when the user asks who played, what the score was, who plays tonight, a team's recent results, or wants a game id for another call. Covers NBA, WNBA, men's and women's college. Do not use for odds comparison, see odds-explorer. Do not use for team strength, see team-analysis. Do not use for a pre-game breakdown, see game-preview."
metadata:
  version: 1.0.0
  author: DunkAPI
---

# Game Lookup

> **Default data tool:** DunkAPI (`dunkapi-tool`).
> `list_games` (2 credits) for results, `get_schedule` (2) for upcoming games, `get_game` (5) for one game in full.

You find the right game fast and return it cleanly. Most other skills need a `game_id` first; this one produces it.

## When to Use

- "What was the score of the Knicks game?" / "Last night's NBA results"
- "Who plays tonight?" / "Celtics schedule this week"
- "Show me the box score for that game"
- "Every Lakers road game this season"
- Any request that needs a `game_id` before another skill can run

## When NOT to Use

- Comparing sportsbooks or reading line moves, see `odds-explorer`
- Ranking teams or reading efficiency, see `team-analysis`
- A full matchup breakdown with injuries and ratings, see `game-preview`
- Shot-level detail from a game, see `shot-zone-analysis`

## Commands Available

| Command | What it does | Credits |
|---------|-------------|---------|
| `list_teams` | Team ids and abbreviations for a season | 1 |
| `list_games` | Games with scores by season, date, range or team, newest first | 2 |
| `get_schedule` | Next 1-30 days with the median spread, total and moneylines | 2 |
| `get_game` | One game: team box scores, every player line, each book's open and close, win-probability range | 5 |

## Commands That Do NOT Exist

| Not available | Use instead |
|---------------|-------------|
| `get_box_score` | `get_game` |
| `get_scoreboard` | `list_games` with `date` (finals) or `get_schedule` (upcoming) |
| `get_live_scores` | None. Data is historical and next-day, not live |
| `get_head_to_head` | `list_games` with `team`, then filter the opponent in code |

## Season Resolution

- `season` is the year the season ends: 2025-26 is `2026`, 2026-27 is `2027`.
- Oct 20, 2026 is the NBA opener. Before it, `get_schedule` returns `preseason` games tagged `season: 2027`.
- WNBA is the calendar year. `season_type` values: `regular`, `postseason`, `play_in`, `preseason`.
- Dates are US Eastern. A 10:30 pm ET tip can have a UTC `starts_at` on the next day; filter by the `date` field, not `starts_at`.

## How It Works

**Step 1: Resolve the team.** If the user says "the Knicks" and you do not have the abbreviation, call `list_teams` (1 credit). The API accepts an id or an abbreviation (`NY`, `BOS`, `GS`, `SA`). Do not guess; `GS` and `NY` are the codes here, not `GSW` or `NYK`.

**Step 2: Pick the listing call.**

| Question | Call |
|----------|------|
| Last night's scores | `list_games` with `date` set to yesterday |
| A team's recent games | `list_games` with `team` and `limit` |
| A playoff series | `list_games` with `team`, `season`, `season_type: "postseason"` |
| A date range | `list_games` with `from` and `to` |
| Tonight and the week | `get_schedule` with `days` and optionally `team` |

**Step 3: Get the box score only when needed.** `list_games` already has the score, venue and overtime count. Call `get_game` (5 credits) for player lines, team box scores, books' lines or the win-probability range.

**Step 4: Present it.** Lead with the answer (score, winner, margin), then the detail.

### Live example

`list_games {"team": "NY", "season": 2026, "limit": 3}` returned the latest postseason games (NY vs SA, June 2026), newest first. Trimmed:

```json
{"data": {"games": [
  {"game_id": "401859967", "season": 2026, "season_type": "postseason",
   "date": "2026-06-13", "status": "final",
   "home": {"abbrev": "SA", "score": 90}, "away": {"abbrev": "NY", "score": 94},
   "periods": 4, "overtime_periods": 0, "venue": "Frost Bank Center"}
 ], "count": 3, "next_offset": 3}}
```

Pass `next_offset` back as `offset` for the next page. Paging past 50 games (the default `limit`) costs 2 credits per page.

### What `get_game` returns

- `game`: score, venue, attendance, periods
- `team_stats`: per team `pts fgm fga tpm tpa ftm fta oreb dreb reb ast stl blk tov pf fast_break_pts paint_pts points_off_turnovers largest_lead`
- `players`: per player `minutes pts fgm fga tpm tpa ftm fta oreb dreb reb ast stl blk tov pf plus_minus`, plus `starter` and `did_not_play`
- `odds`: per book opening and closing moneyline, spread and total
- `win_probability`: `home_min`, `home_max`, `plays_with_probability`

## Reading a box score

- **Possessions** ~ `fga - oreb + tov + 0.44 * fta` (same formula the API uses for ratings). Points per possession is a better efficiency read than raw points.
- **True shooting** = `pts / (2 * (fga + 0.44 * fta))`.
- **Effective FG%** = `(fgm + 0.5 * tpm) / fga`.
- Compare `paint_pts`, `fast_break_pts` and `points_off_turnovers` to see how a team scored, not just how much.
- `plus_minus` in a single game is noisy. Do not rank players on it.
- A very wide `home_min` to `home_max` win-probability range means the lead changed hands; a narrow band means a wire-to-wire game.

## Gotchas

| Gotcha | Handling |
|--------|----------|
| `list_games` is newest first | Reverse before computing rolling stats |
| Postseason, play-in and preseason are separate | Filter `season_type` or you mix preseason with real games |
| Scheduled games have `score: null` | Do not treat null as zero |
| Overtime games | Check `overtime_periods`; per-game totals and pace need adjusting |
| A game with no line | `line.books` can be 1 or 0 on preseason games; do not call it "the market" |

## Credit Usage

| Operation | Credits |
|-----------|---------|
| Look up a team abbreviation | 1 |
| One page of results (up to 50 games) | 2 |
| Tonight's slate | 2 |
| One full box score | 5 |
| Every box score for a 6-game series | 30 |

## Output Format

```
New York Knicks 94, San Antonio Spurs 90 (Final, Jun 13 2026)
Frost Bank Center | Postseason | game_id 401859967

Top lines: [player] [pts], [fgm]-[fga] FG, [tpm]-[tpa] 3P, [ftm]-[fta] FT
```

## What to Do Next

| Found | Next | Skill |
|-------|------|-------|
| A game to analyze before tip | Full preview | `game-preview` |
| A game with lines | Compare books | `odds-explorer` |
| Shot detail | Zone profile for the game | `shot-zone-analysis` |
| A player's big night | Context against his average | `player-form` |
