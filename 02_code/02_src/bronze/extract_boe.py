import csv
import os
import re
import time

from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from pathlib import Path
from urllib.parse import urljoin
from io import BytesIO

import requests
import urllib3

from bs4 import BeautifulSoup
from minio import Minio


# =========================================================
# Configuration
# =========================================================

BASE_URL = "https://laws.boe.gov.sa"

BOE_PROXY_URL = os.getenv("BOE_PROXY_URL")

BOE_VERIFY_SSL = (
    os.getenv("BOE_VERIFY_SSL", "true")
    .strip()
    .lower()
    in ("1", "true", "yes")
)


def get_request_proxies():

    if not BOE_PROXY_URL:
        return None

    return {
        "http": BOE_PROXY_URL,
        "https": BOE_PROXY_URL,
    }


PROJECT_DIR = Path(__file__).resolve().parent

RAW_DIR = PROJECT_DIR / "data" / "raw"
LOG_DIR = PROJECT_DIR / "data" / "processed"


SEARCH_URL = (
    f"{BASE_URL}/BoeLaws/Laws/Search?"
    "PageNumber={page}"
    "&LanguageId=1"
    "&SearchText="
    "&LawTypeId="
    "&LawCategoryId="
    "&LawStatusId="
    "&SortBy=IssueDate"
    "&SortDirection=DESC"
)

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
}


# =========================================================
# SeaweedFS
# =========================================================

SEAWEEDFS_CLIENT = Minio(
    "74.235.104.131:8333",
    access_key="",
    secret_key="",
    secure=False,
)

SEAWEEDFS_BUCKET = "bayan-bronze"


urllib3.disable_warnings(
    urllib3.exceptions.InsecureRequestWarning
)


# =========================================================
# HTTP
# =========================================================

def fetch_page(url, max_retries=5):

    for attempt in range(1, max_retries + 1):

        try:
            response = requests.get(
                url,
                headers=HEADERS,
                timeout=60,
                proxies=get_request_proxies(),
                verify=BOE_VERIFY_SSL,
            )

            response.raise_for_status()

            return response

        except (
            requests.exceptions.SSLError,
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
        ) as e:

            if attempt == max_retries:
                print(
                    f"Request failed after {max_retries} attempts: {url}"
                )
                raise

            wait_seconds = 2 ** attempt

            print(
                f"Request failed "
                f"(attempt {attempt}/{max_retries}): "
                f"{type(e).__name__}"
            )

            print(
                f"Retrying in {wait_seconds} seconds..."
            )

            time.sleep(wait_seconds)
# =========================================================
# Generic HTML helpers
# =========================================================

def get_label_value(soup, label_text):

    for label in soup.find_all("label"):

        text = label.get_text(
            " ",
            strip=True,
        )

        if label_text in text:

            parent = label.parent

            if parent:

                span = parent.find("span")

                if span:

                    value = span.get_text(
                        " ",
                        strip=True,
                    )

                    if value:
                        return value

                value = parent.get_text(
                    " ",
                    strip=True,
                )

                value = value.replace(
                    text,
                    "",
                    1,
                ).strip()

                if value:
                    return value

    return None


# =========================================================
# Date extraction
# =========================================================

def extract_gregorian_date(text):

    if not text:
        return None

    match = re.search(
        r"(?:Corresponding\s*To|الموافق)\s*:?\s*"
        r"(\d{1,2})/(\d{1,2})/(\d{4})",
        text,
        re.IGNORECASE,
    )

    if not match:
        return None

    day, month, year = match.groups()

    return (
        f"{year}-"
        f"{month.zfill(2)}-"
        f"{day.zfill(2)}"
    )


def extract_date_from_label(
    soup,
    label_text,
):

    value = get_label_value(
        soup,
        label_text,
    )

    return extract_gregorian_date(value)


# =========================================================
# Status
# =========================================================

def translate_status(status):

    if not status:
        return None

    status = status.strip()

    mapping = {
        "Active": "Active",
        "Repealed": "Repealed",
        "ساري": "Active",
        "لاغي": "Repealed",
        "ملغي": "Repealed",
    }

    for key, value in mapping.items():

        if status.lower().startswith(
            key.lower()
        ):
            return value

    return status


