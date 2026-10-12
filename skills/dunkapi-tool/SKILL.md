---
name: dunkapi-tool
description: "Default data source for the DunkAPI skills. Routes every call to the 18 DunkAPI tools for NBA, WNBA, men's and women's college basketball: games, box scores, play-by-play, shot charts, team ratings, odds, line movement and player props. Use when any other skill needs basketball data, or when the user asks which tool answers a question or what a call costs. Do not use for analysis, modeling or bet sizing, see team-analysis, shot-zone-analysis, prop-modeling or edge-detection."
metadata:
  version: 1.0.0
  author: DunkAPI
  user-invocable: false
---

# DunkAPI Tool

Every other skill delegates data retrieval here. This skill owns the 18 tools, picks the cheapest call that answers the question, tracks credits, and explains the response envelope.

Free tier: 500 credits every month, no card. Plans and top-ups are on https://dunkapi.com/pricing. Full per-tool reference: https://dunkapi.com/docs. Live coverage by season: https://dunkapi.com/docs/atlas.

## Connecting

| Path | How |
|------|-----|
| MCP | `https://mcp.dunkapi.com/mcp` with header `x-api-key: YOUR_API_KEY` (or `?key=YOUR_API_KEY` on the URL for clients that cannot send headers) |
| REST | `POST https://mcp.dunkapi.com/v1/<tool>` with a JSON body and header `x-api-key: YOUR_API_KEY` |
| Tool catalogue | `GET https://mcp.dunkapi.com/v1/tools` (JSON Schema for every tool) |

```bash
curl -X POST https://mcp.dunkapi.com/v1/get_standings \
  -H "x-api-key: YOUR_API_KEY" -H "content-type: application/json" \
  -d '{"season": 2026}'
```

Over REST, every response is wrapped: `{"data": {...}}`. Read `response["data"]["standings"]`, not `response["standings"]`. REST responses carry `X-Credits-Used` and `X-Credits-Remaining` headers.

## Conventions every tool shares

- `league`: `nba` (default), `wnba`, `ncaam` (men's college), `ncaaw` (women's college). Not every tool accepts every league (table below).
- `season` is the year the season ends: `2026` = 2025-26, `2027` = 2026-27. WNBA seasons are the calendar year.
- `season_type`: `regular`, `postseason`, `play_in`, `preseason`.
- Dates are `YYYY-MM-DD` in US Eastern time.
- Game ids are ESPN game ids (strings like `"401859967"`). Player ids are ESPN athlete ids (like `"3934672"`). Teams take an id or an abbreviation (`NY`, `BOS`, `GS`, `SA`).
- Paged tools return `next_offset`; pass it back as `offset`.

## The 18 tools

| Tool | Credits | Leagues | Returns | Used by |
|------|---------|---------|---------|---------|
| `list_teams` | 1 | all | Team ids, abbreviations, conference | game-lookup, team-analysis |
| `search_players` | 1 | all | Player id from a name | player-scouting, player-form, prop-modeling |
| `list_games` | 2 | all | Games with scores, newest first | game-lookup, backtesting, feature-engineering |
| `get_schedule` | 2 | all | Next 1-30 days with the median line | game-preview, odds-explorer |
| `get_standings` | 2 | all | Standings computed from final games | team-analysis |
| `get_injuries` | 2 | nba, wnba | Status, injury type, expected return | game-preview, prop-modeling |
| `get_ratings` | 2 | all | DunkAPI Elo ratings, ranked | team-analysis, game-preview |
| `get_game` | 5 | all | Both box scores, every player line, each book's open and close, win probability range | game-lookup, game-preview |
| `get_player` | 5 | all | Profile, season averages and splits, last 10 games | player-scouting |
| `get_player_games` | 5 | all | A player's game log | player-form, prop-modeling |
| `get_leaders` | 5 | all | Season leaders by stat | player-scouting |
| `get_team_stats` | 5 | all | Pace, ratings, four factors, three-point rate | team-analysis, feature-engineering |
| `get_odds` | 5 per game, 10 per date | all | Every book's moneyline, spread, total, with results against the line | odds-explorer, odds-analysis, backtesting, edge-detection |
| `get_line_movement` | 10 | all | Snapshots of each book's line before tip-off | odds-explorer |
| `get_plays` | 10 | all | Play-by-play with shot x/y, zone, expected points, win probability | shot-zone-analysis |
| `get_shot_chart` | 10 | nba, wnba | Zone profile with expected points per shot | shot-zone-analysis |
| `get_player_props` | 10 (per game, see below) | nba, wnba, ncaam | Prop lines by book, opening or closing | prop-modeling |
| `get_prop_history` | 10 (up to 200 games) | nba, wnba, ncaam | Prop line vs actual, game by game, over rate | prop-modeling, edge-detection |

