from flask import Flask, jsonify
from flask_restful import Api
from marshmallow import ValidationError

from resources.product import Product, ProductList
from resources.supplier import Supplier, SupplierList, SupplierListByCity, ProductListBySupplier
from resources.customer import Customer, CustomerList, CustomerListByCity
from resources.warehouse import Warehouse, WarehouseList, WarehouseListByCity, CustomerListByWarehouse

from db import db
from ma import ma

app = Flask(__name__)

# # Using a production configuration
# app.config.from_object('config.ProdConfig')

# Using a development configuration
app.config.from_object('config.DevConfig')

api = Api(app)


@app.before_first_request
def create_tables():
    db.create_all()


@app.errorhandler(ValidationError)
def handle_marshmallow_validation(err):
    return jsonify(err.messages), 400


api.add_resource(Product, "/product/<string:product_code>")
api.add_resource(ProductList, "/products")
api.add_resource(Supplier, "/supplier/<int:id>")
api.add_resource(SupplierListByCity, "/suppliers/<string:city>")
api.add_resource(ProductListBySupplier, "/supplier/<int:id>/products")
api.add_resource(SupplierList, "/suppliers")
api.add_resource(Customer, "/customer/<int:id>")
api.add_resource(CustomerList, "/customers")
api.add_resource(CustomerListByCity, "/customers/<string:city>")
api.add_resource(Warehouse, "/warehouse/<int:id>")
api.add_resource(WarehouseList, "/warehouses")
api.add_resource(WarehouseListByCity, "/warehouses/<string:city>")
api.add_resource(CustomerListByWarehouse, "/warehouse/<int:id>/customers")


if __name__ == "__main__":
    db.init_app(app)
    ma.init_app(app)
    app.run(port=5000, debug=True)