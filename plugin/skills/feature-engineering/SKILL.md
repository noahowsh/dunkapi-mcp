---
name: feature-engineering
description: "Builds leak-free features for basketball prediction models from DunkAPI data: rolling team margin and efficiency, Elo rebuilt game by game, rest days and back-to-backs, home court, opponent-adjusted form, market features and player minutes. Use when the user wants to build a model of game outcomes, margins, totals or player stats, or asks what features to use or whether a feature leaks. Do not use for choosing a validation scheme, see walk-forward-validation. Do not use for calibrating output probabilities, see probability-calibration. Do not use for descriptive team or player summaries, see team-analysis or player-form."
metadata:
  version: 1.0.0
  author: DunkAPI
---

# Feature Engineering

> **Default data tool:** DunkAPI (`dunkapi-tool`).
> Cheapest feature source: `list_games` (2 credits per page of up to 50 games). Box-score features need `get_game` (5 credits per game) or `get_player_games` (5 per player-season).

A basketball model fails in one of two ways: the features contain the future, or they contain nothing the market does not already know. This skill is about the first problem and honest about the second.

## When to Use

- "What features should I use to predict NBA margins?"
- "Build me rolling team ratings that don't leak"
- "Is using `get_team_stats` for a backtest okay?" (usually no, see below)
- Setting up a training table for game, total or player-stat models

## When NOT to Use

- Splitting data for validation, see `walk-forward-validation`
- Making probabilities trustworthy, see `probability-calibration`
- Describing a team or player without building a model, see `team-analysis`, `player-form`

## Commands Available

| Command | What it gives a feature table | Credits |
|---------|-------------------------------|---------|
| `list_games` | Date, teams, scores, overtime, season type, neutral site: enough for margin, rest, Elo | 2 per page |
| `get_game` | Team box scores (possessions, four factors) and each book's open and close | 5 per game |
| `get_player_games` | Player-level minutes and lines for availability and role features | 5 per player-season |
| `get_odds` | Opening and closing lines per book; `date` returns a whole day for 10 | 5 / 10 |
| `get_injuries` | Current availability only (not a historical archive by default) | 2 |
| `get_team_stats`, `get_ratings`, `get_standings` | Season-level summaries: do not use as pre-game features for past games | 5 / 2 / 2 |

## Commands That Do NOT Exist

| Not available | Use instead |
|---------------|-------------|
| `get_features`, `get_training_data` | Build from `list_games` and `get_game` |
| `get_historical_ratings` (as of a past date) | Rebuild Elo from `list_games` (below) |
| `get_historical_injuries` by game | `get_injuries` accepts a `date`, one report per call; archive it going forward |
| `get_lineups`, `get_tracking` | Not served |

## The Rule: As-Of Features Only

A feature for game N may use only information available before tip-off of game N.

| Source | Safe for past games? | Why |
|--------|---------------------|-----|
| `list_games` rolled with `shift(1)` | Yes | Built from earlier games only |
| `get_team_stats {"season": 2025}` for a 2024-25 game | No | Whole-season average includes the game and every game after it |
| `get_ratings` end-of-season Elo | No | Includes later games; also regresses at season boundaries |
| `get_standings` | No | Final standings |
| `get_player` season averages | No | Same as team stats |
| Closing line | At tip only | Use opening for earlier decisions |
| Opening line (`*_open`) | Yes if you act at open | Check `captured_at` |

If the model scores well with season-level inputs and badly with as-of ones, the first score was leakage.

## How It Works

**Step 1: Build the game table.** Page `list_games` for the seasons you want (oldest first after sorting). Keep `date`, home and away ids, scores, `overtime_periods`, `season_type`, `neutral_site`. Drop preseason; decide on play-in and postseason separately.

**Step 2: Target.** Pick one and keep it fixed:

| Target | Definition | Use |
|--------|-----------|-----|
| Margin | `home_score - away_score` | Spread model; regress, then convert to a cover probability |
| Home win | `margin > 0` | Moneyline model |
| Total | `home_score + away_score` | Totals model |
| Cover | `margin + home_spread_close > 0` against the median close (`home_covered` on `get_odds`) | Betting-specific |

**Step 3: Rest and schedule (cheap, strong).**

```python
g = g.sort_values("date")
for side in ("home", "away"):
    # long format: one row per team-game, then merge back
    ...
t["rest_days"] = t.groupby("team").date.diff().dt.days.clip(upper=7)   # NaN for first game
t["back_to_back"] = (t.rest_days == 1)
t["games_last_7"] = t.groupby("team").rolling("7D", on="date").date.count().values - 1
```

**Step 4: Rolling form with `shift(1)`.**

