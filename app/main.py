import os
from contextlib import asynccontextmanager
from decimal import Decimal
import httpx
from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from .database import Base, engine, get_db
from .models import Order
from .schemas import OrderCreate, OrderOut, StatusUpdate

MENU_SERVICE_URL = os.getenv("MENU_SERVICE_URL", "http://localhost:8000").rstrip("/")
ALLOWED_STATUSES = {"PLACED", "CONFIRMED", "PREPARING", "READY", "COMPLETED"}

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(title="Food Ordering - Order Service", version="1.0.0", lifespan=lifespan)

@app.get("/health")
def health():
    return {"service": "order-service", "status": "healthy"}

@app.post("/orders", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
def create_order(payload: OrderCreate, db: Session = Depends(get_db)):
    snapshots = []
    total = Decimal("0.00")
    try:
        with httpx.Client(timeout=4.0) as client:
            for line in payload.items:
                response = client.get(f"{MENU_SERVICE_URL}/menu/items/{line.item_id}")
                if response.status_code == 404:
                    raise HTTPException(status_code=400, detail=f"Menu item {line.item_id} does not exist")
                response.raise_for_status()
                item = response.json()
                if not item["available"]:
                    raise HTTPException(status_code=400, detail=f"Menu item {line.item_id} is unavailable")
                unit_price = Decimal(str(item["price"]))
                line_total = unit_price * line.quantity
                total += line_total
                snapshots.append({"item_id": item["id"], "name": item["name"], "unit_price": str(unit_price), "quantity": line.quantity, "line_total": str(line_total)})
    except HTTPException:
        raise
    except (httpx.HTTPError, ValueError, KeyError) as exc:
        raise HTTPException(status_code=503, detail="Menu Service is unavailable or returned an invalid response") from exc

    order = Order(customer_id=payload.customer_id, items=snapshots, total_amount=total, status="PLACED")
    db.add(order)
    db.commit()
    db.refresh(order)
    return order

@app.get("/orders", response_model=list[OrderOut])
def list_orders(customer_id: str | None = None, db: Session = Depends(get_db)):
    query = select(Order).order_by(Order.id.desc())
    if customer_id:
        query = query.where(Order.customer_id == customer_id)
    return db.scalars(query).all()

@app.get("/orders/{order_id}", response_model=OrderOut)
def get_order(order_id: int, db: Session = Depends(get_db)):
    order = db.get(Order, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@app.patch("/orders/{order_id}/status", response_model=OrderOut)
def update_status(order_id: int, payload: StatusUpdate, db: Session = Depends(get_db)):
    new_status = payload.status.upper()
    if new_status not in ALLOWED_STATUSES:
        raise HTTPException(status_code=400, detail=f"Status must be one of: {', '.join(sorted(ALLOWED_STATUSES))}")
    order = db.get(Order, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status in {"CANCELLED", "COMPLETED"}:
        raise HTTPException(status_code=409, detail="A completed or cancelled order cannot be changed")
    order.status = new_status
    db.commit()
    db.refresh(order)
    return order

@app.patch("/orders/{order_id}/cancel", response_model=OrderOut)
def cancel_order(order_id: int, db: Session = Depends(get_db)):
    order = db.get(Order, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status not in {"PLACED", "CONFIRMED"}:
        raise HTTPException(status_code=409, detail="Only placed or confirmed orders can be cancelled")
    order.status = "CANCELLED"
    db.commit()
    db.refresh(order)
    return order
