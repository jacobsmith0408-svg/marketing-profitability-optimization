import sqlite3
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

# -----------------------------
# Load channel totals from SQLite
# -----------------------------
project_root = Path(__file__).resolve().parents[1]
db_path = project_root / "data" / "marketing.db"

conn = sqlite3.connect(db_path)
df = pd.read_sql(
    """
    SELECT
      channel,
      SUM(ad_spend) AS spend,
      SUM(purchases) AS purchases,
      SUM(revenue) AS revenue
    FROM campaign_daily
    GROUP BY channel
    """,
    conn
)
conn.close()

# -----------------------------
# Assumptions
# -----------------------------
GROSS_MARGIN = 0.60
AFFILIATE_COMMISSION = 0.12  # % of revenue
TIKTOK_CUT_FROM = "TikTok"
REALLOCATE_TO = "Paid Search"

# Diminishing returns model for Paid Search:
# As Search spend increases, efficiency declines.
# search_eff_multiplier = 1 - alpha * (spend_increase_pct)
# Example alpha=0.30 means +30% spend -> 9% efficiency drop (0.30 * 0.30 = 0.09).
SEARCH_DIMINISH_ALPHA = 0.30  # tune 0.15–0.45; higher = harsher diminishing returns

# Fix affiliate spend to commission model (baseline)
df.loc[df["channel"] == "Affiliate", "spend"] = (
    df.loc[df["channel"] == "Affiliate", "revenue"] * AFFILIATE_COMMISSION
)

# Baseline profit
df["gross_profit"] = df["revenue"] * GROSS_MARGIN
df["net_profit"] = df["gross_profit"] - df["spend"]
baseline_profit = float(df["net_profit"].sum())

# Keep Email fixed in all simulations (owned channel, spend=0)
# For channels with spend > 0, compute baseline efficiency
paid = df[df["spend"] > 0].copy()
paid["purchases_per_dollar"] = paid["purchases"] / paid["spend"]
paid["revenue_per_dollar"] = paid["revenue"] / paid["spend"]

eff_base = paid.set_index("channel")[["purchases_per_dollar", "revenue_per_dollar"]].copy()

# -----------------------------
# Simulation function
# -----------------------------
def simulate_shift(shift_pct: float, apply_diminishing_returns: bool) -> dict:
    """
    shift_pct: fraction of TikTok spend moved to Paid Search (0.0–1.0)
    apply_diminishing_returns: if True, reduce Paid Search efficiency as spend increases
    """
    df_sim = df.copy()
    df_sim["sim_purchases"] = df_sim["purchases"].astype(float)
    df_sim["sim_revenue"] = df_sim["revenue"].astype(float)

    # Shift dollars
    tiktok_spend = float(df_sim.loc[df_sim["channel"] == TIKTOK_CUT_FROM, "spend"].values[0])
    shift_amount = tiktok_spend * shift_pct

    df_sim.loc[df_sim["channel"] == TIKTOK_CUT_FROM, "spend"] -= shift_amount
    df_sim.loc[df_sim["channel"] == REALLOCATE_TO, "spend"] += shift_amount

    # Start from baseline efficiencies
    eff = eff_base.copy()

    # Apply diminishing returns ONLY to Paid Search if requested
    if apply_diminishing_returns:
        base_search_spend = float(df.loc[df["channel"] == REALLOCATE_TO, "spend"].values[0])
        new_search_spend = float(df_sim.loc[df_sim["channel"] == REALLOCATE_TO, "spend"].values[0])
        spend_increase_pct = (new_search_spend - base_search_spend) / base_search_spend if base_search_spend > 0 else 0.0

        # Efficiency declines linearly with spend increase (clamped)
        mult = 1.0 - SEARCH_DIMINISH_ALPHA * spend_increase_pct
        mult = max(0.60, min(1.00, mult))  # clamp so we don't get absurd
        eff.loc[REALLOCATE_TO, "purchases_per_dollar"] *= mult
        eff.loc[REALLOCATE_TO, "revenue_per_dollar"] *= mult

    # Recompute purchases/revenue for spend>0 channels using efficiency
    for ch in eff.index:
        spend = float(df_sim.loc[df_sim["channel"] == ch, "spend"].values[0])
        df_sim.loc[df_sim["channel"] == ch, "sim_purchases"] = spend * float(eff.loc[ch, "purchases_per_dollar"])
        df_sim.loc[df_sim["channel"] == ch, "sim_revenue"] = spend * float(eff.loc[ch, "revenue_per_dollar"])

    # Re-apply affiliate commission on simulated revenue
    df_sim.loc[df_sim["channel"] == "Affiliate", "spend"] = df_sim.loc[df_sim["channel"] == "Affiliate", "sim_revenue"] * AFFILIATE_COMMISSION

    # Profit
    df_sim["sim_gross_profit"] = df_sim["sim_revenue"] * GROSS_MARGIN
    df_sim["sim_net_profit"] = df_sim["sim_gross_profit"] - df_sim["spend"]

    sim_profit = float(df_sim["sim_net_profit"].sum())
    return {
        "shift_pct": shift_pct,
        "shift_amount": shift_amount,
        "baseline_profit": baseline_profit,
        "sim_profit": sim_profit,
        "profit_change": sim_profit - baseline_profit,
    }

