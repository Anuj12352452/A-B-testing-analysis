# A/B Testing — Checkout Page Conversion Study

I've been learning data science for the past few months and wanted to do something more realistic than the usual toy datasets. This project came out of a question I kept thinking about: how do companies actually decide whether to ship a new feature or roll it back?

The answer, at least for product teams that care about doing it properly, is a controlled experiment. So I built one from scratch using real experiment data.

---

## What I was trying to answer

A company redesigned their checkout page. The new version looked cleaner and they thought it would convert better. But "looks better" isn't good enough when you have 2 million monthly users. I wanted to know: is there actual statistical evidence of improvement, or is the difference just random noise?

---

## What I found

Short version: the new design showed a tiny improvement (12.00% vs 11.94% conversion rate) but the result wasn't statistically significant. P-value came out at 0.625, which is nowhere near the 0.05 threshold. The Bayesian analysis agreed — 68.8% probability that treatment beats control, which sounds reasonable until you realise we need 95% before making a shipping decision.

So I recommended not shipping it. Which felt a bit anticlimactic, but that's actually the point. Knowing when NOT to ship is just as valuable as knowing when to ship.

| What I measured | Result |
|---|---|
| Users in the experiment | 294,478 |
| Control conversion rate | 11.94% |
| New design conversion rate | 12.00% |
| Difference | +0.06 percentage points |
| Relative change | +0.49% |
| Z-statistic | 0.4883 |
| P-value | 0.6254 |
| 95% confidence interval | −0.18% to +0.29% |
| Bayesian probability (treatment wins) | 68.8% |
| Final call | Don't ship |

---

## The bit most analyses skip

I've seen a lot of A/B test notebooks online that just run a t-test and call it done. I wanted mine to be more honest about the process, so I added a few extra steps:

**Checking for contamination first.** Before touching any statistics, I checked whether any users appeared in both the control and treatment groups. If they do, the experiment is invalid. Zero contaminated users here — good start.

**Sample ratio mismatch.** The split was supposed to be 50/50. If it's not, the randomisation is broken and you can't trust the results. It was exactly 50/50 in this case (147,239 each).

**Power analysis.** This is the one people forget. I worked out how many users we needed before interpreting the result. We needed 144,740 per group and got 147,239. So the experiment was fully powered — which means the null result is real, not just a consequence of not having enough data.

**Novelty effect.** New designs sometimes get a temporary boost because users are curious. I checked whether the conversion gap was higher in week 1 than week 8. It wasn't — the pattern was stable throughout.

**Segmentation.** The overall result was flat, but mobile users showed +0.61% lift. That's the most actionable finding in the whole project — I'd use it to design a follow-up test focused specifically on mobile.

**Bayesian alongside frequentist.** The p-value tells you whether the result is statistically significant under the null hypothesis. The Bayesian result gives you a probability that treatment is genuinely better. Both pointed the same direction here, which is reassuring.

---

## Tools I used

| Tool | What for |
|---|---|
| Python (pandas, numpy, scipy) | Data processing and statistical tests |
| matplotlib, seaborn | Charts |
| PostgreSQL + 12 SQL queries | Business analysis and data exploration |
| plotly | Interactive HTML dashboard |
| scipy.stats.norm | Z-test, confidence intervals |
| numpy random (Beta distribution) | Bayesian Monte Carlo simulation |

---

## Files

```
ab-testing-analysis/
├── README.md
├── ab_testing_analysis.py        ← main analysis script
├── ab_testing_sql_queries.sql    ← 12 SQL queries
├── ab_testing_dashboard.html     ← open in browser for interactive charts
├── AB_Testing_Analysis_Report.docx
└── outputs/
    └── ab_test_charts.png
```

---

## Running it yourself

```bash
pip install pandas numpy scipy matplotlib seaborn

python ab_testing_analysis.py
```

Dataset is the Udacity A/B Test on Kaggle (free, search "zhangluyuan ab-testing"). Download the CSV and save it as `ab_data.csv` in the same folder.

For the SQL queries, load the data into PostgreSQL first, then run `ab_testing_sql_queries.sql`.

---

## A few things I'd do differently next time

The segmentation finding (mobile +0.61%) came after the fact. Ideally I'd have pre-registered mobile as a secondary metric before the experiment started. Running subgroup analysis without pre-registration is fine for hypothesis generation, but you can't use it as a confirmatory result — the false positive rate goes up when you test multiple segments.

I'd also set a stopping rule upfront. This experiment ran for 205 days, which is long. In practice you'd want to define in advance: "we stop at X users or Y days, whichever comes first." Peeking at results and stopping early when things look good inflates false positives.

---

## What I'd do next

Run a mobile-specific experiment. Mobile is 62% of traffic and showed the strongest positive signal. A dedicated test would need around 580,000 mobile users and could be powered in 4–6 weeks. That's a concrete next step rather than just "do more tests."

---

Dataset credit: Udacity A/B Test via Kaggle (CC0 public domain)
