import pendulum

from airflow.sdk import dag, task


RIYADH_TZ = pendulum.timezone("Asia/Riyadh")


@dag(
    dag_id="boe_pipeline",

    # Every day at 1:00 AM Riyadh time
    schedule="0 1 * * *",

    start_date=pendulum.datetime(
        2026,
        9,
        28,
        tz=RIYADH_TZ,
    ),

    catchup=False,

    # Never run two BOE pipelines simultaneously
    max_active_runs=1,

    tags=[
        "bayan",
        "boe",
        "data-engineering",
    ],
)
def boe_pipeline():

    # ======================================================
    # Collection Date
    # ======================================================

    @task
    def get_collection_date():
        """
        Return the current Riyadh calendar date.

        The same date is passed to Bronze and Silver so both
        layers operate on the same SeaweedFS partition.
        """

        return pendulum.now(
            "Asia/Riyadh"
        ).format("YYYY-MM-DD")

    # ======================================================
    # Bronze
    # ======================================================

    @task
    def bronze_layer(collection_date: str):

        from bronze.extract_boe import run_scraper

        print("=" * 80)
        print("BAYAN - BOE — BRONZE LAYER")
        print(f"Collection date: {collection_date}")
        print("=" * 80)

        run_scraper(
            run_date=collection_date
        )

    # ======================================================
    # Silver
    # ======================================================

    @task
    def silver_layer(collection_date: str):

        from silver.main import main

        print("=" * 80)
        print("BAYAN - BOE — SILVER LAYER")
        print(f"Collection date: {collection_date}")
        print("=" * 80)

        main(
            collection_date=collection_date
        )

    # ======================================================
    # Gold
    # ======================================================

    @task
    def gold_layer():

        from gold.main import main

        print("=" * 80)
        print("BAYAN - BOE — GOLD LAYER")
        print("=" * 80)

        main()

    # ======================================================
    # Pipeline
    # ======================================================

    collection_date = get_collection_date()

    bronze = bronze_layer(collection_date)
    silver = silver_layer(collection_date)
    gold = gold_layer()

    bronze >> silver >> gold


boe_pipeline()