# DunkAPI examples

Runnable examples for the [DunkAPI](https://dunkapi.com). Python uses only the standard library (`urllib` and `json`). Node uses the built-in `fetch` (Node 18 or newer). No packages to install.

NBA, WNBA and college basketball data API. Every tool is a REST call: `POST https://mcp.dunkapi.com/v1/<tool_name>` with a JSON body and an `x-api-key` header. The same tools are available over MCP at `https://mcp.dunkapi.com/mcp`.

## Get a key

1. Sign up at https://dunkapi.com/signup. The free plan gives 500 credits every month, no card.
2. Copy a key from https://dunkapi.com/dashboard/keys.
3. Export it. The scripts read it from the environment and never print it.

```bash
export DUNKAPI_API_KEY=your_key
```

## What is here

| File | What it does | Tools | Credits |
| --- | --- | --- | --- |
| `python/quickstart.py` | Upcoming schedule plus one headline call, printed as small tables | `get_schedule`, `get_leaders` | about 7 |
| `python/nba_player_props.py` | Player prop lines against results. Looks up a player, then pulls each game's closing line (median across books), what he actually recorded, and the over rate. Defaults to Jayson Tatum points for the 2025-26 season. Works for any of the seven markets. | `search_players`, `get_prop_history` | about 11 |
| `node/quickstart.mjs` | Same as the Python quickstart, for Node | `get_schedule`, `get_leaders` | about 7 |

## Run

```bash
python3 python/quickstart.py
python3 python/nba_player_props.py
node node/quickstart.mjs
```

The use-case script takes optional arguments. For example:

```bash
python3 nba_player_props.py "Jalen Brunson" --market player_assists
```

Run any script with `--help` (Python) to see its options.

## Credits and errors

- Every call costs credits, priced per tool. The cost is shown next to each call in the script output, and the response header `X-Credits-Remaining` is printed at the end.
- To see what a call would cost without running it, send `"estimate_only": true` on the tools that accept it (see the tool schema).
- When you are out of credits the API returns HTTP 402 with `{"error": "insufficient_credits", "message": "...", "upgrade_url": "..."}`. The scripts print that message and the upgrade link.
- HTTP 401 means the key is missing or wrong. The scripts print a hint to check `DUNKAPI_API_KEY`.
- NBA is the default. Pass `"league": "wnba"`, `"ncaam"` or `"ncaaw"` in the request body to switch.
- The tool list with input schemas is public: `curl https://mcp.dunkapi.com/v1/tools`.

## More

- Docs and example responses for every tool: https://dunkapi.com/docs
- Full reference in one file: https://dunkapi.com/llms-full.txt
- Free key: https://dunkapi.com/signup
