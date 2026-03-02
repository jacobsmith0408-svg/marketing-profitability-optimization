Multi-Channel Marketing Profitability & Optimization
1. Business Problem
A direct-to-consumer fitness apparel brand wants to evaluate the profitability of its marketing channels and determine whether reallocating budget or improving channel efficiency would have a greater impact on net profit.
Specifically:
	•	Are paid acquisition channels profitable on first purchase?
	•	Which channels exceed break-even CAC thresholds?
	•	Does reallocating budget improve profitability?
	•	Is performance optimization a higher-leverage strategy?

2. Data
	•	365-day synthetic multi-channel marketing dataset
	•	Channels: Paid Search, Paid Social, TikTok, Affiliate, Email
	•	Metrics: Impressions, Clicks, Sessions, Purchases, Revenue, Ad Spend
	•	Customer segments: New vs Returning
The dataset was intentionally generated to simulate realistic DTC marketing dynamics while allowing controlled margin and efficiency assumptions.

3. Assumptions
	•	Average Order Value ≈ $90
	•	Gross Margin = 60%
	•	Break-even CAC = AOV × Margin = $54
	•	Affiliate modeled at 12% revenue commission
	•	Paid Search subject to diminishing returns when scaled
These assumptions were made explicit to isolate economic decision-making logic.

4. Methodology
SQL
	•	Aggregated channel-level performance
	•	Calculated new CAC by channel
	•	Modeled revenue and spend distributions
Python
	•	Calculated margin-adjusted net profit
	•	Simulated budget reallocation from TikTok → Paid Search
	•	Modeled diminishing returns on scaled channels
	•	Built CAC improvement scenarios for TikTok
	•	Ran sensitivity analysis across multiple allocation percentages
Tableau
	•	Built executive dashboard visualizing:
	◦	Channel net profit contribution
	◦	New CAC vs break-even threshold
	◦	Reallocation sensitivity curve
	◦	CAC optimization impact

5. Key Findings
	1	Paid acquisition channels were slightly negative on first-order profitability.
	2	TikTok CAC significantly exceeded the $54 break-even threshold.
	3	Reallocating 15–20% of TikTok spend improved profit modestly (~$3K annually).
	4	Improving TikTok CAC by 10% increased annual profit by ~$84K.
	5	Performance optimization offered materially greater upside than capital reallocation.

6. Strategic Recommendation
Moderate budget reallocation can reduce marginal losses, but the highest-leverage strategy is improving underperforming channel efficiency.
Prioritizing creative and targeting optimization within TikTok offers substantially greater profit impact than shifting spend across channels.

7. Future Improvements
	•	Incorporate customer lifetime value modeling
	•	Analyze cohort-level retention by acquisition channel
	•	Model time-to-second-purchase dynamics
	•	Stress test margin scenarios (50–70%)
