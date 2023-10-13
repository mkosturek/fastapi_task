import random

from sqlalchemy.orm import Session

from .models import OrderModel


class OrdersQueue:
    def get_carrier(self, order: OrderModel, db: Session) -> str | None:
        if not self.is_ready(order, db):
            return None
        return random.choice(["DHL", "InPost", "DPD", "FedEx", "UPS", "GLS"])

    def is_ready(self, order: OrderModel, db: Session) -> bool:
        if not order.ready and self._query_external_service_for_readiness(order):
            order.ready = True
            db.commit()
        return order.ready

    @staticmethod
    def _query_external_service_for_readiness(order: OrderModel) -> bool:
        return random.random() > 0.8  # mocked behavior


WAREHOUSE_QUEUE = OrdersQueue()
