from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
import argparse
import re
from datetime import datetime

# --- Static configuration ---

TIMEOUT_S = 20
LOGIN_TIMEOUT_S = 300
MANUAL_LOGIN_CONFIRMATION = False
EXCLUDE_INVOICES_WITHOUT_CREDIT_CARD_CHARGE = True

# --- Runtime configuration ---

@dataclass
class OrderFilter:
    year: str
    start_date: datetime
    end_date: datetime

@dataclass
class UserConfiguration:
    filter : OrderFilter
    print_results : bool
    # If these are not set, then the script will not create these CSVs
    item_csv_path : Optional[str]
    order_csv_path : Optional[str]

def _get_raw_user_arguments() -> Dict[str, Any]:
    parser = argparse.ArgumentParser(
        description="Scrape Amazon order history for a specific time period",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Year argument
    parser.add_argument("-y", "--year", required=True, 
                        help="Year to scrape orders from (e.g., 2025)")
    
    # Date range options
    date_group = parser.add_argument_group("Date range options")
    date_group.add_argument("--start-date", 
                           help="Start date in MM-DD format (e.g., 01-15)")
    date_group.add_argument("--end-date", 
                           help="End date in MM-DD format (e.g., 12-31)")
    
    # Month range options
    month_group = parser.add_argument_group("Month range options")
    month_group.add_argument("--start-month", 
                            help="Start month in MM format (e.g., 01)")
    month_group.add_argument("--end-month", 
                            help="End month in MM format (e.g., 12)")
    
    # Output options
    parser.add_argument("--print-results", action="store_true",
                       help="Print results to stdout")
    parser.add_argument("--dump-items", metavar="FILE",
                       help="Path to CSV file where item data should be exported")
    parser.add_argument("--dump-orders", metavar="FILE",
                       help="Path to CSV file where order summary data should be exported")
    
    args = parser.parse_args()
    
    # Validate year format
    if not re.match(r'^\d{4}$', args.year):
        parser.error("Year must be in YYYY format")
    
    # Validate date formats if provided
    date_pattern = re.compile(r'^(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])$')
    month_pattern = re.compile(r'^(0[1-9]|1[0-2])$')
    
    if args.start_date and not date_pattern.match(args.start_date):
        parser.error("Start date must be in MM-DD format (e.g., 01-15)")
    if args.end_date and not date_pattern.match(args.end_date):
        parser.error("End date must be in MM-DD format (e.g., 12-31)")
    
    if args.start_month and not month_pattern.match(args.start_month):
        parser.error("Start month must be in MM format (e.g., 01)")
    if args.end_month and not month_pattern.match(args.end_month):
        parser.error("End month must be in MM format (e.g., 12)")
    
    # Check for conflicting options
    if (args.start_date or args.end_date) and (args.start_month or args.end_month):
        parser.error("Cannot use both date range and month range options together")
    
    return vars(args)

def _parse_user_arguments(args: Dict[str, Any]) -> UserConfiguration:
    year = args['year']
    
    # Handle date range
    if args['start_date'] or args['end_date']:
        start_date_str = args['start_date'] or "01-01"
        end_date_str = args['end_date'] or "12-31"
        
        start_date = datetime.strptime(f"{year}-{start_date_str}", "%Y-%m-%d")
        end_date = datetime.strptime(f"{year}-{end_date_str}", "%Y-%m-%d")
    
    # Handle month range
    elif args['start_month'] or args['end_month']:
        start_month = args['start_month'] or "01"
        end_month = args['end_month'] or "12"
        
        start_date = datetime.strptime(f"{year}-{start_month}-01", "%Y-%m-%d")
        
        # For end date, use the last day of the month
        if end_month == "12":
            end_date = datetime.strptime(f"{year}-12-31", "%Y-%m-%d")
        elif end_month in ["04", "06", "09", "11"]:
            end_date = datetime.strptime(f"{year}-{end_month}-30", "%Y-%m-%d")
        elif end_month == "02":
            # Handle February (including leap years)
            if (int(year) % 4 == 0 and int(year) % 100 != 0) or (int(year) % 400 == 0):
                end_date = datetime.strptime(f"{year}-02-29", "%Y-%m-%d")
            else:
                end_date = datetime.strptime(f"{year}-02-28", "%Y-%m-%d")
        else:
            end_date = datetime.strptime(f"{year}-{end_month}-31", "%Y-%m-%d")
    
    # Default to full year
    else:
        start_date = datetime.strptime(f"{year}-01-01", "%Y-%m-%d")
        end_date = datetime.strptime(f"{year}-12-31", "%Y-%m-%d")
    
    return UserConfiguration(
        filter=OrderFilter(
            year=year,
            start_date=start_date,
            end_date=end_date
        ),
        print_results=args.get('print_results', False),
        item_csv_path=args.get('dump_items'),
        order_csv_path=args.get('dump_orders')
    )

def get_user_arguments() -> UserConfiguration:
    return _parse_user_arguments(_get_raw_user_arguments())
