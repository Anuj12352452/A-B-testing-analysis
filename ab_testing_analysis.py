"""
A/B Testing Analysis — E-Commerce Checkout Conversion
======================================================
Dataset : Udacity A/B Test (294,478 page visits)
Scenario: UK fintech tests a redesigned checkout page
Goal    : Decide statistically whether the new design lifts conversions

Sections
--------
1.  Load & Validate Experiment Data
2.  Data Quality Checks
3.  Baseline Metrics
4.  Two-Proportion Z-Test (Frequentist)
5.  Power Analysis & Sample Size Calculation
6.  Confidence Intervals
7.  Segmentation Analysis (new vs returning users)
8.  Novelty Effect Check
9.  Bayesian A/B Test
10. Decision Framework
11. Business Impact Quantification
"""

# ── 0. IMPORTS ────────────────────────────────────────────────────────────────
import pandas as pd
import numpy as np
from scipy import stats
from scipy.stats import norm
import matplotlib
matplotlib.use("Agg")  # non-interactive backend (safe for all environments)
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import warnings
warnings.filterwarnings("ignore")

# Colour palette
TEAL   = "#0D9488"
NAVY   = "#0F172A"
AMBER  = "#D97706"
RED    = "#DC2626"
GREEN  = "#16A34A"
PURPLE = "#7C3AED"
SLATE  = "#64748B"

print("=" * 65)
print("  A/B TESTING ANALYSIS — E-COMMERCE CHECKOUT CONVERSION")
print("=" * 65)

# ── 1. LOAD & VALIDATE ────────────────────────────────────────────────────────
print("\n[1] LOADING & VALIDATING EXPERIMENT DATA")
print("-" * 45)

# Simulate the Udacity A/B dataset with realistic parameters
# (download real file: kaggle.com/datasets/zhangluyuan/ab-testing)
np.random.seed(42)
n_control   = 147_239
n_treatment = 147_239

control_rate   = 0.1203   # 12.03% baseline conversion
treatment_rate = 0.1188   # 11.88% new design (slightly worse — realistic)

control_converted   = np.random.binomial(1, control_rate,   n_control)
treatment_converted = np.random.binomial(1, treatment_rate, n_treatment)

df = pd.DataFrame({
    "user_id":   range(1, n_control + n_treatment + 1),
    "timestamp": pd.date_range("2024-01-01", periods=n_control + n_treatment, freq="1min"),
    "group":     (["control"] * n_control) + (["treatment"] * n_treatment),
    "converted": list(control_converted) + list(treatment_converted),
    "new_user":  np.random.choice([0, 1], size=n_control + n_treatment, p=[0.45, 0.55]),
    "device":    np.random.choice(["mobile", "desktop", "tablet"],
                                  size=n_control + n_treatment, p=[0.62, 0.31, 0.07]),
})

print(f"Total rows        : {len(df):,}")
print(f"Date range        : {df.timestamp.min().date()} → {df.timestamp.max().date()}")
print(f"Groups            : {df.group.unique().tolist()}")
print(f"Converted values  : {sorted(df.converted.unique().tolist())}")

# ── 2. DATA QUALITY ───────────────────────────────────────────────────────────
print("\n[2] DATA QUALITY CHECKS")
print("-" * 45)

# Check for duplicate users
dupes = df.groupby("user_id")["group"].nunique()
contaminated = (dupes > 1).sum()
print(f"Duplicate user IDs      : {df.user_id.duplicated().sum()}")
print(f"Users in both groups    : {contaminated}  {'✓ Clean' if contaminated == 0 else '⚠ Remove!'}")

# Group sizes
group_sizes = df.groupby("group").size()
print(f"\nControl size            : {group_sizes['control']:,}")
print(f"Treatment size          : {group_sizes['treatment']:,}")
balance_ratio = group_sizes.min() / group_sizes.max()
print(f"Balance ratio           : {balance_ratio:.3f}  {'✓ Balanced' if balance_ratio > 0.95 else '⚠ Imbalanced'}")

# Missing values
print(f"Missing values          : {df.isnull().sum().sum()}")

# ── 3. BASELINE METRICS ───────────────────────────────────────────────────────
print("\n[3] BASELINE METRICS")
print("-" * 45)

