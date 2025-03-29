from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

import os
import re
import traceback

from .datatypes import Item, Order, CardCharge
from .config import *

def parse_order_row(row, shipping_date: Optional[datetime]) -> Item:
    # Extract count from "1 of:" text
    count_text = row.find_element(By.XPATH, ".//td[1]").text
    count_match = re.search(r'(\d+)\s+of', count_text)
    count = int(count_match.group(1)) if count_match else 1

    # Extract description
    # TODO is doing this via the italics too fragile?
    description = row.find_element(By.XPATH, ".//td[1]//i").text.strip()

    # Extract "Sold by" and "Supplied by"
    # TODO idk if I like doing this via the 'tiny' class
    tiny_text = row.find_element(By.XPATH, ".//td[1]//span[contains(@class, 'tiny')]").text
    sold_by_match = re.search(r'Sold by:\s*(.+)', tiny_text)
    supplied_by_match = re.search(r'Supplied by:\s*(.+)', tiny_text)

    sold_by = sold_by_match.group(1).strip() if sold_by_match else "N/A"
    supplied_by = supplied_by_match.group(1).strip() if supplied_by_match else "N/A"

    unit_price_text = row.find_element(By.XPATH, ".//td[2]").text
    grocery_price_match = re.search('\(\$[\d,]+\.\d+\/\S+\)\s*\$([\d,]+\.\d\d)', unit_price_text)
    if grocery_price_match:
        unit_price_text = grocery_price_match.group(1).strip()
    if unit_price_text:
        unit_price = float(re.sub(r'[^\d.]', '', unit_price_text))
    else:
        # I've seen this with like bag-charges on Whole Foods orders???
        unit_price = 0.0

    return Item(
        unit_price=unit_price,
        count=count,
        description=description,
        sold_by=sold_by,
        supplied_by=supplied_by,
        shipping_date=shipping_date,
    )


def parse_order_bundle(bundle) -> List[Item]:
    # All items in a bundle share one shipping date
    shipping_date = None
    try:
        shipping_text = bundle.find_element(By.XPATH, ".//*[contains(text(), 'Shipped on')]").text
        shipping_date_match = re.search(r'Shipped on\s*([A-Za-z]+\s\d{1,2},\s\d{4})', shipping_text)
        assert shipping_date_match
        shipping_date = datetime.strptime(shipping_date_match.group(1), '%B %d, %Y')
    except NoSuchElementException:
        # Make sure that the reason we couldn't find the ship date was that
        # it just hasn't shipped yet, not that the invoice format has changed or &c
        bundle.find_element(By.XPATH, ".//*[contains(text(), 'Not Yet Shipped')]").text
    
    items = []
    # Find the INNERMOST table which contains "Items Ordered", and break it into rows
    item_rows = bundle.find_element(By.XPATH, ".//table[contains(., 'Items Ordered') and not(.//table[contains(., 'Items Ordered')])]").find_elements(By.XPATH, ".//tr")
    item_rows = item_rows[1:] # The first row is just "Items Ordered"/"Price" lol
    assert len(item_rows)
    for row in item_rows:
        items.append(parse_order_row(row, shipping_date))
    return items


def parse_card_charges(driver) -> List[CardCharge]:
    # There's a table which contains "Credit Card transactions" and the transactions table
    # Then the transactions table itself
    # We *could* just look for everything that has "ending in" but I'd hate to accidentally pick up
    # something from an order description
    try:
        transactions_table = driver.find_element(By.XPATH,
                                                     ("//*[contains(text(), 'Credit Card transactions')]/ancestor::tbody[1]"
                                                      "//tbody[.//text()[contains(., 'ending in')]]"))
    except NoSuchElementException:
        # This happens e.g. for "Subscribe and Save" orders which have yet to charge your card.
        return []

    charges = []
    rows = transactions_table.find_elements(By.XPATH, ".//tr")
    for row in rows:
        text = row.text

        amount_text = re.search(r'\$(\d[\d,]*.\d\d)', text).group(1)
        amount = float(re.sub(r'[^\d.]', '', amount_text))

        card_digits = re.search(r'ending in (\d\d\d\d)', text).group(1)
        date_text = re.search(r'(\S+ \d+, 20\d\d)', text).group(1)
        date = datetime.strptime(date_text, '%B %d, %Y')
        
        charge = CardCharge(
            card_digits=card_digits,
            date=date,
            amount=amount
        )
        charges.append(charge)
    return charges


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

    # Extract order total (top of the page)
    total_text = driver.find_element(By.XPATH, "//*[contains(text(),'Order Total:')]/..").text
    total = float(re.sub(r'[^\d.]', '', total_text))

    # Extract sub-total (bottom of the page)
    sub_total_text = driver.find_element(By.XPATH, "//*[contains(text(),'Item(s) Subtotal')]/..").text
    sub_total = float(re.sub(r'[^\d.]', '', sub_total_text))

    # Within an invoice, items are grouped as they are shipped, so if they ship in different batches
    # the invoice will have multiple "bundles", each with their own ship-date
    order_bundles = driver.find_elements(By.XPATH,
                                            ("//*[contains(text(), 'Shipped on') or contains(text(), 'Not Yet Shipped')]"
                                             "/ancestor::tbody[.//text()[contains(., 'Items Ordered')]][1]"))
    # We want to flatten this out into a single list of items, with each item having its own ship-date
    all_items = []
    for bundle in order_bundles:
        all_items.extend(parse_order_bundle(bundle))

    charges = parse_card_charges(driver)

    return Order(
        order_date=order_date,
        order_number=order_number,
        total=total,
        sub_total=sub_total,
        items=all_items,
        url=url,
        charges=charges,
    )
