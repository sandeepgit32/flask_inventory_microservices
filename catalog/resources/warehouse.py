from flask_restful import Resource
from flask import request
from models.warehouse import WarehouseModel
from schemas.warehouse import WarehouseSchema
from schemas.customer import CustomerSchema
from libs.strings import gettext
from libs.pagination import get_paginated_list

warehouse_schema = WarehouseSchema()
warehouse_list_schema = WarehouseSchema(many=True)
customer_list_schema = CustomerSchema(many=True)


class Warehouse(Resource):
    # GET /warehouse/<int:id>
    @classmethod
    def get(cls, id: int):
        warehouse = WarehouseModel.find_by_id(id)
        if warehouse:
            return warehouse_schema.dump(warehouse), 200

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
            # Dynamically setting attributes of the object 'warehouse' from 'warehouse_json' dict
            for attribute in warehouse_json.keys():
                setattr(warehouse, attribute, warehouse_json[attribute])
            warehouse.save_to_db()
        else:
            return {"message": gettext("warehouse_not_found")}, 404

        return warehouse_schema.dump(warehouse), 200


class WarehouseList(Resource):
    # GET /warehouses
    # @classmethod
    # def get(cls):
    #     return {"warehouses": warehouse_list_schema.dump(WarehouseModel.find_all())}, 200

    @classmethod
    def get(cls):
        return get_paginated_list(
            warehouse_list_schema.dump(WarehouseModel.find_all()),
            request.url, 
            start=request.args.get('start', default=1), 
            limit=request.args.get('limit')
        ), 200


    # POST /warehouses
    @classmethod
    def post(cls):
        warehouse_json = request.get_json()
        print('request', request.headers)
        warehouse_name = warehouse_json["name"]

        if WarehouseModel.find_by_name(warehouse_name):
            return {"message": gettext("warehouse_exists").format(warehouse_name)}, 400

        warehouse = warehouse_schema.load(warehouse_json)

        try:
            warehouse.save_to_db()
        except:
            return {"message": gettext("warehouse_error_inserting")}, 500

        return warehouse_schema.dump(warehouse), 201


class WarehouseListByCity(Resource):
    # GET /warehouses/<string:city>
    @classmethod
    def get(cls, city: str):
        return get_paginated_list(
            warehouse_list_schema.dump(WarehouseModel.filter_by_city(city)),
            request.url, 
            start=request.args.get('start', default=1), 
            limit=request.args.get('limit')
        ), 200


class CustomerListByWarehouse(Resource):
    # GET /warehouse/<int:id>/customers
    @classmethod
    def get(cls, id: int):
        return get_paginated_list(
            customer_list_schema.dump(WarehouseModel.find_associated_customers_by_id(id)),
            request.url, 
            start=request.args.get('start', default=1), 
            limit=request.args.get('limit')
        ), 200