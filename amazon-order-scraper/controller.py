from rich.progress import Progress

from .scrape_order_list import load_order_page_and_get_order_count_for_year, scrape_transaction_urls
from .scrape_invoice import parse_invoice

def collect_invoice_urls(driver, year : str, order_count : int):
    invoice_urls = []
    with Progress() as progress:
        status_bar = progress.add_task("[blue]Collecting Amazon invoices...",
                                       total=order_count)
        while len(invoice_urls) < order_count:
            target_page = f"https://www.amazon.com/your-orders/orders?timeFilter=year-{year}&startIndex={len(invoice_urls)}"
            urls = scrape_transaction_urls(driver, target_page)
            progress.update(status_bar, advance=len(urls))
            invoice_urls.extend(urls)
        assert progress.finished
    return invoice_urls


def filter_invoice_urls(urls):
    # TODO filter by date
    return urls


def scrape_invoices(driver, invoice_urls):
    parsed_orders = []
    with Progress() as progress:
        status_bar = progress.add_task("[blue]Scraping Amazon transactions...",
                                       total=len(invoice_urls))

        for url in invoice_urls:
            parsed_orders.append(parse_invoice(driver, url))
            progress.update(status_bar, advance=1)
        assert progress.finished
    return parsed_orders


def parse_amazon_transactions_for_year(driver, year : str):
    # Start on the generic per-year page to see how many orders there are
    order_count = load_order_page_and_get_order_count_for_year(driver, year)
    invoice_urls = collect_invoice_urls(driver, year, order_count)
    invoice_urls = filter_invoice_urls(invoice_urls)
    orders = scrape_invoices(driver, invoice_urls)
    return orders
