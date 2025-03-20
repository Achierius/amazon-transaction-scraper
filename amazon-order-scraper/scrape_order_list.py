from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
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

from .datatypes import Item, Order, OrderSummary
from .scrape_invoice import parse_invoice
from .config import *

def scrape_order_summaries(driver, url):
    driver.get(url)
    order_containers = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.XPATH, "//div[contains(@class, 'order-header')]"))
    )

    orders = []
    for container in order_containers:
        # TODO the current way of finding these spans is a bit fragile
        # Since I think we always have XPath 2.0, we can use match instead of the weird stuff I'm doing rn?

        order_date_parent_elem = container.find_element(By.XPATH, ".//div[.//span[contains(text(), 'Order placed')] and .//span[contains(text(), ',')]]")
        order_date_elem = order_date_parent_elem.find_element(By.XPATH, ".//span[contains(text(), ',')]")
        order_date = datetime.strptime(order_date_elem.text.strip(), '%B %d, %Y')
    
        total_parent_elem = container.find_element(By.XPATH, ".//div[.//span[contains(text(), 'Total')] and .//span[contains(text(), '$')]]")
        total_elem = total_parent_elem.find_element(By.XPATH, ".//span[contains(text(), '$')]")
        total = total_elem.text.strip()
    
        order_number_parent_elem = container.find_element(By.XPATH, ".//div[.//span[contains(text(), 'Total')] and .//span[contains(text(), '-')]]")
        order_number_elem = order_number_parent_elem.find_element(By.XPATH, ".//span[contains(text(), '-')]")
        order_number = order_number_elem.text.strip()

        # TODO don't be lazy, get the date too
        try:
            delivered = bool(container.find_element(By.XPATH, ".//span[contains(text(), 'Delivered')]").text)
        except NoSuchElementException:
            delivered = False
    
        invoice_link_elem = container.find_element(By.XPATH, ".//a[contains(text(), 'View invoice')]")
        invoice_url = invoice_link_elem.get_attribute("href")
        
        summary = OrderSummary(
            order_date=order_date,
            total=total,
            order_number=order_number,
            invoice_url=invoice_url,
            delivered=delivered,
        )
        orders.append(summary)

    return orders


def scrape_transaction_urls(driver, url):
    """ Essentially legacy """
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

    # TODO Logging print(target_page)
    driver.get(f"https://www.amazon.com/your-orders/orders?timeFilter=year-{year}")
    orders_text_element = wait.until(
        EC.visibility_of_element_located(
            (By.XPATH, "//span[contains(@class, 'num-orders')]")
        )
    )
    order_count = int(re.search(r'(\d+)\s*orders', orders_text_element.text).group(1))
    return order_count
