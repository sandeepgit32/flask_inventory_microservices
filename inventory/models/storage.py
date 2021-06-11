# from typing import List
# from db import db
# from models.customer import CustomerModel


# class WarehouseModel(db.Model):
#     __tablename__ = "storage"

#     id = db.Column(db.Integer, primary_key=True)
#     quantity = db.Column(db.String(80), nullable=False, unique=True)

#     product_code = db.Column(db.String(80), db.ForeignKey("products.product_code"), nullable=False)
#     warehouse_id = db.Column(db.Integer, db.ForeignKey("warehouses.id"))


#     @classmethod
#     def find_by_id(cls, id: int) -> "WarehouseModel":
#         return cls.query.filter_by(id=id).first()

#     @classmethod
#     def find_by_name(cls, name: str) -> "WarehouseModel":
#         return cls.query.filter_by(name=name).first()

#     @classmethod
#     def find_all(cls) -> List["WarehouseModel"]:
#         return cls.query.all()

#     @classmethod
#     def filter_by_city(cls, city: str) -> List["WarehouseModel"]:
#         return cls.query.filter_by(city=city)

#     def save_to_db(self) -> None:
#         db.session.add(self)
#         db.session.commit()

#     def delete_from_db(self) -> None:
#         db.session.delete(self)
#         db.session.commit()