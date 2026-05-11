# Success Metrics – Supplier Risk Intelligence System

**Purpose:** Define objective, measurable KPIs to evaluate whether the system detects supplier degradation early, accurately, and without excessive false alarms.  
**Audience:** Data team (you), Procurement Manager, CFO, Quality Assurance.  
**Computation:** Automated via scheduled dbt models and Python scripts. Results stored in `metrics.metrics_daily` table and shown in Maintainer Dashboard.

---

## 1. Detection Lag (Primary Business KPI)

**Definition:** Number of days between a supplier’s *true* performance degradation (as defined by a statistically significant drop in on‑time rate) and the system’s first alert.

**Why it matters:** This is the core value proposition. Every day of earlier warning allows procurement to mitigate shortage costs.

### Formula
Detection Lag = Alert_Date - Degradation_Start_Date


where:
- `Degradation_Start_Date` = the first date when a supplier’s 14‑day rolling on‑time rate fell below its historical baseline by more than 2 standard deviations (calculated retrospectively using the last 90 days of data before that date).
- `Alert_Date` = the date the system generated an alert (EWMA violation or critical cluster transition).

### Target

| Category | Target |
|----------|--------|
| Excellent | `≤ 7 days` |
| Acceptable | `8–14 days` |
| Poor | `> 14 days` |

### Computation (Python, run weekly)

