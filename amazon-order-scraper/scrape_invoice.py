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
from .config import *

def parse_order_row(driver, row):
    try:
        # Extract count from "1 of:" text
        count_text = row.find_element(By.XPATH, ".//td[1]").text
        count_match = re.search(r'(\d+)\s+of', count_text)
        count = int(count_match.group(1)) if count_match else 1

        # Extract description
        description = row.find_element(By.XPATH, ".//td[1]//i").text.strip()

        # Extract "Sold by" and "Supplied by"
        tiny_text = row.find_element(By.XPATH, ".//td[1]//span[contains(@class, 'tiny')]").text
        sold_by_match = re.search(r'Sold by:\s*(.+)', tiny_text)
        supplied_by_match = re.search(r'Supplied by:\s*(.+)', tiny_text)

        sold_by = sold_by_match.group(1).strip() if sold_by_match else "N/A"
        supplied_by = supplied_by_match.group(1).strip() if supplied_by_match else "N/A"

        # Extract unit price
        unit_price_text = row.find_element(By.XPATH, ".//td[2]").text
        if unit_price_text:
            unit_price = float(re.sub(r'[^\d.]', '', unit_price_text))
        else:
            unit_price = 0.0
    except Exception as e:
        breakpoint()
        print(e)

    return Item(
        unit_price=unit_price,
        count=count,
        description=description,
        sold_by=sold_by,
        supplied_by=supplied_by
    )


def parse_invoice(driver, url) -> Order:
    wait = WebDriverWait(driver, TIMEOUT_S)
    driver.get(url)

    # Extract order date
    order_date_text = wait.until(
        EC.visibility_of_element_located((By.XPATH, "//*[contains(text(), 'Order Placed:')]/.."))
    ).text
    order_date = re.search(r'Order Placed:\s*([A-Za-z]+\s\d{1,2},\s\d{4})', order_date_text)
    order_date = datetime.strptime(order_date.group(1), '%B %d, %Y') if order_date else None

    # Extract order number
    order_number_el = driver.find_element(By.XPATH, "//b[contains(text(), 'order number:')]/..")
    order_number = re.search(r'order number:\s*(\d+-\d+-\d+)', order_number_el.text).group(1)

    # Extract shipping date (optional fallback if available)
    shipping_date = None
    try:
        shipping_text = driver.find_element(By.XPATH, "//*[contains(text(), 'Shipped on')]").text
        shipping_date_match = re.search(r'Shipped on\s*([A-Za-z]+\s\d{1,2},\s\d{4})', shipping_text)
        if shipping_date_match:
            shipping_date = datetime.strptime(shipping_date_match.group(1), '%B %d, %Y')
    except:
        pass # TODO come on

    # Extract order total (top of the page)
    total_text = driver.find_element(By.XPATH, "//*[contains(text(),'Order Total:')]/..").text
    total = float(re.sub(r'[^\d.]', '', total_text))

    # Extract sub-total (bottom of the page)
    sub_total_text = driver.find_element(By.XPATH, "//*[contains(text(),'Item(s) Subtotal')]/..").text
    sub_total = float(re.sub(r'[^\d.]', '', sub_total_text))

    items = []
    # Find the INNERMOST table which contains "Items Ordered", and break it into rows
    item_rows = driver.find_element(By.XPATH, "//table[contains(., 'Items Ordered') and not(.//table[contains(., 'Items Ordered')])]").find_elements(By.XPATH, ".//tr")
    item_rows = item_rows[1:] # The first row is just "Items Ordered"/"Price" lol
    for row in item_rows:
        items.append(parse_order_row(driver, row))

    return Order(
        order_date=order_date,
        shipping_date=shipping_date,
        order_number=order_number,
        total=total,
        sub_total=sub_total,
        items=items,
        url=url
    )
