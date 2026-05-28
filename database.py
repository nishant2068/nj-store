import os
from datetime import datetime

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
)

from sqlalchemy.orm import declarative_base, sessionmaker, Session


# =========================================================
# DATABASE CONFIG
# =========================================================

DATABASE_URL = os.getenv(
    "DB_URL",
    "sqlite:///./njstore.db"
)

# Needed for SQLite compatibility
connect_args = {}

if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


# =========================================================
# MODELS
# =========================================================

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    icon = Column(String, default="📦")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, default="")
    price = Column(Float, nullable=False)
    image_url = Column(String, default="")
    category_id = Column(
        Integer,
        ForeignKey("categories.id"),
        nullable=False,
    )
    stock = Column(Integer, default=0)
    featured = Column(Boolean, default=False)


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String, nullable=False)
    customer_phone = Column(String, nullable=False)
    customer_address = Column(Text, nullable=False)
    total = Column(Float, nullable=False)
    status = Column(String, default="pending")
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
    )


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(
        Integer,
        ForeignKey("orders.id"),
        nullable=False,
    )
    product_id = Column(
        Integer,
        ForeignKey("products.id"),
        nullable=False,
    )
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    sender_name = Column(String, nullable=False)
    sender_phone = Column(String, nullable=False)
    message_type = Column(String, default="general")
    subject = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    product_id = Column(Integer, nullable=True)
    is_read = Column(Boolean, default=False)
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
    )


# =========================================================
# INIT DATABASE
# =========================================================

def init_db():
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        if db.query(Category).count() == 0:
            _seed_categories(db)

    except Exception as e:
        print("DATABASE INIT ERROR:", e)

    finally:
        db.close()


# =========================================================
# SEED DATA
# =========================================================

def _seed_categories(db: Session):

    categories = [
        Category(name="Food & Snacks", icon="🍎"),
        Category(name="Drinks", icon="🥤"),
        Category(name="Household", icon="🏠"),
        Category(name="Personal Care", icon="🧴"),
        Category(name="Stationery", icon="✏️"),
        Category(name="Electronics", icon="📱"),
        Category(name="Clothing", icon="👕"),
        Category(name="Other", icon="📦"),
    ]

    for category in categories:
        db.add(category)

    db.commit()


# =========================================================
# DB SESSION
# =========================================================

def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()
