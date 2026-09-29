import hashlib
import re

from datetime import datetime, timedelta
import calendar

from hijridate import Hijri


def normalize_text_for_hash(text):
    """
    Normalize non-semantic text differences before hashing.

    This prevents false version changes caused by differences such as:
        Windows line endings: \\r\\n
        Unix line endings:   \\n
        Old Mac line endings: \\r

    It intentionally preserves:
        - Arabic text
        - punctuation
        - spaces inside lines
        - actual line structure
    """

    if text is None:
        return ""

    # Normalize all line endings to Unix LF.
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    # Remove trailing whitespace from each line.
    # This prevents "text   " and "text" from producing
    # different hashes because of invisible trailing spaces.
    lines = [
        line.rstrip(" \t")
        for line in text.split("\n")
    ]

    text = "\n".join(lines)

    # Ignore whitespace/newlines surrounding the whole article.
    return text.strip()

# ============================================================
# ARABIC ORDINAL NORMALIZATION
# ============================================================
ORDINAL_ONES = {
    1: "الأولى",
    2: "الثانية",
    3: "الثالثة",
    4: "الرابعة",
    5: "الخامسة",
    6: "السادسة",
    7: "السابعة",
    8: "الثامنة",
    9: "التاسعة",
}

ORDINAL_COMPOUND_ONES = {
    1: "الحادية",
    2: "الثانية",
    3: "الثالثة",
    4: "الرابعة",
    5: "الخامسة",
    6: "السادسة",
    7: "السابعة",
    8: "الثامنة",
    9: "التاسعة",
}

ORDINAL_TEENS = {
    10: "العاشرة",
    11: "الحادية عشرة",
    12: "الثانية عشرة",
    13: "الثالثة عشرة",
    14: "الرابعة عشرة",
    15: "الخامسة عشرة",
    16: "السادسة عشرة",
    17: "السابعة عشرة",
    18: "الثامنة عشرة",
    19: "التاسعة عشرة",
}

ORDINAL_TENS = {
    20: "العشرون",
    30: "الثلاثون",
    40: "الأربعون",
    50: "الخمسون",
    60: "الستون",
    70: "السبعون",
    80: "الثمانون",
    90: "التسعون",
}

ORDINAL_HUNDREDS = {
    100: "المائة",
    200: "المائتان",
    300: "الثلاثمائة",
    400: "الأربعمائة",
    500: "الخمسمائة",
    600: "الستمائة",
    700: "السبعمائة",
    800: "الثمانمائة",
    900: "التسعمائة",
}


def number_to_arabic_ordinal(number):

    number = int(number)

    if number <= 0:
        raise ValueError(
            f"Ordinal number must be positive: {number}"
        )

    # 1-9
    if number in ORDINAL_ONES:
        return ORDINAL_ONES[number]

    # 10-19
    if number in ORDINAL_TEENS:
        return ORDINAL_TEENS[number]

    # 20, 30, ..., 90
    if number in ORDINAL_TENS:
        return ORDINAL_TENS[number]

    # 21-99
    if number < 100:

        ones = number % 10
        tens = number - ones

        return (
            f"{ORDINAL_COMPOUND_ONES[ones]}"
            f" و{ORDINAL_TENS[tens]}"
        )

    # Exact hundreds
    if number in ORDINAL_HUNDREDS:
        return ORDINAL_HUNDREDS[number]

    # 101-999
    if number < 1000:

        hundreds = (
            number // 100
        ) * 100

        remainder = (
            number % 100
        )

        return (
            f"{number_to_arabic_ordinal(remainder)} "
            f"بعد {ORDINAL_HUNDREDS[hundreds]}"
        )

    raise ValueError(
        f"Unsupported ordinal number: {number}"
    )

def normalize_article_title(article_number):

    return (
        f"المادة "
        f"{number_to_arabic_ordinal(article_number)}"
    )

ORDINAL_MASCULINE_ONES = {
    1: "الأول",
    2: "الثاني",
    3: "الثالث",
    4: "الرابع",
    5: "الخامس",
    6: "السادس",
    7: "السابع",
    8: "الثامن",
    9: "التاسع",
}

ORDINAL_MASCULINE_TEENS = {
    10: "العاشر",
    11: "الحادي عشر",
    12: "الثاني عشر",
    13: "الثالث عشر",
    14: "الرابع عشر",
    15: "الخامس عشر",
    16: "السادس عشر",
    17: "السابع عشر",
    18: "الثامن عشر",
    19: "التاسع عشر",
}

ORDINAL_MASCULINE_TENS = {
    20: "العشرون",
    30: "الثلاثون",
    40: "الأربعون",
    50: "الخمسون",
    60: "الستون",
    70: "السبعون",
    80: "الثمانون",
    90: "التسعون",
}


def number_to_arabic_ordinal_masculine(number):

    number = int(number)

    if number <= 0:
        raise ValueError(
            f"Ordinal number must be positive: {number}"
        )

    # 1-9
    if number in ORDINAL_MASCULINE_ONES:
        return ORDINAL_MASCULINE_ONES[number]

    # 10-19
    if number in ORDINAL_MASCULINE_TEENS:
        return ORDINAL_MASCULINE_TEENS[number]

    # 20, 30, ..., 90
    if number in ORDINAL_MASCULINE_TENS:
        return ORDINAL_MASCULINE_TENS[number]

    # 21-99
    if number < 100:

        ones = number % 10
        tens = number - ones

        compound_ones = {
            1: "الحادي",
            2: "الثاني",
            3: "الثالث",
            4: "الرابع",
            5: "الخامس",
            6: "السادس",
            7: "السابع",
            8: "الثامن",
            9: "التاسع",
        }

        return (
            f"{compound_ones[ones]}"
            f" و{ORDINAL_MASCULINE_TENS[tens]}"
        )

    raise ValueError(
        f"Unsupported chapter number: {number}"
    )


def normalize_chapter_title(chapter_number):

    return (
        f"الفصل "
        f"{number_to_arabic_ordinal_masculine(chapter_number)}"
    )


def hijri_to_gregorian(year, month, day):
    try:
        gregorian = Hijri(
            int(year),
            int(month),
            int(day),
        ).to_gregorian()

        return datetime(
            gregorian.year,
            gregorian.month,
            gregorian.day,
        )

    except (ValueError, OverflowError):
        return None


