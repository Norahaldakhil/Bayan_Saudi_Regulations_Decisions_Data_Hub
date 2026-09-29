from silver.config import (
    SOURCE_NAME,
    SEAWEEDFS_BUCKET,
)

from silver.connections import (
    get_postgres_connection,
    get_seaweedfs_client,
)

from silver.extract import (
    get_raw_keys,
    read_raw_file,
)

from silver.transform import (
    transform_law,
    transform_law_version,
    transform_chapters,
    transform_articles,
    transform_statuses,
    transform_articles_versions,
    validate_raw_text,
)

from silver.load import (
    get_source_id,
    get_or_create_law,
    get_or_create_law_version,
    get_or_create_chapter,
    get_or_create_article,
    get_or_create_status,
    get_or_create_article_version,
    save_law_version_extraction_status,
    is_bronze_object_processed,
    mark_bronze_object_processed
)


# ============================================================
# Single-law test
# ============================================================

def dry_run():

    s3 = get_seaweedfs_client()
    connection = get_postgres_connection()

    key = (
        "2026-09-15/"
        "43344715-1e0d-4e7f-9895-aa3d00f670e6/"
        "raw.txt"
    )

    try:

        text = read_raw_file(
            s3,
            SEAWEEDFS_BUCKET,
            key
        )

        transformed_law = transform_law(
            text,
            key,
            source_id=1
        )

        statuses = transform_statuses(text)

        if not statuses:
            print("Status not found.")
            return

        status = statuses[0]

        # ----------------------------------------------------
        # Law
        # ----------------------------------------------------

        law_id, law_created = get_or_create_law(
            connection,
            transformed_law
        )

        # ----------------------------------------------------
        # Status
        # ----------------------------------------------------

        status_id, status_created = get_or_create_status(
            connection,
            status
        )

        # ----------------------------------------------------
        # Law version
        # ----------------------------------------------------

        law_version, extraction_status = (
            transform_law_version(
                text,
                key,
                law_id,
                transformed_law["issue_date"],
                transformed_law["publication_date"],
                status_id
            )
        )

        law_version_id, law_version_created = (
            get_or_create_law_version(
                connection,
                law_version
            )
        )

        # ----------------------------------------------------
        # Effective-date extraction diagnostics
        # ----------------------------------------------------

        save_law_version_extraction_status(
            connection,
            law_version_id,
            extraction_status
        )

        print("LAW ID:", law_id)
        print("LAW VERSION ID:", law_version_id)
        print("CREATED:", law_version_created)
        print("LAW VERSION:", law_version)
        print(
            "EXTRACTION STATUS:",
            extraction_status
        )

    finally:
        connection.close()


# ============================================================
# Full pipeline
# ============================================================

