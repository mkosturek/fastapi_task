from datetime import datetime
from typing import List
import uuid
from pydantic import BaseModel, EmailStr, constr


class CustomerBaseSchema(BaseModel):
    name: str
    description: str

    class Config:
        from_attributes = True


class CreateCustomerSchema(CustomerBaseSchema):
    ...


class CustomerSchema(CustomerBaseSchema):
    id: uuid.UUID


# class SendEmailSchema(BaseModel):
#     text: str
#     receiver_email: EmailStr


class OrderBaseSchema(BaseModel):
    product_name: str
    customer_id: uuid.UUID

    class Config:
        from_attributes = True


class CreateOrderSchema(OrderBaseSchema):
    ...


class OrderSchema(OrderBaseSchema):
    id: uuid.UUID
    ready: bool
    carrier: str | None
