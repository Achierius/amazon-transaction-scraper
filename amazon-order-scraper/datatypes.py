from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class Item:
    unit_price: float
    count: int
    description: str
    sold_by: str
    supplied_by: str
    shipping_date: Optional[datetime]

    def __str__(self):
        return (f"{self.count}x '{self.description}' @ ${self.unit_price:.2f} each\n"
                f"  Sold by: {self.sold_by}\n"
                f"  Supplied by: {self.supplied_by if self.supplied_by else 'N/A'}\n"
                f"  Shipping Date: {self.shipping_date.strftime('%Y-%m-%d') if self.shipping_date else 'N/A'}")


@dataclass
class Order:
    order_date: datetime
    order_number: str
    total: float
    sub_total: float
    items: List[Item]
    url: str # TODO we can just get this from the order_number

    def __str__(self):
        order_str = (
            f"Order #{self.order_number}\n"
            f"Link: <{self.url}>\n"
            f"Order Date: {self.order_date.strftime('%Y-%m-%d')}\n"
            f"Order Total: ${self.total:.2f}\n"
            f"Sub-Total: ${self.sub_total:.2f}\n"
            f"Items:"
        )
        for item in self.items:
            order_str += f"  {str(item)}\n"
        return order_str


@dataclass
class OrderSummary:
    order_date: datetime
    total: float
    order_number: str
    invoice_url: str
    delivered: bool

    def __str__(self):
        delivered_str = "Delivered" if delivered else "Not Delivered"
        order_str = (
            f"Order Summary for Order #{self.order_number}\n"
            f"Invoice Link: <{self.invoice_url}>\n"
            f"Order Date: {self.order_date.strftime('%Y-%m-%d')}\n"
            f"Order Total: ${self.total:.2f}\n"
            f"Status: {delivered_str}"
        )