def get_status(soup):

    value = get_label_value(
        soup,
        "الحالة",
    )

    if value:
        return translate_status(value)

    page_text = soup.get_text(
        " ",
        strip=True,
    )

    match = re.search(
        r"Law\s*Status\s*(Active|Repealed)",
        page_text,
        re.IGNORECASE,
    )

    if match:

        return translate_status(
            match.group(1)
        )

    return None


# =========================================================
# Law metadata
# =========================================================

def get_law_name(soup):

    value = get_label_value(
        soup,
        "الاسم",
    )

    if value:
        return value

    page_text = soup.get_text(
        " ",
        strip=True,
    )

    match = re.search(
        r"Law\s*name\s*(.*?)\s*Law\s*description",
        page_text,
        re.IGNORECASE,
    )

    if match:
        return match.group(1).strip()

    return None


def get_law_description(soup):

    brief = soup.find(
        "div",
        class_="system_brief",
    )

    if brief:

        container = brief.find(
            "div",
            class_="HTMLContainer",
        )

        if container:

            value = container.get_text(
                " ",
                strip=True,
            )

            if value:
                return value

    page_text = soup.get_text(
        " ",
        strip=True,
    )

    match = re.search(
        r"Law\s*description\s*(.*?)\s*Law\s*Name",
        page_text,
        re.IGNORECASE,
    )

    if match:
        return match.group(1).strip()

    return None


def get_issuing_tool(soup):

    value = get_label_value(
        soup,
        "أدوات إصدار النظام",
    )

    if value:
        return value

    for label in soup.find_all("label"):

        text = label.get_text(
            " ",
            strip=True,
        )

        if "Issue Tools" in text:

            parent = label.parent

            if parent:

                link = parent.find("a")

                if link:

                    return link.get_text(
                        " ",
                        strip=True,
                    )

    return None


# =========================================================
# Translated document
# =========================================================

def find_translated_document_url(soup):

    for a in soup.find_all(
        "a",
        href=True,
    ):

        link_text = a.get_text(
            " ",
            strip=True,
        ).lower()

        href = a["href"]

        if (
            "translated document" in link_text
            or "الوثيقة المترجمة" in link_text
        ):

            return urljoin(
                BASE_URL,
                href,
            )

    return None


# =========================================================
# Document ID
# =========================================================

def get_document_id(url):

    match = re.search(
        r"/LawDetails/([0-9a-fA-F-]+)/",
        url,
    )

    if match:
        return match.group(1)

    return None


# =========================================================
# Discover law URLs
# =========================================================

def discover_law_urls(page_number):

    url = SEARCH_URL.format(
        page=page_number
    )

    response = fetch_page(url)

    soup = BeautifulSoup(
        response.text,
        "html.parser",
    )

    urls = []

    for a in soup.find_all(
        "a",
        href=True,
    ):

        href = a["href"]

        if "/BoeLaws/Laws/LawDetails/" in href:

            full_url = urljoin(
                BASE_URL,
                href,
            )

            if full_url not in urls:
                urls.append(full_url)

    return urls


# =========================================================
# SeaweedFS upload
# =========================================================

def upload_to_seaweedfs(
    content,
    object_name,
    content_type,
):

    SEAWEEDFS_CLIENT.put_object(
        SEAWEEDFS_BUCKET,
        object_name,
        BytesIO(content),
        length=len(content),
        content_type=content_type,
    )


# =========================================================
# Extract individual document
# =========================================================

