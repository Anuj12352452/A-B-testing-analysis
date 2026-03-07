-- ============================================================
-- A/B TESTING SQL QUERIES — E-COMMERCE CHECKOUT CONVERSION
-- Database : ab_test_db
-- Table    : ab_test_results
-- Columns  : user_id, timestamp, group (control/treatment),
--            converted (0/1), new_user (0/1), device
-- ============================================================


-- ─────────────────────────────────────────────────────────────
-- Q1. EXPERIMENT OVERVIEW
--     Basic sanity check — rows, groups, date range
-- ─────────────────────────────────────────────────────────────
SELECT
    "group",
    COUNT(*)                              AS total_users,
    SUM(converted)                        AS total_conversions,
    ROUND(AVG(converted) * 100, 4)        AS conversion_rate_pct,
    MIN(timestamp)::DATE                  AS start_date,
    MAX(timestamp)::DATE                  AS end_date
FROM ab_test_results
GROUP BY "group"
ORDER BY "group";


-- ─────────────────────────────────────────────────────────────
-- Q2. DATA QUALITY — CHECK FOR CONTAMINATED USERS
--     Users who appear in BOTH control and treatment
--     These must be removed before analysis
-- ─────────────────────────────────────────────────────────────
SELECT
    user_id,
    COUNT(DISTINCT "group") AS groups_seen
FROM ab_test_results
GROUP BY user_id
HAVING COUNT(DISTINCT "group") > 1;

-- Count contaminated users (should be 0 for a clean experiment)
SELECT
    COUNT(*) AS contaminated_user_count
FROM (
    SELECT user_id
    FROM ab_test_results
    GROUP BY user_id
    HAVING COUNT(DISTINCT "group") > 1
) sub;


-- ─────────────────────────────────────────────────────────────
-- Q3. CONVERSION RATE WITH CONFIDENCE INTERVAL
--     95% CI using normal approximation (Wilson method)
-- ─────────────────────────────────────────────────────────────
WITH stats AS (
    SELECT
        "group",
        COUNT(*)           AS n,
        SUM(converted)     AS x,
        AVG(converted)     AS p
    FROM ab_test_results
    GROUP BY "group"
)
SELECT
    "group",
    n,
    x AS conversions,
    ROUND(p * 100, 4)                                      AS conv_rate_pct,
    ROUND((p - 1.96 * SQRT(p*(1-p)/n)) * 100, 4)          AS ci_lower_pct,
    ROUND((p + 1.96 * SQRT(p*(1-p)/n)) * 100, 4)          AS ci_upper_pct
FROM stats
ORDER BY "group";


-- ─────────────────────────────────────────────────────────────
-- Q4. ABSOLUTE AND RELATIVE LIFT
--     Key business metric: how much better/worse is treatment?
-- ─────────────────────────────────────────────────────────────
WITH rates AS (
    SELECT
        "group",
        AVG(converted) AS conversion_rate
    FROM ab_test_results
    GROUP BY "group"
),
pivoted AS (
    SELECT
        MAX(CASE WHEN "group" = 'control'   THEN conversion_rate END) AS cr_control,
        MAX(CASE WHEN "group" = 'treatment' THEN conversion_rate END) AS cr_treatment
    FROM rates
)
SELECT
    ROUND(cr_control   * 100, 4)                           AS control_rate_pct,
    ROUND(cr_treatment * 100, 4)                           AS treatment_rate_pct,
    ROUND((cr_treatment - cr_control) * 100, 4)            AS absolute_diff_pct,
    ROUND((cr_treatment - cr_control) / cr_control * 100, 2) AS relative_lift_pct,
    CASE
        WHEN cr_treatment > cr_control THEN 'Treatment BETTER'
        WHEN cr_treatment < cr_control THEN 'Treatment WORSE'
        ELSE 'NO DIFFERENCE'
    END AS direction
FROM pivoted;


