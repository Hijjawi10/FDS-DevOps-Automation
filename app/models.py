
from sqlalchemy import (
    Column,
    Integer,
    String,
    Numeric,
    Boolean,
    CheckConstraint,
)

from app.database import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(100), nullable=False)

    price = Column(Numeric(10, 2), nullable=False)

    quantity = Column(Integer, nullable=False)

    __table_args__ = (
        CheckConstraint(
            "price >= 0",
            name="check_price_positive"
        ),
        CheckConstraint(
            "quantity >= 0",
            name="check_quantity_positive"
        ),
    )

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    username = Column(
        String(50),
        unique=True,
        index=True,
        nullable=False
    )

    email = Column(
        String(255),
        unique=True,
        index=True,
        nullable=False
    )

    hashed_password = Column(
        String(255),
        nullable=False
    )

    role = Column(
        String(20),
        nullable=False,
        default="user",
        server_default="user"
    )

    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true"
    )

    __table_args__ = (
        CheckConstraint(
            "role IN ('admin', 'user')",
            name="check_user_role"
        ),
    )
