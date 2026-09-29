-- =========================================================
-- BAYAN GOLD LAYER VALIDATION
-- =========================================================


-- =========================================================
-- 1. Row counts
-- =========================================================

SELECT
    'dim_regulations' AS table_name,
    COUNT(*) AS row_count
FROM gold.dim_regulations

UNION ALL

SELECT
    'dim_articles',
    COUNT(*)
FROM gold.dim_articles

UNION ALL

SELECT
    'dim_date',
    COUNT(*)
FROM gold.dim_date

UNION ALL

SELECT
    'dim_change_type',
    COUNT(*)
FROM gold.dim_change_type

UNION ALL

SELECT
    'fact_article_changes',
    COUNT(*)
FROM gold.fact_article_changes;


-- =========================================================
-- 2. Duplicate regulation keys
-- Expected: 0
-- =========================================================

SELECT
    COUNT(*) - COUNT(DISTINCT regulation_id)
        AS duplicate_regulations
FROM gold.dim_regulations;


-- =========================================================
-- 3. Duplicate article keys
-- Expected: 0
-- =========================================================

SELECT
    COUNT(*) - COUNT(DISTINCT article_id)
        AS duplicate_articles
FROM gold.dim_articles;


-- =========================================================
-- 4. Articles without regulation
-- Expected: 0
-- =========================================================

SELECT
    COUNT(*) AS orphan_articles
FROM gold.dim_articles a

LEFT JOIN gold.dim_regulations r
    ON r.regulation_id = a.regulation_id

WHERE r.regulation_id IS NULL;


-- =========================================================
-- 5. Regulations without current version
-- Ideally: 0
-- =========================================================

SELECT
    COUNT(*) AS missing_current_version
FROM gold.dim_regulations
WHERE current_version IS NULL;


-- =========================================================
-- 6. Fact rows with invalid regulations
-- Expected: 0
-- =========================================================

SELECT
    COUNT(*) AS orphan_fact_regulations
FROM gold.fact_article_changes f

LEFT JOIN gold.dim_regulations r
    ON r.regulation_id = f.regulation_id

WHERE r.regulation_id IS NULL;


-- =========================================================
-- 7. Fact rows with invalid articles
-- Expected: 0
-- =========================================================

SELECT
    COUNT(*) AS orphan_fact_articles
FROM gold.fact_article_changes f

LEFT JOIN gold.dim_articles a
    ON a.article_id = f.article_id

WHERE a.article_id IS NULL;


-- =========================================================
-- 8. Fact rows with invalid dates
-- Expected: 0
-- NULL date_key is allowed.
-- =========================================================

SELECT
    COUNT(*) AS invalid_fact_dates
FROM gold.fact_article_changes f

LEFT JOIN gold.dim_date d
    ON d.date_key = f.date_key

WHERE f.date_key IS NOT NULL
  AND d.date_key IS NULL;


-- =========================================================
-- 9. Duplicate fact events
-- Expected: 0
-- =========================================================

SELECT
    regulation_id,
    article_id,
    law_version_id,
    change_type_key,
    COUNT(*) AS occurrences
FROM gold.fact_article_changes

GROUP BY
    regulation_id,
    article_id,
    law_version_id,
    change_type_key

HAVING COUNT(*) > 1;


-- =========================================================
-- 10. Gold update count vs Silver
--
-- THESE TWO COUNTS SHOULD MATCH.
-- =========================================================

SELECT
    (
        SELECT COUNT(*)
        FROM silver.articles_versions
        WHERE is_changed = TRUE
    ) AS silver_changed_articles,

    (
        SELECT COUNT(*)
        FROM gold.fact_article_changes
        WHERE change_type_key = 2
    ) AS gold_updated_articles;


-- =========================================================
-- 11. Show detected changes
-- =========================================================

SELECT
    r.title_ar AS regulation,
    a.title_ar AS article,
    lv.version_number,
    ct.change_type,
    f.date_key,
    f.article_id,
    f.law_version_id

FROM gold.fact_article_changes f

JOIN gold.dim_regulations r
    ON r.regulation_id = f.regulation_id

JOIN gold.dim_articles a
    ON a.article_id = f.article_id

JOIN silver.laws_versions lv
    ON lv.id = f.law_version_id

JOIN gold.dim_change_type ct
    ON ct.change_type_key = f.change_type_key

ORDER BY
    r.title_ar,
    a.title_ar,
    lv.version_number;