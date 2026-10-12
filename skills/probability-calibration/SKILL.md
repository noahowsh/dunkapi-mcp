---
name: probability-calibration
description: "Checks and fixes whether basketball model probabilities mean what they say: reliability tables, Brier score and log loss, Platt scaling and isotonic regression fitted out of sample, converting predicted margins to win and cover probabilities, and shrinking toward the market. Use when a model outputs win, cover or over probabilities and the user wants to bet on them, asks if 65% really wins 65% of the time, or needs probabilities from a margin model. Do not use for building the model, see feature-engineering. Do not use for choosing splits, see walk-forward-validation. Do not use for turning a calibrated probability into a stake, see edge-detection."
metadata:
  version: 1.0.0
  author: DunkAPI
---

# Probability Calibration

> **Default data tool:** DunkAPI (`dunkapi-tool`) only for outcomes and the market benchmark: `list_games` (2 credits per page), `get_odds` (`result.home_covered`, `result.over`). Calibration itself is local.

A bet size is a function of a probability. An uncalibrated 70% that is really 60% turns a small edge into a negative one, and Kelly sizing amplifies the error.

## When to Use

- "My model says 68% for the Knicks. Can I trust that?"
- "Is Platt scaling or isotonic better here?"
- "How do I turn a predicted margin into a win probability?"
- Before any `edge-detection` run that uses model probabilities

## When NOT to Use

- Fitting the model itself, see `feature-engineering`
- Time-ordered evaluation design, see `walk-forward-validation`
- Stake sizing, see `edge-detection`

## Commands Available

| Command | Role | Credits |
|---------|------|---------|
| `list_games` | Final scores to label outcomes | 2 per page |
| `get_odds` | Market probability to benchmark (and `home_covered`, `over` to label cover and total outcomes) | 5 per game, 10 per date |

## Commands That Do NOT Exist

| Not available | Use instead |
|---------------|-------------|
| `get_calibration`, `get_model_probabilities` | Compute locally from your own predictions |
| `get_historical_predictions` | The API does not serve picks; log your own (see `edge-detection`) |

## What Calibrated Means

Among all games where the model said about 70%, the home side should win about 70% of them. Two separate qualities:

- **Calibration:** do stated probabilities match frequencies?
- **Discrimination (sharpness):** does the model separate likely from unlikely outcomes?

A model that always says 58% for the home team in a league where home teams win 58% is calibrated and useless. You need both.

## How It Works

**Step 1: Use out-of-sample predictions only.** Generate predictions with `walk-forward-validation`. Calibrating on training predictions measures overfit, not reliability.

**Step 2: Reliability table.** Bin predictions (deciles, or equal-count bins), and compare the mean prediction to the observed rate.

```python
import numpy as np, pandas as pd
df["bin"] = pd.qcut(df.p, 10, duplicates="drop")
rel = df.groupby("bin").agg(pred=("p","mean"), obs=("y","mean"), n=("y","size"))
rel["se"] = np.sqrt(rel.obs * (1 - rel.obs) / rel.n)
```

Read it with the standard error: a bin of 120 games has a standard error near 4.5 points, so a 3-point miss is noise. Plot `obs` against `pred` with error bars; the diagonal is perfect.

**Step 3: Scores.**

| Metric | Formula | Notes |
|--------|---------|-------|
| Log loss | `-mean(y*log(p) + (1-y)*log(1-p))` | Coin flip 0.693; punishes overconfidence |
| Brier | `mean((p - y)^2)` | Coin flip 0.25 |
| Calibration slope | Logistic regression of `y` on `logit(p)` | 1.0 ideal; below 1 means overconfident |
| Calibration intercept | Same regression | 0 ideal |

Brier decomposes into reliability (bad) minus resolution (good) plus uncertainty (fixed). Improve reliability by calibrating; improve resolution only with better features.

**Step 4: Choose a correction.**

| Method | Use when | Risk |
|--------|----------|------|
| Platt (logistic on the score) | Under about 3,000 calibration games | Assumes a sigmoid shape |
| Isotonic regression | 3,000+ calibration games | Steps; overfits small samples |
| Shrink toward the market: `p' = w*p_model + (1-w)*p_market` | Model has some edge but is overconfident | Needs a devigged market probability (see `odds-analysis`) |

NBA seasons are small. One season is about 1,230 games, so Platt or shrinkage is usually right; isotonic needs several seasons pooled.

```python
from sklearn.linear_model import LogisticRegression
platt = LogisticRegression(C=1e6).fit(logit(p_cal).reshape(-1, 1), y_cal)   # fit on a calibration block
p_adj = platt.predict_proba(logit(p_test).reshape(-1, 1))[:, 1]
```

Calibration data must be earlier than the data it is applied to. Fit on seasons `s-2..s-1`, apply to `s`.

**Step 5: Margin models to probabilities.** If the model predicts a home margin `m`, the win probability is `Phi(m / sigma)`, where `sigma` is the residual standard deviation of margin around the prediction (about 12 points for NBA games; estimate it from your own out-of-sample residuals, because it changes with the era and the model). For covers against a spread `s` (home spread, negative when the home team is favoured): `P(cover) = Phi((m + s) / sigma)`. For totals use the same with the total prediction and its own sigma. Then calibrate those probabilities like any others.

**Step 6: Re-check after correction.** Rebuild the reliability table on a later block. If the slope moved toward 1 and log loss dropped, keep it.

### Worked Example (market benchmark)

The closing moneylines for game 401859967 from `get_odds` (SA home, NY away) devig to a home probability between 0.631 (DraftKings) and 0.651 (Bovada); Pinnacle's devigged value is 0.643. SA lost. One result says nothing about calibration: even a perfectly calibrated 64% favourite loses 36% of the time. That is why calibration is judged over hundreds of games, with bin standard errors, never from a single outcome.

## Common Failures

| Symptom | Cause | Fix |
|---------|-------|-----|
| Slope well below 1 | Overfit model; extreme probabilities | Shrink toward the market or a prior |
| Over-prediction of home wins | Home advantage double counted | Check intercept; refit |
| Good overall, bad on underdogs | Regression to the mean in tails | Calibrate by bin; isotonic with enough data |
| Calibrated in-sample only | Calibration fitted on training predictions | Refit on held-out data |
| Probabilities above 0.9 for NBA games | Model too sure | Cap; NBA favourites rarely exceed 90% |
| Different periods calibrate differently | Drift | Calibrate on a rolling recent window |

## Sample Size Warning

Reliability needs data. With 1,000 games in 10 bins, each bin has 100 games and a standard error near 5 points. Do not slice by team, month and conference at once; every slice you add multiplies the false alarms.

## Credit Usage

No calibration calls. Outcome labels come free from the `list_games` scores you already pulled. If you want cover and over labels, use `get_odds` by date (10 credits per day of games) and read `result.home_covered` and `result.over`.

## Output Format

```
Out-of-sample games: [n], seasons [..]
Log loss [x] (market [x]) | Brier [x] | slope [x], intercept [x]
Reliability (deciles): [pred -> obs +/- se] ...
Correction: [Platt/isotonic/shrink w=..], fitted on [window]
After: log loss [x], slope [x]
Usable range: [pred interval where bins are within 1.5 se]
```

## What to Do Next

| Found | Next | Skill |
|-------|------|-------|
| Calibrated, still behind the market | Look for better features | `feature-engineering` |
| Calibrated and competitive | Compute edges | `edge-detection` |
| Need a market probability | Remove the vig | `odds-analysis` |
