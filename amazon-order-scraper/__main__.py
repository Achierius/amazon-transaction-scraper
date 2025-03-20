from typing import List

from .controller import parse_amazon_transactions_for_year
from .driver import do_manual_amazon_login, make_headless_driver, \
                    login_to_amazon_from_cookies
from .datatypes import Order
from .config import get_user_arguments


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
        orders = parse_amazon_transactions_for_year(driver, userconf.filter)
    finally:
        driver.quit()

    if userconf.print_results:
        print_results(orders)


if __name__ == "__main__":
    main()