`get_player_props` costs 10 credits for a whole game, or 10 credits per game returned when you pass `player_id` with `from_date` (up to 100 games). Pass `estimate_only: true` first to see the price without being charged.

## Tool selection guide

| You need | Use | Not |
|----------|-----|-----|
| Last night's scores | `list_games` with `date` | `get_game` per game |
| Tonight's games and spread | `get_schedule` | `list_games` (past and scheduled mixed, no line) |
| One game's box score and every book's line | `get_game` | `get_odds` + `get_plays` |
| A day's lines for 3+ games | `get_odds` with `date` (10 flat) | `get_odds` per game (5 each) |
| Player id | `search_players` | guessing from a name |
| Last 10 games for a player | `get_player` (already included) | `get_player_games` (5 more credits) |
| Rolling form over a season | `get_player_games` | `get_plays` |
| Where a player shoots | `get_shot_chart` | `get_plays` and aggregating by hand |
| Individual shots with game context | `get_plays` with `shots_only` | `get_shot_chart` |
| Does a player beat his points line | `get_prop_history` | `get_player_props` per game |
| Today's prop prices across books | `get_player_props` with `game_id` | `get_prop_history` |

## Commands That Do NOT Exist

| Not available | Use instead |
|---------------|-------------|
| `get_box_score` | `get_game` |
| `get_player_stats` | `get_player` (profile, averages) or `get_player_games` (log) |
| `get_live_odds`, `get_live_scores` | None. Data is historical and next-day; `get_schedule` shows posted pre-game lines |
| `get_lineups`, `get_on_off` | None. Lineup and on/off data are not served |
| `get_player_tracking` | None. No speed, touches or defender-distance data |
| `get_advanced_stats` | `get_team_stats` for team ratings; compute player rates from `get_player_games` |
| `get_head_to_head` | `list_games` with `team`, filter the opponent yourself |

## Credit discipline

- Look up ids once (1 credit each) and reuse them.
- Prefer the date form of `get_odds` over per-game calls once you need 3 or more games.
- `get_plays` and `get_shot_chart` are 10 credits each. Ask for a zone, a period, `clutch` or `shots_only` instead of pulling everything.
- Never loop `get_line_movement` over a slate without telling the user the cost (10 per game).
- A backtest over a full season of lines is thousands of credits. Sample first, then scale.

## Error handling

- Required fields are `game_id` (`get_game`, `get_line_movement`), `player_id` (`get_player`, `get_player_games`, `get_prop_history`), `name` (`search_players`), `stat` (`get_leaders`) and `market` (`get_prop_history`). Fix a rejected call, do not retry it blindly.
- An empty list usually means the season, league or date has no data, not that the call failed. Check `season` (ends-in-year convention) and `league` first.
- In `get_odds`, `count` is the number of book rows returned, not the number of games. Count `len(data["games"])`.
- Opening and closing fields can be `null` for one book while others have values.

## Bring your own data

If the user supplies a CSV or JSON, skip the API and work with the file. State which columns you need (`date`, `home`, `away`, `home_score`, `away_score` at minimum for team work) and verify dates parse before any modeling.

## What to Do Next

| Situation | Skill |
|-----------|-------|
| Don't know which skill to load | `dispatch` |
| Want games or scores | `game-lookup` |
| Want team strength | `team-analysis` |
| Want lines and prices | `odds-explorer` |
