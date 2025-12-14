# Notes — Cashflow Stress Testing Under Rate & Vacancy Shocks

## What this repo is (and is not)
This repo implements a **deterministic stress test** for a levered rental cashflow under:
- parallel interest-rate shocks, and
- vacancy/occupancy revenue interruption.

It is **not**:
- a house price model
- a rent forecasting model
- a return optimiser
- an investment recommendation engine

The goal is to map **feasibility / failure regions**.

## Canonical model (one-year, proportional opex, interest-only)
Let:
- `R` = gross annual rent (normalised to 1.0 in code)
- `occ` = occupancy multiplier (fraction of rent realised), `0 ≤ occ ≤ 1`
- `c` = operating cost ratio (fraction of realised rent)
- `D` = outstanding debt balance
- `r` = interest rate

Then:
- `rev = R·occ`
- `NOI = (1−c)·R·occ`
- `int = r·D`
- `CF = NOI − int`
- `DSCR = NOI / int` (take DSCR = 0 if `NOI=0`)

Failure rule:
- infeasible if `CF < 0` or `DSCR < 1`.

## Why DSCR = 1 and CF = 0 coincide (in this simplified model)
Because:
- `CF = NOI − int`
- `DSCR = NOI / int`

Then:
- `CF = 0  ⇔  NOI = int  ⇔  NOI/int = 1  ⇔  DSCR = 1`

So both metrics define the same break-even set **as long as**:
- opex is purely proportional (no fixed costs),
- debt service is interest-only (no principal),
- there are no reserve flows / covenants / taxes.

This keeps the stress boundary interpretable and allows an analytic line overlay.

## Analytical break-even occupancy
From `NOI = int`:

\[
(1-c)R\,occ = rD \quad \Rightarrow \quad occ^*(r) = \frac{rD}{(1-c)R}
\]

Using the calibration scalar `θ = R/D`:

\[
occ^*(r) = \frac{r}{(1-c)\theta}
\]

This shows:
- increasing `r` raises required occupancy linearly,
- increasing `θ` (more rent per unit debt) lowers required occupancy.

## Structural vs calibrated interpretation
Structural mode (`θ = 1`) is **not a realistic property**. It is a sanity check that:
- DSCR decreases as rates rise (monotone in `r`),
- DSCR increases as occupancy rises (monotone in `occ`),
- the analytic break-even line matches the numerical break-even.

Calibrated presets (`durham_typical`, `rightmove_example`) move `θ` into realistic ranges so the break-even boundary lies inside the occupancy grid (e.g., 0.4–1.0).

## When transferability breaks (what changes invalidate “scale-free”)
The single-scalar calibration `θ = R/D` stops being sufficient if you add:
- fixed annual costs (licensing, insurance, compliance, letting fees)
- amortising principal payments
- non-proportional maintenance (lumpy repairs)
- taxes and timing effects
- reserve accounts (DSRA) and covenant triggers

Any of the above will generally separate `CF = 0` from `DSCR = 1`, changing the geometry.

## Interpretation pitfalls
- `occ=0` implies `NOI=0`, so DSCR is defined as 0 (not NaN).
- Under the proportional-opex assumption, `occ=0` also implies `opex=0` (but interest still accrues), so `CF(occ=0) = - r·D`.
- A model can look “safe” if the occupancy grid never reaches the break-even boundary; that means “safe within the tested grid”, not “safe universally”.
- This repo is a **screening tool**. If a deal is fragile here, it’s likely fragile under richer modelling too.

## Future extensions (explicitly out-of-scope for Project 1)
- add fixed annual costs to separate DSCR and CF boundaries
- add amortising mortgage cashflows
- model vacancy as a discrete process (e.g., regime persistence)
- introduce refinancing spreads and transaction costs
- optimal refinancing as a stopping problem (Project 4)
