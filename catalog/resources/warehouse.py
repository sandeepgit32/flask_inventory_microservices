from flask_restful import Resource
from flask import request
from pydantic import ValidationError
from models.warehouse import WarehouseModel
from schemas.warehouse import WarehouseCreate, WarehouseUpdate, WarehouseResponse
from schemas.customer import CustomerResponse
from libs.strings import gettext
from libs.pagination import get_paginated_list
from libs.pydantic_helpers import serialize_model, serialize_models, validate_request_data


class Warehouse(Resource):
    # GET /warehouse/<int:id>
    @classmethod
    def get(cls, id: int):
        warehouse = WarehouseModel.find_by_id(id)
        if warehouse:
            return serialize_model(warehouse, WarehouseResponse), 200

        return {"message": gettext("warehouse_not_found")}, 404


    # DELETE /warehouse/<int:id>
    @classmethod
    def delete(cls, id: int):
        warehouse = WarehouseModel.find_by_id(id)
        if warehouse:
            warehouse.delete_from_db()
            return {"message": gettext("warehouse_deleted")}, 200

        return {"message": gettext("warehouse_not_found")}, 404


    # PUT /warehouse/<int:id>
    @classmethod
    def put(cls, id: int):
        # When a client needs to replace an existing Resource entirely, they can use PUT. 
        # When they're doing a partial update, they can use HTTP PATCH.
        warehouse_json = request.get_json()
        warehouse = WarehouseModel.find_by_id(id)

        if warehouse:
            try:
                validated_data = validate_request_data(warehouse_json, WarehouseUpdate)
                # Dynamically setting attributes of the object 'warehouse' from validated data
                for field, value in validated_data.model_dump(exclude_unset=True).items():
                    setattr(warehouse, field, value)
                warehouse.save_to_db()
            except ValidationError as e:
                return {"errors": e.errors()}, 400
        else:
            return {"message": gettext("warehouse_not_found")}, 404

        return serialize_model(warehouse, WarehouseResponse), 200


class WarehouseList(Resource):
    # GET /warehouses
    # @classmethod
    # def get(cls):
    #     return {"warehouses": warehouse_list_schema.dump(WarehouseModel.find_all())}, 200

    @classmethod
    def get(cls):
        return get_paginated_list(
            serialize_models(WarehouseModel.find_all(), WarehouseResponse),
            request.url, 
            start=request.args.get('start', default=1), 
            limit=request.args.get('limit')
        ), 200


    # POST /warehouses
    @classmethod
    def post(cls):
        warehouse_json = request.get_json()
        print('request', request.headers)
        warehouse_name = warehouse_json.get("name")

        if WarehouseModel.find_by_name(warehouse_name):
            return {"message": gettext("warehouse_exists").format(warehouse_name)}, 400

        try:
            validated_data = validate_request_data(warehouse_json, WarehouseCreate)
            warehouse = WarehouseModel(**validated_data.model_dump())
            warehouse.save_to_db()
        except ValidationError as e:
            return {"errors": e.errors()}, 400
        except:
            return {"message": gettext("warehouse_error_inserting")}, 500

        return serialize_model(warehouse, WarehouseResponse), 201


class WarehouseListByCity(Resource):
    # GET /warehouses/<string:city>
    @classmethod
    def get(cls, city: str):
        return get_paginated_list(
            serialize_models(WarehouseModel.filter_by_city(city), WarehouseResponse),
            request.url, 
            start=request.args.get('start', default=1), 
            limit=request.args.get('limit')
        ), 200


class CustomerListByWarehouse(Resource):
    # GET /warehouse/<int:id>/customers
    @classmethod
    def get(cls, id: int):
        return get_paginated_list(
            serialize_models(WarehouseModel.find_associated_customers_by_id(id), CustomerResponse),
            request.url, 
            start=request.args.get('start', default=1), 
            limit=request.args.get('limit')
        ), 200