def normalize_arabic(text):

    # Remove Arabic diacritics
    text = re.sub(
        r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]",
        "",
        text
    )

    # Normalize whitespace
    text = re.sub(r"[ \t]+", " ", text)

    return text


def transform_law(text, key, source_id):

    collecting_date = key.split("/")[0]

    collected_at = datetime.strptime(
        collecting_date,
        "%Y-%m-%d"
    )

    title_match = re.search(
        r"الاسم\s*\n(.+?)\s*\nتاريخ الإصدار",
        text
    )

    issue_match = re.search(
        r"تاريخ الإصدار\s*\n(.+?)\s*\nتاريخ النشر",
        text
    )

    publication_match = re.search(
        r"تاريخ النشر\s*\n(.+?)\s*\nالحالة",
        text
    )

    date_pattern = (
        r"(\d{4}/\d{2}/\d{2})\s*هـ"
        r".*?"
        r"(\d{2}/\d{2}/\d{4})\s*م"
    )
    
    normalized_text = normalize_arabic(text)
    
    immediate_match = re.search(
        r"(?:"
            r"يعمل\s+(?:به|بها|بهذا\s+\S+|بهذه\s+\S+|بالنظام|بالتنظيم|باللائحة)"
            r"|"
            r"يسري\s+(?:هذا\s+)?(?:النظام|التنظيم|القانون)"
            r"|"
            r"يسري\s+مفعول\s+(?:هذا\s+)?(?:النظام|التنظيم|القانون)"
            r"|"
            r"ينفذ\s+(?:هذا\s+)?(?:النظام|التنظيم|القانون)"
        r")"
        r"\s+(?:اعتبارا\s+)?من\s+تاريخ\s+نشر(?:ه|ها)"
        r"(?:\s+في\s+الجريدة\s+الرسمية)?",
        normalized_text
    )
            
    delayed_match = re.search(
        r"يعمل\s+"
        r"(?:به|بها|بهذا\s+\S+|بالنظام|بالتنظيم)"
        r"\s+بعد\s+"
        r"(?:مضي\s+)?"
        r"(.{1,60}?)\s+"
        r"من\s+تاريخ\s+نشر(?:ه|ها)",
        normalized_text
    )    

    issue_dates = re.search(
        date_pattern,
        issue_match.group(1)
    )
    
    

    issue_date_hijri = issue_dates.group(1) + " هـ"
    issue_date_gregorian = issue_dates.group(2)

    issue_date = datetime.strptime(
        issue_date_gregorian,
        "%d/%m/%Y"
    )

    publication_dates = re.search(
        date_pattern,
        publication_match.group(1)
    )

    if publication_dates:

        publication_date_hijri = (
            publication_dates.group(1) + " هـ"
        )

        publication_date_gregorian = (
            publication_dates.group(2)
        )

        publication_date = datetime.strptime(
            publication_date_gregorian,
            "%d/%m/%Y"
        )

    else:

        publication_date_hijri = None
        publication_date = None

    return {
        "source_id": source_id,
        "title_en": None,
        "title_ar": title_match.group(1).strip(),
        "issue_date": issue_date,
        "issue_date_hijri": issue_date_hijri,
        "publication_date": publication_date,
        "publication_date_hijri": publication_date_hijri,
        "collected_at": collected_at,
    }

def add_months(date, months):

    month = date.month - 1 + months

    year = date.year + month // 12

    month = month % 12 + 1

    day = min(
        date.day,
        calendar.monthrange(year, month)[1]
    )

    return date.replace(
        year=year,
        month=month,
        day=day
    )


def parse_effective_duration(duration):

    duration = duration.strip()

    # Numeric days: 90, 180, 120, etc.
    numeric_match = re.search(
        r"\(?\s*(\d+)\s*\)?",
        duration
    )

    if numeric_match:
        return (
            "days",
            int(numeric_match.group(1))
        )

    # Arabic number expressions for days
    day_values = [
        ("مائة وثمانين", 180),
        ("مئة وثمانين", 180),
        ("مائة وثمانيين", 180),
        ("مائة وعشرين", 120),
        ("مئة وعشرين", 120),
        ("ثلاثين", 30),
        ("ستين", 60),
        ("تسعين", 90),
        ("مائتين", 200),
    ]

    for phrase, days in day_values:

        if phrase in duration:
            return ("days", days)

    # Calendar months
    month_values = [
        ("ثمانية عشر شهرا", 18),
        ("ثمانية عشر شهراً", 18),
        ("ثمانية عشر شهرًا", 18),
        ("ستة أشهر", 6),
        ("ستة اشهر", 6),
        ("ثلاثة أشهر", 3),
        ("ثلاثة اشهر", 3),
        ("شهرين", 2),
        ("شهر", 1),
    ]

    for phrase, months in month_values:

        if phrase in duration:
            return ("months", months)

    # Years
    if "سنة" in duration or "عام" in duration:
        return ("months", 12)

    return None


