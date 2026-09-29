-- =========================================================
-- 1. Refresh dim_regulations
-- =========================================================

INSERT INTO gold.dim_regulations (
    regulation_id,
    title_ar,
    title_en,
    issue_date,
    publication_date,
    issue_date_hijri,
    publication_date_hijri,
    current_version,
    effective_date,
    status_en,
    status_ar
)
SELECT DISTINCT ON (l.id)
    l.id,
    l.title_ar,
    l.title_en,
    l.issue_date,
    l.publication_date,
    l.issue_date_hijri,
    l.publication_date_hijri,
    lv.version_number,
    lv.effective_date,
    s.status_en,
    s.status_ar
FROM silver.laws l
LEFT JOIN silver.laws_versions lv
    ON l.id = lv.law_id
LEFT JOIN silver.status s
    ON lv.status_id = s.id
ORDER BY l.id, lv.version_number DESC

ON CONFLICT (regulation_id)
DO UPDATE SET
    title_ar = EXCLUDED.title_ar,
    title_en = EXCLUDED.title_en,
    issue_date = EXCLUDED.issue_date,
    publication_date = EXCLUDED.publication_date,
    issue_date_hijri = EXCLUDED.issue_date_hijri,
    publication_date_hijri = EXCLUDED.publication_date_hijri,
    current_version = EXCLUDED.current_version,
    effective_date = EXCLUDED.effective_date,
    status_en = EXCLUDED.status_en,
    status_ar = EXCLUDED.status_ar;


-- =========================================================
-- 2. Refresh dim_articles
-- =========================================================

INSERT INTO gold.dim_articles (
    article_id,
    title_ar,
    title_en,
    content_ar,
    content_en,
    chapter_id,
    chapter_title_ar,
    chapter_title_en,
    regulation_id
)
SELECT
    a.id,
    a.title_ar,
    a.title_en,
    a.content_ar,
    a.content_en,
    c.id,
    c.title_ar,
    c.title_en,
    c.law_id
FROM silver.articles a
JOIN silver.chapters c
    ON a.chapter_id = c.id

ON CONFLICT (article_id)
DO UPDATE SET
    title_ar = EXCLUDED.title_ar,
    title_en = EXCLUDED.title_en,
    content_ar = EXCLUDED.content_ar,
    content_en = EXCLUDED.content_en,
    chapter_id = EXCLUDED.chapter_id,
    chapter_title_ar = EXCLUDED.chapter_title_ar,
    chapter_title_en = EXCLUDED.chapter_title_en,
    regulation_id = EXCLUDED.regulation_id;


-- =========================================================
-- 3. Refresh dim_date
-- Only insert missing dates
-- =========================================================

INSERT INTO gold.dim_date (
    date_key,
    full_date,
    year,
    month,
    month_name,
    day,
    weekday
)
SELECT
    TO_CHAR(d, 'YYYYMMDD')::INTEGER,
    d::DATE,
    EXTRACT(YEAR FROM d)::INTEGER,
    EXTRACT(MONTH FROM d)::INTEGER,
    TO_CHAR(d, 'Month'),
    EXTRACT(DAY FROM d)::INTEGER,
    TO_CHAR(d, 'Day')
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
) AS g(d)

ON CONFLICT (date_key)
DO NOTHING;


-- =========================================================
-- 4. Change types
-- =========================================================

INSERT INTO gold.dim_change_type (
    change_type_key,
    change_type
)
VALUES
    (1, 'Added'),
    (2, 'Updated'),
    (3, 'Deleted')
ON CONFLICT (change_type_key)
DO UPDATE SET
    change_type = EXCLUDED.change_type;


-- =========================================================
-- 5. Add detected article updates
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
    2
FROM silver.articles_versions av
JOIN silver.laws_versions lv
    ON av.law_version_id = lv.id
WHERE av.is_changed = true

ON CONFLICT (
    article_id,
    law_version_id,
    change_type_key
)
DO NOTHING;


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
