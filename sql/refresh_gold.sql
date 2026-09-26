BEGIN;

-- =========================================================
-- 1. Refresh dim_regulations
-- Latest version only for each regulation
-- =========================================================

TRUNCATE TABLE gold.dim_regulations;

INSERT INTO gold.dim_regulations
SELECT DISTINCT ON (l.id)
    l.id AS regulation_id,
    l.title_ar,
    l.title_en,
    l.issue_date,
    l.publication_date,
    l.issue_date_hijri,
    l.publication_date_hijri,
    lv.version_number AS current_version,
    lv.effective_date,
    s.status_en,
    s.status_ar
FROM silver.laws l
LEFT JOIN silver.laws_versions lv
    ON l.id = lv.law_id
LEFT JOIN silver.status s
    ON lv.status_id = s.id
ORDER BY l.id, lv.version_number DESC;


-- =========================================================
-- 2. Refresh dim_articles
-- =========================================================

TRUNCATE TABLE gold.dim_articles;

INSERT INTO gold.dim_articles
SELECT
    a.id AS article_id,
    a.title_ar,
    a.title_en,
    a.content_ar,
    a.content_en,
    c.id AS chapter_id,
    c.title_ar AS chapter_title_ar,
    c.title_en AS chapter_title_en,
    c.law_id AS regulation_id
FROM silver.articles a
JOIN silver.chapters c
    ON a.chapter_id = c.id;


-- =========================================================
-- 3. Refresh dim_date
-- Rebuild date range if newer dates appear
-- =========================================================

TRUNCATE TABLE gold.dim_date;

INSERT INTO gold.dim_date
SELECT
    TO_CHAR(d, 'YYYYMMDD')::INTEGER AS date_key,
    d::DATE AS full_date,
    EXTRACT(YEAR FROM d)::INTEGER AS year,
    EXTRACT(MONTH FROM d)::INTEGER AS month,
    TO_CHAR(d, 'Month') AS month_name,
    EXTRACT(DAY FROM d)::INTEGER AS day,
    TO_CHAR(d, 'Day') AS weekday
FROM generate_series(
    (
        SELECT MIN(dt)
        FROM (
            SELECT MIN(issue_date)::DATE AS dt
            FROM silver.laws

            UNION ALL

            SELECT MIN(effective_date)::DATE
            FROM silver.laws_versions
        ) x
    ),
    (
        SELECT MAX(dt)
        FROM (
            SELECT MAX(issue_date)::DATE AS dt
            FROM silver.laws

            UNION ALL

            SELECT MAX(effective_date)::DATE
            FROM silver.laws_versions
        ) x
    ),
    INTERVAL '1 day'
) AS g(d);


-- =========================================================
-- 4. Keep change types ready
-- =========================================================

INSERT INTO gold.dim_change_type (
    change_type_key,
    change_type
)
VALUES
    (1, 'Added'),
    (2, 'Updated'),
    (3, 'Deleted')
ON CONFLICT DO NOTHING;


-- =========================================================
-- 5. Add NEW article changes to fact table
-- Currently Silver explicitly supports Updated via is_changed
-- =========================================================

INSERT INTO gold.fact_article_changes (
    regulation_id,
    article_id,
    law_version_id,
    date_key,
    change_type_key
)
SELECT
    lv.law_id,
    av.article_id,
    av.law_version_id,
    TO_CHAR(lv.effective_date, 'YYYYMMDD')::INTEGER,
    2 AS change_type_key
FROM silver.articles_versions av
JOIN silver.laws_versions lv
    ON av.law_version_id = lv.id
WHERE av.is_changed = true
AND NOT EXISTS (
    SELECT 1
    FROM gold.fact_article_changes f
    WHERE f.article_id = av.article_id
      AND f.law_version_id = av.law_version_id
      AND f.change_type_key = 2
);


COMMIT;


-- =========================================================
-- 6. Validation summary
-- =========================================================

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
