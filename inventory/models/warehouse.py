from typing import List
from db import db
from models.customer import CustomerModel
from models.storage import StorageModel


class WarehouseModel(db.Model):
    __tablename__ = "warehouses"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False, unique=True)
    city = db.Column(db.String(50))

    customers = db.relationship("CustomerModel", backref='warehouse', lazy="dynamic")
    storages = db.relationship("StorageModel", backref='warehouse', lazy="dynamic", cascade="all, delete-orphan")

    @classmethod
    def find_by_id(cls, id: int) -> "WarehouseModel":
        return cls.query.filter_by(id=id).first()

    @classmethod
    def find_associated_customers_by_id(cls, id: int) -> List["CustomerModel"]:
        return cls.query.filter_by(id=id).first().customers.all()

    @classmethod
    def find_by_name(cls, name: str) -> "WarehouseModel":
        return cls.query.filter_by(name=name).first()

    @classmethod
    def find_all(cls) -> List["WarehouseModel"]:
        return cls.query.all()

    @classmethod
    def filter_by_city(cls, city: str) -> List["WarehouseModel"]:
        return cls.query.filter_by(city=city)

    def save_to_db(self) -> None:
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self) -> None:
        db.session.delete(self)
        db.session.commit()