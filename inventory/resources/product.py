from flask_restful import Resource
from flask import request
from models.product import ProductModel
from schemas.product import ProductSchema
from libs.strings import gettext

product_schema = ProductSchema()
product_list_schema = ProductSchema(many=True)


class Product(Resource):
    # GET /product/<string:product_code>
    @classmethod
    def get(cls, product_code: str):
        product = ProductModel.find_by_code(product_code)
        if product:
            return product_schema.dump(product), 200

        return {"message": gettext("product_not_found")}, 404


    # DELETE /product/<string:product_code>
    @classmethod
    def delete(cls, product_code: str):
        product = ProductModel.find_by_code(product_code)
        if product:
            product.delete_from_db()
            return {"message": gettext("product_deleted")}, 200

        return {"message": gettext("product_not_found")}, 404


    # PUT /product/<string:product_code>
    @classmethod
    def put(cls, product_code: str):
        # When a client needs to replace an existing Resource entirely, they can use PUT. 
        # When they're doing a partial update, they can use HTTP PATCH.
        product_json = request.get_json()
        product = ProductModel.find_by_code(product_code)

        if product:
            # Dynamically setting attributes of the object 'product' from 'product_json' dict
            for attribute in product_json.keys():
                setattr(supplier, product, product_json[attribute])
            product.save_to_db()
        else:
            return {"message": gettext("product_not_found")}, 404

        return product_schema.dump(product), 200


class ProductList(Resource):
    # GET /products
    @classmethod
    def get(cls):
        return {"products": product_list_schema.dump(ProductModel.find_all())}, 200

    # POST /products
    @classmethod
    def post(cls):
        product_json = request.get_json()
        product_code = product_json["product_code"]

        if ProductModel.find_by_code(product_code):
            return {"message": gettext("product_code_exists").format(product_code)}, 400

        product = product_schema.load(product_json)

        try:
            product.save_to_db()
        except:
            return {"message": gettext("product_error_inserting")}, 500

        return product_schema.dump(product), 201
