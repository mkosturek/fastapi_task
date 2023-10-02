import uuid
from .database import Base
from sqlalchemy import TIMESTAMP, Column, ForeignKey, String, Boolean, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.orders_queue import WAREHOUSE_QUEUE


class CustomerModel(Base):
    __tablename__ = "users"
    id = Column(
        "id", String(length=36), default=lambda: str(uuid.uuid4()), primary_key=True
    )
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    receiver_email = Column(String, nullable=True)

    orders = relationship("OrderModel", back_populates="customer")

    def place_order(self, order: "OrderModel"):
        WAREHOUSE_QUEUE.send_order(order)


class OrderModel(Base):
    __tablename__ = "orders"
    id = Column(
        "id", String(length=36), default=lambda: str(uuid.uuid4()), primary_key=True
    )
    customer_id = Column(String, ForeignKey("users.id"))
    product_name = Column(String, nullable=False)
    ready = Column(Boolean, default=False, nullable=False)
    customer = relationship("CustomerModel", back_populates="orders")
