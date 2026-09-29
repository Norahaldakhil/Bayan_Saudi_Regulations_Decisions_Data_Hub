# ============================================================
# SILVER EXTRACTION
# ============================================================


# ============================================================
# GET BRONZE RAW OBJECT KEYS
# ============================================================

def get_raw_keys(
    s3,
    bucket,
    collection_date=None
):

    paginator = s3.get_paginator(
        "list_objects_v2"
    )

    keys = []

    # --------------------------------------------------------
    # Specific date / Airflow run
    # --------------------------------------------------------

    if collection_date:

        prefix = f"{collection_date}/"

        for page in paginator.paginate(
            Bucket=bucket,
            Prefix=prefix
        ):

            for obj in page.get("Contents", []):

                key = obj["Key"]

                if key.endswith("/raw.txt"):
                    keys.append(key)

    # --------------------------------------------------------
    # No date supplied
    #
    # List all Bronze objects.
    # main.py will skip objects that have already been
    # successfully processed.
    # --------------------------------------------------------

    else:

        for page in paginator.paginate(
            Bucket=bucket
        ):

            for obj in page.get("Contents", []):

                key = obj["Key"]

                if key.endswith("/raw.txt"):
                    keys.append(key)

    keys.sort()

    return keys


# ============================================================
# READ BRONZE RAW OBJECT
# ============================================================

def read_raw_file(
    s3,
    bucket,
    key
):

    response = s3.get_object(
        Bucket=bucket,
        Key=key
    )

    text = (
        response["Body"]
        .read()
        .decode("utf-8")
    )

    return text