summary = df.groupby("group")["converted"].agg(
    users="count",
    conversions="sum",
    conversion_rate="mean"
).reset_index()
summary["conversion_rate_pct"] = (summary["conversion_rate"] * 100).round(4)

print(summary.to_string(index=False))

cr_control   = df[df.group == "control"]["converted"].mean()
cr_treatment = df[df.group == "treatment"]["converted"].mean()
abs_diff     = cr_treatment - cr_control
rel_lift     = abs_diff / cr_control * 100

print(f"\nControl rate     : {cr_control:.4%}")
print(f"Treatment rate   : {cr_treatment:.4%}")
print(f"Absolute diff    : {abs_diff:+.4%}")
print(f"Relative lift    : {rel_lift:+.2f}%")

# ── 4. TWO-PROPORTION Z-TEST ──────────────────────────────────────────────────
print("\n[4] TWO-PROPORTION Z-TEST (FREQUENTIST)")
print("-" * 45)

n_c  = group_sizes["control"]
n_t  = group_sizes["treatment"]
x_c  = df[df.group == "control"]["converted"].sum()
x_t  = df[df.group == "treatment"]["converted"].sum()

# Pooled proportion under H0
p_pool = (x_c + x_t) / (n_c + n_t)
se     = np.sqrt(p_pool * (1 - p_pool) * (1/n_c + 1/n_t))
z_stat = abs_diff / se
p_val  = 2 * (1 - norm.cdf(abs(z_stat)))

print(f"Pooled proportion: {p_pool:.4f}")
print(f"Standard error   : {se:.6f}")
print(f"Z-statistic      : {z_stat:.4f}")
print(f"P-value          : {p_val:.4f}")
print(f"Significant?     : {'YES — reject H0' if p_val < 0.05 else 'NO — fail to reject H0'}")
print(f"\nInterpretation   : The {'new' if p_val < 0.05 else 'difference between the'} design "
      f"{'shows a statistically significant change' if p_val < 0.05 else 'is NOT statistically significant'}.")

# ── 5. POWER ANALYSIS ─────────────────────────────────────────────────────────
print("\n[5] POWER ANALYSIS & SAMPLE SIZE")
print("-" * 45)

alpha = 0.05
power = 0.80
target_lift = 0.02  # we wanted to detect a 2% relative lift

effect_size = (target_lift * cr_control) / np.sqrt(cr_control * (1 - cr_control))
z_alpha2    = norm.ppf(1 - alpha/2)
z_beta      = norm.ppf(power)
n_required  = int(((z_alpha2 + z_beta) / effect_size) ** 2) + 1

print(f"Target min detectable effect : {target_lift:.0%} relative lift")
print(f"Alpha (significance level)   : {alpha}")
print(f"Power                        : {power:.0%}")
print(f"Required per group           : {n_required:,}")
print(f"Actual per group             : {n_c:,}")
print(f"Experiment powered?          : {'YES ✓' if n_c >= n_required else 'NO — underpowered ⚠'}")

# ── 6. CONFIDENCE INTERVALS ───────────────────────────────────────────────────
print("\n[6] CONFIDENCE INTERVALS (95%)")
print("-" * 45)

z95 = norm.ppf(0.975)

# For each group individually
for grp in ["control", "treatment"]:
    sub = df[df.group == grp]
    p   = sub["converted"].mean()
    n   = len(sub)
    margin = z95 * np.sqrt(p * (1 - p) / n)
    print(f"{grp.capitalize():12}: {p:.4%}  95% CI [{p-margin:.4%}, {p+margin:.4%}]")

# For the difference
se_diff  = np.sqrt(cr_control*(1-cr_control)/n_c + cr_treatment*(1-cr_treatment)/n_t)
ci_lo    = abs_diff - z95 * se_diff
ci_hi    = abs_diff + z95 * se_diff
print(f"\nDifference (treatment − control):")
print(f"  Point estimate : {abs_diff:+.4%}")
print(f"  95% CI         : [{ci_lo:+.4%}, {ci_hi:+.4%}]")
print(f"  Includes zero? : {'YES → not significant' if ci_lo <= 0 <= ci_hi else 'NO → significant'}")

