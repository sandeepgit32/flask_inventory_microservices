from flask_restful import Resource
from flask import request
from pydantic import ValidationError
from models.storage import StorageModel
from schemas.storage import StorageCreate, StorageUpdate, StorageResponse
from libs.strings import gettext
from libs.pagination import get_paginated_list
from libs.pydantic_helpers import serialize_model, serialize_models, validate_request_data


class Storage(Resource):
    # GET /storage/<string:product_code>/<string:warehouse_name>
    @classmethod
    def get(cls, product_code: str, warehouse_name: str):
        print(product_code, warehouse_name)
        storage = StorageModel.find_by_product_code_and_warehouse_name(product_code, warehouse_name)
        if storage:
            return serialize_model(storage, StorageResponse), 200

        return {"message": gettext("storage_not_found").format(product_code, warehouse_name)}, 404


class StorageInsert(Resource):
    # PUT /storage/<string:product_code>/<string:warehouse_name>/<string:type>
    @classmethod
    def put(cls, product_code: str, warehouse_name: str, type: str):
        # In this particular case HTTP PUT request is somehow tweaked. It is also being used
        # as a POST request is no entry for the given product_code and warehouse_name is found.
        # "type" is an extra variable used for 'insert'/ or 'update' operation. Insert operation
        # will replace the existing values while update operation will add over the existing values.
        storage_json = request.get_json()
        storage = StorageModel.find_by_product_code_and_warehouse_name(product_code, warehouse_name)

        if storage:
            if type == 'insert':
                storage.quantity = storage_json["quantity"]
            elif type == 'update':
                storage.quantity += storage_json["quantity"]
            else:
                return {"message": gettext("storage_cannot_be_updated")}, 404
        else:
            try:
                storage_json["product_code"] = product_code
                storage_json["warehouse_name"] = warehouse_name
                validated_data = validate_request_data(storage_json, StorageCreate)
                storage = StorageModel(**validated_data.model_dump())
            except ValidationError as e:
                return {"errors": e.errors()}, 400
        
        storage.save_to_db()

        return serialize_model(storage, StorageResponse), 200


class StorageList(Resource):
    # GET /storages
    @classmethod
    def get(cls):
        return get_paginated_list(
            serialize_models(StorageModel.find_all(), StorageResponse),
            request.url, 
            start=request.args.get('start', default=1), 
            limit=request.args.get('limit')
        ), 200


    # POST /storages
    @classmethod
    def post(cls):
        # This request will not be used in practice. This is defined only to insert dummy data for testing
        # through 'upload.py' script.
        storage_json = request.get_json()
        try:
            validated_data = validate_request_data(storage_json, StorageCreate)
            storage = StorageModel(**validated_data.model_dump())
            storage.save_to_db()
        except ValidationError as e:
            return {"errors": e.errors()}, 400
        except:
            return {"message": gettext("storage_error_inserting")}, 500

        return serialize_model(storage, StorageResponse), 201


class StorageListByProduct(Resource):
    # GET /storages/product/<string:product_code>
    @classmethod
    def get(cls, product_code: str):
        return get_paginated_list(
            serialize_models(StorageModel.filter_by_product_code(product_code), StorageResponse),
            request.url, 
            start=request.args.get('start', default=1), 
            limit=request.args.get('limit')
        ), 200


class StorageListByWarehouse(Resource):
    # GET /storages/warehouse/<string:warehouse_name>
    @classmethod
    def get(cls, warehouse_name: str):
        return get_paginated_list(
            serialize_models(StorageModel.filter_by_warehouse_name(warehouse_name), StorageResponse),
            request.url,
            start=request.args.get('start', default=1), 
            limit=request.args.get('limit')
        ), 200
