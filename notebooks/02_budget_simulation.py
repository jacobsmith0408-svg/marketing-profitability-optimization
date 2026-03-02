import pandas as pd
import sqlite3
from pathlib import Path

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

GROSS_MARGIN = 0.60
AFFILIATE_COMMISSION = 0.12  # 12% of revenue (more realistic than CPC spend)

# Fix affiliate spend to commission model
df.loc[df["channel"] == "Affiliate", "spend"] = (
    df.loc[df["channel"] == "Affiliate", "revenue"] * AFFILIATE_COMMISSION
)

# Compute baseline profits
df["gross_profit"] = df["revenue"] * GROSS_MARGIN
df["net_profit"] = df["gross_profit"] - df["spend"]

print("=== Baseline (with affiliate commission model) ===")
print(df.sort_values("net_profit", ascending=False)[["channel", "spend", "purchases", "revenue", "net_profit"]])

baseline_profit = df["net_profit"].sum()

# Only simulate paid channels with spend > 0
paid = df[df["spend"] > 0].copy()

paid["purchases_per_dollar"] = paid["purchases"] / paid["spend"]
paid["revenue_per_dollar"] = paid["revenue"] / paid["spend"]

# Scenario: cut TikTok spend 25%, move to Paid Search
df_sim = df.copy()

tiktok_spend = float(df_sim.loc[df_sim["channel"] == "TikTok", "spend"].values[0])
shift_amount = tiktok_spend * 0.25

df_sim.loc[df_sim["channel"] == "TikTok", "spend"] -= shift_amount
df_sim.loc[df_sim["channel"] == "Paid Search", "spend"] += shift_amount

# Keep Email fixed (spend=0, and we are not scaling it)
# Recompute simulated purchases/revenue only for channels with spend > 0, using baseline efficiency
eff = paid.set_index("channel")[["purchases_per_dollar", "revenue_per_dollar"]]

df_sim["sim_purchases"] = df_sim["purchases"]
df_sim["sim_revenue"] = df_sim["revenue"]

for ch in eff.index:
    spend = float(df_sim.loc[df_sim["channel"] == ch, "spend"].values[0])
    df_sim.loc[df_sim["channel"] == ch, "sim_purchases"] = spend * float(eff.loc[ch, "purchases_per_dollar"])
    df_sim.loc[df_sim["channel"] == ch, "sim_revenue"] = spend * float(eff.loc[ch, "revenue_per_dollar"])

# Apply affiliate commission again under simulated revenue
df_sim.loc[df_sim["channel"] == "Affiliate", "spend"] = df_sim.loc[df_sim["channel"] == "Affiliate", "sim_revenue"] * AFFILIATE_COMMISSION

df_sim["sim_gross_profit"] = df_sim["sim_revenue"] * GROSS_MARGIN
df_sim["sim_net_profit"] = df_sim["sim_gross_profit"] - df_sim["spend"]

sim_profit = df_sim["sim_net_profit"].sum()

print("\n=== Simulated Scenario (cut TikTok 25%, shift to Search) ===")
print(df_sim.sort_values("sim_net_profit", ascending=False)[["channel", "spend", "sim_purchases", "sim_revenue", "sim_net_profit"]])

print("\n=== Portfolio Impact ===")
print(f"Baseline Net Profit: {baseline_profit:,.2f}")
print(f"Simulated Net Profit: {sim_profit:,.2f}")
print(f"Change in Profit: {(sim_profit - baseline_profit):,.2f}")