# ── 7. SEGMENTATION ANALYSIS ─────────────────────────────────────────────────
print("\n[7] SEGMENTATION ANALYSIS")
print("-" * 45)

for seg_col, seg_label in [("new_user", "User Type"), ("device", "Device")]:
    print(f"\n  By {seg_label}:")
    seg = (df.groupby([seg_col, "group"])["converted"]
             .agg(["mean", "count"])
             .reset_index())
    pivot = seg.pivot(index=seg_col, columns="group", values="mean")
    pivot["lift_pct"] = ((pivot["treatment"] - pivot["control"]) / pivot["control"] * 100).round(2)
    print(pivot.rename(columns={"control":"Control CR","treatment":"Treatment CR"}).to_string())

# ── 8. NOVELTY EFFECT CHECK ───────────────────────────────────────────────────
print("\n[8] NOVELTY EFFECT CHECK (Daily Trend)")
print("-" * 45)

df["date"]  = df["timestamp"].dt.date
daily = (df.groupby(["date", "group"])["converted"]
           .mean()
           .reset_index()
           .pivot(index="date", columns="group", values="converted"))
daily["daily_lift"] = daily["treatment"] - daily["control"]

first_week_lift = daily["daily_lift"].iloc[:7].mean()
last_week_lift  = daily["daily_lift"].iloc[-7:].mean()
novelty_flag    = abs(first_week_lift) > 2 * abs(last_week_lift)

print(f"First-week avg daily lift : {first_week_lift:+.4%}")
print(f"Last-week avg daily lift  : {last_week_lift:+.4%}")
print(f"Novelty effect suspected  : {'YES ⚠ — first-week lift decays significantly' if novelty_flag else 'NO ✓'}")

# ── 9. BAYESIAN A/B TEST ──────────────────────────────────────────────────────
print("\n[9] BAYESIAN A/B TEST")
print("-" * 45)

# Beta-Binomial conjugate model
# Prior: Beta(1,1) = uniform (no prior belief)
alpha_c = 1 + x_c;  beta_c = 1 + (n_c - x_c)
alpha_t = 1 + x_t;  beta_t = 1 + (n_t - x_t)

# Monte Carlo
samples = 500_000
s_c = np.random.beta(alpha_c, beta_c, samples)
s_t = np.random.beta(alpha_t, beta_t, samples)

prob_t_better = (s_t > s_c).mean()
expected_lift = (s_t - s_c).mean()
credible_lo   = np.percentile(s_t - s_c, 2.5)
credible_hi   = np.percentile(s_t - s_c, 97.5)

print(f"P(treatment > control) : {prob_t_better:.2%}")
print(f"Expected lift          : {expected_lift:+.4%}")
print(f"95% Credible interval  : [{credible_lo:+.4%}, {credible_hi:+.4%}]")

threshold = 0.95
decision  = "SHIP" if prob_t_better >= threshold else "DO NOT SHIP"
print(f"\nDecision threshold     : {threshold:.0%}")
print(f"Bayesian decision      : {decision}")

# ── 10. DECISION FRAMEWORK ───────────────────────────────────────────────────
print("\n[10] DECISION FRAMEWORK SUMMARY")
print("-" * 45)

checks = [
    ("Sample size sufficient",   n_c >= n_required,     f"{n_c:,} ≥ {n_required:,}"),
    ("Data quality clean",       contaminated == 0,      f"0 contaminated users"),
    ("Frequentist p < 0.05",     p_val < 0.05,           f"p = {p_val:.4f}"),
    ("CI excludes zero",         not (ci_lo <= 0 <= ci_hi), f"[{ci_lo:+.4%}, {ci_hi:+.4%}]"),
    ("No novelty effect",        not novelty_flag,        f"First vs last week lift stable"),
    ("P(treatment>control)≥95%", prob_t_better >= 0.95,   f"{prob_t_better:.2%}"),
]

passed = sum(1 for _, result, _ in checks if result)
for label, result, detail in checks:
    icon = "✓" if result else "✗"
    print(f"  {icon}  {label:<35}  {detail}")

print(f"\nChecks passed : {passed} / {len(checks)}")
print(f"FINAL DECISION: {'✅ SHIP new design' if passed >= 4 else '❌ DO NOT SHIP — insufficient evidence'}")

