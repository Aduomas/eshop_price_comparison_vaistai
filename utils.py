import httpx
from lxml import html


def get_herba_price(url):
    r = httpx.get(url, follow_redirects=True, timeout=30)

    content = html.fromstring(r.content)

    price = content.xpath(
        '//div[@class="product-info-main"]/div/span/span/span[2]/@data-price-amount'
    )

    if price:
        try:
            price = round(float(price[0]), 2)
        except ValueError:
            print(f"Price is not float: {price}")
            price = None
        return price

    price = content.xpath(
        '//div[@class="product-info-main"]/div/span/span/@data-price-amount'
    )
    if price:
        try:
            price = round(float(price[0]), 2)
        except ValueError:
            print(f"Price is not float: {price}")
            price = None
        return price

    price = content.xpath(
        '//li[@class="item product product-item"][1]/div/div[2]/div[2]/span[1]/span/span[2]/@data-price-amount'
    )
    if price:
        try:
            price = round(float(price[0]), 2)
        except ValueError:
            print(f"Price is not float: {price}")
            price = None
        return price

    print(f"Failed with link -- Getting price from herba: {url}")
    return None


def get_price_magento(sku):

    data = {
        "username": "martynas",
        "password": "sAWvBasbD4p#",
    }

    r = httpx.post("https://dev.herba.lt/rest/V1/integration/admin/token", json=data)
    token = r.text

    r = httpx.get(
        f"https://dev.herba.lt/rest/V1/products/{sku}",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )
    print(r.text)


if __name__ == "__main__":
    # get_price_magento("U15001500")

    from magento import Client

    api = Client(f"dev.herba.lt", "martynas", "sAWvBasbD4p#")
    product = api.products.by_sku("U15001500")
    print(product.price)
