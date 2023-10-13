import uuid
from pydantic import BaseModel


class CustomerBaseSchema(BaseModel):
    name: str
    description: str

    class Config:
        from_attributes = True


class CreateCustomerSchema(CustomerBaseSchema):
    ...


class CustomerSchema(CustomerBaseSchema):
    id: uuid.UUID


class OrderBaseSchema(BaseModel):
    product_name: str

    class Config:
        from_attributes = True


class CreateOrderSchema(OrderBaseSchema):
    customer_id: str


class OrderSchema(OrderBaseSchema):
    customer_id: uuid.UUID
    id: uuid.UUID
    ready: bool
    carrier: str | None