# -----------------------------
# Run sweep
# -----------------------------
shift_pcts = [0.00, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50]

rows_no_dr = [simulate_shift(p, apply_diminishing_returns=False) for p in shift_pcts]
rows_dr = [simulate_shift(p, apply_diminishing_returns=True) for p in shift_pcts]

res_no_dr = pd.DataFrame(rows_no_dr).rename(columns={
    "sim_profit": "sim_profit_noDR",
    "profit_change": "profit_change_noDR"
})

res_dr = pd.DataFrame(rows_dr).rename(columns={
    "sim_profit": "sim_profit_withDR",
    "profit_change": "profit_change_withDR"
})

# Join on shift_pct (both frames have it)
res = res_no_dr.merge(res_dr[["shift_pct", "sim_profit_withDR", "profit_change_withDR"]], on="shift_pct")

# Format for readability
res["shift_%_of_tiktok_spend"] = (res["shift_pct"] * 100).round(0).astype(int)
res["shift_amount"] = res["shift_amount"].round(2)
res["profit_change_noDR"] = res["profit_change_noDR"].round(2)
res["profit_change_withDR"] = res["profit_change_withDR"].round(2)
res["sim_profit_noDR"] = res["sim_profit_noDR"].round(2)
res["sim_profit_withDR"] = res["sim_profit_withDR"].round(2)

res = res[[
    "shift_%_of_tiktok_spend",
    "shift_amount",
    "profit_change_noDR",
    "profit_change_withDR",
    "sim_profit_noDR",
    "sim_profit_withDR"
]]

print("\n=== Sensitivity Results (TikTok -> Paid Search) ===")
print(res.to_string(index=False))

# Save results
out_csv = project_root / "data" / "budget_sensitivity_results.csv"
res.to_csv(out_csv, index=False)
print(f"\nSaved results CSV: {out_csv}")

# Plot
plt.figure()
plt.plot(res["shift_%_of_tiktok_spend"], res["profit_change_noDR"], marker="o")
plt.plot(res["shift_%_of_tiktok_spend"], res["profit_change_withDR"], marker="o")
plt.xlabel("Shift % of TikTok Spend to Paid Search")
plt.ylabel("Profit Change vs Baseline ($)")
plt.title("Profit Impact of Reallocating TikTok Spend to Paid Search")
plt.axhline(0)
plt.legend(["No diminishing returns", "With diminishing returns"])

out_png = project_root / "dashboard" / "profit_sensitivity.png"
plt.savefig(out_png, bbox_inches="tight", dpi=200)
print(f"Saved chart: {out_png}")

# -----------------------------
# TikTok Efficiency Improvement Scenario
# -----------------------------

def simulate_tiktok_improvement(cac_improvement_pct):
    """
    cac_improvement_pct: e.g., 0.10 means CAC improves by 10%
    """
    df_sim = df.copy()
    df_sim["sim_revenue"] = df_sim["revenue"].astype(float)
    df_sim["sim_spend"] = df_sim["spend"].astype(float)

    # Improve TikTok efficiency by reducing spend required per revenue
    # We simulate by reducing spend proportionally
    df_sim.loc[df_sim["channel"] == "TikTok", "sim_spend"] *= (1 - cac_improvement_pct)

    # Recompute affiliate commission
    df_sim.loc[df_sim["channel"] == "Affiliate", "sim_spend"] = (
        df_sim.loc[df_sim["channel"] == "Affiliate", "sim_revenue"] * AFFILIATE_COMMISSION
    )

    df_sim["sim_gross_profit"] = df_sim["sim_revenue"] * GROSS_MARGIN
    df_sim["sim_net_profit"] = df_sim["sim_gross_profit"] - df_sim["sim_spend"]

    return df_sim["sim_net_profit"].sum()

print("\n=== TikTok Efficiency Improvement Scenario ===")

# Collect TikTok improvement results
improvement_rows = []

for pct in [0.05, 0.10, 0.15, 0.20]:
    sim_profit = simulate_tiktok_improvement(pct)
    improvement_rows.append({
        "cac_improvement_pct": int(pct * 100),
        "profit_change": sim_profit - baseline_profit
    })

improvement_df = pd.DataFrame(improvement_rows)

out_path = project_root / "data" / "tiktok_improvement_scenario.csv"
improvement_df.to_csv(out_path, index=False)

print(f"Saved TikTok improvement CSV: {out_path}")
