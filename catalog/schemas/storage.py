from pydantic import BaseModel, ConfigDict
from typing import Optional


class StorageBase(BaseModel):
    product_code: str
    warehouse_name: str
    quantity: int


class StorageCreate(StorageBase):
    pass


class StorageUpdate(BaseModel):
    quantity: Optional[int] = None


class StorageResponse(StorageBase):
    id: int
    
    model_config = ConfigDict(from_attributes=True)