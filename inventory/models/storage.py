from typing import List
from db import db
from models.customer import CustomerModel
from sqlalchemy import and_


class StorageModel(db.Model):
    __tablename__ = "storages"

    id = db.Column(db.Integer, primary_key=True)
    product_code = db.Column(db.String(80), db.ForeignKey("products.product_code"), nullable=False)
    warehouse_name = db.Column(db.String(80), db.ForeignKey("warehouses.name"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

    # UniqueConstraint for product_code and warehouse_id
    db.UniqueConstraint(product_code, warehouse_name)


    @classmethod
    def find_by_id(cls, id: int) -> "StorageModel":
        return cls.query.filter_by(id=id).first()

    @classmethod
    def find_by_product_code_and_warehouse_name(cls, product_code: str, warehouse_name: str) -> "StorageModel":
        # 'cls.' is a must alongside the parameters within and_(), otherwise it will not work.
        return cls.query.filter(and_(cls.warehouse_name==warehouse_name, cls.product_code==product_code)).first()

    @classmethod
    def filter_by_product_code(cls, product_code: str) -> List["StorageModel"]:
        return cls.query.filter_by(product_code=product_code)
    
    @classmethod
    def filter_by_warehouse_name(cls, warehouse_name: str) -> List["StorageModel"]:
        return cls.query.filter_by(warehouse_name=warehouse_name)

    @classmethod
    def find_all(cls) -> List["StorageModel"]:
        return cls.query.all()

    def save_to_db(self) -> None:
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self) -> None:
        db.session.delete(self)
        db.session.commit()