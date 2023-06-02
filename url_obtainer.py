import httpx
from lxml import html
import re
import pandas as pd

USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/80.0.3987.163 Chrome/80.0.3987.163 Safari/537.36"
headers = {"User-Agent": USER_AGENT}


def get_urls_from_page(page):
    products = page.xpath("//td[@class='vp_list_title']")

    titles_urls = []

    for product in products:
        title = product.xpath("descendant::*/text()")
        title = "".join(title).strip()

        url = product.xpath("a/@href")[0]
        titles_urls.append((title, url))

    print(f"Found {len(titles_urls)}.")

    return titles_urls


def get_products_urls(manufacturer):
    url = f"https://vaistai.lt/paieska/{manufacturer}.html?"
    print(f"getting url: {url}")
    r = httpx.get(url, headers=headers, follow_redirects=True)
    content = html.fromstring(r.content)

    page_count = content.xpath('//a[@title="paskutinis puslapis"]/@href')[0]
    page_count = int(re.search(r"page=(\d+)", page_count).group(1))

    titles_urls = []
    titles_urls.extend(get_urls_from_page(content))

    for page in range(2, page_count + 1):
        url = f"https://vaistai.lt/paieska/{manufacturer}.html?page={page}"
        print(f"getting url: {url}")
        r = httpx.get(url, headers=headers)
        content = html.fromstring(r.content)
        titles_urls.extend(get_urls_from_page(content))

    return titles_urls
