# DunkAPI MCP server

[![Smithery](https://img.shields.io/badge/Smithery-listed-ff5601?style=flat-square)](https://smithery.ai/servers/noahowsh/DunkAPI) [![MCP Registry](https://img.shields.io/badge/MCP%20Registry-io.github.noahowsh%2Fdunkapi-0b7285?style=flat-square)](https://registry.modelcontextprotocol.io/v0/servers?search=io.github.noahowsh/dunkapi)

**The basketball data API.** NBA play-by-play with the location of every shot, box scores, win probability, standings, injuries, our own team Elo ratings, sportsbook lines and player prop lines, plus the WNBA and men's and women's Division I college basketball. REST API and MCP server. 500 free credits every month, no card.

Website: https://dunkapi.com · Docs: https://dunkapi.com/docs · Get a key: https://dunkapi.com/signup

```
You:    "What was each sportsbook's closing spread for every Celtics home game in 2023-24?"
Claude: [calls get_odds]

You:    "Which players took the most shots at the rim in the 2025 playoffs?"
Claude: [calls get_shot_chart]

You:    "How often has Jalen Brunson gone over his points line this season?"
Claude: [calls get_prop_history]
```


## Run it locally (stdio)

Most clients connect to `https://mcp.dunkapi.com/mcp` directly. For a client that launches a local process instead:

```bash
git clone https://github.com/noahowsh/dunkapi-mcp.git && cd dunkapi-mcp && npm install
DUNKAPI_API_KEY=your_key node index.js
```

```json
{ "mcpServers": { "dunkapi": { "command": "node", "args": ["/path/to/dunkapi-mcp/index.js"], "env": { "DUNKAPI_API_KEY": "your_key" } } } }
```

It forwards to the hosted server with your key, so every tool and credit cost is the same.

## Skills

[`skills/`](skills/) holds 16 free Claude skills that turn Claude into a basketball analyst for the NBA, WNBA and men's and women's college basketball. A skill is a markdown file: when to use it, which DunkAPI tools it calls and what they cost, the method (shot zones and expected points, pace and efficiency, rolling game logs, prop modeling, devigging, backtesting), and examples taken from real API responses.

```bash
git clone https://github.com/noahowsh/dunkapi-mcp.git
```

Or install them as a Claude Code plugin:

```
/plugin marketplace add noahowsh/dunkapi-mcp
/plugin install dunkapi-skills@dunkapi
```

Or with the skills CLI: `npx skills add noahowsh/dunkapi-mcp`.

Point Claude at the `skills/` folder, connect the MCP server below, and ask a question. Start with the `dispatch` skill if you are not sure which one applies. Skills also work on your own CSV or JSON files, with no key. Full list: [`skills/README.md`](skills/README.md).

## Python

The official Python client is on PyPI: [dunkapi](https://pypi.org/project/dunkapi/).

```bash
pip install dunkapi
export DUNKAPI_API_KEY=sk_live_...
```

```python
from dunkapi import Client, to_dataframe

client = Client()

props = client.get_player_props(
    game_id="401810726",
    market="player_points",
    bookmaker="draftkings",
)
df = to_dataframe(props, key="props")
print(df[["player_name", "line", "over_odds", "under_odds"]].head(10))
```

Typed errors for a bad key, no credits left, not found and rate limits, automatic retries, and `to_dataframe` for pandas.

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

## Examples

Runnable Python (standard library only) and Node 18+ (no dependencies) examples live in [`examples/`](examples/):

- [`examples/python/quickstart.py`](examples/python/quickstart.py) and [`examples/node/quickstart.mjs`](examples/node/quickstart.mjs): schedule plus a headline call.
- [`examples/python/nba_player_props.py`](examples/python/nba_player_props.py): Player prop lines against results.

```bash
export DUNKAPI_API_KEY=your_key
python3 examples/python/quickstart.py
node examples/node/quickstart.mjs
```

See [`examples/README.md`](examples/README.md) for details. Get a free key (500 credits a month, no card) at https://dunkapi.com/signup.

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

## Useful pages

- Live odds and lines: https://dunkapi.com/odds
- Player props today (best price per player across books, live from the 2026-27 opener): https://dunkapi.com/props
- College basketball player props today (live from the 2026-27 season): https://dunkapi.com/props/college-basketball
- College props history guides: [points](https://dunkapi.com/guides/college-basketball-points-prop-history-python), [rebounds](https://dunkapi.com/guides/college-basketball-rebounds-prop-history-python)
- Props guides: [points prop history](https://dunkapi.com/guides/nba-points-prop-history-python), [threes prop history](https://dunkapi.com/guides/nba-threes-prop-history-python)
- Guides (Python, run against the live API): https://dunkapi.com/guides
  - [NBA play-by-play](https://dunkapi.com/guides/nba-play-by-play-python), [shot chart by zone](https://dunkapi.com/guides/nba-shot-chart-by-zone-python), [backtest closing lines](https://dunkapi.com/guides/backtest-nba-closing-lines-python), [team pace and efficiency](https://dunkapi.com/guides/nba-pace-and-efficiency-by-team-pandas), [player game log and rolling average](https://dunkapi.com/guides/nba-player-game-log-rolling-average)
- Docs and endpoint reference: https://dunkapi.com/docs
- Coverage by season: https://dunkapi.com/docs/atlas
- Datasets: https://dunkapi.com/data ([play-by-play](https://dunkapi.com/data/nba-play-by-play), [shot charts](https://dunkapi.com/data/nba-shot-chart-data), [odds history](https://dunkapi.com/data/nba-odds-history), [player props](https://dunkapi.com/data/player-props))
- Pricing: https://dunkapi.com/pricing
- Comparisons: [BallDontLie](https://dunkapi.com/compare/balldontlie), [nba_api and stats.nba.com](https://dunkapi.com/compare/nba-api-stats-nba), [Basketball Reference](https://dunkapi.com/compare/basketball-reference), [Sportradar](https://dunkapi.com/compare/sportradar), [SportsDataIO](https://dunkapi.com/compare/sportsdataio-nba)
- Leagues: [WNBA](https://dunkapi.com/wnba), [men's college](https://dunkapi.com/college-basketball), [women's college](https://dunkapi.com/womens-college-basketball)

## Pricing

500 free credits every month, no card. Plans: Starter $19/mo (10,000 credits), Pro $49/mo (30,000), Scale $149/mo (125,000). Wallet top-ups from $5, never expire. https://dunkapi.com/pricing

## Attribution

Basketball data from public ESPN data; sportsbook lines and player props from ESPN and The Odds API. Ratings are ours. Not affiliated with the NBA, WNBA, NCAA or any team.

## License

MIT for the contents of this repository. Data terms as above.

## Use with Codex

Add this repo as a Codex plugin marketplace, then install the plugin:

```bash
codex plugin marketplace add noahowsh/dunkapi-mcp
```

Then open the plugin directory in Codex and install `dunkapi-skills` from the `dunkapi` marketplace. The plugin bundles the skills in `skills/` and the DunkAPI MCP server (https://mcp.dunkapi.com/mcp). Set your key first (free at https://dunkapi.com/signup):

```bash
export DUNKAPI_API_KEY=your_key
```

Codex sends it as a bearer token.

## Use with Gemini CLI

```bash
export DUNKAPI_API_KEY=your_key
gemini extensions install https://github.com/noahowsh/dunkapi-mcp
```

The extension adds the DunkAPI MCP server (https://mcp.dunkapi.com/mcp) and sends the key in the `x-api-key` header. Get a free key (500 credits a month) at https://dunkapi.com/signup.
