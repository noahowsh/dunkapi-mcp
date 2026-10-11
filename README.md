# DunkAPI MCP server

[![Smithery](https://img.shields.io/badge/Smithery-listed-ff5601?style=flat-square)](https://smithery.ai/servers/noahowsh/DunkAPI) [![MCP Registry](https://img.shields.io/badge/MCP%20Registry-io.github.noahowsh%2Fdunkapi-0b7285?style=flat-square)](https://registry.modelcontextprotocol.io/v0/servers?search=io.github.noahowsh/dunkapi)

**The basketball data API.** NBA play-by-play with the location of every shot, box scores, win probability, standings, injuries, our own team Elo ratings, sportsbook lines and player prop lines, plus the WNBA and men's and women's Division I college basketball. REST API and MCP server. 500 free credits, no card.

Website: https://dunkapi.com · Docs: https://dunkapi.com/docs · Get a key: https://dunkapi.com/signup

```
You:    "What was each sportsbook's closing spread for every Celtics home game in 2023-24?"
Claude: [calls get_odds]

You:    "Which players took the most shots at the rim in the 2025 playoffs?"
Claude: [calls get_shot_chart]

You:    "How often has Jalen Brunson gone over his points line this season?"
Claude: [calls get_prop_history]
```

## Quick start

This is a hosted (remote) MCP server over Streamable HTTP. There is nothing to install.

**Claude Code**

```bash
claude mcp add --transport http dunkapi "https://mcp.dunkapi.com/mcp?key=YOUR_API_KEY"
```

**Claude Desktop, Cursor and other clients**

```json
{
  "mcpServers": {
    "dunkapi": {
      "url": "https://mcp.dunkapi.com/mcp?key=YOUR_API_KEY"
    }
  }
}
```

The key can also be sent as an `x-api-key` header or `Authorization: Bearer`. Connecting and listing tools works without a key; calling a tool needs one.

**REST**

```bash
curl -X POST https://mcp.dunkapi.com/v1/list_teams -H "x-api-key: YOUR_API_KEY"
```

Every tool is `POST /v1/{tool}` with a JSON body.

## Tools (18)

| Tool | What it returns |
|------|-----------------|
| `list_teams` | Team ids, abbreviations and colours for a season |
| `search_players` | Find players by name |
| `list_games` | Games with scores by season, date, range or team |
| `get_schedule` | Upcoming games with the median line across sportsbooks |
| `get_standings` | Standings from every final game: overall, conference, home, away, last 10 |
| `get_injuries` | The latest injury report: status, injury and expected return (NBA, WNBA) |
| `get_ratings` | Our team Elo ratings, ranked |
| `get_game` | One game: both box scores, every player's line, each book's line, win probability |
| `get_player` | Profile, per-season averages and shooting splits, last 10 games |
| `get_player_games` | A player's full game log |
| `get_leaders` | Season leaders per game, by percentage or in total |
| `get_team_stats` | Pace, offensive, defensive and net rating, and the four factors |
| `get_odds` | Every sportsbook's moneyline, spread and total for a game (5) or a day (10), with results against the line |
| `get_plays` | Play-by-play with shot locations, zones, expected points and win probability |
| `get_shot_chart` | Shot profile by zone for a player, team or defence, with every shot's x/y |
| `get_line_movement` | Snapshots of each sportsbook's line before tip-off |
| `get_player_props` | Player prop lines by sportsbook, opening and closing |
| `get_prop_history` | A player's prop lines against the result, game by game |

Leagues: nba (default), wnba, ncaam, ncaaw (pass `league` to any tool).

## Data

- NBA games since 2003-04 with play-by-play and shot locations (x/y, zone, expected points, win probability)
- The WNBA and men's and women's Division I college basketball through the same tools
- Team Elo ratings, standings from every final game, injury report (NBA, WNBA)
- Per-sportsbook moneylines, spreads and totals: 4 to 12 books per regular-season NBA game from 2013-14 to 2023-24 (10 to 12 from 2020-21), plus opening and closing lines from The Odds API since July 2020 (a median of 7 books per NBA game in 2020-21 to 2022-23, 8 since); pre-game line snapshots from launch: ESPN's once a day, The Odds API's every hour for games in the next two days
- Player prop lines by sportsbook (points, rebounds, assists, threes, points + rebounds + assists, blocks, steals) from May 2023 for the NBA and WNBA and from the 2023-24 season for men's college basketball, with the result against each line (`get_player_props`, `get_prop_history`)
- Women's college basketball: opening and closing lines from November 2024 (a median of 4 books); no player props

Coverage by season, read live from the database: https://dunkapi.com/docs

## Pricing

500 free credits on signup, no card. Plans: Starter $19/mo (10,000 credits), Pro $49/mo (30,000), Scale $149/mo (125,000). Wallet top-ups from $5, never expire. https://dunkapi.com/pricing

## Attribution

Basketball data from public ESPN data; sportsbook lines and player props from ESPN and The Odds API. Ratings are ours. Not affiliated with the NBA, WNBA, NCAA or any team.

## License

MIT for the contents of this repository. Data terms as above.
