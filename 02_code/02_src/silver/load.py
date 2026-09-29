from silver.transform import normalize_text_for_hash

# ============================================================
# BRONZE PROCESSING CHECKPOINT
# ============================================================

def is_bronze_object_processed(
    connection,
    raw_object_key
):
    """
    Return True if this Bronze object has already been
    completely processed by the Silver pipeline.
    """

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT 1
        FROM silver.processed_bronze_objects
        WHERE raw_object_key = %s
        LIMIT 1
        """,
        (raw_object_key,)
    )

    result = cursor.fetchone()

    cursor.close()

    return result is not None


def mark_bronze_object_processed(
    connection,
    raw_object_key
):
    """
    Mark a Bronze object as successfully processed.

    This must only be called AFTER the complete law,
    including chapters, articles, and article versions,
    has finished successfully.
    """

    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO silver.processed_bronze_objects (
            raw_object_key
        )
        VALUES (%s)
        ON CONFLICT (raw_object_key)
        DO NOTHING
        """,
        (raw_object_key,)
    )

    connection.commit()

    cursor.close()

# ============================================================
# SOURCE
# ============================================================

def get_source_id(
    connection,
    source_name
):

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id
        FROM silver.sources
        WHERE name_en = %s
        """,
        (source_name,)
    )

    result = cursor.fetchone()

    cursor.close()

    return result[0] if result else None


# ============================================================
# LAW
# ============================================================

def get_or_create_law(
    connection,
    law
):

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id
        FROM silver.laws
        WHERE source_id = %s
          AND title_ar = %s
          AND issue_date = %s
        LIMIT 1
        """,
        (
            law["source_id"],
            law["title_ar"],
            law["issue_date"],
        )
    )

    result = cursor.fetchone()

    if result:

        law_id = result[0]

        cursor.close()

        return law_id, False

    cursor.execute(
        """
        INSERT INTO silver.laws (
            source_id,
            title_en,
            title_ar,
            issue_date,
            issue_date_hijri,
            publication_date,
            publication_date_hijri,
            collected_at
        )
        VALUES (
            %(source_id)s,
            %(title_en)s,
            %(title_ar)s,
            %(issue_date)s,
            %(issue_date_hijri)s,
            %(publication_date)s,
            %(publication_date_hijri)s,
            %(collected_at)s
        )
        RETURNING id
        """,
        law
    )

    law_id = cursor.fetchone()[0]

    connection.commit()

    cursor.close()

    return law_id, True


# ============================================================
# LAW VERSION
# ============================================================

def get_or_create_law_version(
    connection,
    law_version
):

    cursor = connection.cursor()

    # --------------------------------------------------------
    # Check whether this exact version already exists
    # --------------------------------------------------------

    cursor.execute(
        """
        SELECT id
        FROM silver.laws_versions
        WHERE law_id = %s
          AND hash = %s
        LIMIT 1
        """,
        (
            law_version["law_id"],
            law_version["hash"],
        )
    )

    result = cursor.fetchone()

    if result:
        law_version_id = result[0]

        # Important:
        # Existing rows may have been created before status_id
        # was added, so update it.
        cursor.execute(
            """
            UPDATE silver.laws_versions
            SET status_id = %s
            WHERE id = %s;
            """,
            (
                law_version["status_id"],
                law_version_id,
            )
        )

        connection.commit()
        cursor.close()

        return law_version_id, False

    # --------------------------------------------------------
    # Determine version number
    # --------------------------------------------------------

    cursor.execute(
        """
        SELECT COALESCE(MAX(version_number), 0)
        FROM silver.laws_versions
        WHERE law_id = %s
        """,
        (
            law_version["law_id"],
        )
    )

    max_version = cursor.fetchone()[0]

    version_number = max_version + 1
    is_changed = version_number > 1

    # --------------------------------------------------------
    # Insert version
    # --------------------------------------------------------

    cursor.execute(
        """
        INSERT INTO silver.laws_versions (
            law_id,
            version_number,
            status_id,
            effective_date,
            hash,
            raw_object_key,
            is_changed,
            collected_at
        )
        VALUES (
            %s, %s, %s, %s,
            %s, %s, %s, %s
        )
        RETURNING id;
        """,
        (
            law_version["law_id"],
            version_number,
            law_version["status_id"],
            law_version["effective_date"],
            law_version["hash"],
            law_version["raw_object_key"],
            is_changed,
            law_version["collected_at"],
        )
    )

    law_version_id = cursor.fetchone()[0]

    connection.commit()
    cursor.close()

    return law_version_id, True

