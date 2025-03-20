from rich.progress import Progress

from .scrape_order_list import load_order_page_and_get_order_count_for_year, scrape_order_summaries
from .scrape_invoice import parse_invoice
from .config import OrderFilter, EXCLUDE_INVOICES_WITHOUT_CREDIT_CARD_CHARGE

def collect_order_summaries(driver, year : str, order_count : int):
    all_summaries = []
    with Progress() as progress:
        status_bar = progress.add_task("[blue]Collecting Amazon invoices...",
                                       total=order_count)
        while len(all_summaries) < order_count:
            target_page = f"https://www.amazon.com/your-orders/orders?timeFilter=year-{year}&startIndex={len(all_summaries)}"
            # TODO Logging print(target_page)
            summaries = scrape_order_summaries(driver, target_page)
            progress.update(status_bar, advance=len(summaries))
            all_summaries.extend(summaries)
        assert progress.finished
    return all_summaries


def filter_order_summaries(summaries, filter : OrderFilter):
    return [s for s in summaries if (s.order_date <= filter.end_date and s.order_date >= filter.start_date)]


def scrape_invoices(driver, order_summaries):
    parsed_orders = []
    with Progress() as progress:
        status_bar = progress.add_task(f"[blue]Processing {len(order_summaries)} Amazon invoices...",
                                       total=len(order_summaries))

        for summary in order_summaries:
            order = parse_invoice(driver, summary.invoice_url)
            progress.update(status_bar, advance=1)
            if EXCLUDE_INVOICES_WITHOUT_CREDIT_CARD_CHARGE and not order.charges:
                continue
            parsed_orders.append(order)
        assert progress.finished
    return parsed_orders


def parse_amazon_transactions_for_year(driver, filter : OrderFilter):
    # Start on the generic per-year page to see how many orders there are
    print(f"Scraping transactions for year {filter.year}...")
    order_count = load_order_page_and_get_order_count_for_year(driver, filter.year)
    order_summaries = collect_order_summaries(driver, filter.year, order_count)
    order_summaries = filter_order_summaries(order_summaries, filter)
    if not order_summaries:
        # TODO logging
        print(f"No orders found in given date-range: {filter.start_date} to {filter.end_date}")
        return []
    orders = scrape_invoices(driver, order_summaries)
    print(f"Scraped {len(orders)} orders")
    return orders