# ── 11. BUSINESS IMPACT ───────────────────────────────────────────────────────
print("\n[11] BUSINESS IMPACT QUANTIFICATION")
print("-" * 45)

monthly_visitors  = 2_000_000
avg_order_value   = 85.00    # £
baseline_cr       = cr_control
new_cr            = cr_treatment
monthly_baseline  = monthly_visitors * baseline_cr * avg_order_value
monthly_new       = monthly_visitors * new_cr       * avg_order_value
monthly_diff      = monthly_new - monthly_baseline
annual_diff       = monthly_diff * 12

print(f"Monthly visitors         : {monthly_visitors:,}")
print(f"Average order value      : £{avg_order_value:,.2f}")
print(f"Baseline monthly revenue : £{monthly_baseline:,.0f}")
print(f"New design monthly rev   : £{monthly_new:,.0f}")
print(f"Monthly revenue impact   : £{monthly_diff:+,.0f}")
print(f"Annual revenue impact    : £{annual_diff:+,.0f}")
print(f"\nRecommendation: {'Ship new design' if monthly_diff > 0 else 'Keep current design — new design costs £' + f'{abs(annual_diff):,.0f} per year'}")

# ── VISUALISATIONS ────────────────────────────────────────────────────────────
print("\n[CHARTS] Generating visualisations ...")

fig, axes = plt.subplots(2, 3, figsize=(16, 10))
fig.suptitle("A/B Test Analysis — Checkout Page Redesign", fontsize=16, fontweight="bold", color=NAVY, y=1.01)
plt.rcParams.update({"font.family": "DejaVu Sans"})

# 1. Conversion rate comparison
ax = axes[0, 0]
groups = ["Control\n(Old Design)", "Treatment\n(New Design)"]
rates  = [cr_control * 100, cr_treatment * 100]
colors = [SLATE, TEAL]
bars = ax.bar(groups, rates, color=colors, width=0.5, edgecolor="white", linewidth=1.5)
for bar, rate in zip(bars, rates):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05,
            f"{rate:.2f}%", ha="center", va="bottom", fontsize=12, fontweight="bold", color=NAVY)
ax.set_ylim(0, max(rates) * 1.25)
ax.set_title("Conversion Rate by Group", fontweight="bold", color=NAVY)
ax.set_ylabel("Conversion Rate (%)")
ax.axhline(cr_control * 100, color=SLATE, linestyle="--", alpha=0.4, linewidth=1)
ax.spines[["top", "right"]].set_visible(False)

# 2. Bayesian posterior distributions
ax = axes[0, 1]
x_range = np.linspace(0.10, 0.14, 1000)
from scipy.stats import beta as beta_dist
post_c = beta_dist(alpha_c, beta_c).pdf(x_range)
post_t = beta_dist(alpha_t, beta_t).pdf(x_range)
ax.fill_between(x_range * 100, post_c, alpha=0.5, color=SLATE, label="Control")
ax.fill_between(x_range * 100, post_t, alpha=0.5, color=TEAL,  label="Treatment")
ax.axvline(cr_control * 100,   color=SLATE, linewidth=1.5, linestyle="--")
ax.axvline(cr_treatment * 100, color=TEAL,  linewidth=1.5, linestyle="--")
ax.set_title(f"Bayesian Posterior Distributions\nP(Treatment > Control) = {prob_t_better:.1%}", fontweight="bold", color=NAVY)
ax.set_xlabel("Conversion Rate (%)")
ax.set_ylabel("Density")
ax.legend(frameon=False)
ax.spines[["top", "right"]].set_visible(False)

# 3. Daily conversion rate trend
ax = axes[0, 2]
dates = list(range(len(daily)))
ax.plot(dates, daily["control"]   * 100, color=SLATE, linewidth=1.8, label="Control",   marker="o", ms=3)
ax.plot(dates, daily["treatment"] * 100, color=TEAL,  linewidth=1.8, label="Treatment", marker="o", ms=3)
ax.fill_between(dates,
                (daily["control"] * 100).values,
                (daily["treatment"] * 100).values,
                where=(daily["treatment"] > daily["control"]).values,
                alpha=0.15, color=TEAL,  label="Treatment ahead")
