from flask import Flask, jsonify
from flask_restful import Api
from marshmallow import ValidationError

from db import db
from ma import ma
from resources.product import Product, ProductList
from resources.supplier import Supplier, SupplierList

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
api.add_resource(SupplierList, "/suppliers")


if __name__ == "__main__":
    db.init_app(app)
    ma.init_app(app)
    app.run(port=5000, debug=True)