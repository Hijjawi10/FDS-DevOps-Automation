
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# Base Product Schema
class ProductBase(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Product name"
    )

    price: Decimal = Field(
        ...,
        gt=0,
        max_digits=12,
        decimal_places=2,
        description="Product price"
    )

    quantity: int = Field(
        ...,
        ge=0,
        description="Available stock quantity"
    )


# Schema for creating a product
class ProductCreate(ProductBase):
    pass


# Schema for updating a product
class ProductUpdate(BaseModel):
    name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100
    )

    price: Optional[Decimal] = Field(
        default=None,
        gt=0,
        max_digits=12,
        decimal_places=2
    )

    quantity: Optional[int] = Field(
        default=None,
        ge=0
    )


class ProductResponse(ProductBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
