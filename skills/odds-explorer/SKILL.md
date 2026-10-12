---
name: odds-explorer
description: "Multi-book basketball odds comparison: best moneyline, spread and total across sportsbooks, vig per book, opening versus closing lines, and pre-tip line movement. Use when the user asks for current or historical odds, the best price, which book is off the market, how a line moved, or whether the home side covered. Covers NBA, WNBA, men's and women's college. Do not use for devigging or probability math, see odds-analysis. Do not use for model-versus-market edge, see edge-detection. Do not use for player props, see prop-modeling."
metadata:
  version: 1.0.0
  author: DunkAPI
---

# Odds Explorer

> **Default data tool:** DunkAPI (`dunkapi-tool`).
> `get_schedule` (2 credits) for the median line on upcoming games, `get_odds` (5 per game, 10 per date) for every book, `get_line_movement` (10 per game) for snapshots before tip-off.

You find the best available price, show what each book charges, and read line movement without overstating what snapshots can prove.

## When to Use

- "Best spread on Knicks-Spurs?" / "Which book has the highest total?"
- "What were the closing lines for last night's slate?"
- "Did the home team cover?" / "Did it go over?"
- "How did the line move before tip?"
- Reading the market before a game preview or a bet

## When NOT to Use

- Converting prices to true probabilities, see `odds-analysis`
- Comparing a model's number to the market, see `edge-detection`
- Backtesting a strategy over many games, see `backtesting`
- Player prop lines, see `prop-modeling`

## Commands Available

| Command | What it does | Credits |
|---------|-------------|---------|
| `get_schedule` | Upcoming games with the median spread, total and moneylines across posted books | 2 |
| `get_odds` | Every book's moneyline, spread and total, opening and closing, with results against the median close. `game_id` for one game, `date` for a day | 5 per game, 10 per date |
| `get_line_movement` | Snapshots of each book's moneyline, spread and total before tip-off. Optional `provider` | 10 |
| `get_game` | Box score plus each book's open and close (use when you want both) | 5 |

## Commands That Do NOT Exist

| Not available | Use instead |
|---------------|-------------|
| `get_live_odds` | None. Lines are pre-game; `get_schedule` shows what is posted |
| `get_best_book` | Compute from `get_odds` rows |
| `get_public_betting` | Not served. Do not infer public percentages |
| `get_closing_line` | Closing fields (`*_close`) on `get_odds` rows |
| `get_alt_lines` | Not served; one spread and one total per book |

## Coverage and What a Line Is

- Per-book moneyline, spread and total with opening and closing values. Opening and closing per book come from The Odds API from July 2020 and from ESPN from 2023-24; before that, only ESPN's final line. Check https://dunkapi.com/docs/atlas for coverage by season and league before promising history.
- Women's college lines start November 2024, with fewer books.
- Pre-game snapshots: ESPN's once a day, The Odds API's every hour for games in the next two days. That sets the resolution of `get_line_movement`: you can see a half-point move across hours or days, not a 90-second steam move.
- Books appear under their display names in `get_odds` and `get_line_movement` (`DraftKings`, `FanDuel`, `ESPN BET`, `Pinnacle`, `BetMGM`, `Bovada`, `BetOnline`, `MyBookie` in the live call below). Prop calls use lowercase keys (`draftkings`); do not mix them.
- Preseason games can have one book and no moneyline. Say so; one book is not a market.

## Season Resolution

For games before the Oct 20, 2026 opener, `get_schedule` returns preseason games with `season: 2027`. Use `get_schedule` for lines on future games and `get_odds` for lines on games already played or about to be.

## How It Works

**Step 1: Identify the game.** Use `get_schedule {"days": 3, "team": "NY"}` or `list_games` (see `game-lookup`). Do not pull odds for a guessed id.

**Step 2: Pull every book.** One game: `get_odds {"game_id": "401859967"}`. A whole day, 10 flat: `get_odds {"date": "2026-06-13"}`. For three or more games the date form is cheaper.

**Step 3: Read the columns.** Each `books` row has `provider`, `home_ml_open`, `home_ml_close`, `away_ml_open`, `away_ml_close`, `home_close_prob`, `away_close_prob`, `home_spread_open`, `home_spread_close`, `spread_home_odds`, `spread_away_odds`, `total_open`, `total_close`, `over_odds`, `under_odds`, `captured_at`. The `result` object holds `median_home_spread`, `median_total`, `home_covered` and `over` for finished games.

