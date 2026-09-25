"""
Bronze -> Silver -> Gold pipeline
German Public EV Charging Rollout vs. EV Registration Growth
Data: Bundesnetzagentur Ladesaeulenregister (2026-09-01) + KBA FZ14 EV registrations by Zulassungsbezirk
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

DATA = "data"

# ---------------------------------------------------------------------------
# BRONZE: raw ingestion
# ---------------------------------------------------------------------------
print("Loading Ladesaeulenregister (charging points)...")
lsr = pd.read_csv(f"{DATA}/ladesaeulenregister.csv", sep=";", skiprows=10,
                   encoding="utf-8", on_bad_lines="skip", low_memory=False)
print(f"  bronze rows: {len(lsr):,}")

print("Loading KBA EV registrations by Zulassungsbezirk...")
kba = pd.read_csv(f"{DATA}/kba_ev_zulassungsbezirk.csv", encoding="utf-8-sig", low_memory=False)
print(f"  bronze rows: {len(kba):,}")

print("Loading vehicle density (population denominator)...")
dichte = pd.read_csv(f"{DATA}/fahrzeugdichte_gesamt.csv", encoding="utf-8-sig", low_memory=False)
print(f"  bronze rows: {len(dichte):,}")

# ---------------------------------------------------------------------------
# SILVER: clean, type, standardise keys
# ---------------------------------------------------------------------------

# --- Charging stations: aggregate to Bundesland level ---
lsr["Anzahl Ladepunkte"] = pd.to_numeric(lsr["Anzahl Ladepunkte"], errors="coerce").fillna(0)
lsr["Nennleistung Ladeeinrichtung [kW]"] = (
    lsr["Nennleistung Ladeeinrichtung [kW]"].astype(str).str.replace(",", ".", regex=False)
)
lsr["Nennleistung Ladeeinrichtung [kW]"] = pd.to_numeric(lsr["Nennleistung Ladeeinrichtung [kW]"], errors="coerce")
lsr["is_fast"] = lsr["Nennleistung Ladeeinrichtung [kW]"] >= 43  # DC fast-charging threshold (AC fast = 22kW, DC fast >=43kW)
lsr = lsr.dropna(subset=["Bundesland"])
lsr = lsr[lsr["Bundesland"].str.strip() != ""]

state_charging = lsr.groupby("Bundesland").agg(
    charging_locations=("Ladeeinrichtungs-ID", "nunique"),
    charge_points=("Anzahl Ladepunkte", "sum"),
    fast_locations=("is_fast", "sum"),
).reset_index()
state_charging["fast_share_pct"] = (state_charging["fast_locations"] / state_charging["charging_locations"] * 100).round(1)

# --- KBA EV registrations: latest quarter per state ---
kba["Berichtszeitpunkt"] = kba["Berichtszeitpunkt"].astype(str)
latest_period = kba["Berichtszeitpunkt"].max()
print(f"  latest KBA period: {latest_period}")

kba_latest = kba[kba["Berichtszeitpunkt"] == latest_period].copy()
for col in ["Pkw Insgesamt", "Pkw Elektro", "Pkw BEV"]:
    kba_latest[col] = pd.to_numeric(kba_latest[col], errors="coerce")

# Zulassungsbezirk doesn't carry Bundesland directly in this file; use the Regionen file which does.
kba_reg = pd.read_csv(f"{DATA}/kba_ev_regionen.csv", encoding="utf-8-sig", low_memory=False)
kba_reg["Berichtszeitpunkt"] = kba_reg["Berichtszeitpunkt"].astype(str)
latest_reg_period = kba_reg["Berichtszeitpunkt"].max()
kba_reg_latest = kba_reg[kba_reg["Berichtszeitpunkt"] == latest_reg_period].copy()
for col in ["Pkw Insgesamt", "Pkw Elektro", "Pkw BEV"]:
    kba_reg_latest[col] = pd.to_numeric(kba_reg_latest[col], errors="coerce")

state_ev = kba_reg_latest.groupby("Bundesland").agg(
    pkw_insgesamt=("Pkw Insgesamt", "sum"),
    pkw_elektro=("Pkw Elektro", "sum"),
    pkw_bev=("Pkw BEV", "sum"),
).reset_index()
state_ev = state_ev[~state_ev["Bundesland"].isin(["Sonstige"])]

# --- Time series: EV share growth over all available quarters (national) ---
kba_reg_ts = kba_reg.copy()
for col in ["Pkw Insgesamt", "Pkw Elektro", "Pkw BEV"]:
    kba_reg_ts[col] = pd.to_numeric(kba_reg_ts[col], errors="coerce")
national_ts = kba_reg_ts.groupby("Berichtszeitpunkt").agg(
    pkw_insgesamt=("Pkw Insgesamt", "sum"),
    pkw_elektro=("Pkw Elektro", "sum"),
    pkw_bev=("Pkw BEV", "sum"),
).reset_index().sort_values("Berichtszeitpunkt")
national_ts["ev_share_pct"] = (national_ts["pkw_elektro"] / national_ts["pkw_insgesamt"] * 100).round(2)

# --- population density file: derive population estimate from Pkw + density ---
dichte["Berichtsjahr"] = pd.to_numeric(dichte["Berichtsjahr"], errors="coerce")
latest_year = dichte["Berichtsjahr"].max()
dichte_latest = dichte[dichte["Berichtsjahr"] == latest_year].copy()
dichte_latest["Personenkraftwagen"] = pd.to_numeric(dichte_latest["Personenkraftwagen"], errors="coerce")
dichte_latest["Dichte Pkw je 1.000 Einwohner"] = pd.to_numeric(dichte_latest["Dichte Pkw je 1.000 Einwohner"], errors="coerce")
dichte_latest["population_est"] = dichte_latest["Personenkraftwagen"] / dichte_latest["Dichte Pkw je 1.000 Einwohner"] * 1000
state_pop = dichte_latest.groupby("GEN").agg(population_est=("population_est", "sum")).reset_index()
state_pop = state_pop.rename(columns={"GEN": "Bundesland"})

print("\nSilver layer built. State charging rows:", len(state_charging), "| State EV rows:", len(state_ev), "| State pop rows:", len(state_pop))
print(sorted(state_charging["Bundesland"].unique()))
print(sorted(state_ev["Bundesland"].unique()))
print(sorted(state_pop["Bundesland"].unique()))

state_charging.to_csv(f"{DATA}/../silver_state_charging.csv", index=False)
state_ev.to_csv(f"{DATA}/../silver_state_ev.csv", index=False)
state_pop.to_csv(f"{DATA}/../silver_state_pop.csv", index=False)
national_ts.to_csv(f"{DATA}/../silver_national_ts.csv", index=False)
