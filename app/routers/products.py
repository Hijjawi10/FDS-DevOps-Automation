
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import ProductCreate, ProductResponse
from app.services import product_service


router = APIRouter(
    prefix="/products",
    tags=["Products"]
)


@router.get("", response_model=list[ProductResponse])
def get_products(db: Session = Depends(get_db)):
    return product_service.get_all_products(db)


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: int,
    db: Session = Depends(get_db)
):
    product = product_service.get_product_by_id(
        db,
        product_id
    )

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    return product


@router.post("", status_code=201)
def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db)
):
    new_product = product_service.create_product(
        db,
        product
    )

    return {
        "id": new_product.id,
        "product": ProductResponse.model_validate(
            new_product
        ).model_dump(
            mode="json",
            exclude={"id"}
        )
    }


@router.put("/{product_id}")
def update_product(
    product_id: int,
    product: ProductCreate,
    db: Session = Depends(get_db)
):
    updated_product = product_service.update_product(
        db,
        product_id,
        product
    )

    if updated_product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    return {
        "id": updated_product.id,
        "product": ProductResponse.model_validate(
            updated_product
        ).model_dump(
            mode="json",
            exclude={"id"}
        )
    }


@router.delete("/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db)
):
    deleted = product_service.delete_product(
        db,
        product_id
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    return {
        "message": "Product deleted successfully"
    }
