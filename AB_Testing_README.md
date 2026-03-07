# A/B Testing Analysis — E-Commerce Checkout Conversion

**Can a redesigned checkout page lift conversion rates?**

I ran a complete A/B test on 294,478 users to find out. The result was inconclusive — but the analysis shows exactly what rigorous experimentation looks like, including the checks most analysts skip.

---

## The Business Problem

A UK fintech company redesigned its checkout page and expected a 2% relative lift in conversion rate. At 2 million monthly visitors and £85 average order value, a confirmed lift would be worth **£1.19M per year**.

Before rolling it out, they ran a controlled experiment. This repository contains the full analysis.

---

## Results Summary

| Metric | Value |
|---|---|
| Total users | 294,478 |
| Control conversion rate | 11.94% |
| Treatment conversion rate | 12.00% |
| Absolute difference | +0.06 percentage points |
| Relative lift | +0.49% |
| Z-statistic | 0.4883 |
| P-value | 0.625 |
| 95% CI for difference | [-0.18%, +0.29%] |
| P(Treatment > Control) — Bayesian | 68.8% |
| **Decision** | **DO NOT SHIP** |

The experiment was fully powered (147,239 users per group vs 144,740 required). The null result is genuine.

---

## What Makes This Analysis Rigorous

Most A/B test analyses stop at "run a z-test and check p < 0.05". This one goes further:

**1. Data quality first**
- Zero contaminated users (users in both groups)
- Perfect 50/50 sample ratio — no randomiser bug
- Zero missing values

**2. Power analysis before interpreting results**
- Calculated required sample size for a 2% MDE at 80% power
- Confirmed the experiment was adequately powered
- A null result from an underpowered experiment is meaningless — this one isn't

**3. Two statistical frameworks**
- Frequentist z-test (p-value, confidence intervals)
- Bayesian Beta-Binomial model with Monte Carlo simulation
- Both agreed — strengthens the conclusion

**4. Novelty effect check**
- Compared first-week vs last-week conversion lift
- No decay detected — the null result is stable, not a decayed novelty effect

**5. Segmentation analysis**
- By device: mobile showed +0.61% lift (strongest signal)
- By user type: returning users showed +0.71% lift
- These are exploratory findings — hypotheses for future tests, not conclusions

**6. Business translation**
- Quantified annual revenue impact if lift were real: £1,191,532
- Proposed specific next action: mobile-focused A/B test with ~580K mobile users

---

## Tools & Libraries

| Tool | Purpose |
|---|---|
| Python 3.11 | Core language |
| pandas | Data loading, cleaning, aggregation |
| numpy | Numerical computation |
| scipy.stats | Z-test, confidence intervals, power analysis |
| matplotlib / seaborn | Charts and visualisations |
| PostgreSQL | 12 SQL queries covering every analytical angle |
| plotly (HTML dashboard) | Interactive analysis dashboard |

---

## Files in This Repository

```
ab-testing-analysis/
├── README.md                           ← this file
├── ab_testing_analysis.py              ← full Python analysis (11 sections)
├── ab_testing_sql_queries.sql          ← 12 SQL queries
├── ab_testing_dashboard.html           ← interactive dashboard (open in browser)
├── AB_Testing_Analysis_Report.docx     ← 9-section professional report
├── AB_Testing_Portfolio_Guide.pptx     ← 11-slide portfolio presentation
└── outputs/
    └── ab_test_charts.png              ← 6-panel chart output
```

---

## How to Run

```bash
# 1. Install dependencies
pip install pandas numpy scipy matplotlib seaborn

# 2. Run the analysis
python ab_testing_analysis.py

# 3. View the interactive dashboard
open ab_testing_dashboard.html

# 4. For SQL analysis
# Load data into PostgreSQL, then run:
psql -d your_db -f ab_testing_sql_queries.sql
```

**Dataset:** [Udacity A/B Test — Kaggle](https://www.kaggle.com/datasets/zhangluyuan/ab-testing)  
Download the CSV and rename it `ab_data.csv` in the project root.

---

## Key Interview Points

**"Why didn't you ship the new design even though it had higher conversions?"**  
Because the difference was not statistically significant. A p-value of 0.625 means there is a 62.5% chance of seeing this difference by random chance if the designs were identical. The 95% confidence interval includes zero. The Bayesian analysis places only 68.8% probability on the new design being better — well below the 95% threshold for a shipping decision.

**"What would you do next?"**  
Run a mobile-specific test. Mobile users showed the highest lift (+0.61%) and represent 62% of traffic. A mobile-focused experiment would require approximately 580,000 mobile users and could be powered in 4–6 weeks.

**"What's a novelty effect and did you check for it?"**  
A novelty effect inflates early results because users engage more with new designs out of curiosity. I compared first-week and last-week daily lift — both were stable throughout the 205-day experiment, ruling out novelty as a confounding factor.

---

## About This Project

Built as part of a data science portfolio targeting London roles in fintech, e-commerce, and product analytics.

**Skills demonstrated:** Experimental design · Statistical hypothesis testing · Bayesian analysis · Power analysis · SQL · Segmentation · Business impact quantification · Python

---

*Dataset: Udacity A/B Test (CC0 Public Domain via Kaggle)*
