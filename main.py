import os, base64, shutil, uuid
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from database import init_db, get_db, Category, Product, Order, OrderItem, Message
from sqlalchemy.orm import Session

ADMIN_PIN = os.getenv("ADMIN_PIN", "nj2024")

app = FastAPI(title="NJ Store API")
app = FastAPI(title="NJ Store API")

app.mount("/static", StaticFiles(directory="static"), name="static")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()

UPLOADS_DIR = Path("uploads")
UPLOADS_DIR.mkdir(exist_ok=True)

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

@app.post("/api/admin/login")
def admin_login(body: AdminLogin):
    if body.pin != ADMIN_PIN:
        raise HTTPException(status_code=401, detail="Wrong PIN")
    return {"ok": True}

@app.get("/api/categories")
def list_categories(db: Session = Depends(get_db)):
    cats = db.query(Category).all()
    return [{"id": c.id, "name": c.name, "icon": c.icon} for c in cats]

@app.get("/api/products")
def list_products(category_id: Optional[int] = None, featured: Optional[bool] = None, db: Session = Depends(get_db)):
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
    db.add(p); db.commit(); db.refresh(p)
    return _product_dict(p)

@app.put("/api/products/{product_id}")
def update_product(product_id: int, product: ProductCreate, db: Session = Depends(get_db)):
    p = db.query(Product).filter(Product.id == product_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Not found")
    for k, v in product.model_dump().items():
        setattr(p, k, v)
    db.commit(); db.refresh(p)
    return _product_dict(p)

@app.delete("/api/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    p = db.query(Product).filter(Product.id == product_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(p); db.commit()
    return {"ok": True}

def _product_dict(p):
    return {"id": p.id, "name": p.name, "description": p.description,
            "price": float(p.price), "image_url": p.image_url,
            "category_id": p.category_id, "stock": p.stock, "featured": p.featured}

@app.post("/api/upload")
async def upload_image(file: UploadFile = File(...)):
    ext = Path(file.filename).suffix or ".jpg"
    filename = f"{uuid.uuid4()}{ext}"
    save_path = UPLOADS_DIR / filename
    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    return {"url": f"/uploads/{filename}"}

@app.get("/api/orders")
def list_orders(db: Session = Depends(get_db)):
    orders = db.query(Order).order_by(Order.created_at.desc()).all()
    return [_order_dict(o, db) for o in orders]

@app.post("/api/orders")
def create_order(body: OrderCreate, db: Session = Depends(get_db)):
    order = Order(customer_name=body.customer_name, customer_phone=body.customer_phone,
                  customer_address=body.customer_address, total=body.total, status="pending")
    db.add(order); db.flush()
    for item in body.items:
        db.add(OrderItem(order_id=order.id, product_id=item.product_id,
                         quantity=item.quantity, price=item.price))
        p = db.query(Product).filter(Product.id == item.product_id).first()
        if p:
            p.stock = max(0, p.stock - item.quantity)
    db.commit(); db.refresh(order)
    return _order_dict(order, db)

@app.patch("/api/orders/{order_id}/status")
def update_order_status(order_id: int, body: dict, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Not found")
    order.status = body.get("status", order.status)
    db.commit()
    return _order_dict(order, db)

def _order_dict(o, db):
    items = db.query(OrderItem).filter(OrderItem.order_id == o.id).all()
    return {"id": o.id, "customer_name": o.customer_name, "customer_phone": o.customer_phone,
            "customer_address": o.customer_address, "total": float(o.total), "status": o.status,
            "created_at": o.created_at.isoformat() if o.created_at else None,
            "items": [{"product_id": i.product_id, "quantity": i.quantity, "price": float(i.price)} for i in items]}

@app.get("/api/messages")
def list_messages(db: Session = Depends(get_db)):
    msgs = db.query(Message).order_by(Message.created_at.desc()).all()
    return [_message_dict(m) for m in msgs]

@app.post("/api/messages")
def create_message(body: MessageCreate, db: Session = Depends(get_db)):
    m = Message(**body.model_dump())
    db.add(m); db.commit(); db.refresh(m)
    return _message_dict(m)

@app.patch("/api/messages/{message_id}/read")
def mark_message_read(message_id: int, db: Session = Depends(get_db)):
    m = db.query(Message).filter(Message.id == message_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Not found")
    m.is_read = True; db.commit()
    return _message_dict(m)

def _message_dict(m):
    return {"id": m.id, "sender_name": m.sender_name, "sender_phone": m.sender_phone,
            "message_type": m.message_type, "subject": m.subject, "body": m.body,
            "product_id": m.product_id, "is_read": m.is_read,
            "created_at": m.created_at.isoformat() if m.created_at else None}

@app.get("/api/stats")
def get_stats(db: Session = Depends(get_db)):
    orders = db.query(Order).all()
    return {"total_products": db.query(Product).count(),
            "total_orders": db.query(Order).count(),
            "total_messages": db.query(Message).count(),
            "unread_messages": db.query(Message).filter(Message.is_read == False).count(),
            "total_revenue": sum(float(o.total) for o in orders)}

@app.get("/uploads/{filename}")
def serve_upload(filename: str):
    path = UPLOADS_DIR / filename
    if not path.exists():
        raise HTTPException(status_code=404)
    return FileResponse(path)

app.mount("/", StaticFiles(directory="static", html=True), name="static")
