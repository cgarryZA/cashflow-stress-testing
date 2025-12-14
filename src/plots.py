import os
import argparse
import yaml
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm, Normalize

from simulate import run_stress_test, select_calibration
from model import analytical_break_even_occupancy


# ---------- PATH HARDENING ----------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))

ASSUMPTIONS_PATH = os.path.join(REPO_DIR, "data", "assumptions.yaml")
RESULTS_DIR      = os.path.join(REPO_DIR, "results")
# ----------------------------------


def load_assumptions(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _centers_to_edges(centers: np.ndarray) -> np.ndarray:
    centers = np.asarray(centers, dtype=float)
    if centers.ndim != 1 or centers.size < 2:
        raise ValueError("centers must be a 1D array with length >= 2")

    edges = np.empty(centers.size + 1, dtype=float)
    edges[1:-1] = 0.5 * (centers[:-1] + centers[1:])
    edges[0] = centers[0] - 0.5 * (centers[1] - centers[0])
    edges[-1] = centers[-1] + 0.5 * (centers[-1] - centers[-2])
    return edges


def _pivot_grid(df, value_col: str):
    x_centers = np.sort(df["rate_shock_bp"].unique())
    y_centers = np.sort(df["occupancy_multiplier"].unique())

    pivot = df.pivot(
        index="occupancy_multiplier",
        columns="rate_shock_bp",
        values=value_col,
    ).reindex(index=y_centers, columns=x_centers)

    Z = pivot.values.astype(float)
    return x_centers, y_centers, Z


def _clamp_axes(ax, x_edges, y_edges):
    ax.set_xlim(float(x_edges[0]), float(x_edges[-1]))
    ax.set_ylim(float(y_edges[0]), float(y_edges[-1]))


def _diverging_norm_around_zero(Z: np.ndarray):
    vmin = float(np.nanmin(Z))
    vmax = float(np.nanmax(Z))

    if not np.isfinite(vmin) or not np.isfinite(vmax):
        return Normalize(vmin=0.0, vmax=1.0)

    if np.isclose(vmin, vmax):
        eps = 1e-9 if vmax == 0 else abs(vmax) * 1e-9
        return Normalize(vmin=vmin - eps, vmax=vmax + eps)

    m = max(abs(vmin), abs(vmax))
    if m == 0:
        m = 1e-9
    return TwoSlopeNorm(vmin=-m, vcenter=0.0, vmax=m)


def plot_dscr_gap_surface(df, assumptions, theta, base_rate, preset_name):
    os.makedirs(RESULTS_DIR, exist_ok=True)

    df = df.copy()
    df["dscr_gap"] = df["dscr"] - 1.0

    x, y, Z = _pivot_grid(df, "dscr_gap")
    x_edges = _centers_to_edges(x)
    y_edges = _centers_to_edges(y)

    norm = _diverging_norm_around_zero(Z)

    fig, ax = plt.subplots(figsize=(9, 6))
    mesh = ax.pcolormesh(
        x_edges,
        y_edges,
        Z,
        cmap="RdYlGn",
        norm=norm,
        shading="auto",
    )

    ax.set_xlabel("Interest Rate Shock (bp)")
    ax.set_ylabel("Occupancy Multiplier")
    ax.set_title(f"Distance to Break-Even (DSCR − 1) — {preset_name}")

    _clamp_axes(ax, x_edges, y_edges)

    # Analytical DSCR=1 boundary
    operating_cost_ratio = float(assumptions["base_cashflow"]["operating_cost_ratio"])
    base_rent = float(assumptions["base_cashflow"]["gross_annual_rent"])
    debt_balance = base_rent / float(theta)

    shocks_bp = x
    rates = base_rate + shocks_bp / 10_000.0
    occ_star = np.array(
        [
            analytical_break_even_occupancy(
                float(r),
                operating_cost_ratio,
                debt_balance,
                base_rent,
            )
            for r in rates
        ],
        dtype=float,
    )

    ax.plot(shocks_bp, occ_star, color="black", linewidth=2, label="Analytical DSCR = 1")
    ax.legend(loc="upper right")

    fig.colorbar(mesh, ax=ax, label="DSCR − 1")
    plt.tight_layout()

    out_path = os.path.join(RESULTS_DIR, f"dscr_gap_surface__{preset_name}.png")
    plt.savefig(out_path)
    plt.close()
    return out_path


def plot_net_cashflow_surface(df, preset_name):
    os.makedirs(RESULTS_DIR, exist_ok=True)

    x, y, Z = _pivot_grid(df, "net_cashflow")
    x_edges = _centers_to_edges(x)
    y_edges = _centers_to_edges(y)

    norm = _diverging_norm_around_zero(Z)

    fig, ax = plt.subplots(figsize=(9, 6))
    mesh = ax.pcolormesh(
        x_edges,
        y_edges,
        Z,
        cmap="RdYlGn",
        norm=norm,
        shading="auto",
    )

    _clamp_axes(ax, x_edges, y_edges)

    # CF=0 contour (only if 0 lies in range)
    Xc, Yc = np.meshgrid(x, y)
    try:
        ax.contour(Xc, Yc, Z, levels=[0.0], colors="black", linewidths=2)
    except Exception:
        pass

    ax.set_xlabel("Interest Rate Shock (bp)")
    ax.set_ylabel("Occupancy Multiplier")
    ax.set_title(f"Net Cashflow Stress Surface (Black = CF 0) — {preset_name}")

    fig.colorbar(mesh, ax=ax, label="Net Cashflow")
    plt.tight_layout()

    out_path = os.path.join(RESULTS_DIR, f"net_cashflow_surface__{preset_name}.png")
    plt.savefig(out_path)
    plt.close()
    return out_path


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

    p1 = plot_dscr_gap_surface(df, assumptions, theta, base_rate, preset_name)
    p2 = plot_net_cashflow_surface(df, preset_name)

    print("Saved plots to:", RESULTS_DIR)
    print(" -", p1)
    print(" -", p2)


if __name__ == "__main__":
    main()
