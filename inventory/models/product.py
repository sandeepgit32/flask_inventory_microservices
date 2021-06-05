from typing import List
from db import db


class ProductModel(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    product_code = db.Column(db.String(80), nullable=False, unique=True)
    name = db.Column(db.String(80), nullable=False, unique=True)
    category = db.Column(db.String(50))
    price_buy = db.Column(db.Float(precision=2), nullable=False)
    price_sell = db.Column(db.Float(precision=2), nullable=False)
    measure_unit = db.Column(db.String(10))

    supplier_id = db.Column(db.Integer, db.ForeignKey("suppliers.id"), nullable=False)


    @classmethod
    def find_by_name(cls, name: str) -> "ProductModel":
        return cls.query.filter_by(name=name).first()

    @classmethod
    def find_by_code(cls, product_code: str) -> "ProductModel":
        return cls.query.filter_by(product_code=product_code).first()

    @classmethod
    def find_all(cls) -> List["ProductModel"]:
        return cls.query.all()

    @classmethod
    def filter_by_category(cls) -> List["SupplierModel"]:
        return cls.query.filter_by(category=category)

    def save_to_db(self) -> None:
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self) -> None:
        db.session.delete(self)
        db.session.commit()