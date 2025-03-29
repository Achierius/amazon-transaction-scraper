from typing import List

import sys

from .controller import parse_amazon_transactions_for_year
from .driver import do_manual_amazon_login, make_headless_driver, \
                    login_to_amazon_from_cookies
from .datatypes import Order
from .config import get_user_arguments
from .scrape_invoice import parse_invoice
from .serialization import store_items_to_csv, store_orders_to_csv


def print_results(orders: List[Order]):
    print(f"-----")
    for order in orders:
        print(order)
        print(f"-----")
    print(f"Printed {len(orders)} orders")


def main():
    userconf = get_user_arguments()
    login_cookie_file_path = do_manual_amazon_login()
    driver = make_headless_driver()
    login_to_amazon_from_cookies(driver, login_cookie_file_path)

    try:
        if userconf.test_invoice_path:
            print(parse_invoice(driver, userconf.test_invoice_path))
        else:
            orders = parse_amazon_transactions_for_year(driver, userconf.filter)
    finally:
        driver.quit()

    # Core work is done, now produce outputs + exit
    exit_code = 0
    if userconf.print_results:
        print_results(orders)
    if userconf.item_csv_path:
        try:
            store_items_to_csv(orders, userconf.item_csv_path)
        except Exception as e:
            print(f"error: failed to create item-csv at {userconf.item_csv_path}")
            exit_code = 1
    if userconf.order_csv_path:
        try:
            store_orders_to_csv(orders, userconf.order_csv_path)
        except Exception as e:
            print(f"error: failed to create order-csv at {userconf.item_csv_path}")
            exit_code = 1
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
