# DunkAPI skills

Sixteen Claude skills that turn Claude into a basketball analyst for the NBA, WNBA and men's and women's college basketball. Each skill is a `SKILL.md` with when to use it, the exact DunkAPI tools and credit costs, the method, and examples taken from real API responses.

Point Claude at this folder (for example `git clone https://github.com/noahowsh/dunkapi-mcp.git` and add `skills/` to your skills directory), connect the MCP server (see the root README), and ask a question. Start with `dispatch` if you are unsure which skill applies. Free tier: 500 credits every month, no card: https://dunkapi.com/signup

| Skill | Category | What it does |
|-------|----------|--------------|
| [`game-lookup`](game-lookup/SKILL.md) | Data Exploration | Find games and box scores by date, team or season; tonight's schedule |
| [`team-analysis`](team-analysis/SKILL.md) | Data Exploration | Standings, Elo, pace, net rating and the four factors for any team |
| [`player-scouting`](player-scouting/SKILL.md) | Data Exploration | Player profiles, per-36 comparisons, shooting efficiency and leaderboards |
| [`odds-explorer`](odds-explorer/SKILL.md) | Data Exploration | Best price, vig and line movement across sportsbooks for any game |
| [`game-preview`](game-preview/SKILL.md) | Data Exploration | Pre-game page: Elo, efficiency, rest, injuries, market line and projection |
| [`shot-zone-analysis`](shot-zone-analysis/SKILL.md) | Basketball Analytics | Shot zones and expected points: shot quality vs shot making, defence by zone |
| [`player-form`](player-form/SKILL.md) | Basketball Analytics | Rolling game logs, minutes trends and shrunk projections for any player |
| [`feature-engineering`](feature-engineering/SKILL.md) | Methodology | Leak-free rolling, rest and Elo features for game and prop models |
| [`walk-forward-validation`](walk-forward-validation/SKILL.md) | Methodology | Chronological validation with market benchmarks and significance tests |
| [`probability-calibration`](probability-calibration/SKILL.md) | Methodology | Reliability tables, Platt scaling and margin-to-probability conversion |
| [`odds-analysis`](odds-analysis/SKILL.md) | Methodology | Implied probability, vig and four devigging methods with live examples |
| [`edge-detection`](edge-detection/SKILL.md) | Betting | Expected value, fractional Kelly and closing line value, framed as estimates |
| [`backtesting`](backtesting/SKILL.md) | Betting | Replay a betting rule on historical closing lines with realistic settlement |
| [`prop-modeling`](prop-modeling/SKILL.md) | Betting | Points, rebounds and assists props: minutes, rates, distributions, history |
| [`dispatch`](dispatch/SKILL.md) | Workflow | Routes a basketball request to the right two or three skills |
| [`dunkapi-tool`](dunkapi-tool/SKILL.md) | Infrastructure | Router for all 18 DunkAPI tools: credits, REST, MCP, response envelope |

## Notes

- Every tool name and parameter in these skills is checked against the live tool catalogue (`GET https://mcp.dunkapi.com/v1/tools`).
- Data is historical and next-day, not a live feed. Edges are estimates; read the variance and sample size warnings before acting on any number.
- Season convention: `season` is the year the season ends (2026-27 is `2027`); the WNBA uses the calendar year.
- Reference: https://dunkapi.com/docs and https://dunkapi.com/llms-full.txt