def extract_document(
    url,
    run_date,
):

    try:

        response = fetch_page(url)

        soup = BeautifulSoup(
            response.text,
            "html.parser",
        )

        document_id = get_document_id(url)

        if not document_id:

            raise ValueError(
                "Could not extract document ID from URL"
            )

        law_name = get_law_name(soup)

        law_description = (
            get_law_description(soup)
        )

        issue_date = extract_date_from_label(
            soup,
            "تاريخ الإصدار",
        )

        publication_date = (
            extract_date_from_label(
                soup,
                "تاريخ النشر",
            )
        )

        status = get_status(soup)

        issuing_tool = get_issuing_tool(
            soup
        )

        translated_document_url = (
            find_translated_document_url(
                soup
            )
        )

        # ---------------------------------------------
        # Raw HTML text
        # ---------------------------------------------

        raw_text = soup.get_text(
            "\n",
            strip=True,
        )

        txt_object_name = (
            f"{run_date}/"
            f"{document_id}/"
            "raw.txt"
        )

        upload_to_seaweedfs(
            raw_text.encode("utf-8"),
            txt_object_name,
            "text/plain; charset=utf-8",
        )

        # ---------------------------------------------
        # Optional translated PDF
        # ---------------------------------------------

        pdf_object_name = None

        if translated_document_url:

            pdf_response = fetch_page(
                translated_document_url
            )

            pdf_object_name = (
                f"{run_date}/"
                f"{document_id}/"
                "translated.pdf"
            )

            upload_to_seaweedfs(
                pdf_response.content,
                pdf_object_name,
                "application/pdf",
            )

        # ---------------------------------------------
        # Metadata
        # ---------------------------------------------

        document = {
            "document_id":
                document_id,

            "law_name":
                law_name,

            "law_description":
                law_description,

            "document_type":
                "Law",

            "issue_date":
                issue_date,

            "publication_date":
                publication_date,

            "status":
                status,

            "issuing_tool":
                issuing_tool,

            "source_name":
                "Bureau of Experts at the Council of Ministers",

            "source_url":
                url,

            "translated_document_url":
                translated_document_url,

            "bronze_txt_path":
                txt_object_name,

            "bronze_pdf_path":
                pdf_object_name,

            "collected_at":
                datetime.now(
                    timezone.utc
                ).isoformat(),
        }

        return document

    except Exception as e:

        return {
            "source_url": url,
            "error": str(e),
        }


# =========================================================
# Save scraping log
# =========================================================

def save_log(results):

    LOG_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    log_file = (
        LOG_DIR
        / "scrape_log.csv"
    )

    with open(
        log_file,
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=[
                "source_url",
                "status",
                "error",
            ],
        )

        writer.writeheader()

        for result in results:

            writer.writerow({
                "source_url":
                    result.get(
                        "source_url"
                    ),

                "status":
                    (
                        "FAILED"
                        if result.get("error")
                        else "SUCCESS"
                    ),

                "error":
                    result.get(
                        "error"
                    ),
            })


# =========================================================
# Main scraper
# =========================================================

def run_scraper(run_date=None):

    if run_date is None:

        run_date = datetime.now(
            ZoneInfo("Asia/Riyadh")
        ).strftime(
            "%Y-%m-%d"
        )

    print(
        f"Bronze collection date: "
        f"{run_date}"
    )

    if BOE_PROXY_URL:

        print(
            "BOE proxy: enabled"
        )

    else:

        print(
            "BOE proxy: disabled"
        )

    all_urls = []

    page_number = 1

    # -----------------------------------------------------
    # Discover all law URLs
    # -----------------------------------------------------

    while True:

        print(
            f"Discovering page "
            f"{page_number}..."
        )

        urls = discover_law_urls(
            page_number
        )

        if not urls:
            break

        for url in urls:

            if url not in all_urls:
                all_urls.append(url)

        page_number += 1

        time.sleep(1)

    print(
        f"\nTotal unique law URLs: "
        f"{len(all_urls)}"
    )

    # -----------------------------------------------------
    # Extract documents
    # -----------------------------------------------------

    results = []

    success_count = 0
    failed_count = 0

    for i, url in enumerate(
        all_urls,
        start=1,
    ):

        print(
            f"Scraping "
            f"{i}/{len(all_urls)}"
        )

        result = extract_document(
            url,
            run_date,
        )

        results.append(result)

        if result.get("error"):

            failed_count += 1

            print(
                "FAILED:",
                result["error"],
            )

        else:

            success_count += 1

            print(
                "SUCCESS:",
                result.get(
                    "law_name"
                ),
            )

        time.sleep(1)

    # -----------------------------------------------------
    # Save run log
    # -----------------------------------------------------

    save_log(results)

    print(
        "\n=============================="
    )

    print(
        "SCRAPING COMPLETED"
    )

    print(
        "=============================="
    )

    print(
        f"Total URLs: "
        f"{len(all_urls)}"
    )

    print(
        f"Successful: "
        f"{success_count}"
    )

    print(
        f"Failed: "
        f"{failed_count}"
    )

    print(
        f"SeaweedFS bucket: "
        f"{SEAWEEDFS_BUCKET}"
    )


# =========================================================
# Entry point
# =========================================================

if __name__ == "__main__":
    run_scraper()