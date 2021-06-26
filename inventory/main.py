import os
from flask import jsonify
from flask_restful import Api
from app import create_app
from marshmallow import ValidationError

from resources.product import Product, ProductList
from resources.supplier import Supplier, SupplierList, SupplierListByCity, ProductListBySupplier
from resources.customer import Customer, CustomerList, CustomerListByCity
from resources.warehouse import Warehouse, WarehouseList, WarehouseListByCity, CustomerListByWarehouse
from resources.storage import Storage, StorageInsert, StorageList, StorageListByProduct, StorageListByWarehouse

app = create_app(os.environ.get("FLASK_ENV"))

api = Api(app)


# product endpoints
api.add_resource(Product, "/product/<string:product_code>")
api.add_resource(ProductList, "/products")
# supplier endpoints
api.add_resource(Supplier, "/supplier/<int:id>")
api.add_resource(SupplierListByCity, "/suppliers/<string:city>")
api.add_resource(ProductListBySupplier, "/supplier/<int:id>/products")
api.add_resource(SupplierList, "/suppliers")
# suppplier endpoints
api.add_resource(Customer, "/customer/<int:id>")
api.add_resource(CustomerList, "/customers")
api.add_resource(CustomerListByCity, "/customers/<string:city>")
# warehouse endpoints
api.add_resource(Warehouse, "/warehouse/<int:id>")
api.add_resource(WarehouseList, "/warehouses")
api.add_resource(WarehouseListByCity, "/warehouses/<string:city>")
api.add_resource(CustomerListByWarehouse, "/warehouse/<int:id>/customers")
# storage endpoints
api.add_resource(Storage, "/storage/<string:product_code>/<string:warehouse_name>")
api.add_resource(StorageList, "/storages")
api.add_resource(StorageInsert, "/storage/<string:product_code>/<string:warehouse_name>/<string:type>")
api.add_resource(StorageListByProduct, "/storages/product/<string:product_code>")
api.add_resource(StorageListByWarehouse, "/storages/warehouse/<string:warehouse_name>")


@app.errorhandler(ValidationError)
def handle_marshmallow_validation(err):
    return jsonify(err.messages), 400


if __name__ == "__main__":
    # The host='0.0.0.0' must be mentioned, otherwise docker networking wont work.
    app.run(host='0.0.0.0', port=5000, debug=True)