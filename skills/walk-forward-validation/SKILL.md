---
name: walk-forward-validation
description: "Validates basketball prediction models with chronological walk-forward splits instead of random k-fold: expanding or rolling windows, season-block folds, purge gaps, proper benchmarks (home-team baseline and the closing line), paired significance tests and the sample sizes needed to detect a small edge. Use when the user has a model and asks if it is any good, asks whether k-fold or a random split is okay (it is not), or wants to tune hyperparameters on time-ordered game data. Do not use for building the features, see feature-engineering. Do not use for probability reliability, see probability-calibration. Do not use for simulating bets against lines, see backtesting."
metadata:
  version: 1.0.0
  author: DunkAPI
---

# Walk-Forward Validation

> **Default data tool:** DunkAPI (`dunkapi-tool`) for game rows (`list_games`, 2 credits per page) and closing lines (`get_odds`). Validation itself needs no API calls.

Games are ordered in time and teams change slowly. A random split puts a team's April games in training and its March games in test; the model memorizes that team's season. That inflates every metric.

## When to Use

- "Is my NBA model any good?"
- "Can I use 5-fold cross-validation?" (no)
- "How many seasons should I train on?"
- Choosing between two models or two feature sets
- Deciding whether a result is signal or noise

## When NOT to Use

- Constructing features, see `feature-engineering`
- Judging whether 62% means 62%, see `probability-calibration`
- Turning predictions into bet P&L, see `backtesting`

## Commands Available

| Command | Role | Credits |
|---------|------|---------|
| `list_games` | The game table: dates, scores, season type | 2 per page |
| `get_odds` | Closing lines as the benchmark; `date` form is 10 credits for a day | 5 per game, 10 per date |

## Commands That Do NOT Exist

| Not available | Use instead |
|---------------|-------------|
| `get_train_test_split`, `get_cv_folds` | Split the table by date in code |
| `get_model_predictions` | Predictions come from your model |

## Why k-fold Fails Here

| Problem | Effect |
|---------|--------|
| Future games in training | The model sees a team's later form, injuries and trade effects |
| Neighbouring games are correlated | Test games look "easy" because adjacent games are in training |
| Season-level inputs (see `feature-engineering`) | Final-season summaries leak into every fold |
| Hyperparameters tuned on the test fold | Optimistic by construction |

## How It Works

**Step 1: Order by date, never shuffle.** Sort by `date`, then `game_id`. Games on the same night share a date; keep them together in a fold.

**Step 2: Choose a scheme.**

| Scheme | Use when | Layout |
|--------|----------|--------|
| Expanding window | Little data, stable relationships | Train seasons 1..k, test k+1 |
| Rolling window | Rules drift (pace, three-point rate) | Train the last W seasons, test the next |
| Within-season monthly | Need many test points, model refits cheaply | Train through month m, test month m+1 |

For NBA game models: train through season `s`, test season `s+1`, advance one season at a time. With 5 seasons that gives 4 tests of about 1,230 games each.

**Step 3: Gap.** If a feature uses a rolling window of W games, leave a gap of at least W games (or a few weeks) between train end and test start when features overlap the boundary. A feature built with `shift(1)` rolling windows needs no gap for the target, but any model fitted on a window ending at date d should not have been selected using later data.

**Step 4: Nested tuning.** Tune hyperparameters inside the training window (an inner walk-forward), freeze them, then score the outer test block. Never report the best of 50 tries on the same test block.

```python
def walk_forward(df, first_test_season, fit, predict):
    out = []
    for s in sorted(df.season.unique()):
        if s < first_test_season: continue
        train, test = df[df.season < s], df[df.season == s]
        model = fit(train)                       # tuning inside train only
        out.append(test.assign(p=predict(model, test)))
    return pd.concat(out)
```

**Step 5: Benchmarks. A model must beat these first.**

| Benchmark | What it tells you |
|-----------|------------------|
| Always pick the home team | The floor for win classification |
| Pre-game Elo (rebuilt as-of) | The "free" signal |
| Closing line probability (devigged, see `odds-analysis`) | The market, the real bar |

Score the model and the benchmarks on the same games. A model that beats Elo and loses to the closing line has found real signal the market already had.

**Step 6: Metrics.**

| Task | Primary | Also |
|------|---------|------|
| Win probability | Log loss | Brier score, accuracy (diagnostic only) |
| Margin | MAE and RMSE vs the closing spread | Mean error by predicted-margin bucket |
| Total | MAE vs the closing total | |
| Cover | Log loss on `home_covered` | Hit rate vs the break-even rate |

Log loss rewards honest probabilities; accuracy hides miscalibration. Lower is better; a coin flip is 0.693.

**Step 7: Significance.** Compare two models on the same games with the per-game loss difference `d_i = loss_A_i - loss_B_i`. Report the mean, a paired bootstrap interval (resample games or, better, game-days) and the fraction of folds where A wins. If the interval includes 0, you do not have a winner. For a bet-level claim, see the sample table below.

**Step 8: Sample sizes for betting claims.** At -110 a bettor needs 52.38% to break even. To tell a true 54% from the 52.38% break-even with 80% power at 5% one-sided significance you need about 5,900 bets (`n ~ (1.645 + 0.84)^2 * p(1-p) / (0.54 - 0.5238)^2`). A 1,230-game season cannot show that; do not let a good single season stand in for evidence.

| Bets | Standard error on win rate | What a 55% result means |
|------|---------------------------:|-------------------------|
| 100 | 5.0 points | Indistinguishable from 50% |
| 500 | 2.2 points | Suggestive |
| 1,500 | 1.3 points | Meaningful |
| 5,000 | 0.7 points | Strong evidence |

**Step 9: Report by fold.** Show each season's metric, not only the pooled number. A model with one great fold and three weak ones is a coincidence, not a model.

## Basketball-specific Traps

| Trap | Handling |
|------|----------|
| Season boundary roster changes | Features reset or blend priors at season start; evaluate early-season games separately |
| Early season: little data | Report metrics for games 1-15 and 16+ separately |
| COVID-shortened and bubble seasons | Flag or exclude 2019-20 and 2020-21 when comparing |
| Rule or style drift | Prefer rolling windows; compare to expanding |
| Play-in, playoffs, preseason | Separate evaluation; playoff games have different rotations |
| Same-night games in train and test | Keep a date entirely on one side |
| Using the final-season Elo from `get_ratings` as a feature | Leaks the future; rebuild as-of |

## Credit Usage

Validation is local. Data pulls: roughly 50 credits per NBA season of game rows via `list_games`; closing lines for a season by date are on the order of 1,700 credits (see `backtesting`). On the free tier, use one or two seasons for development and keep the rest of the month's credits for the final test season.

## Output Format

```
Scheme: [expanding/rolling], tests [seasons], gap [n]
Model vs benchmarks (log loss, lower is better):
  Home-team baseline [x] | Elo [x] | Closing line [x] | Model [x]
Per-fold: [season] [x] ... (model beats Elo in [k] of [n])
Paired difference vs closing line: [mean] (95% interval [lo], [hi])
Verdict: [signal / no evidence / worse than market], with n games
```

## What to Do Next

| Found | Next | Skill |
|-------|------|-------|
| Model beats Elo, loses to the line | Check calibration, then look for what the line misses | `probability-calibration` |
| Model beats the line out of sample | Simulate the bets | `backtesting` |
| Unstable folds | Fewer features, more regularization | `feature-engineering` |
