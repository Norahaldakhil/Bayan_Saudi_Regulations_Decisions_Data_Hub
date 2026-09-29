from pathlib import Path

from silver.connections import get_seaweedfs_client
from silver.config import SEAWEEDFS_BUCKET


DUMMY_ROOT = Path("/opt/airflow/bayan/bayan_dummy_bronze")


def main():
    s3 = get_seaweedfs_client()

    files = sorted(DUMMY_ROOT.glob("*/*/raw.txt"))

    print(f"Found {len(files)} dummy raw files.")
    print(f"Bucket: {SEAWEEDFS_BUCKET}")
    print()

    if len(files) != 8:
        raise RuntimeError(
            f"Expected 8 raw.txt files, found {len(files)}"
        )

    for path in files:
        key = path.relative_to(DUMMY_ROOT).as_posix()

        print(f"Uploading: {key}")

        with path.open("rb") as f:
            s3.put_object(
                Bucket=SEAWEEDFS_BUCKET,
                Key=key,
                Body=f,
                ContentType="text/plain; charset=utf-8",
            )

    print()
    print("Upload complete.")


if __name__ == "__main__":
    main()
