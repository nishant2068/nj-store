# main.py (FULL CLEAN VERSION)
print("MAIN STARTED")

import os
import base64
import shutil
import uuid
import requests

from io import BytesIO
from pathlib import Path
from typing import Optional

from PIL import Image

from fastapi import (
    FastAPI,
    HTTPException,
    Depends,
    UploadFile,
    File,
)

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel

from sqlalchemy.orm import Session

try:
    from database import (
        init_db,
        get_db,
        Category,
        Product,
        Order,
        OrderItem,
        Message,
    )

    print("DATABASE IMPORT OK")

except Exception as e:
    print("DATABASE IMPORT ERROR:", e)
    raise e


# =========================================================
# CONFIG
# =========================================================

ADMIN_PIN = os.getenv("ADMIN_PIN", "nj2024")

app = FastAPI(title="NJ Store API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# DATABASE
# =========================================================
try:
    init_db()
    print("DATABASE INIT OK")

except Exception as e:
    print("DATABASE INIT FAILED:", e)
    raise e


# =========================================================
# UPLOADS
# =========================================================

UPLOADS_DIR = Path("uploads")
UPLOADS_DIR.mkdir(exist_ok=True)


# =========================================================
# MODELS
# =========================================================

class ProductCreate(BaseModel):
    name: str
    description: str
    price: float
    category_id: int
    stock: int = 0
    featured: bool = False
    image_url: str = ""


class OrderItemIn(BaseModel):
    product_id: int
    quantity: int
    price: float


class OrderCreate(BaseModel):
    customer_name: str
    customer_phone: str
    customer_address: str
    items: list[OrderItemIn]
    total: float


class MessageCreate(BaseModel):
    sender_name: str
    sender_phone: str
    message_type: str = "general"
    subject: str
    body: str
    product_id: Optional[int] = None


class AdminLogin(BaseModel):
    pin: str


class ImageUrlRequest(BaseModel):
    url: str


class Base64Image(BaseModel):
    data: str


# =========================================================
# HELPERS
# =========================================================


def _product_dict(p):
    return {
        "id": p.id,
        "name": p.name,
        "description": p.description,
        "price": float(p.price),
        "image_url": p.image_url,
        "category_id": p.category_id,
        "stock": p.stock,
        "featured": p.featured,
    }



def _order_dict(o, db):
    items = db.query(OrderItem).filter(OrderItem.order_id == o.id).all()

    return {
        "id": o.id,
        "customer_name": o.customer_name,
        "customer_phone": o.customer_phone,
        "customer_address": o.customer_address,
        "total": float(o.total),
        "status": o.status,
        "created_at": o.created_at.isoformat() if o.created_at else None,
        "items": [
            {
                "product_id": i.product_id,
                "quantity": i.quantity,
                "price": float(i.price),
            }
            for i in items
        ],
    }



def _message_dict(m):
    return {
        "id": m.id,
        "sender_name": m.sender_name,
        "sender_phone": m.sender_phone,
        "message_type": m.message_type,
        "subject": m.subject,
        "body": m.body,
        "product_id": m.product_id,
        "is_read": m.is_read,
        "created_at": m.created_at.isoformat() if m.created_at else None,
    }


# =========================================================
# ADMIN
# =========================================================

@app.post("/api/admin/login")
def admin_login(body: AdminLogin):

    if body.pin != ADMIN_PIN:
        raise HTTPException(status_code=401, detail="Wrong PIN")

    return {"ok": True}


# =========================================================
# CATEGORIES
# =========================================================

@app.get("/api/categories")
def list_categories(db: Session = Depends(get_db)):

    cats = db.query(Category).all()

    return [
        {
            "id": c.id,
            "name": c.name,
            "icon": c.icon,
        }
        for c in cats
    ]


# =========================================================
# PRODUCTS
# =========================================================

@app.get("/api/products")
def list_products(
    category_id: Optional[int] = None,
    featured: Optional[bool] = None,
    db: Session = Depends(get_db),
):

    q = db.query(Product)

    if category_id:
        q = q.filter(Product.category_id == category_id)

    if featured is not None:
        q = q.filter(Product.featured == featured)

    return [_product_dict(p) for p in q.all()]


@app.get("/api/products/{product_id}")
def get_product(product_id: int, db: Session = Depends(get_db)):

    p = db.query(Product).filter(Product.id == product_id).first()

    if not p:
        raise HTTPException(status_code=404, detail="Not found")

    return _product_dict(p)


@app.post("/api/products")
def create_product(product: ProductCreate, db: Session = Depends(get_db)):

    p = Product(**product.model_dump())

    db.add(p)
    db.commit()
    db.refresh(p)

    return _product_dict(p)


@app.put("/api/products/{product_id}")
def update_product(
    product_id: int,
    product: ProductCreate,
    db: Session = Depends(get_db),
):

    p = db.query(Product).filter(Product.id == product_id).first()

    if not p:
        raise HTTPException(status_code=404, detail="Not found")

    for k, v in product.model_dump().items():
        setattr(p, k, v)

    db.commit()
    db.refresh(p)

    return _product_dict(p)


@app.delete("/api/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):

    p = db.query(Product).filter(Product.id == product_id).first()

    if not p:
        raise HTTPException(status_code=404, detail="Not found")

    db.delete(p)
    db.commit()

    return {"ok": True}


# =========================================================
# IMAGE UPLOADS
# =========================================================

@app.post("/api/upload")
async def upload_image(file: UploadFile = File(...)):
    """Upload image from file"""

    try:
        ext = Path(file.filename).suffix or ".jpg"

        filename = f"{uuid.uuid4()}{ext}"

        save_path = UPLOADS_DIR / filename

        with open(save_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        return {
            "url": f"/uploads/{filename}"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/upload-base64")
async def upload_base64_image(payload: Base64Image):
    """Upload image from base64"""

    try:
        base64_data = payload.data

        if "," in base64_data:
            base64_data = base64_data.split(",")[1]

        image_data = base64.b64decode(base64_data)

        filename = f"{uuid.uuid4()}.jpg"

        save_path = UPLOADS_DIR / filename

        with open(save_path, "wb") as f:
            f.write(image_data)

        return {
            "url": f"/uploads/{filename}"
        }

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid base64 image: {str(e)}",
        )


@app.post("/api/upload-url")
async def upload_image_url(data: ImageUrlRequest):
    """Upload image from external URL"""

    try:
        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        response = requests.get(
            data.url,
            headers=headers,
            timeout=15,
        )

        if response.status_code != 200:
            raise HTTPException(
                status_code=400,
                detail="Cannot fetch image",
            )

        content_type = response.headers.get(
            "content-type",
            "",
        )

        if not content_type.startswith("image/"):
            raise HTTPException(
                status_code=400,
                detail="URL is not an image",
            )

        image = Image.open(BytesIO(response.content))

        filename = f"{uuid.uuid4()}.jpg"

        save_path = UPLOADS_DIR / filename

        image.convert("RGB").save(save_path)

        return {
            "url": f"/uploads/{filename}"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =========================================================
# ORDERS
# =========================================================

@app.get("/api/orders")
def list_orders(db: Session = Depends(get_db)):

    orders = db.query(Order).order_by(Order.created_at.desc()).all()

    return [_order_dict(o, db) for o in orders]


@app.post("/api/orders")
def create_order(body: OrderCreate, db: Session = Depends(get_db)):

    order = Order(
        customer_name=body.customer_name,
        customer_phone=body.customer_phone,
        customer_address=body.customer_address,
        total=body.total,
        status="pending",
    )

    db.add(order)
    db.flush()

    for item in body.items:

        db.add(
            OrderItem(
                order_id=order.id,
                product_id=item.product_id,
                quantity=item.quantity,
                price=item.price,
            )
        )

        p = db.query(Product).filter(Product.id == item.product_id).first()

        if p:
            p.stock = max(0, p.stock - item.quantity)

    db.commit()
    db.refresh(order)

    return _order_dict(order, db)


@app.patch("/api/orders/{order_id}/status")
def update_order_status(
    order_id: int,
    body: dict,
    db: Session = Depends(get_db),
):

    order = db.query(Order).filter(Order.id == order_id).first()

    if not order:
        raise HTTPException(status_code=404, detail="Not found")

    order.status = body.get("status", order.status)

    db.commit()

    return _order_dict(order, db)


# =========================================================
# MESSAGES
# =========================================================

@app.get("/api/messages")
def list_messages(db: Session = Depends(get_db)):

    msgs = db.query(Message).order_by(Message.created_at.desc()).all()

    return [_message_dict(m) for m in msgs]


@app.post("/api/messages")
def create_message(body: MessageCreate, db: Session = Depends(get_db)):

    m = Message(**body.model_dump())

    db.add(m)
    db.commit()
    db.refresh(m)

    return _message_dict(m)


@app.patch("/api/messages/{message_id}/read")
def mark_message_read(message_id: int, db: Session = Depends(get_db)):

    m = db.query(Message).filter(Message.id == message_id).first()

    if not m:
        raise HTTPException(status_code=404, detail="Not found")

    m.is_read = True

    db.commit()

    return _message_dict(m)


# =========================================================
# STATS
# =========================================================

@app.get("/api/stats")
def get_stats(db: Session = Depends(get_db)):

    orders = db.query(Order).all()

    return {
        "total_products": db.query(Product).count(),
        "total_orders": db.query(Order).count(),
        "total_messages": db.query(Message).count(),
        "unread_messages": db.query(Message)
        .filter(Message.is_read == False)
        .count(),
        "total_revenue": sum(float(o.total) for o in orders),
    }


# =========================================================
# SERVE UPLOADS
# =========================================================

@app.get("/uploads/{filename}")
def serve_upload(filename: str):

    path = UPLOADS_DIR / filename

    if not path.exists():
        raise HTTPException(status_code=404)

    return FileResponse(path)


# =========================================================
# FRONTEND
# =========================================================

app.mount(
    "/",
    StaticFiles(directory="static", html=True),
    name="static",
)