-- ─────────────────────────────────────────────────────────────
-- Q5. TWO-PROPORTION Z-TEST IN SQL
--     Calculate z-statistic and approximate p-value
--     (for exact p-value use Python scipy)
-- ─────────────────────────────────────────────────────────────
WITH stats AS (
    SELECT
        "group",
        COUNT(*)       AS n,
        SUM(converted) AS x,
        AVG(converted) AS p
    FROM ab_test_results
    GROUP BY "group"
),
pooled AS (
    SELECT
        SUM(x)::float / SUM(n)          AS p_pool,
        MAX(CASE WHEN "group"='control'   THEN n END) AS n_c,
        MAX(CASE WHEN "group"='treatment' THEN n END) AS n_t,
        MAX(CASE WHEN "group"='control'   THEN p END) AS p_c,
        MAX(CASE WHEN "group"='treatment' THEN p END) AS p_t
    FROM stats
)
SELECT
    ROUND(p_pool, 6)                                           AS pooled_proportion,
    ROUND(SQRT(p_pool*(1-p_pool)*(1.0/n_c + 1.0/n_t)), 6)    AS standard_error,
    ROUND((p_t - p_c) /
          SQRT(p_pool*(1-p_pool)*(1.0/n_c + 1.0/n_t)), 4)    AS z_statistic,
    CASE
        WHEN ABS((p_t - p_c) /
                 SQRT(p_pool*(1-p_pool)*(1.0/n_c + 1.0/n_t)))
             > 1.96 THEN 'SIGNIFICANT (p < 0.05)'
        ELSE 'NOT SIGNIFICANT (p >= 0.05)'
    END AS significance
FROM pooled;


-- ─────────────────────────────────────────────────────────────
-- Q6. DAILY CONVERSION RATE (NOVELTY EFFECT CHECK)
--     If the treatment advantage disappears after week 1,
--     the initial lift was just novelty, not real improvement
-- ─────────────────────────────────────────────────────────────
WITH daily AS (
    SELECT
        timestamp::DATE                AS test_date,
        "group",
        COUNT(*)                       AS daily_users,
        SUM(converted)                 AS daily_conversions,
        ROUND(AVG(converted) * 100, 4) AS daily_cr_pct
    FROM ab_test_results
    GROUP BY 1, 2
)
SELECT
    d.test_date,
    MAX(CASE WHEN d."group" = 'control'   THEN d.daily_cr_pct END) AS control_cr_pct,
    MAX(CASE WHEN d."group" = 'treatment' THEN d.daily_cr_pct END) AS treatment_cr_pct,
    ROUND(
        MAX(CASE WHEN d."group" = 'treatment' THEN d.daily_cr_pct END)
        - MAX(CASE WHEN d."group" = 'control'  THEN d.daily_cr_pct END),
    4)                                                               AS daily_lift_pct
FROM daily d
GROUP BY d.test_date
ORDER BY d.test_date;


-- ─────────────────────────────────────────────────────────────
-- Q7. SEGMENTATION BY DEVICE TYPE
--     Different segments may respond differently.
--     A positive overall result can hide a negative on mobile.
-- ─────────────────────────────────────────────────────────────
SELECT
    device,
    "group",
    COUNT(*)                              AS users,
    SUM(converted)                        AS conversions,
    ROUND(AVG(converted) * 100, 4)        AS conversion_rate_pct
FROM ab_test_results
GROUP BY device, "group"
ORDER BY device, "group";

-- Pivot to compare side-by-side
SELECT
    device,
    ROUND(MAX(CASE WHEN "group"='control'   THEN AVG(converted)*100 END), 4) AS control_cr_pct,
    ROUND(MAX(CASE WHEN "group"='treatment' THEN AVG(converted)*100 END), 4) AS treatment_cr_pct,
    ROUND(MAX(CASE WHEN "group"='treatment' THEN AVG(converted)*100 END)
        - MAX(CASE WHEN "group"='control'   THEN AVG(converted)*100 END), 4) AS lift_pct
FROM ab_test_results
GROUP BY device
ORDER BY lift_pct DESC;


-- ─────────────────────────────────────────────────────────────
-- Q8. SEGMENTATION BY USER TYPE (NEW vs RETURNING)
--     New users have no prior experience with the old design —
--     they may react differently to the new checkout page
-- ─────────────────────────────────────────────────────────────
SELECT
    CASE WHEN new_user = 1 THEN 'New User' ELSE 'Returning User' END AS user_type,
    "group",
    COUNT(*)                              AS users,
    ROUND(AVG(converted) * 100, 4)        AS conversion_rate_pct
FROM ab_test_results
GROUP BY new_user, "group"
ORDER BY user_type, "group";


-- ─────────────────────────────────────────────────────────────
-- Q9. WEEKLY COHORT ANALYSIS
--     Users who entered the experiment in week 1 vs week 2+
--     Helps detect if the experiment ran long enough
-- ─────────────────────────────────────────────────────────────
WITH weekly AS (
    SELECT
        user_id,
        "group",
        converted,
        DATE_TRUNC('week', timestamp)::DATE AS experiment_week
    FROM ab_test_results
)
SELECT
    experiment_week,
    "group",
    COUNT(*)                              AS weekly_users,
    SUM(converted)                        AS weekly_conversions,
    ROUND(AVG(converted) * 100, 4)        AS weekly_cr_pct
