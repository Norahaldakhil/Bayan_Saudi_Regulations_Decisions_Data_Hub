import requests
from bs4 import BeautifulSoup

url = "https://laws.boe.gov.sa/BoeLaws/Laws/LawDetails/16b97fcb-4833-4f66-8531-a9a700f161b6/1"

response = requests.get(
    url,
    headers={"User-Agent": "Mozilla/5.0"},
    verify=False
)

soup = BeautifulSoup(response.text, "html.parser")


# اسم النظام
name = soup.find("label", string=lambda x: x and "الاسم" in x)
name = name.parent.find("span").get_text(strip=True)


# تاريخ الإصدار
issue_date = soup.find("label", string=lambda x: x and "تاريخ الإصدار" in x)
issue_date = issue_date.parent.find("span").get_text(strip=True)


# تاريخ النشر
publication_date = soup.find("label", string=lambda x: x and "تاريخ النشر" in x)
publication_date = publication_date.parent.find("span").get_text(strip=True)


# حالة النظام
status = soup.find("label", string=lambda x: x and "الحالة" in x)
status = status.parent.find("span").get_text(strip=True)


# أداة الإصدار
issuing_tool = soup.find(
    "label",
    string=lambda x: x and "أدوات إصدار النظام" in x
)
issuing_tool = issuing_tool.parent.find("a").get_text(strip=True)


# نص النظام
law_text = soup.find("div", id="divLawText").get_text("\n", strip=True)


print("اسم النظام:", name)
print("تاريخ الإصدار:", issue_date)
print("تاريخ النشر:", publication_date)
print("الحالة:", status)
print("أداة الإصدار:", issuing_tool)
print("رابط النظام:", url)

print("\nنص النظام:")
print(law_text)