from rich.progress import Progress

from .scrape_order_list import load_order_page_and_get_order_count_for_year, scrape_transaction_urls
from .scrape_invoice import parse_invoice

def parse_amazon_transactions_for_year(driver, year : str):
    # Start on the generic per-year page to see how many orders there are
    order_count = load_order_page_and_get_order_count_for_year(driver, year)

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
                invoice_orders.append(parse_invoice(driver, url))
                progress.update(status_bar, advance=1)

            orders_processed += len(invoice_orders)
            all_orders.extend(invoice_orders)
        assert progress.finished

    return all_orders
