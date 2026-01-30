from pydantic import BaseModel, ConfigDict
from typing import Optional


class CustomerBase(BaseModel):
    name: str
    city: Optional[str] = None
    zipcode: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    warehouse_id: Optional[int] = None


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    city: Optional[str] = None
    zipcode: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    warehouse_id: Optional[int] = None


class CustomerResponse(CustomerBase):
    id: int
    
    model_config = ConfigDict(from_attributes=True)