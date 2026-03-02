import numpy as np
import pandas as pd
from datetime import datetime

# -----------------------------
# Synthetic marketing dataset
# DTC fitness apparel brand
# Daily x Channel x Segment
# 12 months (2025)
# -----------------------------

np.random.seed(42)

start_date = "2025-01-01"
end_date   = "2025-12-31"
dates = pd.date_range(start=start_date, end=end_date, freq="D")

channels = ["Paid Search", "Paid Social", "TikTok", "Email", "Affiliate"]
segments = ["New", "Returning"]

# Baseline behavior by channel (roughly realistic)
channel_params = {
    "Paid Search":  {"base_impr": 180000, "ctr": 0.020, "sess_from_click": 0.92, "cvr": 0.030, "cpc": 1.60, "aov": 92},
    "Paid Social":  {"base_impr": 260000, "ctr": 0.012, "sess_from_click": 0.88, "cvr": 0.020, "cpc": 1.05, "aov": 88},
    "TikTok":       {"base_impr": 320000, "ctr": 0.010, "sess_from_click": 0.86, "cvr": 0.012, "cpc": 0.70, "aov": 80},
    "Email":        {"base_impr":  35000, "ctr": 0.060, "sess_from_click": 0.95, "cvr": 0.055, "cpc": 0.00, "aov": 96},
    "Affiliate":    {"base_impr":  60000, "ctr": 0.018, "sess_from_click": 0.90, "cvr": 0.028, "cpc": 0.15, "aov": 90},
}

# Segment modifiers by channel: returning customers convert better, often higher AOV
segment_mod = {
    ("New", "Paid Search"):      {"cvr_mult": 0.95, "aov_mult": 0.98},
    ("Returning", "Paid Search"):{"cvr_mult": 1.20, "aov_mult": 1.05},

    ("New", "Paid Social"):      {"cvr_mult": 0.90, "aov_mult": 0.97},
    ("Returning", "Paid Social"):{"cvr_mult": 1.25, "aov_mult": 1.05},

    ("New", "TikTok"):           {"cvr_mult": 0.85, "aov_mult": 0.95},
    ("Returning", "TikTok"):     {"cvr_mult": 1.15, "aov_mult": 1.03},

    ("New", "Email"):            {"cvr_mult": 0.80, "aov_mult": 0.98},
    ("Returning", "Email"):      {"cvr_mult": 1.35, "aov_mult": 1.08},

    ("New", "Affiliate"):        {"cvr_mult": 0.92, "aov_mult": 0.98},
    ("Returning", "Affiliate"):  {"cvr_mult": 1.18, "aov_mult": 1.05},
}

# Promo calendar (discount_rate) — realistic spikes
# You can tweak later, but this is a good starting point.
promo_weeks = []
promo_weeks += list(pd.date_range("2025-01-01", "2025-01-07"))  # New Year sale
promo_weeks += list(pd.date_range("2025-05-23", "2025-05-27"))  # Memorial Day
promo_weeks += list(pd.date_range("2025-07-02", "2025-07-06"))  # July 4
promo_weeks += list(pd.date_range("2025-11-24", "2025-12-01"))  # Black Friday/Cyber Monday
promo_weeks += list(pd.date_range("2025-12-18", "2025-12-26"))  # Holiday push

promo_weeks = set(promo_weeks)

def seasonality_factor(d: pd.Timestamp) -> float:
    """
    Seasonality for fitness apparel:
    - Jan high (resolutions)
    - spring solid
    - summer slight dip
    - Nov/Dec strong (holidays)
    """
    m = d.month
    if m == 1:   return 1.25
    if m in [2, 3, 4]: return 1.05
    if m in [5, 6]: return 1.00
    if m in [7, 8]: return 0.90
    if m in [9, 10]: return 1.00
    if m == 11: return 1.15
    if m == 12: return 1.20
    return 1.00

def promo_discount(d: pd.Timestamp) -> float:
    if d in promo_weeks:
        # promo weeks typically 15–35% off
        return np.clip(np.random.normal(0.25, 0.06), 0.12, 0.40)
    return 0.0