def save_law_version_extraction_status(
    connection,
    law_version_id,
    extraction_status
):

    cursor = connection.cursor()

    # Check whether this extraction result
    # already exists for this law version + field.
    cursor.execute(
        """
        SELECT id
        FROM silver.law_version_extraction_status
        WHERE law_version_id = %s
          AND field_name = %s
        LIMIT 1;
        """,
        (
            law_version_id,
            extraction_status["field_name"],
        )
    )

    existing = cursor.fetchone()

    if existing:

        extraction_status_id = existing[0]

        cursor.execute(
            """
            UPDATE silver.law_version_extraction_status
            SET
                status = %s,
                reason = %s,
                detected_rule = %s
            WHERE id = %s;
            """,
            (
                extraction_status["status"],
                extraction_status["reason"],
                extraction_status["detected_rule"],
                extraction_status_id,
            )
        )

        connection.commit()
        cursor.close()

        return extraction_status_id, False

    cursor.execute(
        """
        INSERT INTO silver.law_version_extraction_status (
            law_version_id,
            field_name,
            status,
            reason,
            detected_rule
        )
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id;
        """,
        (
            law_version_id,
            extraction_status["field_name"],
            extraction_status["status"],
            extraction_status["reason"],
            extraction_status["detected_rule"],
        )
    )

    extraction_status_id = cursor.fetchone()[0]

    connection.commit()
    cursor.close()

    return extraction_status_id, True

# ============================================================
# CHAPTER
# ============================================================

