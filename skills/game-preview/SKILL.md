---
name: game-preview
description: "Builds a full pre-game basketball preview: teams' Elo and efficiency, recent form, rest and back-to-backs, injuries, the market line across books, and a simple projection with its uncertainty. Use when the user asks to preview or break down tonight's game or the season opener, or wants everything needed before tip in one place. Works for the new season before it has games (falls back to last season's numbers and says so). Covers NBA, WNBA, men's and women's college. Do not use for results after the fact, see game-lookup. Do not use for devigging, see odds-analysis. Do not use for sizing a bet, see edge-detection."
metadata:
  version: 1.0.0
  author: DunkAPI
---

# Game Preview

> **Default data tool:** DunkAPI (`dunkapi-tool`).
> A full preview costs about 20 credits: `get_schedule` (2), `get_ratings` (2), `get_team_stats` (5), `get_injuries` (2), `get_odds` (5), and two `list_games` calls (2 each) for form and rest.

A compound skill: it calls several tools in a fixed order and assembles one page. The point is a number you can defend and the list of things that would change it.

## When to Use

- "Preview tonight's Knicks game" / "Break down the opener"
- "What do I need to know before Celtics-Heat?"
- A pre-bet checkpoint before `edge-detection`

## When NOT to Use

- Final scores and box scores, see `game-lookup`
- Only prices and movement, see `odds-explorer`
- Only team strength, see `team-analysis`
- Sizing or evaluating a bet, see `edge-detection`

## Commands Available

| Command | Use in a preview | Credits |
|---------|------------------|---------|
| `get_schedule` | Find the `game_id`, tip time, venue and the median line | 2 |
| `get_ratings` | Elo for both teams | 2 |
| `get_team_stats` | Pace, ratings and four factors (all teams in one call, or one with `team`) | 5 |
| `get_injuries` | Who is out or day-to-day (NBA and WNBA only) | 2 |
| `list_games` | Each team's last 10 results and the dates for rest | 2 each |
| `get_odds` | Every book's line for the game | 5 |
| `get_line_movement` | Optional: how the line has moved | 10 |
| `get_player` | Optional: a key player's last 10 games | 5 |

## Commands That Do NOT Exist

| Not available | Use instead |
|---------------|-------------|
| `get_game_preview`, `get_matchup` | This skill assembles it |
| `get_lineups`, `get_starting_five` | Not served. Infer likely starters from the last box score via `get_game` |
| `get_referee_assignments` | Not served |
| `get_head_to_head` | `list_games` with `team`, filter the opponent |

## Season Resolution (important for the opener)

The 2026-27 NBA regular season opens Oct 20, 2026. Before that:

- `get_schedule` shows preseason games with `season: 2027` and often only one book's spread and total.
- `get_ratings` and `get_team_stats` for `season: 2027` have little or nothing. Use `season: 2026` and label every number "2025-26". Elo regresses a quarter of the way toward 1500 between seasons per the API's method note, so last season's end-of-year rating overstates how far apart teams are.
- Preseason box scores are a poor guide to rotations: starters play limited minutes. Do not fold preseason results into form.
- After about 15 games per team, switch to `season: 2027` and drop the carryover caveat.

## How It Works

**Step 1: Find the game.** `get_schedule {"days": 3, "team": "NY"}`. Take `game_id`, `home.abbrev`, `away.abbrev`, `starts_at` and `line` (`home_spread`, `total`, `home_ml`, `books`).

**Step 2: Strength.** `get_ratings {"season": 2026}` gives Elo for every team. The rating gap `d = rHome - rAway + home_edge`. Home edge is not published as a parameter; use about 60 to 100 points and say it is an assumption. Win probability `= 1 / (1 + 10^(-d/400))`. The API's own anchor: a 100-point gap is about a 64% favourite on a neutral floor.

