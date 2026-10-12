---
name: edge-detection
description: "Compares a calibrated basketball model probability with the market to estimate expected value, applies a minimum-edge threshold, sizes stakes with fractional Kelly, and tracks closing line value as the early test of whether an edge is real. Use when the user asks whether a bet has value, where their model disagrees with the market, how much to stake, or whether they beat the closing line. Frames every edge as an estimate with variance. Do not use for finding prices, see odds-explorer. Do not use for converting prices to probabilities, see odds-analysis. Do not use for testing a rule on history, see backtesting."
metadata:
  version: 1.0.0
  author: DunkAPI
---

# Edge Detection

> **Default data tool:** DunkAPI (`dunkapi-tool`).
> `get_odds` (5 credits per game, 10 per date) for the price and closing line, `get_schedule` (2) for posted lines before tip, `get_player_props` (10) and `get_prop_history` (10) for props.

An edge is an estimate of how far your probability sits from a price, not a promise. Most apparent edges are model error. This skill makes the estimate explicit and keeps the sizing small enough to survive being wrong.

## When to Use

- "My model has the Knicks at 67%. Is -185 worth it?"
- "How much should I stake?"
- "Did I beat the closing line on last week's bets?"
- Screening a slate of model numbers against the market

## When NOT to Use

- Finding the best number across books, see `odds-explorer`
- Devigging to get the market's probability, see `odds-analysis`
- Making the model's probabilities honest, see `probability-calibration`
- Replaying a rule over seasons, see `backtesting`

## Commands Available

| Command | Role | Credits |
|---------|------|---------|
| `get_schedule` | Upcoming median line | 2 |
| `get_odds` | Per-book price now; closing price after the game | 5 / 10 |
| `get_line_movement` | Pre-tip snapshots to check price drift | 10 |
| `get_player_props` | Prop prices | 10 |
| `get_prop_history` | A prop's history against the result | 10 |

## Commands That Do NOT Exist

| Not available | Use instead |
|---------------|-------------|
| `get_edges`, `get_value_bets`, `get_picks` | Compute locally |
| `get_closing_line` | `*_close` fields on `get_odds` rows |
| `get_bet_history` | The API does not store your bets; keep your own log |

## Required Inputs

1. **A calibrated model probability.** If it has not been checked out of sample, stop and use `probability-calibration`.
2. **A market probability** from `odds-analysis` (devigged, median across books).
3. **A price you can actually get** (the best across books, with the line it applies to).

Without all three, the output is a guess.

## How It Works

**Step 1: Expected value of a bet.** With model probability `p` and payout `b` per unit staked (`b = o/100` for positive American odds `o`, `100/-o` for negative):

```
EV per unit = p * b - (1 - p)
ROI-equivalent edge = p - break_even,   break_even = 1 / (1 + b)
```

**Step 2: Screen.** Compare `p` with the market's fair probability `m`. Require a gap large enough to survive model error:

| Gap `p - m` | Treatment |
|-------------|-----------|
| Under 2 points | Noise. No bet |
| 2 to 4 points | Possible; only if the model has a verified out-of-sample record |
| Over 6 points | Suspicious: first check injuries, lineup news, a stale line and a bug |

Basketball markets are efficient on sides and totals; a large gap is more often your error than theirs. Open and look at `get_injuries` and the line movement before believing it.

**Step 3: Shrink.** The honest probability is between yours and the market's. A starting value is `p* = 0.5 * p + 0.5 * m`; fit the weight on walk-forward data. Recompute EV with `p*`. If the edge disappears, there was none.

**Step 4: Size with fractional Kelly.**

```
full Kelly fraction f = (b*p - (1 - p)) / b
stake = bankroll * k * f,    k = 0.25 typical, 0.5 at most
cap each bet at 1% to 2% of bankroll
```