def extract_effective_date(
    text,
    publication_date,
    issue_date
):

    normalized_text = normalize_arabic(text)

    # ==================================================
    # 1. Immediate from publication
    #
    # يعمل به من تاريخ نشره
    # يعمل بها من تاريخ نشرها
    # يعمل بهذا النظام من تاريخ نشره
    # ينفذ هذا النظام من تاريخ نشره
    # ==================================================

    immediate_match = re.search(
        r"(?:"
            r"يعمل\s+(?:به|بها|بهذا\s+\S+|بهذه\s+\S+|بالنظام|بالتنظيم|باللائحة)"
            r"|"
            r"ينفذ\s+(?:هذا\s+)?(?:النظام|التنظيم)"
            r"|"
            r"يسري\s+(?:هذا\s+)?(?:النظام|التنظيم)"
        r")"
        r"\s+من\s+تاريخ\s+نشر(?:ه|ها)",
        normalized_text
    )

    if immediate_match:

        if publication_date is None:
            return {
                "date": None,
                "status": "NOT_COMPUTABLE",
                "reason": "PUBLICATION_DATE_MISSING",
                "rule": "FROM_PUBLICATION",
            }

        return {
            "date": publication_date,
            "status": "EXTRACTED",
            "reason": None,
            "rule": "FROM_PUBLICATION",
        }
        
     # ==================================================
    # Direct statement of effectiveness from publication
    #
    # Example:
    # نفاذ الترتيبات من تاريخ نشرها في الجريدة الرسمية
    # ==================================================

    publication_effect_match = re.search(
        r"نفاذ\s+"
        r"(?:"
            r"النظام"
            r"|التنظيم"
            r"|اللائحة"
            r"|الترتيبات"
            r"|القواعد"
            r"|الضوابط"
        r")"
        r"\s+من\s+تاريخ\s+نشر(?:ه|ها)"
        r"(?:\s+في\s+الجريدة\s+الرسمية)?",
        normalized_text
    )

    if publication_effect_match:

        if publication_date is None:
            return {
                "date": None,
                "status": "NOT_COMPUTABLE",
                "reason": "PUBLICATION_DATE_MISSING",
                "rule": "FROM_PUBLICATION",
            }

        return {
            "date": publication_date,
            "status": "EXTRACTED",
            "reason": None,
            "rule": "FROM_PUBLICATION",
        }

    # ==================================================
    # 2. Next day from publication
    #
    # يعمل به من اليوم التالي لتاريخ نشره
    # يعمل به من اليوم التالي لنشره
    # يعمل بها من اليوم التالي من تاريخ نشرها
    # ==================================================

    next_day_match = re.search(
        r"(?:"
            r"يعمل\s+(?:به|بها|بهذا\s+\S+|بهذه\s+\S+|بالنظام|بالتنظيم|باللائحة)"
            r"|"
            r"يسري\s+(?:هذا\s+)?(?:النظام|التنظيم|القانون)"
            r"|"
            r"ينفذ\s+(?:هذا\s+)?(?:النظام|التنظيم|القانون)"
        r")"
        r"\s+(?:اعتبارا\s+)?من\s+اليوم\s+التالي\s+"
        r"(?:ل(?:تاريخ\s+)?نشر(?:ه|ها)|من\s+تاريخ\s+نشر(?:ه|ها))"
        r"(?:\s+في\s+الجريدة\s+الرسمية)?",
        normalized_text
    )

    if next_day_match:

        if publication_date is None:
            return {
                "date": None,
                "status": "NOT_COMPUTABLE",
                "reason": "PUBLICATION_DATE_MISSING",
                "rule": "NEXT_DAY_FROM_PUBLICATION",
            }

        return {
            "date": publication_date + timedelta(days=1),
            "status": "EXTRACTED",
            "reason": None,
            "rule": "NEXT_DAY_FROM_PUBLICATION",
        }

    # ==================================================
    # 3. First month after publication delay
    #
    # يعمل به ابتداء من أول الشهر التالي
    # لانقضاء ستين يوما من تاريخ نشره
    # ==================================================

    first_month_delay_match = re.search(
        r"يعمل\s+"
        r"(?:به|بها|بهذا\s+\S+|بهذه\s+\S+|بالنظام|بالتنظيم)"
        r"\s+ابتداء\s+من\s+"
        r"اول\s+الشهر\s+التالي\s+"
        r"لانقضاء\s+"
        r"(.{1,50}?)"
        r"\s+من\s+تاريخ\s+نشر(?:ه|ها)",
        normalized_text
    )

    if first_month_delay_match:

        duration = first_month_delay_match.group(1).strip()

        duration_result = parse_effective_duration(duration)

        if not duration_result:
            return {
                "date": None,
                "status": "ERROR",
                "reason": "DURATION_PARSE_FAILED",
                "rule": "FIRST_MONTH_AFTER_PUBLICATION_DELAY",
            }

        if publication_date is None:
            return {
                "date": None,
                "status": "NOT_COMPUTABLE",
                "reason": "PUBLICATION_DATE_MISSING",
                "rule": "FIRST_MONTH_AFTER_PUBLICATION_DELAY",
            }

        unit, value = duration_result

        if unit == "days":
            delayed_date = publication_date + timedelta(days=value)

        elif unit == "months":
            delayed_date = add_months(
                publication_date,
                value
            )

        else:
            return {
                "date": None,
                "status": "ERROR",
                "reason": "UNKNOWN_DURATION_UNIT",
                "rule": "FIRST_MONTH_AFTER_PUBLICATION_DELAY",
            }

        # First day of the following month
        if delayed_date.month == 12:
            effective_date = delayed_date.replace(
                year=delayed_date.year + 1,
                month=1,
                day=1
            )
        else:
            effective_date = delayed_date.replace(
                month=delayed_date.month + 1,
                day=1
            )

        return {
            "date": effective_date,
            "status": "EXTRACTED",
            "reason": None,
            "rule": "FIRST_MONTH_AFTER_PUBLICATION_DELAY",
        }

    # ==================================================
    # 4. Effective after executive regulation
    #
    # يعمل به بعد تسعين يوما من نشر لائحته التنفيذية
    # يبدأ تنفيذه بعد تسعين يوما من صدور اللائحة التنفيذية
    # ==================================================

    executive_regulation_match = re.search(
        r"(?:"
            r"يعمل"
            r"|يسري"
            r"|ينفذ"
            r"|يبدا\s+تنفيذه"
            r"|يكون\s+نافذا"
            r"|يدخل\s+حيز\s+النفاذ"
        r")"
        r".{0,60}?"
        r"(?:بعد(?:\s+مضي|\s+مرور)?|بمضي)"
        r"\s+"
        r"(.{1,50}?)"
        r"\s+"
        r"(?:من\s+)?"
        r"(?:تاريخ\s+)?"
        r"(?:صدور|نشر)"
        r"\s+"
        r"(?:لائحت(?:ه|ها)\s+التنفيذية|اللائحة\s+التنفيذية)",
        normalized_text
    )

    if executive_regulation_match:

        duration = executive_regulation_match.group(1).strip()

        duration_result = parse_effective_duration(duration)

        if not duration_result:
            return {
                "date": None,
                "status": "ERROR",
                "reason": "DURATION_PARSE_FAILED",
                "rule": "AFTER_EXECUTIVE_REGULATION",
            }

        return {
            "date": None,
            "status": "NOT_COMPUTABLE",
            "reason": "EXECUTIVE_REGULATION_DATE_MISSING",
            "rule": "AFTER_EXECUTIVE_REGULATION",
        }

    # ==================================================
    # 5. Delayed from publication
    #
    # يعمل به بعد تسعين يوما من تاريخ نشره
    # يسري هذا النظام بعد 180 يوما من تاريخ نشره
    # يكون نافذا بعد شهر من تاريخ نشره
    #
    # Also catches:
    # عمل بالنظام بعد مائة وثمانين يوما...
    # ==================================================

    delayed_match = re.search(
        r"(?:"
            r"يعمل"
            r"|عمل"
            r"|يسري"
            r"|ينفذ"
            r"|يكون\s+نافذا"
            r"|يدخل\s+حيز\s+النفاذ"
            r"|يبدا\s+تنفيذه"
        r")"
        r".{0,60}?"
        r"(?:"
            r"بعد(?:\s+مرور|\s+مضي)?"
            r"|بمضي"
        r")"
        r"\s+"
        r"(.{1,50}?)"
        r"\s+"
        r"من\s+"
        r"(?:تاريخ\s+)?"
        r"نشر(?:ه|ها|ة)?"
        r"(?:\s+في\s+الجريدة\s+الرسمية)?",
        normalized_text
    )

    if delayed_match:

        duration = delayed_match.group(1).strip()

        duration_result = parse_effective_duration(duration)

        if not duration_result:
            return {
                "date": None,
                "status": "ERROR",
                "reason": "DURATION_PARSE_FAILED",
                "rule": "AFTER_PUBLICATION",
            }

        if publication_date is None:
            return {
                "date": None,
                "status": "NOT_COMPUTABLE",
                "reason": "PUBLICATION_DATE_MISSING",
                "rule": "AFTER_PUBLICATION",
            }

        unit, value = duration_result

        if unit == "days":
            effective_date = (
                publication_date
                + timedelta(days=value)
            )

        elif unit == "months":
            effective_date = add_months(
                publication_date,
                value
            )

        else:
            return {
                "date": None,
                "status": "ERROR",
                "reason": "UNKNOWN_DURATION_UNIT",
                "rule": "AFTER_PUBLICATION",
            }

        return {
            "date": effective_date,
            "status": "EXTRACTED",
            "reason": None,
            "rule": "AFTER_PUBLICATION",
        }

    # ==================================================
    # 6. Immediate from issuance
    #
    # يعمل به من تاريخ صدوره
    # يعمل به من تاريخ صدور هذا المرسوم
    # ==================================================

    issuance_match = re.search(
        r"(?:"
            r"يعمل"
            r"|يسري"
            r"|ينفذ"
        r")"
        r".{0,50}?"
        r"(?:اعتبارا\s+)?"
        r"من\s+تاريخ\s+"
        r"(?:"
            r"صدور(?:ه|ها)"
            r"|صدور\s+هذا\s+(?:المرسوم|النظام|القرار)"
        r")",
        normalized_text
    )

    if issuance_match:

        if issue_date is None:
            return {
                "date": None,
                "status": "NOT_COMPUTABLE",
                "reason": "ISSUE_DATE_MISSING",
                "rule": "FROM_ISSUANCE",
            }

        return {
            "date": issue_date,
            "status": "EXTRACTED",
            "reason": None,
            "rule": "FROM_ISSUANCE",
        }

    # ==================================================
    # 7. Ratification + publication
    #
    # يسري مفعول هذا النظام من تاريخ تصديقه ونشره
    # ==================================================

    ratification_publication_match = re.search(
        r"(?:"
            r"يسري(?:\s+مفعول)?"
            r"|يعمل"
            r"|يدخل\s+(?:هذا\s+\S+\s+)?حيز\s+النفاذ"
        r")"
        r".{0,50}?"
        r"من\s+تاريخ\s+"
        r"تصديق(?:ه|ها)"
        r"\s+و\s*نشر(?:ه|ها)",
        normalized_text
    )

    if ratification_publication_match:
        return {
            "date": None,
            "status": "NOT_COMPUTABLE",
            "reason": "RATIFICATION_DATE_MISSING",
            "rule": "FROM_RATIFICATION_AND_PUBLICATION",
        }

    # ==================================================
    # 8. After ratification by all member states
    #
    # يدخل هذا النظام حيز النفاذ بعد ثلاثة أشهر
    # من مصادقة جميع الدول الأعضاء عليه
    # ==================================================

    all_states_ratification_match = re.search(
        r"يدخل\s+"
        r"(?:هذا\s+)?(?:النظام|القانون)"
        r"\s+حيز\s+النفاذ"
        r"\s+"
        r"(?:بعد(?:\s+مضي|\s+مرور)?|بمضي)"
        r"\s+"
        r"(.{1,50}?)"
        r"\s+من\s+"
        r"مصادقة\s+جميع\s+الدول\s+الاعضاء"
        r"(?:\s+علي(?:ه|ها))?",
        normalized_text
    )

    if all_states_ratification_match:

        duration = (
            all_states_ratification_match
            .group(1)
            .strip()
        )

        duration_result = parse_effective_duration(duration)

        if not duration_result:
            return {
                "date": None,
                "status": "ERROR",
                "reason": "DURATION_PARSE_FAILED",
                "rule": "AFTER_ALL_STATES_RATIFICATION",
            }

        return {
            "date": None,
            "status": "NOT_COMPUTABLE",
            "reason": "RATIFICATION_DATE_MISSING",
            "rule": "AFTER_ALL_STATES_RATIFICATION",
        }

    # ==================================================
    # 9. After ratification deposit
    #
    # يدخل هذا النظام حيز النفاذ بعد مضي ثلاثين يوما
    # من تاريخ إيداع وثيقة تصديق...
    #
    # IMPORTANT:
    # Must come before FROM_RATIFICATION_DEPOSIT.
    # ==================================================

    after_deposit_match = re.search(
        r"يدخل"
        r".{0,50}?"
        r"حيز\s+النفاذ"
        r"\s+"
        r"(?:بعد(?:\s+مضي|\s+مرور)?|بمضي)"
        r"\s+"
        r"(.{1,50}?)"
        r"\s+من\s+تاريخ\s+"
        r"ايداع\s+وثيقة\s+التصديق",
        normalized_text
    )

    if after_deposit_match:

        duration = after_deposit_match.group(1).strip()

        duration_result = parse_effective_duration(duration)

        if not duration_result:
            return {
                "date": None,
                "status": "ERROR",
                "reason": "DURATION_PARSE_FAILED",
                "rule": "AFTER_RATIFICATION_DEPOSIT",
            }

        return {
            "date": None,
            "status": "NOT_COMPUTABLE",
            "reason": "RATIFICATION_DEPOSIT_DATE_MISSING",
            "rule": "AFTER_RATIFICATION_DEPOSIT",
        }

    # ==================================================
    # 10. From ratification deposit
    #
    # يدخل حيز النفاذ من تاريخ إيداع وثيقة التصديق
    # ==================================================

    deposit_match = re.search(
        r"يدخل"
        r".{0,50}?"
        r"حيز\s+النفاذ"
        r"\s+من\s+تاريخ\s+"
        r"ايداع\s+وثيقة\s+التصديق",
        normalized_text
    )

    if deposit_match:
        return {
            "date": None,
            "status": "NOT_COMPUTABLE",
            "reason": "RATIFICATION_DEPOSIT_DATE_MISSING",
            "rule": "FROM_RATIFICATION_DEPOSIT",
        }


    # ==================================================
    # Delayed from approval / adoption
    #
    # Examples:
    # يعمل بالنظام بعد ثلاثة أشهر من تاريخ إقراره
    # يعمل به بعد ستين يوما من تاريخ اعتماده
    # ==================================================

    after_approval_match = re.search(
        r"(?:"
            r"يعمل"
            r"|يسري"
            r"|ينفذ"
            r"|يكون\s+نافذا"
            r"|يدخل\s+حيز\s+النفاذ"
        r")"
        r".{0,60}?"
        r"(?:"
            r"بعد(?:\s+مرور|\s+مضي)?"
            r"|بمضي"
        r")"
        r"\s+"
        r"(.{1,50}?)"
        r"\s+"
        r"من\s+تاريخ\s+"
        r"(?:"
            r"[إا]قرار(?:ه|ها)"
            r"|اعتماد(?:ه|ها)"
            r"|الموافقة\s+علي(?:ه|ها)"
        r")",
        normalized_text
    )

    if after_approval_match:

        duration = (
            after_approval_match
            .group(1)
            .strip()
        )

        duration_result = parse_effective_duration(
            duration
        )

        if not duration_result:
            return {
                "date": None,
                "status": "ERROR",
                "reason": "DURATION_PARSE_FAILED",
                "rule": "AFTER_APPROVAL",
            }

        return {
            "date": None,
            "status": "NOT_COMPUTABLE",
            "reason": "APPROVAL_DATE_MISSING",
            "rule": "AFTER_APPROVAL",
        }
    # ==================================================
    # 12. Immediate from approval / adoption
    #
    # يعمل به من تاريخ الموافقة عليه
    # يعمل بالقواعد من تاريخ الموافقة عليها
    # يعمل به من تاريخ اعتماده
    # ==================================================

    approval_match = re.search(
        r"(?:"
            r"يعمل"
            r"|يسري"
            r"|ينفذ"
            r"|يصبح\s+.{0,30}?\s+نافذا"
            r"|يدخل\s+.{0,30}?\s+حيز\s+النفاذ"
        r")"
        r".{0,60}?"
        r"من\s+تاريخ\s+"
        r"(?:"
            r"الموافقة\s+علي(?:ه|ها)"
            r"|اعتماد(?:ه|ها)"
            r"|اقرار(?:ه|ها)"
        r")",
        normalized_text
    )

    if approval_match:
        return {
            "date": None,
            "status": "NOT_COMPUTABLE",
            "reason": "APPROVAL_DATE_MISSING",
            "rule": "FROM_APPROVAL",
        }

    # ==================================================
    # 13. Effective from another law's effective date
    #
    # يعمل بهذه الآلية من تاريخ نفاذ نظام القضاء
    # ==================================================

    reference_law_match = re.search(
        r"(?:يعمل|يسري)"
        r".{0,70}?"
        r"من\s+تاريخ\s+نفاذ\s+"
        r"(?:نظام|قانون|لائحة|تنظيم)",
        normalized_text
    )

    if reference_law_match:
        return {
            "date": None,
            "status": "NOT_COMPUTABLE",
            "reason": "REFERENCE_EVENT_DATE_MISSING",
            "rule": "FROM_REFERENCE_EVENT",
        }

    # ==================================================
    # 14. Other delayed reference event
    #
    # Example:
    # يعمل به بعد تسعين يوما من بداية مدة مجلس الشورى
    #
    # We understand that this is an effective-date rule,
    # but don't have the base event date.
    # ==================================================

    other_reference_delay_match = re.search(
        r"(?:يعمل|يسري|يدخل|يكون)"
        r".{0,60}?"
        r"(?:بعد(?:\s+مضي|\s+مرور)?|بمضي)"
        r"\s+"
        r"(.{1,50}?)"
        r"\s+من\s+"
        r"(?:بداية|بدء)\s+"
        r".{1,80}",
        normalized_text
    )

    if other_reference_delay_match:

        duration = (
            other_reference_delay_match
            .group(1)
            .strip()
        )

        duration_result = parse_effective_duration(duration)

        if duration_result:
            return {
                "date": None,
                "status": "NOT_COMPUTABLE",
                "reason": "REFERENCE_EVENT_DATE_MISSING",
                "rule": "AFTER_REFERENCE_EVENT",
            }

    # ==================================================
    # 15. Explicit calendar date
    #
    # اعتبارا من الأول من يناير عام 2004م
    #
    # We recognize it but don't parse Arabic explicit
    # calendar dates yet.
    # ==================================================

        
    determined_date_match = re.search(
        r"(?:"
            r"تنفذ"
            r"|ينفذ"
            r"|يعمل"
            r"|يسري"
        r")"
        r".{0,50}?"
        r"من\s+التاريخ\s+الذي\s+يحدد(?:ه|ها)",
        normalized_text
    )

    if determined_date_match:
        return {
            "date": None,
            "status": "NOT_COMPUTABLE",
            "reason": "REFERENCE_EVENT_DATE_MISSING",
            "rule": "DATE_DETERMINED_BY_AUTHORITY",
        }
        
    # ==================================================
    # Explicit Hijri effective date
    #
    # Examples:
    # ينفذ النظام اعتبارا من 1 / 1 / 1370 هـ
    # ينفذ النظام اعتبارا من 1 /7 /1393هـ
    # يعمل به اعتبارا من 1/1/1440هـ
    # ==================================================

    explicit_hijri_match = re.search(
        r"(?:"
            r"يعمل"
            r"|يسري"
            r"|ينفذ"
            r"|يكون\s+نافذا"
            r"|يدخل\s+حيز\s+النفاذ"
        r")"
        r".{0,60}?"
        r"اعتبارا\s+من\s+"
        r"(\d{1,2})"
        r"\s*/\s*"
        r"(\d{1,2})"
        r"\s*/\s*"
        r"(\d{3,4})"
        r"\s*ه",
        normalized_text
    )

    if explicit_hijri_match:

        day = int(
            explicit_hijri_match.group(1)
        )
        month = int(
            explicit_hijri_match.group(2)
        )
        year = int(
            explicit_hijri_match.group(3)
        )

        effective_date = hijri_to_gregorian(
            year,
            month,
            day,
        )

        if effective_date is None:
            return {
                "date": None,
                "status": "NOT_COMPUTABLE",
                "reason": "HIJRI_DATE_CONVERSION_FAILED",
                "rule": "EXPLICIT_HIJRI_DATE",
            }

        return {
            "date": effective_date,
            "status": "EXTRACTED",
            "reason": None,
            "rule": "EXPLICIT_HIJRI_DATE",
        }

    # ==================================================
    # 16. Nothing recognized
    # ==================================================

    return {
        "date": None,
        "status": "NOT_FOUND",
        "reason": "NO_RECOGNIZED_RULE",
        "rule": None,
    }
    