**Step 3: Efficiency.** `get_team_stats {"season": 2026}` (all teams, 5 credits). Pull `pace`, `off_rating`, `def_rating`, `net_rating`, `efg_pct`, `tov_pct`, `oreb_pct`, `ft_rate`, `three_rate` for both teams. Projected margin (home minus away, neutral):

```
home_pts = (home.off_rating + away.def_rating) / 2 * pace_game / 100
away_pts = (away.off_rating + home.def_rating) / 2 * pace_game / 100
pace_game = (home.pace + away.pace) / 2
```

Add the home edge in points (about 2 to 3). This is a prior from last season's averages; it knows nothing about roster changes.

**Step 4: Form and rest.** `list_games {"team": "NY", "limit": 10}` for each side. Compute from the `date` field: days since the previous game, whether this is the second night of a back-to-back, games in the last 7 days, and the last-10 margin. Exclude preseason from form (filter `season_type`).

**Step 5: Availability.** `get_injuries {"team": "NY"}` returns `name position status type detail return_date`. `Day-To-Day` is not `Out`. Quote the `detail` text when it names a decision (rest, coach's decision). If a top-three rotation player is out, the efficiency numbers in step 3 overstate the team; say by how much you cannot know, and widen the range rather than invent an adjustment.

**Step 6: Market.** `get_odds {"game_id": "..."}`. Take the median spread and total, the range across books, and the best prices (see `odds-explorer`). Convert the market to a probability with `odds-analysis`.

**Step 7: Compare and conclude.** Your projected margin versus the median spread, and your Elo-based win probability versus the devigged market probability. A gap of 1 to 2 points on the spread is inside the error of this method; do not call it an edge.

## Uncertainty

A single NBA game has a standard deviation of roughly 12 points around the projected margin; a 3-point projected edge is therefore only about a 60% proposition even if the projection were exact. Say "lean", not "pick", and show the numbers.

## Output Format

```
[Away] @ [Home], [date, time ET] | [venue]
Market: [Home] [spread], total [x] ([n] books, range [lo] to [hi]) | ML [h]/[a]
Strength (2025-26 carryover): Elo [home] [r] vs [away] [r] -> home [p]%
Efficiency: [Home] off [x] def [x] pace [x] | [Away] off [x] def [x] pace [x]
Projection: [Home] by [m] (range +/- 12), total [t] vs market [x]
Form: [Home] [W-L last 10], [rest]; [Away] [W-L last 10], [rest]
Availability: [Out/Day-To-Day with detail]
What would change this: [injury news, rest decisions, line move > 1 point]
Verdict: [lean or no lean, one sentence]
```

## Worked Example (shape only)

On Oct 11, 2026 the real schedule showed `get_schedule {"days": 7}` returning 34 games, all `preseason`, each with `line.books: 1`, for example CLE (home) vs ORL with `home_spread: -5.5, total: 226.5` and `home_ml: null`. A preview of that game would say: single-book line, no moneyline, preseason; rely on 2025-26 Elo (CLE 1602.9 against ORL 1564.8, a 38-point gap before home edge) and efficiency, and treat the market as indicative only. At 38 points plus an assumed 70 home edge, `d = 108`, which is about a 65% home win probability by the formula above, consistent with a 5.5-point favourite. Preseason rest decisions dominate; check `get_injuries` for "Coach's Decision" entries before saying more.

## Credit Usage

| Operation | Credits |
|-----------|---------|
| Core preview (steps 1-6) | ~20 |
| Add line movement | +10 |
| Add one player profile | +5 |
| Preview a 10-game slate | ~120 (share the all-teams calls across games) |

## What to Do Next

| Found | Next | Skill |
|-------|------|-------|
| Gap between model and market | Remove the vig and compute EV | `odds-analysis`, `edge-detection` |
| A player's role is in question | His recent minutes | `player-form` |
| Wants a prop angle | Prop history | `prop-modeling` |
| Wants to test a repeatable rule | Replay history | `backtesting` |
