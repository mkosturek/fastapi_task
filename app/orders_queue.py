from dataclasses import dataclass
from .models.order import OrderModel
from sqlalchemy.orm import Session
import random


@dataclass
class OrdersQueue:
    def send_order(self, order: OrderModel):
        print(f"Sending order {order.id} to the warehouse")

    def get_carrier(self, order: OrderModel, db: Session) -> str | None:
        if not self.is_ready(order, db):
            return None
        return random.choice(["DHL", "InPost", "DPD", "FedEx", "UPS", "GLS"])

    def is_ready(self, order: OrderModel, db: Session) -> bool:
        if not order.ready and random.random() > 0.8:
            order.ready = True
            db.commit()
        return order.ready


WAREHOUSE_QUEUE = OrdersQueue()