FROM weekly
GROUP BY experiment_week, "group"
ORDER BY experiment_week, "group";


-- ─────────────────────────────────────────────────────────────
-- Q10. SAMPLE RATIO MISMATCH (SRM) CHECK
--      If groups are unequal in size, randomisation may be broken.
--      Expected: 50/50 split. Alert if > 1% deviation.
-- ─────────────────────────────────────────────────────────────
WITH totals AS (
    SELECT
        "group",
        COUNT(*) AS n
    FROM ab_test_results
    GROUP BY "group"
),
overall AS (
    SELECT SUM(n) AS total FROM totals
)
SELECT
    t."group",
    t.n                                                     AS actual_users,
    (o.total / 2)                                           AS expected_users,
    ROUND(t.n::float / o.total * 100, 2)                    AS actual_pct,
    50.00                                                   AS expected_pct,
    ABS(ROUND(t.n::float / o.total * 100, 2) - 50)         AS deviation_pct,
    CASE
        WHEN ABS(ROUND(t.n::float / o.total * 100, 2) - 50) > 1
        THEN 'SRM DETECTED — check randomisation'
        ELSE 'OK — balanced split'
    END AS srm_status
FROM totals t, overall o
ORDER BY "group";


-- ─────────────────────────────────────────────────────────────
-- Q11. BUSINESS IMPACT CALCULATION
--      Translate statistical result into £ revenue impact
-- ─────────────────────────────────────────────────────────────
WITH rates AS (
    SELECT
        MAX(CASE WHEN "group"='control'   THEN AVG(converted) END) AS cr_c,
        MAX(CASE WHEN "group"='treatment' THEN AVG(converted) END) AS cr_t
    FROM ab_test_results
    GROUP BY TRUE
)
SELECT
    ROUND(cr_c * 100, 4)                                   AS control_rate_pct,
    ROUND(cr_t * 100, 4)                                   AS treatment_rate_pct,
    2000000                                                AS monthly_visitors,
    85                                                     AS avg_order_value_gbp,
    ROUND(2000000 * cr_c * 85, 0)                         AS baseline_monthly_revenue,
    ROUND(2000000 * cr_t * 85, 0)                         AS new_monthly_revenue,
    ROUND(2000000 * (cr_t - cr_c) * 85, 0)               AS monthly_revenue_impact,
    ROUND(2000000 * (cr_t - cr_c) * 85 * 12, 0)          AS annual_revenue_impact
FROM rates;


-- ─────────────────────────────────────────────────────────────
-- Q12. DECISION SUMMARY VIEW
--      Single query to share with non-technical stakeholders
-- ─────────────────────────────────────────────────────────────
WITH stats AS (
    SELECT
        MAX(CASE WHEN "group"='control'   THEN AVG(converted) END) AS cr_c,
        MAX(CASE WHEN "group"='treatment' THEN AVG(converted) END) AS cr_t,
        MAX(CASE WHEN "group"='control'   THEN COUNT(*) END)       AS n_c,
        MAX(CASE WHEN "group"='treatment' THEN COUNT(*) END)       AS n_t
    FROM ab_test_results
    GROUP BY TRUE
),
calc AS (
    SELECT
        cr_c, cr_t, n_c, n_t,
        (cr_t - cr_c) / cr_c * 100   AS rel_lift_pct,
        (cr_t - cr_c)                 AS abs_diff,
        SQRT((cr_c*(1-cr_c)/n_c) + (cr_t*(1-cr_t)/n_t)) AS se
    FROM stats
)
SELECT
    'Checkout Page Redesign'                               AS experiment_name,
    ROUND(cr_c * 100, 2)                                   AS control_conv_pct,
    ROUND(cr_t * 100, 2)                                   AS treatment_conv_pct,
    ROUND(rel_lift_pct, 2)                                 AS relative_lift_pct,
    ROUND(abs_diff / se, 4)                                AS z_statistic,
    CASE WHEN ABS(abs_diff / se) > 1.96
         THEN 'SIGNIFICANT'
         ELSE 'NOT SIGNIFICANT' END                        AS result,
    ROUND(2000000 * abs_diff * 85 * 12, 0)                AS annual_revenue_impact_gbp,
    CASE
        WHEN ABS(abs_diff / se) > 1.96 AND cr_t > cr_c    THEN 'SHIP new design'
        WHEN ABS(abs_diff / se) > 1.96 AND cr_t < cr_c    THEN 'KEEP current design'
        ELSE 'INCONCLUSIVE — run longer or redesign test'
    END AS recommendation
FROM calc;
