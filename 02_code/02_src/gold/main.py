from pathlib import Path

from silver.connections import get_postgres_connection


def main():

    # refresh_gold.sql lives in the same directory as this file.
    sql_path = (
        Path(__file__).resolve().parent
        / "refresh_gold.sql"
    )

    print("=" * 80)
    print("Starting Gold layer refresh")
    print("=" * 80)

    # Read Gold SQL
    with open(
        sql_path,
        "r",
        encoding="utf-8"
    ) as file:
        sql = file.read()

    connection = get_postgres_connection()

    try:

        with connection.cursor() as cursor:

            print(
                f"Executing: {sql_path.name}"
            )

            cursor.execute(sql)

        connection.commit()

        print()
        print("=" * 80)
        print("Gold layer refresh completed successfully.")
        print("=" * 80)

    except Exception:

        connection.rollback()

        print()
        print("=" * 80)
        print("Gold layer refresh FAILED.")
        print("=" * 80)

        raise

    finally:

        connection.close()


if __name__ == "__main__":
    main()