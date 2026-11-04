
from sqlalchemy import Column, Integer, String, Numeric, CheckConstraint
from database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(100), nullable=False)

    price = Column(Numeric(10, 2), nullable=False)

    quantity = Column(Integer, nullable=False)

    __table_args__ = (
        CheckConstraint("price >= 0", name="check_price_positive"),
        CheckConstraint("quantity >= 0", name="check_quantity_positive"),
    )