def get_or_create_chapter(
    connection,
    chapter
):

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id
        FROM silver.chapters
        WHERE law_id = %s
          AND title_ar = %s
        LIMIT 1
        """,
        (
            chapter["law_id"],
            chapter["title_ar"],
        )
    )

    result = cursor.fetchone()

    if result:

        chapter_id = result[0]

        cursor.close()

        return chapter_id, False


    cursor.execute(
        """
        INSERT INTO silver.chapters (
            title_en,
            title_ar,
            law_id
        )
        VALUES (
            %(title_en)s,
            %(title_ar)s,
            %(law_id)s
        )
        RETURNING id
        """,
        chapter
    )

    chapter_id = cursor.fetchone()[0]

    connection.commit()

    cursor.close()

    return chapter_id, True


# ============================================================
# ARTICLE
# ============================================================


def get_or_create_article(
    connection,
    article
):
    """
    Get or create a physical article revision.

    silver.articles stores article CONTENT REVISIONS.

    Same logical article + same normalized content:
        reuse existing article row.

    Same logical article + different normalized content:
        create a new article row.

    Existing rows are NEVER updated.
    """

    cursor = connection.cursor()

    try:
        # Normalize the incoming content using exactly the
        # same normalization used for hashing/change detection.
        current_normalized_content = normalize_text_for_hash(
            article.get("content_ar")
        )

        # Find all previous physical revisions for this
        # logical article.
        cursor.execute(
            """
            SELECT
                id,
                content_ar
            FROM silver.articles
            WHERE chapter_id = %s
              AND title_ar IS NOT DISTINCT FROM %s
            ORDER BY id DESC
            """,
            (
                article["chapter_id"],
                article["title_ar"],
            )
        )

        existing_articles = cursor.fetchall()

        # Compare normalized content rather than raw content.
        for existing_id, existing_content in existing_articles:

            existing_normalized_content = normalize_text_for_hash(
                existing_content
            )

            if (
                existing_normalized_content
                == current_normalized_content
            ):
                return existing_id, False

        # No matching normalized revision exists.
        # Therefore this is a genuinely new physical revision.
        cursor.execute(
            """
            INSERT INTO silver.articles (
                chapter_id,
                title_en,
                title_ar,
                content_en,
                content_ar
            )
            VALUES (
                %(chapter_id)s,
                %(title_en)s,
                %(title_ar)s,
                %(content_en)s,
                %(content_ar)s
            )
            RETURNING id
            """,
            article
        )

        article_id = cursor.fetchone()[0]

        connection.commit()

        return article_id, True

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
# ============================================================
# ARTICLE VERSION
# ============================================================


def get_or_create_article_version(
    connection,
    article_version,
    article_id,
    law_version_id,
    status_id
):
    """
    Create the relationship between an article revision and a
    law version.

    Historical model
    ----------------

    If an article does not change:

        law version 1 ----\
                           -> article row 920
        law version 2 ----/

    If the article changes:

        law version 1 -> article row 920
                         OLD CONTENT

        law version 2 -> article row 1201
                         NEW CONTENT


    is_changed semantics
    --------------------

    False:
        - first known occurrence of the logical article, OR
        - content/hash is unchanged from the previous version.

    True:
        - this version differs from the immediately previous
          version of the same logical article.


    Logical article identity
    ------------------------

    A logical article is identified using:

        law
        + chapter title
        + article title

    We deliberately do NOT search history using article_id,
    because a changed article receives a new article_id.
    """

    cursor = connection.cursor()

    try:
        # ====================================================
        # 1. Load information about the CURRENT article row.
        # ====================================================

        cursor.execute(
            """
            SELECT
                a.id,
                a.title_ar,
                a.content_ar,
                a.chapter_id,
                c.title_ar AS chapter_title_ar,
                c.law_id
            FROM silver.articles a

            JOIN silver.chapters c
                ON c.id = a.chapter_id

            WHERE a.id = %s

            LIMIT 1
            """,
            (
                article_id,
            )
        )

        current_article = cursor.fetchone()

        if current_article is None:
            raise ValueError(
                f"Article ID {article_id} does not exist "
                f"in silver.articles."
            )

        current_article_id = current_article[0]
        current_article_title = current_article[1]
        current_article_content = current_article[2]
        current_chapter_id = current_article[3]
        current_chapter_title = current_article[4]
        current_law_id = current_article[5]

        # ====================================================
        # 2. Load information about the CURRENT law version.
        # ====================================================

        cursor.execute(
            """
            SELECT
                id,
                law_id,
                version_number
            FROM silver.laws_versions
            WHERE id = %s
            LIMIT 1
            """,
            (
                law_version_id,
            )
        )

        current_law_version = cursor.fetchone()

        if current_law_version is None:
            raise ValueError(
                f"Law version ID {law_version_id} does not "
                f"exist in silver.laws_versions."
            )

        current_law_version_id = current_law_version[0]
        law_version_law_id = current_law_version[1]
        current_version_number = current_law_version[2]

        # ====================================================
        # 3. Safety check.
        #
        # The article and law version MUST belong to the
        # same law.
        # ====================================================

        if current_law_id != law_version_law_id:
            raise ValueError(
                "Article/law-version mismatch. "
                f"Article {article_id} belongs to law "
                f"{current_law_id}, but law version "
                f"{law_version_id} belongs to law "
                f"{law_version_law_id}."
            )

        current_hash = article_version["hash"]

        # ====================================================
        # 4. Check whether this law version has already been
        # linked to this exact article revision.
        #
        # This makes reruns idempotent.
        # ====================================================

        cursor.execute(
            """
            SELECT
                id,
                hash,
                is_changed
            FROM silver.articles_versions
            WHERE article_id = %s
              AND law_version_id = %s
            LIMIT 1
            """,
            (
                article_id,
                law_version_id,
            )
        )

        existing = cursor.fetchone()

        if existing is not None:
            article_version_id = existing[0]

            return article_version_id, False

        # ====================================================
        # 5. Find the immediately previous version of this
        # LOGICAL article.
        #
        # DO NOT use:
        #
        #     WHERE av.article_id = article_id
        #
        # because changed content gets a NEW article_id.
        #
        # Instead:
        #
        #   same law
        #   same chapter title
        #   same article title
        #   earlier law version
        # ====================================================

        cursor.execute(
            """
            SELECT
                av.id AS article_version_id,
                av.article_id,
                av.hash,
                av.is_changed,

                lv.id AS law_version_id,
                lv.version_number,

                previous_article.content_ar

            FROM silver.articles_versions av

            JOIN silver.articles previous_article
                ON previous_article.id = av.article_id

            JOIN silver.chapters previous_chapter
                ON previous_chapter.id =
                   previous_article.chapter_id

            JOIN silver.laws_versions lv
                ON lv.id = av.law_version_id

            WHERE previous_chapter.law_id = %s

              AND previous_chapter.title_ar
                  IS NOT DISTINCT FROM %s

              AND previous_article.title_ar
                  IS NOT DISTINCT FROM %s

              AND lv.version_number < %s

            ORDER BY
                lv.version_number DESC,
                av.id DESC

            LIMIT 1
            """,
            (
                current_law_id,
                current_chapter_title,
                current_article_title,
                current_version_number,
            )
        )

        previous = cursor.fetchone()

        # ====================================================
        # 6. Determine is_changed.
        # ====================================================

        if previous is None:
            # ------------------------------------------------
            # No previous version exists.
            #
            # This is the first known occurrence of this
            # logical article.
            # ------------------------------------------------

            is_changed = False

        else:
            previous_article_version_id = previous[0]
            previous_article_id = previous[1]
            previous_hash = previous[2]
            previous_is_changed = previous[3]
            previous_law_version_id = previous[4]
            previous_version_number = previous[5]
            previous_content = previous[6]

            # ------------------------------------------------
            # Compare the stored article hashes.
            #
            # Different hash:
            #     current version changed.
            #
            # Same hash:
            #     unchanged.
            # ------------------------------------------------

            is_changed = (
                previous_hash != current_hash
            )

        # ====================================================
        # 7. Insert the article-version relationship.
        #
        # IMPORTANT:
        #
        # We mark the CURRENT version as changed.
        #
        # We do NOT go back and modify the previous version.
        # ====================================================

        cursor.execute(
            """
            INSERT INTO silver.articles_versions (
                article_id,
                law_version_id,
                hash,
                is_changed,
                status_id
            )
            VALUES (
                %s,
                %s,
                %s,
                %s,
                %s
            )
            RETURNING id
            """,
            (
                article_id,
                law_version_id,
                current_hash,
                is_changed,
                status_id,
            )
        )

        article_version_id = cursor.fetchone()[0]

        connection.commit()

        return article_version_id, True

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        
# ============================================================
# STATUS
# ============================================================

def get_or_create_status(
    connection,
    status
):

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id
        FROM silver.status
        WHERE status_ar = %s
        LIMIT 1
        """,
        (
            status["status_ar"],
        )
    )

    result = cursor.fetchone()

    if result:

        status_id = result[0]

        cursor.close()

        return status_id, False

    cursor.execute(
        """
        INSERT INTO silver.status (
            status_en,
            status_ar
        )
        VALUES (
            %(status_en)s,
            %(status_ar)s
        )
        RETURNING id
        """,
        status
    )

    status_id = cursor.fetchone()[0]

    connection.commit()

    cursor.close()

    return status_id, True