Full Kelly assumes your `p` is exactly right and produces large drawdowns when it is not. Use a quarter or less. Do not stake correlated bets independently (a side and the same game's total, or three props from one game).

**Step 5: Variance reality.** Per-bet standard deviation near 1 unit at roughly even odds. Over 500 bets at -110, one standard deviation of total result is about 21 units, which is a 4.2% swing in ROI. A true 2% edge produces a losing 500-bet stretch roughly a third of the time. Judge a strategy over thousands of bets.

**Step 6: Closing line value (CLV).** CLV compares the price you took with the fair closing probability:

```
CLV (points) = fair_close_prob(your side) - implied_prob_at_your_price
```

Positive means you got a better price than the market settled on. Over many bets, positive CLV is the fastest evidence of a real edge, because it needs hundreds of bets, not thousands of results. Pull the close from `get_odds` (the `*_close` fields), devig it with `odds-analysis`, and compute it per bet. Keep the book consistent: compare to the same book's close or to a sharp reference.

### Worked Example (market real, model hypothetical)

The market: in `get_odds {"game_id": "401859967"}`, ESPN BET's best home moneyline was -185 and Pinnacle's devigged home probability (multiplicative) was 0.643. Suppose a calibrated model said 0.67 for the home side (an assumed number for illustration).

- Price -185: `b = 100/185 = 0.5405`, break-even `1/(1+b) = 0.649`.
- EV per unit with `p = 0.67`: `0.67 * 0.5405 - 0.33 = +0.0321` (3.2%).
- Shrunk `p* = 0.5 * 0.67 + 0.5 * 0.643 = 0.6565`: EV `= 0.6565 * 0.5405 - 0.3435 = +0.0114` (1.1%).
- Full Kelly with `p*`: `(0.5405 * 0.6565 - 0.3435) / 0.5405 = 0.0210`. Quarter Kelly is 0.5% of bankroll.
- CLV if you had taken -185 and the fair close was 0.643: `0.643 - 0.649 = -0.6` points. The best retail price was still worse than the sharp book's fair price, so the apparent edge lived entirely in the model's disagreement. In that game the home side lost, which tells you nothing about the bet's quality.

That shrunk edge, 1.1% on 0.5% of bankroll, is the realistic scale of a basketball side edge. If your pipeline produces many 5%+ edges, the pipeline is wrong.

## Totals and Spreads

For a spread or total, `p` is the probability of covering or going over at that line: from the margin model `P(cover) = Phi((m + s) / sigma)` (see `probability-calibration`). Break-even at -110 is 52.38%. Half-point and full-point differences matter: moving a 215.5 total to 216.5 changes the cover probability by about 2 to 3 points, comparable to a real edge.

## Props

Compare your projected distribution to the line (see `prop-modeling`). A player with a 24.5 line and a projected mean of 26 with a standard deviation near 7 has `P(over) = 1 - Phi((24.5 - 26)/7) = 0.585`, before devigging the price and before shrinking. Different books post different lines for the same player; edges often are just line differences.

## Pitfalls

| Pitfall | Handling |
|---------|----------|
| Uncalibrated `p` | Calibrate first |
| Using the opening or a stale price | Verify `captured_at` and re-pull before acting |
| Treating a win as validation | Judge by CLV and many bets |
| Over-staking correlated bets | Aggregate exposure per game |
| Chasing large edges | Investigate before betting |
| Ignoring limits and availability | A price you cannot get is not a price |
| Ignoring that data lags | The API is historical and next-day, not a live feed; confirm the live price at the book |

This skill does not promise profit. Edges are estimates, results are noisy, and past line behaviour does not guarantee future performance.

## Credit Usage

| Operation | Credits |
|-----------|---------|
| Price and close for one game | 5 |
| A slate of 8 games | 10 (date form) |
| Prop prices for one game | 10 |
| CLV for 100 past bets (by date, ~60 days) | ~600 |

## Output Format

```
Bet: [side] [line] @ [odds] ([book])
Model [p] | Market fair [m] ([n] books) | Shrunk [p*]
EV per unit: [x]% | Kelly [x]% | Stake (0.25 Kelly, cap [c]%): [x]% of bankroll
Checks: injuries [clear/flag], price age [captured_at]
Verdict: [bet / no bet], estimated edge [x] points, uncertainty large
```

## What to Do Next

| Found | Next | Skill |
|-------|------|-------|
| Bets placed | Log and track CLV | Keep a log (date, side, price, close) |
| Edge claim over many games | Replay on history | `backtesting` |
| Doubtful probability | Calibrate | `probability-calibration` |
