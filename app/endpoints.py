import uuid
from fastapi import Depends, HTTPException, status, APIRouter, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.deps import get_db
from app import models
from app import schemas
from typing import List
from io import StringIO
import csv
from app.orders_queue import WAREHOUSE_QUEUE


customer_router = APIRouter()


@customer_router.post("/", status_code=201)
def add_customers(
    payload: schemas.CreateCustomerSchema, db: Session = Depends(get_db)
) -> schemas.CustomerSchema:
    new_customer = models.CustomerModel(**payload.model_dump())
    db.add(new_customer)
    db.commit()
    db.refresh(new_customer)
    return new_customer


@customer_router.get("/")
def get_customers(db: Session = Depends(get_db)) -> List[schemas.CustomerSchema]:
    return db.query(models.CustomerModel).all()


@customer_router.get("/export")
def export_customers(db: Session = Depends(get_db)):
    from_db = db.query(models.CustomerModel).all()
    data = [[obj.id, obj.name, obj.description] for obj in from_db]
    f = StringIO()
    csv.writer(f).writerows(data)

    response = StreamingResponse(iter([f.getvalue()]), media_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=export.csv"
    return response


@customer_router.get("/{id}")
def get_customer(id: str, db: Session = Depends(get_db)):
    customer = (
        db.query(models.CustomerModel).filter(models.CustomerModel.id == id).first()
    )
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No customer with this id: {id} found",
        )
    return customer


# @customer_router.post("/send_email", status_code=201)
# def send_email(
#     sender_id: str, payload: schemas.SendEmailSchema, db: Session = Depends(get_db)
# ) -> bool:
#     sender = (
#         db.query(models.CustomerModel)
#         .filter(models.CustomerModel.id == sender_id)
#         .first()
#     )

#     sender.receiver_email = str(payload.receiver_email)
#     db.commit()

#     dummy_send_email(payload.text, sender)
#     return True


# def dummy_send_email(text: str, customer: models.CustomerModel):
#     email = f"TO: {customer.receiver_email}\n" f"FROM: {customer.name}\n\n" f"{text}"
#     print(email)

order_router = APIRouter()


@order_router.post("/", status_code=201)
def add_order(
    payload: schemas.CreateOrderSchema, db: Session = Depends(get_db)
) -> schemas.OrderSchema:
    customer = (
        db.query(models.CustomerModel)
        .filter(models.CustomerModel.id == payload.customer_id)
        .first()
    )

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No customer with this id: {payload.customer_id} found",
        )

    order = models.OrderModel(**payload.model_dump())
    customer.place_order(order, db)
    return schemas.OrderSchema(
        product_name=order.product_name,
        customer_id=order.customer_id,
        id=order.id,
        ready=order.ready,
        carrier=None,
    )


@order_router.get("/")
def get_orders(
    filter_ready: bool | None = None, db: Session = Depends(get_db)
) -> List[schemas.OrderSchema]:
    orders = []
    for order in db.query(models.OrderModel).all():
        if filter_ready is None or filter_ready == order.ready:
            carrier = WAREHOUSE_QUEUE.get_carrier(order, db)
            orders.append(
                schemas.OrderSchema(
                    product_name=order.product_name,
                    customer_id=order.customer_id,
                    id=order.id,
                    ready=order.ready,
                    carrier=carrier,
                )
            )
    return orders


@order_router.get("/export")
def export_orders(customer_id: uuid.UUID, db: Session = Depends(get_db)):
    orders_from_db = (
        db.query(models.OrderModel)
        .filter(models.OrderModel.customer_id == customer_id)
        .all()
    )
    data = [[order.id, order.product_name, order.ready] for order in orders_from_db]
    f = StringIO()
    csv.writer(f).writerows(data)

    response = StreamingResponse(iter([f.getvalue()]), media_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=export.csv"
    return response


@order_router.get("/{id}")
def get_order(id: str, db: Session = Depends(get_db)) -> schemas.OrderSchema:
    order = db.query(models.OrderModel).filter(models.OrderModel.id == id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No order with this id: {id} found",
        )
    return schemas.OrderSchema(
        product_name=order.product_name,
        customer_id=order.customer_id,
        id=order.id,
        ready=order.ready,
        carrier=WAREHOUSE_QUEUE.get_carrier(order, db),
    )


@order_router.delete("/{id}")
def delete_order(id: str, db: Session = Depends(get_db)) -> schemas.OrderSchema:
    order = db.query(models.OrderModel).filter(models.OrderModel.id == id).first()
    db.delete(order)
    db.commit()

    return schemas.OrderSchema(
        product_name=order.product_name,
        customer_id=order.customer_id,
        id=order.id,
        ready=order.ready,
        carrier=None,
    )