```python
t["margin"] = t.pts_for - t.pts_against
t["roll_margin_10"] = t.groupby("team").margin.transform(lambda s: s.shift(1).rolling(10, min_periods=5).mean())
t["roll_margin_30"] = t.groupby("team").margin.transform(lambda s: s.shift(1).rolling(30, min_periods=10).mean())
t["ewm_margin"]     = t.groupby("team").margin.transform(lambda s: s.shift(1).ewm(halflife=8).mean())
```

Windows: short for form, long for talent. Carry a season-boundary decision (reset, or blend toward the prior season).

**Step 5: Elo, rebuilt as-of.** The API publishes one Elo per team per date range; for a backtest, rebuild it game by game so each pre-game rating is clean:

```python
K, HFA = 20, 70                      # starting values, tune on a training window
def expected(rh, ra): return 1 / (1 + 10 ** (-(rh - ra + HFA) / 400))
def mov_mult(margin, dr): return ((abs(margin) + 3) ** 0.8) / (7.5 + 0.006 * dr)
ratings = defaultdict(lambda: 1500.0)
for g in games_sorted:
    pre_h, pre_a = ratings[g.home], ratings[g.away]
    g.pre_elo_diff = pre_h - pre_a                       # the feature
    e = expected(pre_h, pre_a); s = 1.0 if g.margin > 0 else 0.0
    winner_dr = (pre_h - pre_a) if g.margin > 0 else (pre_a - pre_h)   # winner's rating edge
    delta = K * mov_mult(g.margin, winner_dr) * (s - e)
    ratings[g.home] += delta; ratings[g.away] -= delta
# at each season start: ratings[t] = 1500 + 0.75 * (ratings[t] - 1500)
```

The API's note describes its Elo as including home advantage, a margin-of-victory multiplier and a quarter regression to the mean each season, so this mirrors it. Your constants will not match its exactly; compare your rebuilt end-of-season values with `get_ratings` for a sanity check (rank correlation, not equality).

**Step 6: Efficiency features.** If you can afford `get_game` per game (5 credits each, about 1,230 games per regular season), compute possessions `fga - oreb + tov + 0.44 * fta`, rolling offensive and defensive rating, `efg_pct`, and rebound and turnover rates with `shift(1)` rolling. A cheaper partial route is rolling points for and against from `list_games` alone.

**Step 7: Availability and role.** Roster certainty is the biggest missing signal. Historical injury state per game is not in a ready table; for a live model, archive `get_injuries` daily. For a past season, proxy availability by the share of a team's top-5-minute players who logged minutes in the game (needs `get_game`).

**Step 8: Market features.** Opening spread, total and moneyline probability are strong features and are only "free" if your model's job is not simply to rediscover them. Model the residual (`margin - (-closing_spread)`) to see whether anything beyond the market is left. If a model without market inputs cannot beat the market and one with them is just the market, the honest result is that you have no edge yet.

**Step 9: Player-level features** (props, see `prop-modeling`): rolling minutes, per-36 rates, usage proxy, opponent allowed rate, rest, home/road, all `shift(1)`.

## Leakage Checklist

1. Every rolling feature has `shift(1)` before `rolling`.
2. No season-level API summary for a game inside that season.
3. Train/validation split is chronological (see `walk-forward-validation`).
4. Opening lines only for decisions made before the close.
5. Standardization fitted on the training window only.
6. Opponent features are as-of too; a team's rolling defensive rating comes from the same shifted pipeline.
7. After feature building, correlate each feature with the target; a feature that is suspiciously strong (|r| near 0.5+ on margin from a single column) deserves a leak hunt.

## Sample Size

A regular season is about 1,230 NBA games; the WNBA and women's college have a few hundred to a few thousand games, men's Division I a few thousand. Over 60 features on one NBA season will overfit. Start with 5 to 10 (Elo difference, rest difference, back-to-back flags, rolling margin 10 and 30, home) and add only what improves out-of-sample log loss.

## Credit Usage

| Operation | Credits |
|-----------|---------|
| One NBA season of game rows (`list_games`, ~25 pages of 50) | ~50 |
| Box scores for every game in a season | ~6,150 |
| Opening and closing lines for a season by date | ~1,700 (about 165 game days at 10 credits) |
| A 500-credit free month | One season of game rows, then a sampled slice of box scores |

The date counts are estimates; count game days from your own `list_games` pull.

## What to Do Next

| Built | Next | Skill |
|-------|------|-------|
| Feature table | Validate chronologically | `walk-forward-validation` |
| Probabilities from the model | Check calibration | `probability-calibration` |
| A model vs the market | Replay the lines | `backtesting` |
