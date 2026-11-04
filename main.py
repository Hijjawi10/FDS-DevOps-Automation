
from contextlib import asynccontextmanager
from decimal import Decimal

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.orm import Session

from database import engine, Base, get_db
from models import Product as ProductDB
import os


@asynccontextmanager
async def lifespan(app: FastAPI):
    if os.getenv("TESTING") != "1":
        Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title="FDS DevOps Automation API",
    version="3.0.0",
    lifespan=lifespan
)


class Product(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    price: Decimal = Field(ge=0, max_digits=10, decimal_places=2)
    quantity: int = Field(ge=0)


class ProductResponse(Product):
    model_config = ConfigDict(from_attributes=True)
    id: int


@app.get("/")
def home():
    return {
        "message": "FDS DevOps Application is running"
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/products", response_model=list[ProductResponse])
def get_products(db: Session = Depends(get_db)):
    return db.query(ProductDB).order_by(ProductDB.id).all()


@app.get("/products/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: int,
    db: Session = Depends(get_db)
):
    product = db.get(ProductDB, product_id)

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    return product


@app.post("/products", status_code=201)
def create_product(
    product: Product,
    db: Session = Depends(get_db)
):
    new_product = ProductDB(**product.model_dump())

    db.add(new_product)
    db.commit()
    db.refresh(new_product)

    return {
        "id": new_product.id,
        "product": ProductResponse.model_validate(
            new_product
        ).model_dump(mode="json", exclude={"id"})
    }


@app.put("/products/{product_id}")
def update_product(
    product_id: int,
    product: Product,
    db: Session = Depends(get_db)
):
    existing_product = db.get(ProductDB, product_id)

    if existing_product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    existing_product.name = product.name
    existing_product.price = product.price
    existing_product.quantity = product.quantity

    db.commit()
    db.refresh(existing_product)

    return {
        "id": existing_product.id,
        "product": ProductResponse.model_validate(
            existing_product
        ).model_dump(mode="json", exclude={"id"})
    }


@app.delete("/products/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db)
):
    product = db.get(ProductDB, product_id)

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    db.delete(product)
    db.commit()

    return {
        "message": "Product deleted successfully"
    }