rows = []
campaign_counter = 1000

for d in dates:
    seas = seasonality_factor(d)
    disc = promo_discount(d)

    # Promo boosts CTR/CVR but can lower AOV a bit (discount)
    promo_ctr_boost = 1.00 + (0.10 if disc > 0 else 0.00)
    promo_cvr_boost = 1.00 + (0.18 if disc > 0 else 0.00)
    promo_aov_mult  = 1.00 - disc * 0.55  # discount reduces realized AOV

    # Diminishing returns proxy: on very high-volume days, efficiency slips a bit
    # We'll simulate "fatigue" by noise, not actual spend curves yet.
    day_noise = np.random.normal(1.0, 0.05)

    for ch in channels:
        p = channel_params[ch]

        # impressions vary day-to-day and with seasonality
        impr = int(max(0, np.random.normal(p["base_impr"] * seas * day_noise, p["base_impr"] * 0.10)))

        for seg in segments:
            mod = segment_mod[(seg, ch)]

            # Split impressions between segments (new usually larger share on paid, returning larger on email)
            if ch == "Email":
                seg_share = 0.25 if seg == "New" else 0.75
            elif ch in ["Paid Search", "Paid Social", "TikTok"]:
                seg_share = 0.70 if seg == "New" else 0.30
            else:  # Affiliate
                seg_share = 0.60 if seg == "New" else 0.40

            seg_impr = int(impr * seg_share)

            # CTR, sessions, CVR
            ctr = np.clip(np.random.normal(p["ctr"] * promo_ctr_boost, p["ctr"] * 0.12), 0.001, 0.20)
            clicks = int(seg_impr * ctr)

            sess_rate = np.clip(np.random.normal(p["sess_from_click"], 0.03), 0.70, 1.00)
            sessions = int(clicks * sess_rate)

            cvr = np.clip(np.random.normal(p["cvr"] * mod["cvr_mult"] * promo_cvr_boost, p["cvr"] * 0.18), 0.001, 0.25)
            purchases = int(sessions * cvr)

            # funnel metric
            atc_rate = np.clip(np.random.normal(0.085 * (1.15 if disc > 0 else 1.0), 0.02), 0.01, 0.25)
            add_to_cart = int(sessions * atc_rate)

            # AOV
            aov = np.clip(np.random.normal(p["aov"] * mod["aov_mult"] * promo_aov_mult, 10), 35, 220)

            revenue = purchases * aov

            # Spend: CPC-based for paid channels; Email $0; Affiliate low paid + later we can model commission
            cpc = max(0.0, np.random.normal(p["cpc"], p["cpc"] * 0.10))
            ad_spend = clicks * cpc

            # Give each channel/day a few "campaigns" feel via a simple ID pattern
            campaign_id = f"C{campaign_counter + (hash((str(d.date()), ch)) % 7):05d}"

            rows.append({
                "date": d.date().isoformat(),
                "campaign_id": campaign_id,
                "channel": ch,
                "segment": seg,
                "discount_rate": round(float(disc), 4),
                "impressions": seg_impr,
                "clicks": clicks,
                "sessions": sessions,
                "add_to_cart": add_to_cart,
                "purchases": purchases,
                "ad_spend": round(float(ad_spend), 2),
                "aov": round(float(aov), 2),
                "revenue": round(float(revenue), 2),
            })

    campaign_counter += 10

df = pd.DataFrame(rows)

# Sanity checks (simple)
df["ctr"] = np.where(df["impressions"] > 0, df["clicks"] / df["impressions"], 0)
df["cvr"] = np.where(df["sessions"] > 0, df["purchases"] / df["sessions"], 0)
df["roas"] = np.where(df["ad_spend"] > 0, df["revenue"] / df["ad_spend"], np.nan)

# Save
out_path = "../data/marketing_campaign_daily.csv"
df.to_csv(out_path, index=False)

print("Saved:", out_path)
print("Rows:", len(df))
print(df.head(10))
print("\nQuick KPI ranges:")
print(df[["ctr", "cvr", "roas"]].describe())