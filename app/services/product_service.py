
from sqlalchemy.orm import Session

from app.models import Product as ProductDB
from app.schemas import ProductCreate


def get_all_products(db: Session):
    return (
        db.query(ProductDB)
        .order_by(ProductDB.id)
        .all()
    )


def get_product_by_id(db: Session, product_id: int):
    return db.get(ProductDB, product_id)


def create_product(db: Session, product: ProductCreate):
    new_product = ProductDB(**product.model_dump())

    db.add(new_product)
    db.commit()
    db.refresh(new_product)

    return new_product


def update_product(
    db: Session,
    product_id: int,
    product: ProductCreate
):
    existing_product = db.get(ProductDB, product_id)

    if existing_product is None:
        return None

    existing_product.name = product.name
    existing_product.price = product.price
    existing_product.quantity = product.quantity

    db.commit()
    db.refresh(existing_product)

    return existing_product


def delete_product(db: Session, product_id: int):
    product = db.get(ProductDB, product_id)

    if product is None:
        return False

    db.delete(product)
    db.commit()

    return True
