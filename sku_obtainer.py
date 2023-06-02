import httpx
from lxml import html
import asyncio


class VaistaiCrawler:
    headers = {
        "content-type": "application/x-www-form-urlencoded",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
    }
    timeout = 30
    login_url = "https://market.vaistai.lt/lt/prisijungti.html"
    search_url = "https://market.vaistai.lt/lt/e-suri%C5%A1imai.html"
    data = {
        "option": "com_surisimai",
        "view": "surisimai",
        "limit": "100",
        "limitstart": "0",
        "group_u1": "6",
    }

    def __init__(self, username, password, async_req=False):
        self.username = username
        self.password = password
        self.is_async = async_req
        if self.is_async:
            self.client = httpx.AsyncClient(
                timeout=self.timeout,
                limits=httpx.Limits(
                    max_connections=10  # we can change max connection count here
                ),
            )
        else:
            self.client = httpx.Client(timeout=self.timeout)

    async def _async_authenticate(self):
        r = await self.client.get(self.login_url, headers=self.headers)
        tree = html.fromstring(r.text)
        inputs = tree.xpath('//input[@type="hidden"]')
        return_value = inputs[0].attrib["value"]
        name_value = inputs[1].attrib["name"]
        data = {
            "username": self.username,
            "password": self.password,
            "return": return_value,
            name_value: "1",
        }
        await self.client.post(
            self.login_url + "?task=user.login", data=data, headers=self.headers
        )
        print("Authenticated")

    def _sync_authenticate(self):
        r = self.client.get(self.login_url, headers=self.headers)
        tree = html.fromstring(r.text)
        inputs = tree.xpath('//input[@type="hidden"]')
        return_value = inputs[0].attrib["value"]
        name_value = inputs[1].attrib["name"]
        data = {
            "username": self.username,
            "password": self.password,
            "return": return_value,
            name_value: "1",
        }
        self.client.post(
            self.login_url + "?task=user.login", data=data, headers=self.headers
        )

    def authenticate(self):
        if self.is_async:
            return self._async_authenticate()
        else:
            return self._sync_authenticate()

    async def _async_search(self, queries):
        tasks = []
        for query in queries:
            data = self.data.copy()
            data["search"] = query
            tasks.append(
                self.client.post(self.search_url, data=data, headers=self.headers)
            )
        responses = await asyncio.gather(*tasks)
        results = []
        for response in responses:
            tree = html.fromstring(response.text)
            result = tree.xpath('//table[@class="t_availability"]/tr[2]/td[1]/a/text()')
            results.append(result)
        return results

    def _sync_search(self, query):
        data = self.data.copy()
        data["search"] = query
        r = self.client.post(self.search_url, data=data, headers=self.headers)
        tree = html.fromstring(r.text)
        return tree.xpath('//table[@class="t_availability"]/tr[2]/td[1]/a/text()')

    def search(self, query):
        if self.is_async:
            return self._async_search(query)
        else:
            return self._sync_search(query)


if __name__ == "__main__":
    crawler = VaistaiCrawler("sksherba", "sksherba")
    crawler.authenticate()
    result = crawler.search("Uriage Tolederm kremas drėkinantis 40ml")
    print(result)
