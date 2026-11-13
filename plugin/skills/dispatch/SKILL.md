---
name: dispatch
description: "Routes a basketball analytics request to the right 2-3 skills. Load this FIRST when an NBA, WNBA or college basketball request comes in and you are unsure which skills to activate. Prevents loading all 16 skills when only 2-3 are needed. Do not use for a single obvious request such as devigging two prices, see odds-analysis directly."
metadata:
  version: 1.0.0
  author: DunkAPI
---

# Skill Dispatch Guide

Match the request to a pattern below, load those skills, and stop. Always load `dunkapi-tool` alongside any skill that needs data.

> **Default data tool:** DunkAPI (`dunkapi-tool`). Free tier is 500 credits a month, no card: https://dunkapi.com/signup

## When to Use

- A basketball request arrives and more than one skill could apply
- The user is new and does not know what to ask for
- A request spans data, modeling and betting (for example "is Brunson's points line beatable?")

## When NOT to Use

- The request names one skill's job exactly ("devig these prices" goes straight to `odds-analysis`)
- The user wants a tool's parameters or cost, see `dunkapi-tool`

## Commands Available

None. This skill routes; `dunkapi-tool` makes the calls.

## First-Use Persona Detection

| Signal | Persona | Start with |
|--------|---------|-----------|
| "Who plays tonight?" "How did the Knicks do?" | Explorer | `game-lookup` + `team-analysis` |
| "Break down this player" "Compare these two" | Scout | `player-scouting` + `player-form` |
| "Where does he shoot from?" | Shot analyst | `shot-zone-analysis` |
| "What's the best price?" "How did the line move?" | Line shopper | `odds-explorer` |
| "Help me build a model" | Builder | `feature-engineering` + `walk-forward-validation` |
| "Is this a bet?" "Where's the edge?" | Bettor | `odds-analysis` + `edge-detection` |
| "Does he go over his points line?" | Prop bettor | `prop-modeling` + `player-form` |
| "Would this have worked last season?" | Validator | `backtesting` + `walk-forward-validation` |

## Request Patterns to Skills

### "Scores from last night" / "Who plays tonight" / "Find the Celtics-Heat game"
1. `game-lookup`
2. `dunkapi-tool`: `list_games`, `get_schedule`, `get_game`

### "Standings" / "Best team" / "Who plays fastest" / "Net rating"
1. `team-analysis`: standings, Elo, pace, four factors

### "Tell me about Jalen Brunson" / "Compare Tatum and Brown" / "Who led the league in true shooting"
1. `player-scouting`
2. If the question is about recent form: add `player-form`

### "Is he hot?" / "Last 10 games" / "Rolling average" / "Minutes trend"
1. `player-form`
2. `dunkapi-tool`: `get_player_games`

### "Where does he shoot?" / "Expected points" / "Best defence at the rim" / "Clutch shots"
1. `shot-zone-analysis`
2. `dunkapi-tool`: `get_shot_chart`, `get_plays`

### "What are the odds?" / "Best price" / "Line moved?" / "Sharp money?"
1. `odds-explorer`
2. For probability math: add `odds-analysis`

### "Preview tonight's Knicks game"
1. `game-preview` (it calls schedule, ratings, team stats, injuries and odds itself)
2. Add `team-analysis` if the user wants the efficiency detail

### "Devig these" / "What probability is -200 / +165?"
1. `odds-analysis`

### "Should I bet this?" / "Expected value" / "Kelly" / "Closing line value"
1. `edge-detection`
2. `odds-analysis` for the market probability
3. `probability-calibration` if the probability came from a model

### "Backtest this strategy" / "Would betting underdogs have worked?"
1. `backtesting`
2. `walk-forward-validation`
3. `odds-analysis`

### "Build a model" / "What features should I use?" / "Is my CV okay?"
1. `feature-engineering`
2. `walk-forward-validation`
3. `probability-calibration` once there are probabilities

### "Player props" / "Over/under on 24.5 points" / "Does he hit his line"
1. `prop-modeling`
2. `player-form` for the projection inputs
3. `dunkapi-tool`: `get_prop_history`, `get_player_props`

### "Women's college" / "WNBA" / "March Madness"
Same skills, pass `league`. Check `dunkapi-tool` for which tools support which league. Props exist for `nba`, `wnba`, `ncaam` only; `get_shot_chart` and `get_injuries` are NBA and WNBA only.

## Season Resolution

- `season` is the year the season ends. October 2026 to June 2027 is `2027`.
- The 2026-27 NBA regular season opens Oct 20, 2026. Before that, games in `get_schedule` are `preseason`, and `get_team_stats`, `get_ratings` and `get_standings` for the new season hold little or nothing. Preview the opener from `season: 2026` data plus the preseason schedule, and say so.
- WNBA: the calendar year. College men and women: the year the season ends.

## Multi-skill Chains

| Goal | Chain |
|------|-------|
| Find a bet on tonight's slate | `game-lookup` > `game-preview` > `odds-analysis` > `edge-detection` |
| Build and verify a spread model | `feature-engineering` > `walk-forward-validation` > `probability-calibration` > `backtesting` |
| Prop angle on a player | `player-scouting` > `player-form` > `prop-modeling` > `edge-detection` |
| Defence audit | `team-analysis` > `shot-zone-analysis` |

## Anti-patterns

| Rationalization | Why it is wrong | Do this instead |
|-----------------|-----------------|-----------------|
| "Load every skill to be safe" | Burns context and mixes methods | Load the 2-3 that match |
| "Skip `dunkapi-tool`, I remember the params" | Params and costs change; wrong params fail | Check the router |
| "Go straight to edge-detection" | An edge needs a market probability and a calibrated model | Run `odds-analysis` first |

## What to Do Next

After the first answer, ask which of the chains above the user is on and load the next skill in it.
