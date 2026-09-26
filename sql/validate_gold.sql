-- ==========================================
-- GOLD LAYER VALIDATION
-- ==========================================

-- 1. Row counts
SELECT 'dim_regulations' AS table_name, COUNT(*) AS row_count
FROM gold.dim_regulations

UNION ALL

SELECT 'dim_articles', COUNT(*)
FROM gold.dim_articles

UNION ALL

SELECT 'dim_date', COUNT(*)
FROM gold.dim_date

UNION ALL

SELECT 'dim_change_type', COUNT(*)
FROM gold.dim_change_type

UNION ALL

SELECT 'fact_article_changes', COUNT(*)
FROM gold.fact_article_changes;


-- 2. Duplicate regulations
SELECT
    COUNT(*) - COUNT(DISTINCT regulation_id)
    AS duplicate_regulations
FROM gold.dim_regulations;


-- 3. Duplicate articles
SELECT
    COUNT(*) - COUNT(DISTINCT article_id)
    AS duplicate_articles
FROM gold.dim_articles;


-- 4. Articles without a valid regulation
SELECT
    COUNT(*) AS orphan_articles
FROM gold.dim_articles a
LEFT JOIN gold.dim_regulations r
    ON a.regulation_id = r.regulation_id
WHERE r.regulation_id IS NULL;


-- 5. Regulations without a current version
SELECT
    COUNT(*) AS missing_current_version
FROM gold.dim_regulations
WHERE current_version IS NULL;


-- 6. Fact rows with invalid dates
SELECT
    COUNT(*) AS invalid_fact_dates
FROM gold.fact_article_changes f
LEFT JOIN gold.dim_date d
    ON f.date_key = d.date_key
WHERE f.date_key IS NOT NULL
  AND d.date_key IS NULL;
