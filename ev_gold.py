"""
GOLD layer: join charging infra + EV registrations + population, compute metrics, build charts.
Palette matched to Kiran's existing projects: blue #2B6CB0, green #2F855A, red #C53030 (with gradients).
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.colors import LinearSegmentedColormap

state_charging = pd.read_csv("silver_state_charging.csv")
state_ev = pd.read_csv("silver_state_ev.csv")
state_pop = pd.read_csv("silver_state_pop.csv")
national_ts = pd.read_csv("silver_national_ts.csv")

gold = state_charging.merge(state_ev, on="Bundesland").merge(state_pop, on="Bundesland")

gold["charge_points_per_100k"] = (gold["charge_points"] / gold["population_est"] * 100_000).round(1)
gold["ev_per_100k"] = (gold["pkw_elektro"] / gold["population_est"] * 100_000).round(1)
gold["charge_points_per_1k_ev"] = (gold["charge_points"] / gold["pkw_elektro"] * 1000).round(2)
gold["ev_share_of_fleet_pct"] = (gold["pkw_elektro"] / gold["pkw_insgesamt"] * 100).round(2)

gold = gold.sort_values("charge_points_per_1k_ev", ascending=False)
gold.to_csv("gold_state_summary.csv", index=False)

print(gold[["Bundesland", "charge_points", "pkw_elektro", "charge_points_per_100k",
            "charge_points_per_1k_ev", "fast_share_pct", "ev_share_of_fleet_pct"]].to_string(index=False))

# ---------------------------------------------------------------------------
# Palette: light-to-dark gradients built from the house colors
# ---------------------------------------------------------------------------
blue_cmap = LinearSegmentedColormap.from_list("house_blue", ["#BBD3EA", "#2B6CB0", "#123A5E"])
green_cmap = LinearSegmentedColormap.from_list("house_green", ["#BEE3CC", "#2F855A", "#173D2B"])
red_cmap = LinearSegmentedColormap.from_list("house_red", ["#F0BDBD", "#C53030", "#6B1616"])

def gradient_colors(values, cmap, reverse=False):
    v = np.asarray(values, dtype=float)
    norm = (v - v.min()) / (v.max() - v.min() + 1e-9)
    if reverse:
        norm = 1 - norm
    return [cmap(0.25 + 0.65 * n) for n in norm]  # keep out of the very-light/very-dark extremes

# ---------------------------------------------------------------------------
# CHART 1: Infrastructure ratio (charge points per 1,000 EVs) by state
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(10, 7))
plot_df = gold.sort_values("charge_points_per_1k_ev").reset_index(drop=True)
median_val = plot_df["charge_points_per_1k_ev"].median()
above_mask = (plot_df["charge_points_per_1k_ev"] >= median_val).tolist()
above_colors = iter(gradient_colors(plot_df.loc[plot_df["charge_points_per_1k_ev"] >= median_val, "charge_points_per_1k_ev"], green_cmap))
below_colors = iter(gradient_colors(plot_df.loc[plot_df["charge_points_per_1k_ev"] < median_val, "charge_points_per_1k_ev"], red_cmap, reverse=True))
colors = [next(above_colors) if is_above else next(below_colors) for is_above in above_mask]
ax.barh(plot_df["Bundesland"], plot_df["charge_points_per_1k_ev"], color=colors)
ax.set_xlabel("Charge points per 1,000 registered electric cars")
ax.set_title("Charging Infrastructure Relative to EV Fleet Size, by State", fontsize=13, fontweight="bold")
ax.axvline(median_val, color="gray", linestyle="--", linewidth=1, label="National median")
ax.legend(loc="lower right", fontsize=9)
plt.tight_layout()
plt.savefig("charts/chart_infra_ratio_by_state.png", dpi=150)
plt.close()

# ---------------------------------------------------------------------------
# CHART 2: Charge points per 100k residents vs EV share of fleet (scatter, gradient by ratio)
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(9.5, 7))
sc = ax.scatter(gold["ev_share_of_fleet_pct"], gold["charge_points_per_100k"], s=110,
                 c=gold["charge_points_per_1k_ev"], cmap=blue_cmap, zorder=3, edgecolors="white", linewidths=0.6)
for _, row in gold.iterrows():
    ax.annotate(row["Bundesland"], (row["ev_share_of_fleet_pct"], row["charge_points_per_100k"]),
                fontsize=8, xytext=(5, 5), textcoords="offset points")
cbar = plt.colorbar(sc, ax=ax)
cbar.set_label("Charge points per 1,000 EVs", fontsize=9)
ax.set_xlabel("EV share of registered car fleet (%)")
ax.set_ylabel("Charge points per 100,000 residents")
ax.set_title("Where Infrastructure Density Meets EV Adoption", fontsize=13, fontweight="bold")
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig("charts/chart_density_vs_adoption.png", dpi=150)
plt.close()

# ---------------------------------------------------------------------------
# CHART 3: Fast-charging share by state (blue gradient, matches house palette)
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(10, 7))
plot_df2 = gold.sort_values("fast_share_pct")
colors3 = gradient_colors(plot_df2["fast_share_pct"], blue_cmap)
ax.barh(plot_df2["Bundesland"], plot_df2["fast_share_pct"], color=colors3)
ax.set_xlabel("Share of charging locations offering DC fast charging (>=43kW) (%)")
ax.set_title("Fast-Charging Coverage by State", fontsize=13, fontweight="bold")
plt.tight_layout()
plt.savefig("charts/chart_fast_charging_share.png", dpi=150)
plt.close()

# ---------------------------------------------------------------------------
# CHART 4: National EV share growth over time (green line, gradient area fill)
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(10, 6))
x = list(range(len(national_ts)))
y = national_ts["ev_share_pct"].values
labels = national_ts["Berichtszeitpunkt"].astype(str).tolist()
ax.plot(x, y, marker="o", color="#2F855A", linewidth=2, zorder=3)
# gradient area fill under the line, light-to-dark green with height
for i in range(len(x) - 1):
    ax.fill_between([x[i], x[i + 1]], [y[i], y[i + 1]], color=green_cmap(0.25 + 0.5 * (i / max(len(x) - 2, 1))), alpha=0.35)
ax.set_ylabel("EV share of registered car fleet (%)")
ax.set_xlabel("Reporting quarter")
ax.set_title("National EV Adoption Growth Over Time", fontsize=13, fontweight="bold")
ax.grid(alpha=0.3)
ax.set_xticks(x)
ax.set_xticklabels(labels, rotation=45, ha="right")
plt.tight_layout()
plt.savefig("charts/chart_national_ev_growth.png", dpi=150)
plt.close()

print("\nCharts written to charts/")
