import multiprocessing
from multiprocessing import Process, Queue, Manager
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
import httpx
from lxml import html
import time
from url_obtainer import get_products_urls
import pandas as pd
from utils import get_herba_price
from styler import process_data
from datetime import datetime
import os
from styleframe import StyleFrame

CHROME_DRIVER_FILE = ChromeDriverManager().install()


def element_has_text(locator):
    def check(driver):
        element = driver.find_element(*locator)
        if element.text:
            return True
        for child in element.find_elements(By.XPATH, ".//*"):
            if child.text:
                return True
        return False

    return check


def worker(task_queue, result_list):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("start-maximized")
    chrome_options.add_argument("disable-infobars")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
    chrome_options.add_experimental_option(
        "prefs",
        {
            "profile.managed_default_content_settings.images": 2,
            "profile.managed_default_content_settings.stylesheets": 2,
            "profile.managed_default_content_settings.fonts": 2,
        },
    )
    chrome_options.add_argument("--log-level=3")
    driver = webdriver.Chrome(
        service=Service(CHROME_DRIVER_FILE),
        options=chrome_options,
    )
    wait = WebDriverWait(driver, 10)

    while not task_queue.empty():
        try:
            item = task_queue.get_nowait()
            title, url = item
        except Exception as e:
            print(f"Error: {e}")
            continue

        try:
            driver.get(url)
            wait.until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, '//table[@itemprop="offers"]/tbody/tr')
                )
            )
            time.sleep(0.5)

            offers = driver.find_elements(By.XPATH, '//table[@itemprop="offers"]')

            print(f"Found {len(offers)} offers")

            found_herba = False

            for offer in offers:
                body = offer.find_element(By.XPATH, "./tbody/tr")

                time.sleep(0.1)

                a1_element = body.find_element(By.XPATH, "./td[3]/a")

                eshop = a1_element.get_attribute("onclick")
                eshop = re.search(r"clickShop\('(.+)'\)", eshop).group(1)

                # print(f"text: {a1_element.get_attribute('textContent')}")

                price = (
                    a1_element.get_attribute("textContent")
                    .split("€")[-2]
                    .strip()
                    .replace(",", ".")
                    .replace("€", "")
                    .replace("\xa0", "")
                )

                if eshop == "herba":
                    price = get_herba_price(a1_element.get_attribute("href"))
                    found_herba = True
                else:
                    price = round(float(price), 2)

                print(f"{title} - {eshop} - {price}€")
                result_list.append((title, eshop, price))

            if not found_herba:
                price = get_herba_price(
                    f"https://www.herba.lt/lt/catalogsearch/result/?q={title}"
                )
                result_list.append((title, "herba", price))
                print(f"{title} - {eshop} - {price}€")
        except Exception as e:
            print(f"Error: {e}")
            print(f"Failed to get data for {title} - {url}")

    driver.quit()
    print("Worker finished")


def crawl_data(manufacturer):
    product_list = get_products_urls(manufacturer)
    # product_list = product_list[:10]

    task_queue = Queue()
    with Manager() as manager:
        result_list = manager.list()

        for product in product_list:
            task_queue.put(product)

        processes = []
        num_processes = 6

        for _ in range(num_processes):
            p = Process(target=worker, args=(task_queue, result_list))
            p.start()
            processes.append(p)

        for p in processes:
            p.join()

        print("All processes finished")

        df = pd.DataFrame(list(result_list), columns=["title", "eshop", "price"])
        process_data(
            df,
            f"./reports/eshop_comparison_{manufacturer} {datetime.now().strftime('%Y-%m-%d')}",
        )


def combine_excel_files(input_dir, output_file):
    # Create a Pandas Excel writer using openpyxl as the engine
    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        # Iterate over all files in the directory
        for filename in os.listdir(input_dir):
            if filename.endswith(".xlsx") and filename.startswith(
                "./reports/eshop_comparison_"
            ):
                # Derive the manufacturer name from the file name
                manufacturer = filename.split("_")[2].split(" ")[0]
                # Read the file into a StyleFrame
                sf = StyleFrame.read_excel(
                    os.path.join(input_dir, filename), read_style=True
                )
                # Write the StyleFrame to a new sheet in the Excel file
                sf.to_excel(writer, sheet_name=manufacturer, index=False)


def run_app():
    manufacturers = ["uriage", "apivita", "tepe", "herba humana"]
    # manufacturers = ["uriage"]

    for manufacturer in manufacturers:
        crawl_data(manufacturer)

    # combine all .xlsx files into one as sheet names of manufacturers
    combine_excel_files(
        "./reports/",
        f'./reports/eshop_comparison {datetime.now().strftime("%Y-%m-%d")}.xlsx',
    )

    for filename in os.listdir("./"):
        if filename.endswith(".xlsx") and filename.startswith(
            "./reports/eshop_comparison_"
        ):
            os.remove(filename)


if __name__ == "__main__":
    run_app()