```python
# pseudo‑code
degradation_start = first_date_where (rolling_14d_ontime < (historical_mean - 2*historical_std))
alert_date = min(date from alerts table where supplier_id = x and alert_type in ('EWMA', 'cluster_transition'))
lag_days = (alert_date - degradation_start).days
Result stored in: metrics.detection_lag (aggregated median, p90 per month).'''



## 2. False Positive Rate (FPR)
Definition: Proportion of alerts that are not followed by a true supplier degradation within the next 14 days. In other words, alerts that cried wolf.

Formula
text
FPR = (False_Positives) / (True_Positives + False_Positives)
where:

True Positive = Alert issued, and within 14 days the supplier’s rolling on‑time rate dropped below baseline by ≥2 standard deviations (or actual failure occurred).

False Positive = Alert issued, but no such degradation occurred in the next 14 days.

Target
Business tolerance	Maximum FPR
Low (automotive critical parts)	< 20%
Medium (non‑critical)	< 35%
Maintenance mode	< 40%
The system’s default EWMA control limits (L=3) aim for FPR ~5% under normal conditions. However, real‑world data may increase this.

Computation
Run weekly: join alerts table with actual degradation flags (computed retrospectively).

sql
WITH alert_windows AS (
  SELECT 
    a.supplier_id,
    a.alert_date,
    EXISTS (
      SELECT 1 FROM degradation_ground_truth d
      WHERE d.supplier_id = a.supplier_id
        AND d.degradation_start_date BETWEEN a.alert_date AND a.alert_date + 14
    ) AS had_degradation_within_14d
  FROM alerts a
)
SELECT 
  1 - AVG(had_degradation_within_14d::int) AS false_positive_rate
FROM alert_windows;
Stored in: metrics.fpr_rolling_30d




## 3. False Negative Rate (Miss Rate)
Definition: Proportion of actual degradation events that the system failed to alert on within 7 days of the degradation start.

Formula
text
FNR = Missed_Events / Total_Actual_Degradation_Events
Target
< 10% (i.e., catch at least 90% of real degradations).

Computation
Similar to FPR, but from the degradation perspective:

sql
WITH degradation_events AS (
  SELECT supplier_id, degradation_start_date
  FROM ground_truth_degradation
)
SELECT 
  COUNT(CASE WHEN a.alert_date IS NULL OR a.alert_date > d.degradation_start_date + 7 THEN 1 END)::float
  / COUNT(*) AS false_negative_rate
FROM degradation_events d
LEFT JOIN alerts a ON d.supplier_id = a.supplier_id 
  AND a.alert_date BETWEEN d.degradation_start_date AND d.degradation_start_date + 7



## 4. Precision & Recall (for Cluster Transitions)
Definition: When the system flags a supplier moving into the “Critical” cluster (Cluster 4), how often is that move justified?

Precision = TP / (TP + FP) – of all critical cluster alerts, how many were correct?

Recall = TP / (TP + FN) – of all real critical suppliers, how many did we catch?

Targets
Metric	Target
Precision	> 70%
Recall	> 85%
Computation
Use ground truth defined by actual failure or severe degradation (e.g., 3 consecutive weeks of OTR < 80%). Compare to cluster assignment history.

Stored in: metrics.cluster_transition_performance (monthly).


## 5. Average Lead Time Variance Reduction
Definition: For suppliers flagged as “high risk” (Cluster 3 or 4), we recommend renegotiating lead times or increasing safety stock. This metric measures the reduction in lead time variance (in days) after intervention.

Formula: Variance_before - Variance_after for the 60‑day windows before and after the first alert.

Target
> 2 days reduction in standard deviation of lead time.

This metric requires client action; the system only reports it. If no improvement, the alert logic may need tightening (your maintenance value).




## 6. Financial Impact Realised (Cumulative)
Definition: Sum of avoided shortage costs attributed to the system’s early warnings.

Formula (simplified):

text
Avoided_Cost = Σ over all alerts (Probability_of_failure * Cost_per_failure - implemented_mitigation_cost)
Only computed when client provides actual failure cost data. Otherwise, the system outputs "insufficient data".

Target
Positive ROI: Avoided_Cost / (System operational cost + your maintenance fees) > 2x.




## 7. Model Stability (Technical KPI)
Definition: How much do cluster assignments change when retraining the GMM on slightly different data (e.g., one week apart)? Measured by Adjusted Rand Index (ARI) between clusterings.

Formula
text
ARI = adjusted_rand_score(clusters_week1, clusters_week2)
Target
ARI > 0.8 → clusters are stable. If ARI drops below 0.6, the model may need parameter adjustment (by you).

Automatically computed after each retraining.




## 8. Data Freshness & Pipeline Health
Metric	Definition	Alert threshold	Action
Max days since last delivery record	CURRENT_DATE - MAX(delivery_date)	> 2 days	Email to maintainer & client
dbt run success rate (last 7 runs)	% of runs with exit code 0	< 90%	Reviewed weekly
n8n workflow failure count	number of failed executions in 7 days	> 1	Immediate investigation
Great Expectations validation pass rate	% of expectations met	< 95%	Trigger data quality review
All these are collected in metrics.system_health_daily.




##  9. How Metrics Are Displayed
Procurement Dashboard: Simplified versions (lag, FPR, missed degradations) with green/yellow/red indicators.

Maintainer Dashboard (you only): Full detail – ARI, precision/recall, FPR breakdown by supplier type, cost avoidance estimates.

Weekly PDF Report: Executive summary of key metrics plus trend charts.




## 10. Responsibility & Review Cadence
Metric	Owner	Review frequency
Detection lag, FPR, FNR	System (automated)	Weekly
Precision/Recall	You (maintainer)	Monthly
Model stability (ARI)	You	After each retraining
Financial impact	Client (with your assistance)	Quarterly
System health	n8n alerts + you	Daily monitor
If any metric falls outside its target range for two consecutive weeks, the system automatically creates a ticket in the maintainer’s issue tracker (e.g., GitHub issue) for your review.

Appendix – SQL View for Dashboard

sql
CREATE OR REPLACE VIEW metrics.dashboard_kpis AS
SELECT 
  (SELECT AVG(detection_lag_days) FROM metrics.detection_lag WHERE date > NOW() - INTERVAL '30 days') AS avg_detection_lag,
  (SELECT AVG(false_positive_rate) FROM metrics.fpr_rolling_30d) AS fpr,
  (SELECT AVG(ari) FROM metrics.model_stability WHERE retraining_date > NOW() - INTERVAL '90 days') AS model_stability_ari,
  (SELECT MAX(days_since_last_delivery) FROM metrics.data_freshness) AS data_freshness_days;
This view is what the Evidence dashboard queries. All numbers are recalculated daily.

text

This document gives you and the client a **contract for success** – no vague “improves efficiency”, but concrete, measurable, and automated KPIs.
