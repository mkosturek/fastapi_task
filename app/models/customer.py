import uuid
from app.database import Base
from sqlalchemy import Column, String
from sqlalchemy.orm import relationship


class CustomerModel(Base):
    __tablename__ = "users"
    id = Column(
        "id", String(length=36), default=lambda: str(uuid.uuid4()), primary_key=True
    )
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    receiver_email = Column(String, nullable=True)

    orders = relationship("OrderModel", back_populates="customer")
