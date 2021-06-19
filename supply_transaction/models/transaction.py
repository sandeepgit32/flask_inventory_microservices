from typing import List
from db import db
from sqlalchemy import and_


class TransactionModel(db.Model):
    __tablename__ = "transactions"

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.Date)
    supplier_name = db.Column(db.String(100), nullable=False)
    city = db.Column(db.String(50))
    zipcode = db.Column(db.Integer)
    contact_person = db.Column(db.String(80))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(80))
    product_code = db.Column(db.String(80), nullable=False)
    product_name = db.Column(db.String(80), nullable=False)
    product_category = db.Column(db.String(50))
    unit_price = db.Column(db.Float(precision=2), nullable=False)
    quantity = db.Column(db.Integer)
    total_cost = db.Column(db.Float(precision=2), nullable=False)
    measure_unit = db.Column(db.String(10))


    @classmethod
    def find_by_id(cls, id: int) -> "TransactionModel":
        return cls.query.filter_by(id=id).first()

    @classmethod
    def find_all(cls) -> List["TransactionModel"]:
        return cls.query.all()

    @classmethod
    def filter_by_supplier(cls, supplier_name: str) -> List["TransactionModel"]:
        return cls.query.filter_by(supplier_name=supplier_name)

    @classmethod
    def filter_by_product(cls, product_code: str) -> List["TransactionModel"]:
        return cls.query.filter_by(product_code=product_code)

    @classmethod
    def filter_by_product_and_supplier(cls, product_code: str, supplier_name: str) -> List["TransactionModel"]:
        return cls.query.filter(and_(cls.supplier_name==supplier_name, cls.product_code==product_code)).all()

    
    def save_to_db(self) -> None:
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self) -> None:
        db.session.delete(self)
        db.session.commit()
