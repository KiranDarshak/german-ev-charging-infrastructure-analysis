import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

gold = pd.read_csv("gold_state_summary.csv")
national_ts = pd.read_csv("silver_national_ts.csv")

blue_cmap = LinearSegmentedColormap.from_list("house_blue", ["#BBD3EA", "#2B6CB0", "#123A5E"])
green_cmap = LinearSegmentedColormap.from_list("house_green", ["#BEE3CC", "#2F855A", "#173D2B"])
red_cmap = LinearSegmentedColormap.from_list("house_red", ["#F0BDBD", "#C53030", "#6B1616"])

def gradient_colors(values, cmap, reverse=False):
    v = np.asarray(values, dtype=float)
    norm = (v - v.min()) / (v.max() - v.min() + 1e-9)
    if reverse:
        norm = 1 - norm
    return [cmap(0.25 + 0.65 * n) for n in norm]

fig = plt.figure(figsize=(13, 8.2))
fig.patch.set_facecolor("white")

# Title block
fig.text(0.045, 0.955, "German Public EV Charging Rollout vs. EV Registration Growth", fontsize=17, fontweight="bold", color="#1a1a1a")
fig.text(0.045, 0.925, "Charging Infrastructure Dashboard  •  2026 Ladesäulenregister / KBA EV Registrations", fontsize=10, color="#666666")

# KPI cards
kpi_ax = fig.add_axes([0.045, 0.76, 0.91, 0.13])
kpi_ax.axis("off")
kpis = [
    ("3.04%", "NATIONAL EV SHARE 2025 Q4", "up from 1.93% (2023 Q1)", "#2F855A"),
    ("46", "LOWEST INFRA RATIO", "Saarland, pts per 1,000 EVs", "#C53030"),
    ("111", "HIGHEST INFRA RATIO", "Meck.-Vorpommern, pts per 1,000 EVs", "#2B6CB0"),
    ("21.5%", "LOWEST FAST-CHARGE SHARE", "Berlin, despite high density", "#EF6C00"),
]
n = len(kpis)
w = 1.0 / n
for i, (value, label, sub, color) in enumerate(kpis):
    x0 = i * w
    kpi_ax.add_patch(plt.Rectangle((x0 + 0.01, 0), w - 0.02, 1, transform=kpi_ax.transAxes,
                                    facecolor="#FAFAFA", edgecolor="#E5E5E5", linewidth=1))
    kpi_ax.add_patch(plt.Rectangle((x0 + 0.01, 0), 0.012, 1, transform=kpi_ax.transAxes, facecolor=color))
    kpi_ax.text(x0 + 0.05, 0.62, value, transform=kpi_ax.transAxes, fontsize=19, fontweight="bold", color="#1a1a1a", va="center")
    kpi_ax.text(x0 + 0.05, 0.32, label, transform=kpi_ax.transAxes, fontsize=7.3, color="#555555", va="center", fontweight="bold")
    kpi_ax.text(x0 + 0.05, 0.14, sub, transform=kpi_ax.transAxes, fontsize=7, color="#888888", va="center")
kpi_ax.set_xlim(0, 1)
kpi_ax.set_ylim(0, 1)

# Chart 1: infra ratio bar (compact)
ax1 = fig.add_axes([0.06, 0.06, 0.28, 0.62])
plot_df = gold.sort_values("charge_points_per_1k_ev").reset_index(drop=True)
median_val = plot_df["charge_points_per_1k_ev"].median()
above_mask = (plot_df["charge_points_per_1k_ev"] >= median_val).tolist()
above_colors = iter(gradient_colors(plot_df.loc[plot_df["charge_points_per_1k_ev"] >= median_val, "charge_points_per_1k_ev"], green_cmap))
below_colors = iter(gradient_colors(plot_df.loc[plot_df["charge_points_per_1k_ev"] < median_val, "charge_points_per_1k_ev"], red_cmap, reverse=True))
colors = [next(above_colors) if is_above else next(below_colors) for is_above in above_mask]
ax1.barh(plot_df["Bundesland"], plot_df["charge_points_per_1k_ev"], color=colors)
ax1.set_title("Charge Points per 1,000 EVs", fontsize=9.5, fontweight="bold", loc="left")
ax1.tick_params(axis="y", labelsize=6.5)
ax1.tick_params(axis="x", labelsize=7)
ax1.axvline(median_val, color="gray", linestyle="--", linewidth=0.8)

# Chart 2: scatter
ax2 = fig.add_axes([0.395, 0.06, 0.28, 0.62])
sc = ax2.scatter(gold["ev_share_of_fleet_pct"], gold["charge_points_per_100k"], s=55,
                  c=gold["charge_points_per_1k_ev"], cmap=blue_cmap, edgecolors="white", linewidths=0.5)
ax2.set_title("Infra Density vs. EV Adoption", fontsize=9.5, fontweight="bold", loc="left")
ax2.set_xlabel("EV share of fleet (%)", fontsize=7.5)
ax2.set_ylabel("Charge points / 100k residents", fontsize=7.5)
ax2.tick_params(labelsize=7)
ax2.grid(alpha=0.25)

# Chart 3: national trend
ax3 = fig.add_axes([0.73, 0.06, 0.235, 0.62])
x = list(range(len(national_ts)))
y = national_ts["ev_share_pct"].values
labels = national_ts["Berichtszeitpunkt"].astype(str).tolist()
ax3.plot(x, y, marker="o", color="#2F855A", linewidth=2, markersize=3.5, zorder=3)
for i in range(len(x) - 1):
    ax3.fill_between([x[i], x[i + 1]], [y[i], y[i + 1]], color=green_cmap(0.25 + 0.5 * (i / max(len(x) - 2, 1))), alpha=0.35)
ax3.set_title("National EV Share Growth", fontsize=9.5, fontweight="bold", loc="left")
ax3.set_xticks(x[::2])
ax3.set_xticklabels([labels[i] for i in range(0, len(labels), 2)], rotation=45, ha="right", fontsize=6)
ax3.tick_params(axis="y", labelsize=7)
ax3.grid(alpha=0.25)

plt.savefig("charts/dashboard_preview.png", dpi=160, facecolor="white")
print("done")
