# Project Summary

Amazon no longer lets you dump order data to a CSV, at least not on a reasonable timescale.  
This project provides a utility which will scrape your Amazon or

# Technical Details

## User interface

The user interface is a simple argparse

## Set up headless browser logged into Amazon

First, in order to get login cookies set-up, we launch a browser window which the user will
use to log in, after which we store the resulting cookies in a tmp file and close the visible
driver. Then, we launch a new, headless driver, load the cookies, and navigate to Amazon
so that we're logged in.

## Collect list of invoice links to scan

We use Selenium for our scraping.

For our first step in the actual scraping, we go to the order history for the specified year,
then accumulate a list of all \<links to invoice, date order was placed\> combinations
by scanning through every page in the history for that year one at a time (there are usually
ten orders per page).

Then, after accumulating all the links, we filter them down to the ones
whose orders were placed in the date-range specified by the user.

## Scraping order pages

For each order page, we then need to scrape everything we care about. There are three main levels
of logical hierarchy that we need to scrape through:
  1. Top-level: this is the overall summary of the page. It includes
    - When the order was placed ("Order Placed: February 22, 2025") -- at the top of the page
    - The order number ("Amazon.com order number: 111-7380043-7278630") -- at the top of the page
    - The order total ("Order Total: $19.17") -- at the top of the page
    - The total before tax ("Total before tax:     $61.64") -- at the bottom of the page
    - A list of credit card transactions ("Visa ending in 1792: February 23, 2025:  $32.73") -- at the bottom of the page
  2. Bundles of items which were shipped together: each is a table with the text "Shipped on \<MONTH\> \<DAY\>, \<YEAR\>" at the top.
     They each contain a series of rows which correspond to items in the order. On the left side are the item details, on the right is the price.
     Example:
```
Items Ordered   Price
2 of: Mr. Pen- Clasp Envelopes, 18 Pack, 9" x 12", White, Kraft Letter Size Envelopes, White Envelopes, Document Envelope, Clasp Kraft Envelopes, Clasp and Gummed Closure Envelopes, Manilla Envelopes
Sold by: Mr. Pen (seller profile)
Supplied by: Mr. Pen (seller profile)

Condition: New
    $7.85
```
  3. Each item in the table has a bunch of details we care about.
    - Count
    - Description
    - Sold-by

Once we have all that, we bundle it up and return a single object per invoice with all the details above.

## Creating the output

After that, we just take everything and put it into a CSV -- easy peasy!

# File Hierarchy

- `amazon-order-scraper/`: project root
  - `__init__.py`: for if anyone uses us as a library, which right now they do not
  - `__main__.py`: the entry point for our executable, should contain minimal logic
  - `config.py`: contains global configuration + user-argument handling
  - `datatypes.py`: defines the types we scrape from pages
  - `driver.py`: handles the creation of the web-drivers we use, as well as logging in to Amazon
  - `scrape_invoice.py`: scrapes/parses invoice pages
  - `scrape_order_list.py`: scrapes/parses order summaries from the Your Orders tab
  - `controller.py`: manages logic & user-reporting
