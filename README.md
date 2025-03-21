# Amazon Transaction Scraper

Does what it says on the tin, since Amazon no longer does ([since March 20th, 2023](https://linustechtips.com/topic/1493863-amazon-kills-order-history-reports/)).

Brute-force scrapes invoices one at a time, then collects the orders together and presents them in a useable format. Can either print something 'human readable'
to stdout (though with no claim to behave like a proper shell utility) or dump to csv. When dumping, can choose to dump whole orders (--dump-orders) or all
items from every order (--dump-items). Also parses credit card transactions but as of right now there's no facility for dumping those.

Authentication is first done in a headful Chrome driver, then cookies are stored in a tmp-file and re-used by a headless one.

## Usage

Example usage (with [uv](https://github.com/astral-sh/uv)):
```sh
$ uv run -m amazon-order-scraper -y 2024 --dump-orders 2024_orders.csv --dump-items 2024_items.csv
```

With a date-range:
```sh
$ uv run -m amazon-order-scraper -y 2024 --dump-orders 2024_orders.csv --start-date 12-24 --end-date 12-26
$ uv run -m amazon-order-scraper -y 2024 --dump-orders 2024_orders.csv --start-month 02 # equivalent to --start-date 02-01
```

Print 'human readable' summary to stdout:
```sh
$ uv run -m amazon-order-scraper -y 2024 --dump-orders 2024_orders.csv --print-results
```

## TODOs

- Clean up temp files
- Dump credit card transactions
- Get rid of the separate -y parameter
- Use a pool of drivers to accelerate invoice parsing
- More cleverly collect invoice links
