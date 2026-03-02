import pandas as pd
import sqlite3
from pathlib import Path

# Paths
project_root = Path(__file__).resolve().parents[1]
csv_path = project_root / "data" / "marketing_campaign_daily.csv"
db_path = project_root / "data" / "marketing.db"

# Load CSV
df = pd.read_csv(csv_path)

# Write to SQLite
conn = sqlite3.connect(db_path)
df.to_sql("campaign_daily", conn, if_exists="replace", index=False)

# Basic indexes (optional but nice)
cur = conn.cursor()
cur.execute("CREATE INDEX IF NOT EXISTS idx_date ON campaign_daily(date);")
cur.execute("CREATE INDEX IF NOT EXISTS idx_channel ON campaign_daily(channel);")
cur.execute("CREATE INDEX IF NOT EXISTS idx_segment ON campaign_daily(segment);")
conn.commit()

# Quick row check
rows = cur.execute("SELECT COUNT(*) FROM campaign_daily;").fetchone()[0]
print("Saved SQLite DB:", db_path)
print("Rows in campaign_daily:", rows)

conn.close()