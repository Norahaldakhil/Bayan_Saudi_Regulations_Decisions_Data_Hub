# Bayan dummy Bronze data

Fictional integration-test data for the existing Bayan Bronze → Silver → Gold pipeline.

## Snapshots
- 2026-10-01 = baseline
- 2026-10-02 = changed snapshot

## Deliberate scenarios
1. تنظيم مركز بيان التجريبي للبيانات
   - المادة الثالثة updated
   - المادة السابعة added
2. لائحة الهيئة التجريبية للخدمات الرقمية
   - المواد الثانية والثالثة والرابعة والخامسة updated
3. تنظيم اللجنة التجريبية لحوكمة السجلات
   - المادة الثالثة removed from V2
4. تنظيم المختبر التجريبي للابتكار التقني
   - multiple chapters and multi-line content
   - المادة الثالثة updated by adding list item 4

Expected genuine updates of existing articles in V2: 6.

With the current Gold SQL, only rows where silver.articles_versions.is_changed=true become fact rows and they are hard-coded as change_type_key=2 (Updated). The Added and Deleted source scenarios are intentionally included to expose that limitation.

Suggested order:
docker compose exec airflow-scheduler python -m silver.main 2026-10-01
docker compose exec airflow-scheduler python -m gold.main

Then:
docker compose exec airflow-scheduler python -m silver.main 2026-10-02
docker compose exec airflow-scheduler python -m gold.main
