from typing import List
from db import db
from models.product import ProductModel


class SupplierModel(db.Model):
    __tablename__ = "suppliers"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    city = db.Column(db.String(50))
    zipcode = db.Column(db.String(20))
    contact_person = db.Column(db.String(80))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(80))

    products = db.relationship("ProductModel", backref='supplier', lazy="dynamic", cascade="all, delete-orphan")

    @classmethod
    def find_by_id(cls, id: int) -> "SupplierModel":
        return cls.query.filter_by(id=id).first()

    @classmethod
    def find_related_products_by_id(cls, id: int) -> List["ProductModel"]:
        return cls.query.filter_by(id=id).first().products.all()

    @classmethod
    def find_by_name(cls, name: str) -> "SupplierModel":
        return cls.query.filter_by(name=name).first()

    @classmethod
    def find_all(cls) -> List["SupplierModel"]:
        return cls.query.all()

    @classmethod
    def filter_by_city(cls, city: str) -> List["SupplierModel"]:
        return cls.query.filter_by(city=city)

    @classmethod
    def filter_by_zipcode(cls, zipcode: str) -> List["SupplierModel"]:
        return cls.query.filter_by(zipcode=zipcode)

    def save_to_db(self) -> None:
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self) -> None:
        db.session.delete(self)
        db.session.commit()