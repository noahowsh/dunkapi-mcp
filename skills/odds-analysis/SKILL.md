---
name: odds-analysis
description: "Odds math for basketball betting markets: American, decimal and implied probability conversion, vig, and four devigging methods (multiplicative, additive/Shin, power) applied to moneylines, spreads, totals and player props, plus building a consensus no-vig line across sportsbooks. Use when the user asks what a price implies, how to remove the vig, what the true probability is, or what a fair line is. Do not use for finding the best price or line movement, see odds-explorer. Do not use for comparing a model to the market or sizing a bet, see edge-detection. Do not use for historical strategy simulation, see backtesting."
metadata:
  version: 1.0.0
  author: DunkAPI
---

# Odds Analysis

> **Default data tool:** DunkAPI (`dunkapi-tool`).
> `get_odds` (5 credits per game) for moneylines, spreads and totals with prices. `get_player_props` (10) for prop prices. The math itself is local.

Prices are not probabilities. A book's two sides add to more than 100%; the excess is its margin. Removing it gives the market's own view, which is the benchmark every edge claim has to beat.

## When to Use

- "What probability does -195 imply?"
- "Devig this moneyline: -200 / +165"
- "What is the fair total if over is -108 and under is -112?"
- "What's the no-vig line across all books?"
- Any time a probability from the market is needed for `edge-detection` or `backtesting`

## When NOT to Use

- Hunting the best number or reading line moves, see `odds-explorer`
- Judging a model against the market, see `edge-detection`
- Replaying many games, see `backtesting`

## Commands Available

| Command | Role | Credits |
|---------|------|---------|
| `get_odds` | Per-book prices and closing implied probabilities | 5 per game, 10 per date |
| `get_player_props` | Over and under prices for props | 10 |
| `get_schedule` | Median line and `home_implied_prob` on upcoming games | 2 |

## Commands That Do NOT Exist

| Not available | Use instead |
|---------------|-------------|
| `get_no_vig_odds`, `get_fair_odds` | Compute locally with the methods below |
| `get_true_probability` | Same |

## Conversions

```
American to implied probability:
  odds > 0:  p = 100 / (odds + 100)
  odds < 0:  p = -odds / (-odds + 100)
Decimal odds = 1 / p        (American +165 = 2.65; -195 = 1.513)
American from p:
  p < 0.5:   odds = +100 * (1 - p) / p
  p >= 0.5:  odds = -100 * p / (1 - p)
Payout per 1 unit staked at American odds o:
  o > 0: o/100       o < 0: 100/(-o)
```

The API returns `home_close_prob` and `away_close_prob` on `get_odds` rows: those are the raw implied probabilities of the closing moneyline (they sum above 1). Treat them as inputs to devigging, not as the answer.

## Vig

`overround = pA + pB - 1`. A -110/-110 spread is 4.76%. Sharper books run lower. In the live row set below, raw sums ranged from 1.019 (ESPN BET) to 1.044 (BetMGM) on one game's moneyline.

## Devigging Methods

Given two raw probabilities `a` and `b` with `a + b = S > 1`:

| Method | Formula | Behaviour |
|--------|---------|-----------|
| Multiplicative (proportional) | `a/S`, `b/S` | Simple default. Spreads the margin proportionally |
| Additive | `a - (S-1)/2`, `b - (S-1)/2` | Equal cut from each side. Can push a longshot too low, so check it stays positive |
| Shin | Solves for an insider-trading fraction `z` | Shifts more of the margin onto longshots. For a two-way market it equals the additive result |
| Power | Find `k` so `a^k + b^k = 1`; use `a^k`, `b^k` | Takes relatively more off the longshot, which matches the favourite-longshot bias often seen in betting markets |

### Worked example with live numbers

`get_odds {"game_id": "401859967"}` returned Pinnacle's closing moneyline as SA (home) -195, NY (away) +173. Raw: `0.6610 + 0.3663 = 1.0273` (2.73% margin).

| Method | Home (SA) | Away (NY) |
|--------|----------:|----------:|
| Raw | 0.6610 | 0.3663 |
| Multiplicative | 0.6434 | 0.3566 |
| Additive / Shin | 0.6474 | 0.3526 |
| Power (k = 1.043) | 0.6493 | 0.3507 |

The methods differ by less than 1 point on a favourite priced near 65%, so for NBA sides the choice rarely changes a decision. The spread widens as the favourite gets shorter (-600 or more), where power and Shin cut the longshot harder. Pick one and keep it for the whole analysis; mixing methods inside one backtest adds noise that looks like signal.

Spread and total pairs are devigged the same way. DraftKings' total in that game was over -108 / under -112: raw `0.5192 + 0.5283 = 1.0475`, multiplicative fair over probability `0.4957`.

## Consensus No-Vig Line

For a game with many books:

1. Devig each book's own two-way market (same method).
2. Take the median across books. The median ignores an outlier book's stale price.
3. Optionally weight a sharp reference (Pinnacle appears in the live rows) heavier than a retail book such as a recreational app.
4. Report the range as well: the width of disagreement across books is part of the answer.

For the eight books on that game, multiplicative home probabilities ran from 0.631 to 0.651. Pinnacle at 0.643 sat in the middle of that range; the highest was Bovada at 0.651 and the lowest DraftKings at 0.631.

## Converting Spread to Win Probability

When a game has no moneyline (common in preseason, where one book may post only a spread and total), use the spread. An NBA spread of `s` points corresponds roughly to `Phi(-s / sigma)` for the favourite, with `sigma` near 12. A 5.5-point favourite: `Phi(5.5/12) = Phi(0.458) = 0.677`, a rough guide; the moneyline is better when you have it. When both a spread and a moneyline exist, compare the two; a large gap means a stale line or the wrong sigma.

## Props

A prop has a line and two prices. Devig the pair: with over -125 and under -105 (BetMGM's closing points prop in a call for Jalen Brunson on 2025-10-22), raw `0.5556 + 0.5122 = 1.0678`, fair over probability `0.5203`. Note the line also differs by book (23.5 or 24.5 for the same player that night), so compare prices only at the same line. See `prop-modeling`.

## Pitfalls

| Pitfall | Handling |
|---------|----------|
| Treating raw implied probability as true | Always devig |
| Mixing opening and closing prices | Keep one snapshot type per analysis |
| Using one retail book | Use the median or a sharp reference |
| Different lines treated as the same market | Compare only identical lines (or adjust for the line) |
| Three-way markets | Basketball has none; do not apply soccer logic |
| Tiny overrounds | A raw sum under 1 means a stale or mistaken row; discard |
| Null prices | `home_spread_open` and similar fields can be `null`; skip those rows |

## Credit Usage

| Operation | Credits |
|-----------|---------|
| One game, all books | 5 |
| A day, all games | 10 |
| One game's player props | 10 |
| The conversions themselves | 0 |

## Output Format

```
[Game] closing moneyline, [method]
[Book]: [home odds]/[away odds] -> raw [x]+[y] = [S] -> fair [h]% / [a]%
Consensus (median of [n] books): home [x]% (range [lo]% to [hi]%)
Fair price: home [odds], away [odds]
```

## What to Do Next

| Found | Next | Skill |
|-------|------|-------|
| Fair probability in hand | Compare with a model | `edge-detection` |
| Need the best number to bet | Line shop | `odds-explorer` |
| Want to apply it to history | Backtest | `backtesting` |