def main(collection_date=None):

    connection = get_postgres_connection()
    s3 = get_seaweedfs_client()

    try:
        # --------------------------------------------------
        # Source
        # --------------------------------------------------

        source_id = get_source_id(
            connection,
            SOURCE_NAME
        )

        # --------------------------------------------------
        # Get Bronze raw objects
        # --------------------------------------------------

        raw_keys = get_raw_keys(
            s3,
            SEAWEEDFS_BUCKET,
            collection_date=collection_date
        )

        if collection_date:
            print(
                f"Found {len(raw_keys)} raw files "
                f"for {collection_date}."
            )
        else:
            print(
                f"Found {len(raw_keys)} raw files "
                f"across all dates."
            )

        # --------------------------------------------------
        # Process each law
        # --------------------------------------------------

        for i, key in enumerate(
            raw_keys,
            start=1
        ):
            if is_bronze_object_processed(connection, key):
                print(f"Skipping already processed: {key}")
                continue

            print(
                f"[{i}/{len(raw_keys)}] "
                f"Processing {key}"
            )

            # ------------------------------------------------
            # Extract
            # ------------------------------------------------

            text = read_raw_file(
                s3,
                SEAWEEDFS_BUCKET,
                key
            )

            # ------------------------------------------------
            # Validate
            # ------------------------------------------------

            if not validate_raw_text(text):

                print(
                    "  -> SKIPPED: invalid raw text"
                )

                continue

            # =================================================
            # TRANSFORM
            # =================================================

            # ------------------------------------------------
            # Law
            # ------------------------------------------------

            transformed_law = transform_law(
                text,
                key,
                source_id
            )

            # ------------------------------------------------
            # Status
            # ------------------------------------------------

            statuses = transform_statuses(text)

            if not statuses:

                print(
                    "  -> SKIPPED: status not found"
                )

                continue

            status = statuses[0]

            # =================================================
            # LOAD LAW
            # =================================================

            law_id, law_created = (
                get_or_create_law(
                    connection,
                    transformed_law
                )
            )

            # ------------------------------------------------
            # Load status
            # ------------------------------------------------

            status_id, status_created = (
                get_or_create_status(
                    connection,
                    status
                )
            )

            # ------------------------------------------------
            # Transform law version
            # ------------------------------------------------

            law_version, extraction_status = (
                transform_law_version(
                    text,
                    key,
                    law_id,
                    transformed_law[
                        "issue_date"
                    ],
                    transformed_law[
                        "publication_date"
                    ],
                    status_id
                )
            )

            # ------------------------------------------------
            # Load law version
            # ------------------------------------------------

            (
                law_version_id,
                law_version_created
            ) = get_or_create_law_version(
                connection,
                law_version
            )

            # ------------------------------------------------
            # Effective-date extraction diagnostics
            # ------------------------------------------------

            save_law_version_extraction_status(
                connection,
                law_version_id,
                extraction_status
            )

            # =================================================
            # CHAPTERS
            # =================================================

            transformed_chapters = (
                transform_chapters(
                    text,
                    law_id
                )
            )

            # Keep DB IDs together with their positions
            # in the source text.
            chapter_records = []

            for chapter in transformed_chapters:

                chapter_start = chapter[
                    "_start"
                ]

                # _start is temporary parsing metadata.
                # Do not send it to PostgreSQL.
                chapter_to_load = {
                    "law_id": chapter[
                        "law_id"
                    ],
                    "title_en": chapter[
                        "title_en"
                    ],
                    "title_ar": chapter[
                        "title_ar"
                    ],
                }

                (
                    chapter_id,
                    chapter_created
                ) = get_or_create_chapter(
                    connection,
                    chapter_to_load
                )

                chapter_records.append({
                    "id": chapter_id,
                    "start": chapter_start,
                    "title_ar": chapter[
                        "title_ar"
                    ],
                })

            # =================================================
            # ARTICLES
            # =================================================

            transformed_articles = (
                transform_articles(text)
            )

            # ------------------------------------------------
            # Load each article
            # ------------------------------------------------

            for article in transformed_articles:

                article_start = article[
                    "_start"
                ]

                # --------------------------------------------
                # Find the closest chapter appearing before
                # this article in the source document.
                # --------------------------------------------

                applicable_chapters = [
                    chapter
                    for chapter in chapter_records
                    if (
                        chapter["start"]
                        <= article_start
                    )
                ]

                if applicable_chapters:

                    selected_chapter = max(
                        applicable_chapters,
                        key=lambda chapter: (
                            chapter["start"]
                        )
                    )

                else:
                    # ----------------------------------------
                    # This can happen when a document has
                    # headings, but some articles appear
                    # before the first heading.
                    # ----------------------------------------

                    fallback_chapter = {
                        "law_id": law_id,
                        "title_en": "No Chapters",
                        "title_ar": "بدون فصول",
                    }

                    (
                        fallback_chapter_id,
                        _
                    ) = get_or_create_chapter(
                        connection,
                        fallback_chapter
                    )

                    selected_chapter = {
                        "id": fallback_chapter_id,
                        "start": 0,
                        "title_ar": "بدون فصول",
                    }

                # --------------------------------------------
                # Remove temporary _start before DB insert
                # --------------------------------------------

                article_to_load = {
                    "chapter_id": (
                        selected_chapter["id"]
                    ),
                    "title_en": article[
                        "title_en"
                    ],
                    "title_ar": article[
                        "title_ar"
                    ],
                    "content_en": article[
                        "content_en"
                    ],
                    "content_ar": article[
                        "content_ar"
                    ],
                }

                # --------------------------------------------
                # Load article
                # --------------------------------------------

                (
                    article_id,
                    article_created
                ) = get_or_create_article(
                    connection,
                    article_to_load
                )

                # --------------------------------------------
                # Transform article version
                # --------------------------------------------

                transformed_article_version = (
                    transform_articles_versions(
                        [article_to_load],
                        law_version,
                        status
                    )[0]
                )

                # --------------------------------------------
                # Load article version
                # --------------------------------------------

                (
                    article_version_id,
                    article_version_created
                ) = get_or_create_article_version(
                    connection,
                    transformed_article_version,
                    article_id,
                    law_version_id,
                    status_id
                )

            # =================================================
            # BRONZE CHECKPOINT
            #
            # We only reach this point if the entire law,
            # including ALL articles and article versions,
            # completed successfully.
            # =================================================

            mark_bronze_object_processed(
                connection,
                key
            )
            
            # ------------------------------------------------
            # Progress
            # ------------------------------------------------

            print(
                f"  -> Law ID: {law_id} | "
                f"Version ID: {law_version_id} | "
                f"Chapters: "
                f"{len(transformed_chapters)} | "
                f"Articles: "
                f"{len(transformed_articles)}"
            )
            

        print()
        print("=" * 80)
        print("Pipeline completed.")
        print("=" * 80)

    finally:
        connection.close()

# ============================================================
# Entry point
# ============================================================

if __name__ == "__main__":
    import sys

    collection_date = (
        sys.argv[1]
        if len(sys.argv) > 1
        else None
    )

    main(collection_date=collection_date)