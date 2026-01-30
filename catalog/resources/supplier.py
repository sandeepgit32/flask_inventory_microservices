from flask_restful import Resource
from flask import request
from pydantic import ValidationError
from models.supplier import SupplierModel
from schemas.supplier import SupplierCreate, SupplierUpdate, SupplierResponse
from schemas.product import ProductResponse
from libs.strings import gettext
from libs.pagination import get_paginated_list
from libs.pydantic_helpers import serialize_model, serialize_models, validate_request_data


class Supplier(Resource):
    # GET /supplier/<int:id>
    @classmethod
    def get(cls, id: int):
        supplier = SupplierModel.find_by_id(id)
        if supplier:
            return serialize_model(supplier, SupplierResponse), 200

        return {"message": gettext("supplier_not_found")}, 404


    # DELETE /supplier/<int:id>
    @classmethod
    def delete(cls, id: int):
        supplier = SupplierModel.find_by_id(id)
        if supplier:
            supplier.delete_from_db()
            return {"message": gettext("supplier_deleted")}, 200

        return {"message": gettext("supplier_not_found")}, 404


    # PUT /supplier/<int:id>
    @classmethod
    def put(cls, id: int):
        # When a client needs to replace an existing Resource entirely, they can use PUT. 
        # When they're doing a partial update, they can use HTTP PATCH.
        supplier_json = request.get_json()
        supplier = SupplierModel.find_by_id(id)

        if supplier:
            try:
                validated_data = validate_request_data(supplier_json, SupplierUpdate)
                # Dynamically setting attributes of the object 'supplier' from validated data
                for field, value in validated_data.model_dump(exclude_unset=True).items():
                    setattr(supplier, field, value)
                supplier.save_to_db()
            except ValidationError as e:
                return {"errors": e.errors()}, 400
        else:
            return {"message": gettext("supplier_not_found")}, 404

        return serialize_model(supplier, SupplierResponse), 200


class SupplierList(Resource):
    # GET /suppliers
    @classmethod
    def get(cls):
        return get_paginated_list(
            serialize_models(SupplierModel.find_all(), SupplierResponse),
            request.url, 
            start=request.args.get('start', default=1), 
            limit=request.args.get('limit')
        ), 200


    # POST /suppliers
    @classmethod
    def post(cls):
        supplier_json = request.get_json()
        supplier_name = supplier_json.get("name")

        if SupplierModel.find_by_name(supplier_name):
            return {"message": gettext("supplier_exists").format(supplier_name)}, 400

        try:
            validated_data = validate_request_data(supplier_json, SupplierCreate)
            supplier = SupplierModel(**validated_data.model_dump())
            supplier.save_to_db()
        except ValidationError as e:
            return {"errors": e.errors()}, 400
        except:
            return {"message": gettext("supplier_error_inserting")}, 500

        return serialize_model(supplier, SupplierResponse), 201


class SupplierListByCity(Resource):
    # GET /suppliers/<string:city>
    @classmethod
    def get(cls, city: str):
        return get_paginated_list(
            serialize_models(SupplierModel.filter_by_city(city), SupplierResponse),
            request.url, 
            start=request.args.get('start', default=1), 
            limit=request.args.get('limit')
        ), 200


class ProductListBySupplier(Resource):
    # GET /supplier/<int:id>/products
    @classmethod
    def get(cls, id: int):
        return get_paginated_list(
            serialize_models(SupplierModel.find_related_products_by_id(id), ProductResponse),
            request.url, 
            start=request.args.get('start', default=1), 
            limit=request.args.get('limit')
        ), 200