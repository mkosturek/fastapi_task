import uuid
from app.database import Base
from sqlalchemy import Column, ForeignKey, String, Boolean
from sqlalchemy.orm import relationship


class CustomerModel(Base):
    __tablename__ = "users"
    id = Column(
        "id", String(length=36), default=lambda: str(uuid.uuid4()), primary_key=True
    )
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)

    orders = relationship("OrderModel", back_populates="customer")


class OrderModel(Base):
    __tablename__ = "orders"
    id = Column(
        "id", String(length=36), default=lambda: str(uuid.uuid4()), primary_key=True
    )
    customer_id = Column(String, ForeignKey("users.id"))
    product_name = Column(String, nullable=False)
    ready = Column(Boolean, default=False, nullable=False)
    customer = relationship("CustomerModel", back_populates="orders")
