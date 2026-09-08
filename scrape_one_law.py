import requests
from bs4 import BeautifulSoup



BASE_URL = "https://laws.boe.gov.sa"
HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

# رابط النظام الاساسي للحكم
LAW_URL = (
    "https://laws.boe.gov.sa/BoeLaws/Laws/"
    "LawDetails/16b97fcb-4833-4f66-8531-a9a700f161b6/1"
)



def get_text_by_label(soup, label_text):
    """
    Find a label such as:
    الاسم
    تاريخ الإصدار
    تاريخ النشر
    الحالة

    Then return the text inside its span.
    """

    label = soup.find(
        "label",
        string=lambda x: x and label_text in x
    )

    if not label:
        return None

    parent = label.parent
    span = parent.find("span")

    if span:
        return span.get_text(" ", strip=True)

    return None

# يستخرج أداة إصدار النظام
def get_issuing_tool(soup):
    """
    Extract the issuing instrument, for example:
    أمر ملكي رقم أ/90 بتاريخ 27 / 8 / 1412
    """

    label = soup.find(
        "label",
        string=lambda x: x and "أدوات إصدار النظام" in x
    )

    if not label:
        return None

    parent = label.parent
    link = parent.find("a")

    if link:
        return link.get_text(" ", strip=True)

    return None

# يستخرج نص النظام الكامل
def get_law_text(soup):
    """
    Extract only the actual legal text.

    The official website stores the law text inside:
    <div id="divLawText">
    """

    container = soup.find("div", id="divLawText")

    if not container:
        return None

    return container.get_text("\n", strip=True)




def scrape_law(url):
    """
    Download one law page and extract its data.
    """

    print("جاري تحميل النظام...")

    response = requests.get(
        url,
        headers=HEADERS,
        verify=False,
        timeout=30
    )

    response.raise_for_status()

    print("تم تحميل الصفحة بنجاح.")
    print("Status Code:", response.status_code)

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

   
    law = {
        "name": get_text_by_label(soup, "الاسم"),
        "issue_date": get_text_by_label(soup, "تاريخ الإصدار"),
        "publication_date": get_text_by_label(soup, "تاريخ النشر"),
        "status": get_text_by_label(soup, "الحالة"),
        "issuing_tool": get_issuing_tool(soup),
        "url": url,
        "law_text": get_law_text(soup)
    }

    return law




if __name__ == "__main__":

    law = scrape_law(LAW_URL)

    print("\n==============================")
    print("بيانات النظام")
    print("==============================")

    print("اسم النظام:")
    print(law["name"])

    print("\nتاريخ الإصدار:")
    print(law["issue_date"])

    print("\nتاريخ النشر:")
    print(law["publication_date"])

    print("\nالحالة:")
    print(law["status"])

    print("\nأداة الإصدار:")
    print(law["issuing_tool"])

    print("\nرابط النظام:")
    print(law["url"])

    print("\n==============================")
    print("نص النظام")
    print("==============================")

    if law["law_text"]:
        print(law["law_text"])
    else:
        print("لم يتم العثور على نص النظام.")