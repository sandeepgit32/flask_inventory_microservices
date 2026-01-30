from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import date


class TransactionBase(BaseModel):
    timestamp: date
    customer_name: str
    city: Optional[str] = None
    zipcode: Optional[int] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    product_code: str
    product_name: str
    product_category: Optional[str] = None
    unit_price: float
    quantity: Optional[int] = None
    total_cost: float
    measure_unit: Optional[str] = None


class TransactionCreate(TransactionBase):
    pass


class TransactionResponse(TransactionBase):
    id: int
    
    model_config = ConfigDict(from_attributes=True)
