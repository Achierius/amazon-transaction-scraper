from rich.progress import Progress

from .scrape_order_list import load_order_page_and_get_order_count_for_year, scrape_order_summaries
from .scrape_invoice import parse_invoice

def collect_order_summaries(driver, year : str, order_count : int):
    all_summaries = []
    with Progress() as progress:
        status_bar = progress.add_task("[blue]Collecting Amazon invoices...",
                                       total=order_count)
        while len(all_summaries) < order_count:
            target_page = f"https://www.amazon.com/your-orders/orders?timeFilter=year-{year}&startIndex={len(all_summaries)}"
            summaries = scrape_order_summaries(driver, target_page)
            progress.update(status_bar, advance=len(summaries))
            all_summaries.extend(summaries)
        assert progress.finished
    return all_summaries


def filter_order_summaries(summaries):
    # TODO filter by date
    return summaries


def scrape_invoices(driver, order_summaries):
    parsed_orders = []
    with Progress() as progress:
        status_bar = progress.add_task("[blue]Scraping Amazon transactions...",
                                       total=len(order_summaries))

        for summary in order_summaries:
            parsed_orders.append(parse_invoice(driver, summary.invoice_url))
            progress.update(status_bar, advance=1)
        assert progress.finished
    return parsed_orders


def parse_amazon_transactions_for_year(driver, year : str):
    # Start on the generic per-year page to see how many orders there are
    order_count = load_order_page_and_get_order_count_for_year(driver, year)
    order_summaries = collect_order_summaries(driver, year, order_count)
    order_summaries = filter_order_summaries(order_summaries)
    orders = scrape_invoices(driver, order_summaries)
    return orders
