from .datatypes import Order, Item, CardCharge

from dataclasses import dataclass, fields
from datetime import datetime
from typing import List, Optional
import csv
import copy
import os


# An item separated from the context of its original order
# Ready to be serialized to a CSV
@dataclass
class FlattenedItem:
    base_item: Item
    order_date: datetime
    order_number: str
    charges_allocated: float
    accounted_cost: float


def _flatten_items_from_order(order : Order) -> List[FlattenedItem]:
    # Charges like shipping/tax/fees/etc., as well as the reverse (credits, discounts),
    # need to be allocated between items in the order -- we choose to do so pro-rata.
    charges_to_allocate = order.total - order.sub_total
    def allocate_pro_rata(item : Item) -> tuple[float, float]:
        item_cost = item.count * item.unit_price
        ratio = item_cost / order.sub_total if order.sub_total > 0 else 0
        charges_allocated = ratio * charges_to_allocate
        return charges_allocated, charges_allocated + item_cost

    flattened_items = []
    for item in order.items:
        charges_allocated, total_cost = allocate_pro_rata(item)
        flat = FlattenedItem(
            base_item=copy.deepcopy(item),
            order_date=order.order_date,
            order_number=order.order_number,
            charges_allocated=charges_allocated,
            accounted_cost=total_cost,
        )
        flattened_items.append(flat)
    return flattened_items


def store_items_to_csv(orders : List[Order], target_file_path : str):
    """
    Exports all items from all orders to a CSV file.
    Each item is flattened and includes order context information.
    """
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(os.path.abspath(target_file_path)), exist_ok=True)
    
    # Collect all flattened items
    all_flattened_items = []
    for order in orders:
        all_flattened_items.extend(_flatten_items_from_order(order))
    
    if not all_flattened_items:
        print(f"No items to export to {target_file_path}")
        return
    
    # Define CSV headers
    headers = [
        'order_date', 'order_number', 'charges_allocated', 'accounted_cost',
        'unit_price', 'count', 'description',
        'sold_by', 'supplied_by', 'shipping_date',
    ]
    
    with open(target_file_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(headers)
        
        for flat_item in all_flattened_items:
            item = flat_item.base_item
            writer.writerow([
                flat_item.order_date.strftime('%Y-%m-%d'),
                flat_item.order_number,
                f'${flat_item.charges_allocated:.2f}',
                f'${flat_item.accounted_cost:.2f}',
                f'${item.unit_price:.2f}',
                item.count,
                item.description,
                item.sold_by,
                item.supplied_by,
                item.shipping_date if item.shipping_date else '',
            ])
    
    print(f"Exported {len(all_flattened_items)} items to {target_file_path}")


def store_orders_to_csv(orders : List[Order], target_file_path : str):
    """
    Exports order summaries to a CSV file.
    Each order is exported without its detailed items and charges,
    but includes counts of items and charges.
    """
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(os.path.abspath(target_file_path)), exist_ok=True)
    
    if not orders:
        print(f"No orders to export to {target_file_path}")
        return
    
    # Define CSV headers
    headers = [
        'order_date', 'order_number', 'total', 'sub_total', 
        'item_count', 'charge_count'
    ]
    
    with open(target_file_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(headers)
        
        for order in orders:
            writer.writerow([
                order.order_date.strftime('%Y-%m-%d'),
                order.order_number,
                f'${order.total:.2f}',
                f'${order.sub_total:.2f}',
                len(order.items),
                len(order.charges),
            ])
    
    print(f"Exported {len(orders)} orders to {target_file_path}")