def transform_law_version(
    text,
    key,
    law_id,
    issue_date,
    publication_date,
    status_id
):
    effective_result = extract_effective_date(
        text,
        publication_date,
        issue_date
    )

    collected_at = datetime.strptime(
        key.split("/")[0],
        "%Y-%m-%d"
    )

    normalized_text = normalize_text_for_hash(text)

    law_hash = hashlib.sha256(
        normalized_text.encode("utf-8")
    ).hexdigest()

    law_version = {
        "law_id": law_id,
        "status_id": status_id,
        "effective_date": effective_result["date"],
        "hash": law_hash,
        "raw_object_key": key,
        "collected_at": collected_at,
    }

    extraction_status = {
        "field_name": "effective_date",
        "status": effective_result["status"],
        "reason": effective_result["reason"],
        "detected_rule": effective_result["rule"],
    }

    return law_version, extraction_status

def extract_latest_replacement(text):

    replacement_pattern = re.compile(
        r"(?:"
        r"وبهذا\s*يصبح\s*نص\s*المادة"
        r".*?"
        r"(?:كما\s*يلى|كما\s*يلي|كمايلى|كالتالى|كالتالي)"
        r"|"
        r"ويكون\s*نص\s*المادة"
        r".*?"
        r"(?:كما\s*يلى|كما\s*يلي|كمايلى|كالتالى|كالتالي)"
        r"|"
        r"لتكون\s*بالنص\s*التالي"
        r")"
        r"\s*:?\s*",
        re.DOTALL
    )

    matches = list(
        replacement_pattern.finditer(text)
    )

    if not matches:
        return None

    # If there are several amendments, use the last
    # replacement because it is the latest version.
    match = matches[-1]

    replacement = text[
        match.end():
    ].strip()

    # Remove punctuation left immediately after the marker.
    replacement = re.sub(
        r"^[\s:;،,.\-]+",
        "",
        replacement
    ).strip()

    return replacement


