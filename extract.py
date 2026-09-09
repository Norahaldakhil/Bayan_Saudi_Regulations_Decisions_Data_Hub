import csv
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

import requests
import urllib3
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


BASE_URL = "https://laws.boe.gov.sa"

RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"
LOG_DIR = Path(__file__).resolve().parents[1] / "data" / "processed"

SEARCH_URL = (
    "https://laws.boe.gov.sa/BoeLaws/Laws/Search/"
    "?PageNumber={page}"
    "&LanguageId=1"
    "&FolderId="
    "&PartId="
    "&Name="
    "&SearchTypeId=0"
    "&Query=%20"
    "&LawStatusId="
    "&IssueDateFrom="
    "&IssueDateTo="
    "&PublishDateFrom="
    "&PublishDateTo="
    "&returnUrl="
    "&TitlesOnly=False"
    "&MatchSearchResult=False"
    "&SortDirection=DES"
    "&IsDisplayWithUpdated="
)


def fetch_page(url):
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "en-US,en;q=0.9,ar;q=0.8"
    }

    response = requests.get(
        url,
        headers=headers,
        timeout=30,
        verify=False
    )

    response.raise_for_status()
    return response.text


def get_between(text, start_text, end_text):
    pattern = (
        re.escape(start_text)
        + r"\s*(.*?)\s*"
        + re.escape(end_text)
    )

    match = re.search(
        pattern,
        text,
        re.DOTALL | re.IGNORECASE
    )

    if match:
        return " ".join(match.group(1).split())

    return None


def extract_gregorian_date(text):
    if not text:
        return None

    match = re.search(
        r"\b(\d{2}/\d{2}/\d{4})\b",
        text
    )

    if not match:
        return None

    day, month, year = match.group(1).split("/")

    return f"{year}-{month}-{day}"


def translate_status(status):
    if not status:
        return None

    status = status.strip()

    status_map = {
        "ساري": "Active",
        "لاغي": "Repealed",
        "ملغي": "Repealed"
    }

    return status_map.get(status, status)


def find_original_document_url(soup, base_url):
    for link in soup.find_all("a", href=True):

        link_text = " ".join(
            link.get_text(" ", strip=True).split()
        ).lower()

        href = link.get("href", "")

        if (
            "original document" in link_text
            or "اصل الوثيقة" in link_text
            or "أصل الوثيقة" in link_text
            or "/viewer/" in href.lower()
        ):
            return urljoin(base_url, href)

    return None


def discover_law_urls(page_number):
    url = SEARCH_URL.format(page=page_number)

    print(f"Checking search page {page_number}...")

    html = fetch_page(url)

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    law_urls = []

    for link in soup.find_all("a", href=True):

        href = link["href"]

        if "/LawDetails/" in href:
            full_url = urljoin(
                BASE_URL,
                href
            )

            law_urls.append(full_url)

    return list(dict.fromkeys(law_urls))


def extract_document(url):
    html = fetch_page(url)

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    page_text = " ".join(
        soup.get_text(" ", strip=True).split()
    )

    law_name = get_between(
        page_text,
        "Law name",
        "Law description"
    )

    law_description = get_between(
        page_text,
        "Law description",
        "الاسم"
    )

    issue_date_raw = get_between(
        page_text,
        "تاريخ الإصدار",
        "تاريخ النشر"
    )

    publication_date_raw = get_between(
        page_text,
        "تاريخ النشر",
        "الحالة"
    )

    status_raw = get_between(
        page_text,
        "الحالة",
        "أدوات إصدار النظام"
    )

    original_document_url = find_original_document_url(
        soup,
        url
    )

    return {
        "law_name": law_name,
        "law_description": law_description,
        "document_type": "Law",
        "issue_date": extract_gregorian_date(issue_date_raw),
        "publication_date": extract_gregorian_date(publication_date_raw),
        "status": translate_status(status_raw),
        "source_name": "Bureau of Experts at the Council of Ministers",
        "source_url": url,
        "original_document_url": original_document_url,
        "collected_at": datetime.now(timezone.utc).isoformat()
    }


def make_safe_filename(name):
    if not name:
        return None

    name = name.lower().strip()

    name = re.sub(
        r"[^a-z0-9]+",
        "_",
        name
    )

    return name.strip("_")


def save_document(document):
    RAW_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    filename = make_safe_filename(
        document.get("law_name")
    )

    if not filename:
        return None

    output_path = RAW_DIR / f"{filename}.json"

    with open(
        output_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            document,
            file,
            ensure_ascii=False,
            indent=2
        )

    return output_path


def save_log(log_rows):
    LOG_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    log_path = LOG_DIR / "scrape_log.csv"

    fieldnames = [
        "url",
        "result",
        "law_name",
        "saved_file",
        "error",
        "scraped_at"
    ]

    with open(
        log_path,
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        writer.writeheader()
        writer.writerows(log_rows)

    return log_path


def run_scraper():
    all_urls = []
    page = 1

    while True:
        urls = discover_law_urls(page)

        if not urls:
            print("No more search results.")
            break

        new_urls = [
            url
            for url in urls
            if url not in all_urls
        ]

        if not new_urls:
            print("No new URLs found.")
            break

        all_urls.extend(new_urls)

        print(
            f"Page {page}: "
            f"{len(new_urls)} new URLs "
            f"(total {len(all_urls)})"
        )

        page += 1
        time.sleep(1)

    print(
        f"\nFound {len(all_urls)} unique law URLs."
    )

    success = 0
    skipped = 0
    failed = 0

    log_rows = []

    for index, url in enumerate(
        all_urls,
        start=1
    ):

        print(
            f"\n[{index}/{len(all_urls)}]"
        )

        print(
            f"Extracting: {url}"
        )

        scraped_at = datetime.now(
            timezone.utc
        ).isoformat()

        try:
            document = extract_document(url)

            if not document["law_name"]:

                print(
                    "Skipped: no English law name."
                )

                log_rows.append({
                    "url": url,
                    "result": "SKIPPED",
                    "law_name": "",
                    "saved_file": "",
                    "error": "No English law name",
                    "scraped_at": scraped_at
                })

                skipped += 1
                continue

            output = save_document(document)

            print(
                f"Saved: {output}"
            )

            log_rows.append({
                "url": url,
                "result": "SUCCESS",
                "law_name": document["law_name"],
                "saved_file": str(output),
                "error": "",
                "scraped_at": scraped_at
            })

            success += 1

        except Exception as error:

            print(
                f"FAILED: {error}"
            )

            log_rows.append({
                "url": url,
                "result": "FAILED",
                "law_name": "",
                "saved_file": "",
                "error": str(error),
                "scraped_at": scraped_at
            })

            failed += 1

        time.sleep(1)

    log_path = save_log(log_rows)

    print("\nFinished.")
    print(f"Success: {success}")
    print(f"Skipped: {skipped}")
    print(f"Failed: {failed}")
    print(f"Log saved to: {log_path}")


if __name__ == "__main__":
    run_scraper()