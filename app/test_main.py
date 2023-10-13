from fastapi.testclient import TestClient
import pytest

from .main import app
from .deps import get_db
from .database import Base, create_engine, sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


Base.metadata.create_all(bind=engine)


@pytest.fixture(scope="function", autouse=True)
def clear_tables():
    yield
    meta = Base.metadata  # type: ignore
    session = TestingSessionLocal()

    for table in reversed(meta.sorted_tables):
        session.execute(table.delete())
    session.commit()


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


client = TestClient(app)


def create_customer(name, description):
    return client.post("/api/customer", json={"name": name, "description": description})


def test_create_customer():
    response = create_customer("Company name", "Company description")
    assert response.status_code == 201

    data = response.json()
    assert "id" in data
    assert data["name"] == "Company name"
    assert data["description"] == "Company description"


def test_get_customer():
    company_data = {"name": "Company", "description": "description"}
    data = create_customer(**company_data).json()
    response = client.get(f"/api/customer/{data['id']}")
    assert response.status_code == 200
    assert data == response.json()


def test_get_customers():
    company_data = {"name": "Company", "description": "description"}
    create_customer(**company_data)
    create_customer(**company_data)

    response = client.get("/api/customer")

    assert response.status_code == 200
    assert len(response.json()) == 2


def create_order(customer_id, product_name):
    return client.post(
        "/api/order", json={"customer_id": customer_id, "product_name": product_name}
    )


def test_create_order():
    customer_response = create_customer("Company name", "Company description")
    customer_id = customer_response.json()["id"]
    order_response = create_order(customer_id, "Product name")
    assert order_response.status_code == 201

    data = order_response.json()
    assert "id" in data
    assert "ready" in data
    assert "carrier" in data
    assert data["product_name"] == "Product name"
    assert data["customer_id"] == customer_id


def test_get_order():
    customer_data = create_customer("Company", "description").json()
    order_data = create_order(customer_data["id"], "Prpduct name").json()

    response = client.get(f"/api/order/{order_data['id']}")
    assert response.status_code == 200
    assert order_data == response.json()


def test_get_orders():
    customer_data = create_customer("Company", "description").json()

    create_order(customer_data["id"], "Prpduct name")
    create_order(customer_data["id"], "Prpduct name")

    response = client.get("/api/order")

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_csv_orders():
    customer_data = create_customer("Company", "description").json()

    order_1 = create_order(customer_data["id"], "Prpduct name")
    order_2 = create_order(customer_data["id"], "Prpduct name")

    response = client.get("/api/order/export")

    assert order_1["id"] in str(response.content)
    assert order_2["id"] in str(response.content)
