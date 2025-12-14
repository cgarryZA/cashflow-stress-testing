import os
import argparse
import yaml
import numpy as np
import pandas as pd

from model import net_cashflow, dscr


# ---------- PATH HARDENING ----------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))

ASSUMPTIONS_PATH = os.path.join(REPO_DIR, "data", "assumptions.yaml")
RESULTS_DIR      = os.path.join(REPO_DIR, "results")
# ----------------------------------


def load_assumptions(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _frange(start: float, stop: float, step: float) -> np.ndarray:
    # inclusive stop (within floating tolerance)
    n = int(np.floor((stop - start) / step + 1e-12)) + 1
    vals = start + step * np.arange(n, dtype=float)
    # clamp to stop
    vals = np.clip(vals, min(start, stop), max(start, stop))
    return vals


def get_rate_shocks_bp(assumptions) -> np.ndarray:
    cfg = assumptions["interest_rate_stress"]
    start = float(cfg["start_bp"])
    stop = float(cfg["stop_bp"])
    step = float(cfg["step_bp"])
    return _frange(start, stop, step)


def get_occupancy_grid(assumptions, preset_cfg=None) -> np.ndarray:
    # default global
    occ_cfg = assumptions["revenue_stress"]["occupancy_range"]

    # optional override per preset
    if preset_cfg and isinstance(preset_cfg, dict) and "occupancy_range_override" in preset_cfg:
        occ_cfg = preset_cfg["occupancy_range_override"]

    start = float(occ_cfg["start"])
    stop = float(occ_cfg["stop"])
    step = float(occ_cfg["step"])
    return _frange(start, stop, step)


def select_calibration(assumptions, preset_name: str | None):
    calib = assumptions["calibration"]
    presets = calib["presets"]

    name = preset_name if preset_name is not None else calib.get("default_preset")
    if name not in presets:
        raise ValueError(f"Unknown preset '{name}'. Available: {list(presets.keys())}")

    cfg = presets[name]

    if "rent_to_debt_ratio" in cfg:
        theta = float(cfg["rent_to_debt_ratio"])
    elif "gross_yield" in cfg and "ltv" in cfg:
        theta = float(cfg["gross_yield"]) / float(cfg["ltv"])
    elif "annual_rent_gbp" in cfg and "mortgage_balance_gbp" in cfg:
        theta = float(cfg["annual_rent_gbp"]) / float(cfg["mortgage_balance_gbp"])
    else:
        raise ValueError(
            f"Preset '{name}' must define rent_to_debt_ratio OR (gross_yield and ltv) OR (annual_rent_gbp and mortgage_balance_gbp)."
        )

    return theta, name, cfg


def run_stress_test(assumptions, base_rate: float, theta: float, preset_cfg=None) -> pd.DataFrame:
    # Normalised rent; debt implied by theta (theta = rent/debt)
    rent = float(assumptions["base_cashflow"]["gross_annual_rent"])
    opex_ratio = float(assumptions["base_cashflow"]["operating_cost_ratio"])
    debt = rent / float(theta)

    shocks_bp = get_rate_shocks_bp(assumptions)
    occ_grid = get_occupancy_grid(assumptions, preset_cfg)

    rows = []
    for occ in occ_grid:
        for shock in shocks_bp:
            r = base_rate + float(shock) / 10_000.0
            revenue = rent * float(occ)
            cf = net_cashflow(revenue, opex_ratio, r, debt)
            d = dscr(revenue, opex_ratio, r, debt)

            rows.append(
                {
                    "interest_rate": r,
                    "rate_shock_bp": float(shock),
                    "occupancy_multiplier": float(occ),
                    "net_cashflow": float(cf),
                    "dscr": float(d),
                }
            )

    return pd.DataFrame(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--preset", type=str, default=None, help="Calibration preset name from assumptions.yaml")
    parser.add_argument("--base-rate", type=float, default=None, help="Override base interest rate (decimal, e.g. 0.05)")
    args = parser.parse_args()

    assumptions = load_assumptions(ASSUMPTIONS_PATH)

    yaml_base_rate = float(assumptions.get("financing", {}).get("base_interest_rate_value", 0.05))
    base_rate = float(args.base_rate) if args.base_rate is not None else yaml_base_rate

    theta, preset_name, preset_cfg = select_calibration(assumptions, args.preset)

    df = run_stress_test(assumptions, base_rate, theta, preset_cfg=preset_cfg)

    os.makedirs(RESULTS_DIR, exist_ok=True)
    out_csv = os.path.join(RESULTS_DIR, f"stress_results__{preset_name}.csv")
    df.to_csv(out_csv, index=False)

    print(df.head())
    print(f"\nSaved: {out_csv}")


if __name__ == "__main__":
    main()
