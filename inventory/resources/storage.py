from flask_restful import Resource
from flask import request
from models.storage import StorageModel
from schemas.storage import StorageSchema
from libs.strings import gettext
from libs.pagination import get_paginated_list

storage_schema = StorageSchema()
storage_list_schema = StorageSchema(many=True)


class Storage(Resource):
    # GET /storage/<string:product_code>/<string:warehouse_name>
    @classmethod
    def get(cls, product_code: str, warehouse_name: str):
        print(product_code, warehouse_name)
        storage = StorageModel.find_by_product_code_and_warehouse_name(product_code, warehouse_name)
        if storage:
            return storage_schema.dump(storage), 200

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
            storage_json["product_code"]: product_code
            storage_json["warehouse_name"]: warehouse_name
            storage = storage_schema.load(storage_json)
        
        storage.save_to_db()

        return storage_schema.dump(storage), 200


class StorageList(Resource):
    # GET /storages
    @classmethod
    def get(cls):
        return get_paginated_list(
            storage_list_schema.dump(StorageModel.find_all()),
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
        storage = storage_schema.load(storage_json)
        try:
            storage.save_to_db()
        except:
            return {"message": gettext("storage_error_inserting")}, 500

        return storage_schema.dump(storage), 201


class StorageListByProduct(Resource):
    # GET /storages/product/<string:product_code>
    @classmethod
    def get(cls, product_code: str):
        return get_paginated_list(
            storage_list_schema.dump(StorageModel.filter_by_product_code(product_code)),
            request.url, 
            start=request.args.get('start', default=1), 
            limit=request.args.get('limit')
        ), 200


class StorageListByWarehouse(Resource):
    # GET /storages/warehouse/<string:warehouse_name>
    @classmethod
    def get(cls, warehouse_name: str):
        return get_paginated_list(
            storage_list_schema.dump(StorageModel.filter_by_warehouse_name(warehouse_name)),
            request.url,
            start=request.args.get('start', default=1), 
            limit=request.args.get('limit')
        ), 200