def transform_articles(text):

    article_names = [
        "الأولى",
        "الثانية",
        "الثالثة",
        "الرابعة",
        "الخامسة",
        "السادسة",
        "السابعة",
        "الثامنة",
        "التاسعة",
        "العاشرة",
        "الحادية عشرة",
        "الثانية عشرة",
        "الثالثة عشرة",
        "الرابعة عشرة",
        "الخامسة عشرة",
        "السادسة عشرة",
        "السابعة عشرة",
        "الثامنة عشرة",
        "التاسعة عشرة",
        "العشرون",
        "الحادية والعشرون",
        "الثانية والعشرون",
        "الثالثة والعشرون",
        "الرابعة والعشرون",
        "الخامسة والعشرون",
        "السادسة والعشرون",
        "السابعة والعشرون",
        "الثامنة والعشرون",
        "التاسعة والعشرون",
        "الثلاثون",
    ]

    # ------------------------------------------------------
    # Map written Arabic article names to article numbers
    # ------------------------------------------------------

    article_numbers = {
        name: i + 1
        for i, name in enumerate(article_names)
    }

    # Longer names must be checked first.
    article_names_pattern = sorted(
        article_names,
        key=len,
        reverse=True
    )

    # ------------------------------------------------------
    # Detect article headings
    #
    # Examples:
    #
    # المادة الأولى
    # مادة الأولى
    # المادة (13)
    # المادة 13
    # (المادة الثالثة عشرة)
    # المادة رقم (13)
    # ------------------------------------------------------

    article_pattern = re.compile(
        r"^(?:"
        r"(?:المادة|مادة)\s*(?:"
        r"("
        + "|".join(article_names_pattern)
        + r")"
        r"|"
        r"\(\s*(\d+)\s*\)"
        r"|"
        r"(\d+)"
        r")"
        r"|"
        r"\(المادة\s+("
        + "|".join(article_names_pattern)
        + r")\)"
        r"|"
        r"المادة\s+رقم\s*\((\d+)\)"
        r")"
        r"\s*:?.*$",
        re.MULTILINE
    )

    matches = list(
        article_pattern.finditer(text)
    )

    articles_data = {}

    current_article_number = 0

    # ------------------------------------------------------
    # Process article headings
    # ------------------------------------------------------

    for i, match in enumerate(matches):

        article_name = match.group(1)

        article_number_parenthesized = (
            match.group(2)
        )

        article_number_plain = (
            match.group(3)
        )

        article_name_parenthesized = (
            match.group(4)
        )

        article_number_labeled = (
            match.group(5)
        )

        # --------------------------------------------------
        # Determine article number
        # --------------------------------------------------

        if article_name:

            article_number = article_numbers[
                article_name
            ]

        elif article_number_parenthesized:

            article_number = int(
                article_number_parenthesized
            )

        elif article_number_plain:

            article_number = int(
                article_number_plain
            )

        elif article_name_parenthesized:

            article_number = article_numbers[
                article_name_parenthesized
            ]

        elif article_number_labeled:

            article_number = int(
                article_number_labeled
            )

        else:

            continue

        # --------------------------------------------------
        # BOE page contains another article selector list
        # after the actual law.
        #
        # If numbering restarts at article 1 after we have
        # already processed article 2+, stop parsing.
        # --------------------------------------------------

        if (
            article_number == 1
            and current_article_number >= 2
        ):
            break

        current_article_number = (
            article_number
        )

        # --------------------------------------------------
        # Extract article content
        # --------------------------------------------------

        start = match.end()

        if i + 1 < len(matches):

            end = matches[
                i + 1
            ].start()

        else:

            end = len(text)

        section = text[
            start:end
        ].strip()

        # --------------------------------------------------
        # First occurrence of this article
        # --------------------------------------------------

        if article_number not in articles_data:

            # ----------------------------------------------
            # Article contains amendments
            # ----------------------------------------------

            if "تعديلات المادة" in section:

                original, amendments = (
                    section.split(
                        "تعديلات المادة",
                        1
                    )
                )

                content = original.strip()

                replacement = (
                    extract_latest_replacement(
                        amendments
                    )
                )

                # If a replacement exists, the latest
                # replacement becomes the current content.
                if replacement:

                    content = replacement

            else:

                content = section

            # ----------------------------------------------
            # Store canonical article title
            # ----------------------------------------------

            articles_data[
                article_number
            ] = {
                "title_ar": (
                    normalize_article_title(
                        article_number
                    )
                ),
                "content_ar": content,

                # Position of article heading in raw text.
                "_start": match.start(),
            }

        # --------------------------------------------------
        # Repeated occurrence = amendment
        # --------------------------------------------------

        else:

            replacement = (
                extract_latest_replacement(
                    section
                )
            )

            if replacement:

                articles_data[
                    article_number
                ]["content_ar"] = replacement

    # ------------------------------------------------------
    # Build final articles
    # ------------------------------------------------------

    articles = []

    for article_number in sorted(
        articles_data
    ):

        article_data = articles_data[
            article_number
        ]

        content = article_data[
            "content_ar"
        ].strip()

        # --------------------------------------------------
        # Remove website form after final article
        # --------------------------------------------------

        form_markers = [
            "الإسم",
            "الاسم",
            "البريد الإلكتروني",
            "رقم الجوال",
            "تعليق",
        ]

        for marker in form_markers:

            position = content.find(
                marker
            )

            if position != -1:

                content = content[
                    :position
                ].strip()

                break

        # --------------------------------------------------
        # Remove outer parentheses used by amendments
        # --------------------------------------------------

        if content.startswith("("):

            content = content[
                1:
            ].strip()

            if content.endswith(")."):

                content = content[
                    :-2
                ].strip()

            elif content.endswith(")"):

                content = content[
                    :-1
                ].strip()

        # --------------------------------------------------
        # Final transformed article
        # --------------------------------------------------

        articles.append({
            "title_en": None,

            "title_ar": article_data[
                "title_ar"
            ],

            "content_en": None,

            "content_ar": content,

            # Temporary transformation metadata.
            # main.py uses this to associate the article
            # with the closest preceding chapter.
            "_start": article_data[
                "_start"
            ],
        })

    return articles

