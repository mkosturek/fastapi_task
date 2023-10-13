import csv
import uuid
from io import StringIO
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app import models, schemas
from app.deps import get_db
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


@customer_router.delete("/{id}")
def delete_customer(id: str, db: Session = Depends(get_db)):
    customer = (
        db.query(models.CustomerModel).filter(models.CustomerModel.id == id).first()
    )
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No customer with this id: {id} found",
        )

    db.delete(customer)
    db.commit()
    return customer


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
    db.add(order)
    db.commit()
    db.refresh(order)
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
def export_orders(
    customer_id: uuid.UUID,
    filter_ready: bool | None = None,
    db: Session = Depends(get_db),
):
    orders_from_db = db.query(models.OrderModel).all()

    data_to_report = []
    for order in orders_from_db:
        if order.customer_id == customer_id and (
            filter_ready is None or filter_ready == order.ready
        ):
            data_to_report.append([order.id, order.product_name, order.ready])

    f = StringIO()
    writer = csv.writer(f)
    for order_data in data_to_report:
        writer.writerow(order_data)

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

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No order with this id: {id} found",
        )

    db.delete(order)
    db.commit()

    return schemas.OrderSchema(
        product_name=order.product_name,
        customer_id=order.customer_id,
        id=order.id,
        ready=order.ready,
        carrier=None,
    )


helper_router = APIRouter()


@helper_router.get("/populate-orders")
def populate_orders(count: int, db: Session = Depends(get_db)):
    customer = models.CustomerModel(
        name="TestUserWithManyOrders",
        description="test user with many orders",
        # email="testuserwithmanyorders@example.com",
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)

    for i in range(count):
        order = models.OrderModel(
            customer_id=customer.id,
            product_name=f"product_{i}",
        )
        db.add(order)
    db.commit()
    return customer.id
