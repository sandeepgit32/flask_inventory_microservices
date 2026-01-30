from pydantic import BaseModel, ConfigDict
from typing import Optional


class SupplierBase(BaseModel):
    name: str
    city: Optional[str] = None
    zipcode: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None


class SupplierCreate(SupplierBase):
    pass


class SupplierUpdate(BaseModel):
    name: Optional[str] = None
    city: Optional[str] = None
    zipcode: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None


class SupplierResponse(SupplierBase):
    id: int
    
    model_config = ConfigDict(from_attributes=True)
