from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from dataclasses import dataclass
from datetime import datetime
from typing import List
from rich.progress import Progress

import os
import re
import traceback

from .datatypes import Item, Order
from .scrape_order_page import parse_order_page
from .config import *

def scrape_transaction_urls(driver, url):
    wait = WebDriverWait(driver, TIMEOUT_S)

    driver.get(url)
    invoice_links = wait.until(
        EC.presence_of_all_elements_located(
            (By.XPATH, "//a[contains(text(), 'View invoice')]")
        )
    )
    return [link.get_attribute('href') for link in invoice_links]


def parse_amazon_transactions_for_year(driver, year : str):
    # We assume that we're already logged in

    wait = WebDriverWait(driver, TIMEOUT_S)

    # Start on the generic per-year page to see how many orders there are
    driver.get(f"https://www.amazon.com/your-orders/orders?timeFilter=year-{year}")
    orders_text_element = wait.until(
        EC.visibility_of_element_located(
            (By.XPATH, "//span[contains(@class, 'num-orders')]")
        )
    )
    order_count = int(re.search(r'(\d+)\s*orders', orders_text_element.text).group(1))

    with Progress() as progress:
        status_bar = progress.add_task("[blue]Scraping Amazon transactions...",
                                       total=order_count)

        # Each order page shows us up to 10 orders at a time, loop over them and process reports one at a time
        all_orders = []
        orders_processed = 0
        while orders_processed < order_count:
            page_url = f"https://www.amazon.com/your-orders/orders?timeFilter=year-{year}&startIndex={orders_processed}"
            transaction_urls = scrape_transaction_urls(driver, page_url)

            invoice_orders = []
            for url in transaction_urls:
                # print(f"  ... parsing {url}") # TODO proper logging
                invoice_orders.append(parse_order_page(driver, url))
                progress.update(status_bar, advance=1)

            orders_processed += len(invoice_orders)
            all_orders.extend(invoice_orders)
        assert progress.finished

    return all_orders
