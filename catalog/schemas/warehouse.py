from pydantic import BaseModel, ConfigDict
from typing import Optional


class WarehouseBase(BaseModel):
    name: str
    city: Optional[str] = None


class WarehouseCreate(WarehouseBase):
    pass


class WarehouseUpdate(BaseModel):
    name: Optional[str] = None
    city: Optional[str] = None


class WarehouseResponse(WarehouseBase):
    id: int
    
    model_config = ConfigDict(from_attributes=True)
