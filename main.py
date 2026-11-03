
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(
    title="FDS DevOps Automation API",
    version="2.0.0"
)


class Product(BaseModel):
    name: str
    price: float
    quantity: int


products = {
    1: {"name": "Laptop", "price": 800, "quantity": 10},
    2: {"name": "Keyboard", "price": 50, "quantity": 20}
}


@app.get("/")
def home():
    return {"message": "FDS DevOps Application is running"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/products")
def get_products():
    return products


@app.get("/products/{product_id}")
def get_product(product_id: int):
    if product_id not in products:
        raise HTTPException(status_code=404, detail="Product not found")

    return products[product_id]


@app.post("/products", status_code=201)
def create_product(product: Product):
    new_id = max(products.keys(), default=0) + 1
    products[new_id] = product.model_dump()

    return {
        "id": new_id,
        "product": products[new_id]
    }


@app.put("/products/{product_id}")
def update_product(product_id: int, product: Product):
    if product_id not in products:
        raise HTTPException(status_code=404, detail="Product not found")

    products[product_id] = product.model_dump()

    return {
        "id": product_id,
        "product": products[product_id]
    }


@app.delete("/products/{product_id}")
def delete_product(product_id: int):
    if product_id not in products:
        raise HTTPException(status_code=404, detail="Product not found")

    del products[product_id]

    return {"message": "Product deleted successfully"}
