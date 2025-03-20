from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from dataclasses import dataclass
from datetime import datetime
from typing import List

import os
import re
import traceback

from .datatypes import Item, Order
from .scrape_invoice import parse_invoice
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


def load_order_page_and_get_order_count_for_year(driver, year : str):
    wait = WebDriverWait(driver, TIMEOUT_S)

    # Start on the generic per-year page to see how many orders there are
    driver.get(f"https://www.amazon.com/your-orders/orders?timeFilter=year-{year}")
    orders_text_element = wait.until(
        EC.visibility_of_element_located(
            (By.XPATH, "//span[contains(@class, 'num-orders')]")
        )
    )
    order_count = int(re.search(r'(\d+)\s*orders', orders_text_element.text).group(1))
    return order_count
