from .controller import parse_amazon_transactions_for_year
from .driver import do_manual_amazon_login, make_headless_driver, \
                    login_to_amazon_from_cookies


def main():
    login_cookie_file_path = do_manual_amazon_login()
    driver = make_headless_driver()
    login_to_amazon_from_cookies(driver, login_cookie_file_path)

    try:
        print(f"Scraping transactions for year {2025}...")
        orders = parse_amazon_transactions_for_year(driver, 2025)
        print(f"-----")
        for order in orders:
            print(order)
            print(f"-----")
        print(f"Scraped {len(orders)} orders")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