def transform_articles_versions(
    articles,
    law_version,
    status
):

    article_versions = []

    for article in articles:

        normalized_content = normalize_text_for_hash(
            article["content_ar"]
        )

        article_hash = hashlib.sha256(
            normalized_content.encode("utf-8")
        ).hexdigest()

        article_versions.append({
            "article": article,
            "law_version": law_version,
            "hash": article_hash,
            "is_changed": False,
            "status": status,
        })

    return article_versions

def transform_chapters(text, law_id):

    # ------------------------------------------------------
    # Supported written chapter ordinals
    # ------------------------------------------------------

    chapter_names = {
        "الأول": 1,
        "الثاني": 2,
        "الثالث": 3,
        "الرابع": 4,
        "الخامس": 5,
        "السادس": 6,
        "السابع": 7,
        "الثامن": 8,
        "التاسع": 9,
        "العاشر": 10,
        "الحادي عشر": 11,
        "الثاني عشر": 12,
        "الثالث عشر": 13,
        "الرابع عشر": 14,
        "الخامس عشر": 15,
        "السادس عشر": 16,
        "السابع عشر": 17,
        "الثامن عشر": 18,
        "التاسع عشر": 19,
        "العشرون": 20,
        "الحادي والعشرون": 21,
        "الثاني والعشرون": 22,
        "الثالث والعشرون": 23,
        "الرابع والعشرون": 24,
        "الخامس والعشرون": 25,
        "السادس والعشرون": 26,
        "السابع والعشرون": 27,
        "الثامن والعشرون": 28,
        "التاسع والعشرون": 29,
        "الثلاثون": 30,
    }

    # Longer names first.
    # This prevents shorter ordinals from matching
    # before compound ones.
    chapter_names_pattern = sorted(
        chapter_names,
        key=len,
        reverse=True
    )

    names_pattern = "|".join(
        re.escape(name)
        for name in chapter_names_pattern
    )

    # ------------------------------------------------------
    # Detect الفصل headings
    #
    # Supported examples:
    #
    # الفصل الأول: أحكام عامة
    # الفصل الأول أحكام عامة
    # الفصل الأول ( أحكام عامة )
    # الفصل الأول: (أحكام عامة)
    #
    # الفصل (3): أحكام عامة
    # الفصل 3 أحكام عامة
    #
    # Groups:
    #
    # 1 -> written ordinal
    # 2 -> parenthesized number
    # 3 -> plain number
    # 4 -> descriptive title
    # ------------------------------------------------------

    fasl_pattern = re.compile(
        rf"^الفصل\s*(?:"
        rf"({names_pattern})"
        rf"|"
        rf"\(\s*(\d+)\s*\)"
        rf"|"
        rf"(\d+)"
        rf")"
        rf"(.*)$",
        re.MULTILINE
    )

    # ------------------------------------------------------
    # Detect الباب headings
    #
    # الباب will be normalized to الفصل.
    # ------------------------------------------------------

    bab_pattern = re.compile(
        rf"^الباب\s*(?:"
        rf"({names_pattern})"
        rf"|"
        rf"\(\s*(\d+)\s*\)"
        rf"|"
        rf"(\d+)"
        rf")"
        rf"(.*)$",
        re.MULTILINE
    )

    fasl_matches = list(
        fasl_pattern.finditer(text)
    )

    bab_matches = list(
        bab_pattern.finditer(text)
    )

    # ------------------------------------------------------
    # Structural level selection
    #
    # If the document contains الفصل, use الفصل.
    #
    # Otherwise, use الباب and normalize it to الفصل.
    # ------------------------------------------------------

    if fasl_matches:

        matches = fasl_matches

    elif bab_matches:

        matches = bab_matches

    else:

        return [
            {
                "law_id": law_id,
                "title_en": "No Chapters",
                "title_ar": "بدون فصول",
                "_start": 0,
            }
        ]

    # ------------------------------------------------------
    # Build normalized chapter records
    # ------------------------------------------------------

    chapters = []

    # Used to remove duplicates created by formatting
    # differences in the source.
    seen_titles = set()

    for match in matches:

        chapter_name = match.group(1)

        chapter_number_parenthesized = (
            match.group(2)
        )

        chapter_number_plain = (
            match.group(3)
        )

        remainder = (
            match.group(4) or ""
        ).strip()

        # --------------------------------------------------
        # Determine chapter number
        # --------------------------------------------------

        if chapter_name:

            chapter_number = chapter_names[
                chapter_name
            ]

        elif chapter_number_parenthesized:

            chapter_number = int(
                chapter_number_parenthesized
            )

        elif chapter_number_plain:

            chapter_number = int(
                chapter_number_plain
            )

        else:

            continue

        # --------------------------------------------------
        # Normalize structural prefix
        #
        # الباب الأول
        # الفصل الأول
        # الفصل 1
        # الفصل (1)
        #
        # all become:
        #
        # الفصل الأول
        # --------------------------------------------------

        normalized_prefix = (
            normalize_chapter_title(
                chapter_number
            )
        )

        # --------------------------------------------------
        # Normalize descriptive title
        # --------------------------------------------------

        if remainder:

            # ----------------------------------------------
            # Remove an existing separator after the
            # structural prefix.
            #
            # ": أحكام عامة"
            # " : أحكام عامة"
            #
            # -> "أحكام عامة"
            # ----------------------------------------------

            remainder = re.sub(
                r"^\s*:\s*",
                "",
                remainder
            ).strip()

            # ----------------------------------------------
            # Remove ONE outer pair of parentheses.
            #
            # ( أحكام عامة )
            # -> أحكام عامة
            #
            # (أحكام عامة)
            # -> أحكام عامة
            #
            # We only do this when the parentheses surround
            # the entire title.
            # ----------------------------------------------

            if (
                remainder.startswith("(")
                and remainder.endswith(")")
            ):

                remainder = (
                    remainder[1:-1]
                    .strip()
                )

            # ----------------------------------------------
            # Remove another leading colon if parentheses
            # or strange source formatting exposed one.
            # ----------------------------------------------

            remainder = re.sub(
                r"^\s*:\s*",
                "",
                remainder
            ).strip()

            # ----------------------------------------------
            # Normalize spaces before punctuation
            #
            # "التسجيل ."
            # -> "التسجيل."
            # ----------------------------------------------

            remainder = re.sub(
                r"\s+([،؛:,.])",
                r"\1",
                remainder
            )

            # ----------------------------------------------
            # Collapse repeated spaces
            #
            # "أحكام   عامة"
            # -> "أحكام عامة"
            # ----------------------------------------------

            remainder = re.sub(
                r"\s+",
                " ",
                remainder
            ).strip()

            # ----------------------------------------------
            # Remove trailing period.
            #
            # "التسجيل."
            # -> "التسجيل"
            #
            # "التسجيل ."
            # -> "التسجيل"
            # ----------------------------------------------

            remainder = re.sub(
                r"\s*\.\s*$",
                "",
                remainder
            ).strip()

            # ----------------------------------------------
            # Remove trailing colon.
            #
            # "أحكام عامة:"
            # -> "أحكام عامة"
            #
            # This prevents:
            #
            # الفصل الأول: أحكام عامة:
            # ----------------------------------------------

            remainder = re.sub(
                r"\s*:\s*$",
                "",
                remainder
            ).strip()

        # --------------------------------------------------
        # Build canonical title
        #
        # ALWAYS:
        #
        # الفصل الأول: أحكام عامة
        # --------------------------------------------------

        if remainder:

            title_ar = (
                f"{normalized_prefix}: "
                f"{remainder}"
            )

        else:

            # Some source headings genuinely contain only:
            #
            # الفصل الأول:
            #
            # There is no descriptive title to preserve.
            title_ar = normalized_prefix

        title_ar = title_ar.strip()

        # --------------------------------------------------
        # Deduplicate formatting variants
        #
        # Example:
        #
        # الفصل الأول أحكام عامة
        # الفصل الأول: أحكام عامة
        # الفصل الأول ( أحكام عامة )
        # الفصل الأول: (أحكام عامة)
        #
        # all normalize to:
        #
        # الفصل الأول: أحكام عامة
        #
        # Only ONE record should remain.
        # --------------------------------------------------

        if title_ar in seen_titles:
            continue

        seen_titles.add(
            title_ar
        )

        # --------------------------------------------------
        # Final chapter
        # --------------------------------------------------

        chapters.append({
            "law_id": law_id,
            "title_en": None,
            "title_ar": title_ar,

            # Keep the original source position.
            #
            # main.py needs this to associate articles
            # with the closest preceding chapter.
            "_start": match.start(),
        })

    return chapters
    
def validate_raw_text(text):

    required_fields = [
        "الاسم",
        "تاريخ الإصدار",
        "تاريخ النشر",
        "الحالة",
    ]

    for field in required_fields:
        if field not in text:
            return False

    return True

def transform_statuses(text):

    status_match = re.search(
        r"الحالة\s*\n([^\n]+)",
        text
    )

    if not status_match:
        return []

    status_ar = status_match.group(1).strip()

    status_mapping = {
        "ساري": "Active",
        "لاغي": "Repealed",
        "جاري العمل على النظام": "In Progress",
        "ساري بعد مدة 180 يوم من تاريخ النشر": "Active After 180 Days From Publication",
    }

    status_en = status_mapping.get(
        status_ar,
        status_ar
    )

    return [
        {
            "status_en": status_en,
            "status_ar": status_ar,
        }
    ]
