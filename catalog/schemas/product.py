from pydantic import BaseModel, ConfigDict
from typing import Optional


class ProductBase(BaseModel):
    product_code: str
    name: str
    category: Optional[str] = None
    price_buy: float
    price_sell: float
    measure_unit: Optional[str] = None
    supplier_name: str


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    price_buy: Optional[float] = None
    price_sell: Optional[float] = None
    measure_unit: Optional[str] = None
    supplier_name: Optional[str] = None


class ProductResponse(ProductBase):
    id: int
    
    model_config = ConfigDict(from_attributes=True)