# Cashflow Stress Testing Under Rate and Vacancy Shocks

## Research Question
Where and how does a levered rental cashflow become infeasible under adverse
interest-rate and revenue interruption scenarios?

## Motivation
Levered cashflow assets are vulnerable to nonlinear downside risk.
Small changes in funding costs or occupancy can cause discrete failure,
particularly when equity buffers are thin.

This project applies stress testing techniques commonly used in UK banking
(IRRBB) and project finance to a simplified rental cashflow, with the goal of
identifying failure regions rather than forecasting returns.

## Model Scope
- Geography: UK
- Asset type: Residential rental property
- Objective: Risk and robustness analysis only
- Time horizon: One-year stress window

The model is intentionally static and deterministic. It does not attempt to
predict prices, rents, or macroeconomic variables.

## Assumptions
All modelling assumptions are explicitly defined in `data/assumptions.yaml`.
Key features include:
- Deterministic base cashflow
- Discrete interest-rate shocks (0–200 bp)
- Regime-based revenue stress (vacancy scenarios)
- Interest-only debt structure
- No equity injections under stress

Any scenario producing DSCR < 1.0 or negative net cashflow is considered
infeasible without external capital support.

## Methodology
The model computes net cashflow and DSCR across a grid of stress scenarios
defined by:
- Interest-rate levels
- Occupancy regimes

This produces a stress surface from which break-even conditions are derived.
No optimisation or forecasting is performed.

## Results
The analysis produces four core outputs:
1. Net cashflow stress surface (rate × occupancy)
2. DSCR stress surface with infeasible regions highlighted
3. Break-even interest rate by occupancy regime
4. Break-even occupancy by interest-rate level

Together, these plots identify:
- Failure regions
- Fragility to rate increases
- Sensitivity to vacancy shocks

## Interpretation
The results are intended to support rejection of fragile leverage or properties,
not to select return-maximising configurations.

Stress testing highlights that robustness is driven by:
- Headroom between base DSCR and 1.0
- Sensitivity of cashflow to discrete revenue shocks
- Exposure to interest-rate increases

## Limitations
- No price dynamics or capital appreciation
- No rent growth or inflation modelling
- No behavioural assumptions
- No long-horizon forecasting

These exclusions are deliberate and consistent with standard stress-testing
practice.

## Conclusion
Stress testing provides a transparent and interpretable framework for assessing
the downside risk of levered cashflow assets. Rather than predicting outcomes,
the model identifies where and how the structure breaks under plausible adverse
conditions.
