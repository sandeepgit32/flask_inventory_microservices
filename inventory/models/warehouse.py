from typing import List
from db import db
from models.customer import CustomerModel


class WarehouseModel(db.Model):
    __tablename__ = "warehouses"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False, unique=True)
    city = db.Column(db.String(50))
    zipcode = db.Column(db.Integer)
    contact_person = db.Column(db.String(80))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(80))

    customers = db.relationship("CustomerModel", backref='warehouse')

    @classmethod
    def find_by_name(cls, name: str) -> "WarehouseModel":
        return cls.query.filter_by(name=name).first()

    @classmethod
    def find_all(cls) -> List["WarehouseModel"]:
        return cls.query.all()

    @classmethod
    def filter_by_city(cls) -> List["WarehouseModel"]:
        return cls.query.filter_by(city=city)

    @classmethod
    def filter_by_zipcode(cls) -> List["WarehouseModel"]:
        return cls.query.filter_by(zipcode=zipcode)

    def save_to_db(self) -> None:
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self) -> None:
        db.session.delete(self)
        db.session.commit()