Note: `home_close_prob` and `away_close_prob` are raw implied probabilities from the closing moneyline, not devigged. They add to more than 1; the excess is the vig.

**Step 4: Best price.** For each side independently, the best price is the highest number (+175 beats +160; -185 beats -210). The best home price and best away price usually sit at different books.

**Step 5: Vig.** For a two-way market with decimal implied probabilities `pH` and `pA`: `vig = pH + pA - 1`. For American odds: `p = 100/(odds+100)` if odds are positive, `p = -odds/(-odds+100)` if negative. Spread and total prices of -110/-110 carry a vig of 4.76% (2 * 0.5238 - 1).

**Step 6: Movement, if asked.** `get_line_movement {"game_id": "401585601", "provider": "DraftKings"}` returns `movement[book]` as a list of `{captured_at, home_ml, away_ml, home_spread, total}`. Compare the first and last snapshot.

### Live example

`get_odds {"game_id": "401859967"}` (NY at SA, 2026-06-13). Closing values, trimmed to the columns that matter:

| Book | Home ML | Away ML | Raw sum | Spread | Total |
|------|--------:|--------:|--------:|-------:|------:|
| BetMGM | -200 | +165 | 1.044 | SA -5.5 | 215.5 |
| BetOnline | -187 | +163 | 1.032 | SA -5.5 | 215.5 |
| Bovada | -210 | +175 | 1.041 | SA -5.5 | 215 |
| DraftKings | -192 | +160 | 1.043 | SA -5.5 | 216.5 |
| ESPN BET | -185 | +170 | 1.019 | SA -5.5 | 216.5 |
| FanDuel | -198 | +166 | 1.040 | SA -5.5 | 215.5 |
| MyBookie | -204 | +171 | 1.040 | SA -5.5 | 215.5 |
| Pinnacle | -195 | +173 | 1.027 | SA -5.5 | 215 |

Best home price -185 (ESPN BET), best away price +175 (Bovada). Eight books agreed on the spread and spread within 1.5 points on the total. `result` came back `home_covered: false, over: false` (NY won 94-90 as a 5.5-point underdog; 184 combined points against a 215.5 total). The lowest raw sum, ESPN BET at 1.019, is the cheapest to bet; the highest, BetMGM at 1.044, the most expensive.

## Reading Movement

| Observation | Cautious read |
|-------------|---------------|
| Spread moves 1 point or more across all books | Real information or a large position taken; look for an injury in `get_injuries` |
| One book out of line, rest agree | Stale line or a book managing its own exposure; the others are the market |
| Moneyline moves, spread unchanged | Price adjustment around a key number |
| Total drops 2+ points | Pace or availability news; check injuries and rest |
| Line returns to open | Noise; no signal |

Without bet-count or handle data, "sharp money" and "reverse line movement" cannot be proven from lines alone. Label them hypotheses.

## Anti-patterns

| Rationalization | Why it is wrong | Do this instead |
|-----------------|-----------------|-----------------|
| "Line moved toward the favorite, so favorites are right" | Direction alone says nothing about who is correct | Report size, timing and what else changed |
| "Use the first book that answers" | Differences of 5-10 cents add up over a season | Show the range across books |
| "Pinnacle is always right" | A reference, not an oracle; check availability and limits | Use it as a benchmark line |
| "Open to close tells the whole story" | Snapshots miss intra-day swings | State the snapshot frequency |

## Credit Usage

| Operation | Credits |
|-----------|---------|
| Tonight's median lines | 2 |
| One game, every book | 5 |
| A whole day of lines | 10 |
| One game's movement | 10 |
| Movement for a 10-game slate | 100; warn the user first |

## Output Format

```
[Away] @ [Home], [date] (n books)
Moneyline: [Away] [best] @ [book] | [Home] [best] @ [book]
Spread: [Home] [x] (range [lo] to [hi]) | Total [x] (range [lo] to [hi])
Cheapest to bet: [book] ([vig]%) | Most expensive: [book] ([vig]%)
Result (if final): home covered [yes/no], over [yes/no]
```

## What to Do Next

| Found | Next | Skill |
|-------|------|-------|
| Best prices identified | Remove vig to get true probability | `odds-analysis` |
| Have a model number | Compare model to market | `edge-detection` |
| Large move on one game | Check availability and form | `game-preview` |
| Want history for a strategy | Replay closing lines | `backtesting` |