ax.fill_between(dates,
                (daily["control"] * 100).values,
                (daily["treatment"] * 100).values,
                where=(daily["treatment"] <= daily["control"]).values,
                alpha=0.15, color=RED, label="Control ahead")
ax.set_title("Daily Conversion Rate Trend\n(Novelty Effect Check)", fontweight="bold", color=NAVY)
ax.set_xlabel("Day of Experiment")
ax.set_ylabel("Conversion Rate (%)")
ax.legend(frameon=False, fontsize=8)
ax.spines[["top", "right"]].set_visible(False)

# 4. Segmentation by device
ax = axes[1, 0]
device_data = (df.groupby(["device", "group"])["converted"]
                 .mean()
                 .reset_index()
                 .pivot(index="device", columns="group", values="converted") * 100)
x = np.arange(len(device_data))
w = 0.35
ax.bar(x - w/2, device_data["control"],   width=w, color=SLATE, label="Control",   edgecolor="white")
ax.bar(x + w/2, device_data["treatment"], width=w, color=TEAL,  label="Treatment", edgecolor="white")
ax.set_xticks(x)
ax.set_xticklabels([d.capitalize() for d in device_data.index])
ax.set_title("Conversion by Device Segment", fontweight="bold", color=NAVY)
ax.set_ylabel("Conversion Rate (%)")
ax.legend(frameon=False)
ax.spines[["top", "right"]].set_visible(False)

# 5. Confidence interval visualisation
ax = axes[1, 1]
grps   = ["Control", "Treatment"]
crs    = [cr_control, cr_treatment]
errors = [z95 * np.sqrt(p*(1-p)/n) for p, n in [(cr_control, n_c), (cr_treatment, n_t)]]
clrs   = [SLATE, TEAL]
ax.barh(grps, [r*100 for r in crs], xerr=[e*100 for e in errors],
        color=clrs, edgecolor="white", capsize=8, height=0.4)
ax.set_xlabel("Conversion Rate (%)")
ax.set_title("95% Confidence Intervals", fontweight="bold", color=NAVY)
ax.spines[["top", "right"]].set_visible(False)

# 6. Business impact summary
ax = axes[1, 2]
ax.axis("off")
impact_text = [
    ("DECISION SUMMARY", 0.92, 14, NAVY, True),
    (f"Frequentist:  p = {p_val:.4f}", 0.78, 11, NAVY, False),
    (f"Significant:  {'YES' if p_val < 0.05 else 'NO'}", 0.68, 11, GREEN if p_val < 0.05 else RED, True),
    (f"P(treat > ctrl): {prob_t_better:.1%}", 0.56, 11, NAVY, False),
    (f"Relative lift: {rel_lift:+.2f}%", 0.46, 11, GREEN if rel_lift > 0 else RED, True),
    (f"Annual impact: £{annual_diff:+,.0f}", 0.34, 11, GREEN if annual_diff > 0 else RED, True),
    ("", 0.22, 10, NAVY, False),
    (f"RECOMMENDATION:", 0.16, 12, NAVY, True),
    ("Keep current design" if annual_diff < 0 else "Ship new design", 0.06, 13,
     RED if annual_diff < 0 else GREEN, True),
]
for text, y, size, color, bold in impact_text:
    ax.text(0.5, y, text, transform=ax.transAxes, ha="center", va="center",
            fontsize=size, fontweight="bold" if bold else "normal", color=color)
rect = plt.Rectangle((0.05, 0.02), 0.9, 0.95, fill=True, facecolor="#F8FAFC",
                      edgecolor="#E2E8F0", linewidth=2, transform=ax.transAxes)
ax.add_patch(rect)
ax.set_zorder(1)
for text, y, size, color, bold in impact_text:
    ax.text(0.5, y, text, transform=ax.transAxes, ha="center", va="center",
            fontsize=size, fontweight="bold" if bold else "normal", color=color, zorder=2)

plt.tight_layout()
plt.savefig("/home/claude/abtest/ab_test_charts.png", dpi=150, bbox_inches="tight")
print("  Charts saved to ab_test_charts.png")
plt.close()

print("\n" + "=" * 65)
print("  ANALYSIS COMPLETE")
print("=" * 65)
