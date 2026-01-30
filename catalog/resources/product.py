from flask_restful import Resource
from flask import request
from pydantic import ValidationError
from models.product import ProductModel
from schemas.product import ProductCreate, ProductUpdate, ProductResponse
from libs.strings import gettext
from libs.pagination import get_paginated_list
from libs.pydantic_helpers import serialize_model, serialize_models, validate_request_data


class Product(Resource):
    # GET /product/<string:product_code>
    @classmethod
    def get(cls, product_code: str):
        product = ProductModel.find_by_code(product_code)
        if product:
            return serialize_model(product, ProductResponse), 200

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
            try:
                validated_data = validate_request_data(product_json, ProductUpdate)
                # Dynamically setting attributes of the object 'product' from validated data
                for field, value in validated_data.model_dump(exclude_unset=True).items():
                    setattr(product, field, value)
                product.save_to_db()
            except ValidationError as e:
                return {"errors": e.errors()}, 400
        else:
            return {"message": gettext("product_not_found")}, 404

        return serialize_model(product, ProductResponse), 200


class ProductList(Resource):
    # GET /products
    @classmethod
    def get(cls):
        return get_paginated_list(
            serialize_models(ProductModel.find_all(), ProductResponse),
            request.url, 
            start=request.args.get('start', default=1), 
            limit=request.args.get('limit')
        ), 200

    # POST /products
    @classmethod
    def post(cls):
        product_json = request.get_json()
        product_code = product_json.get("product_code")

        if ProductModel.find_by_code(product_code):
            return {"message": gettext("product_code_exists").format(product_code)}, 400

        try:
            validated_data = validate_request_data(product_json, ProductCreate)
            product = ProductModel(**validated_data.model_dump())
            product.save_to_db()
        except ValidationError as e:
            return {"errors": e.errors()}, 400
        except:
            return {"message": gettext("product_error_inserting")}, 500

        return serialize_model(product, ProductResponse), 201
