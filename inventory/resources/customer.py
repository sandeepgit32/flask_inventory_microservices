from flask import request
from flask_restful import Resource
from models.customer import CustomerModel
from schemas.customer import CustomerSchema
from libs.strings import gettext
from libs.pagination import get_paginated_list

customer_schema = CustomerSchema()
customer_list_schema = CustomerSchema(many=True)


class Customer(Resource):
    # GET /customer/<int:id>
    @classmethod
    def get(cls, id: str):
        customer = CustomerModel.find_by_id(id)
        if customer:
            return customer_schema.dump(customer), 200

        return {"message": gettext("customer_not_found")}, 404


    # DELETE /customer/<int:id>
    @classmethod
    def delete(cls, id: int):
        customer = CustomerModel.find_by_id(id)
        if customer:
            customer.delete_from_db()
            return {"message": gettext("customer_deleted")}, 200

        return {"message": gettext("customer_not_found")}, 404


    # PUT /customer/<int:id>
    @classmethod
    def put(cls, id: int):
        # When a client needs to replace an existing Resource entirely, they can use PUT. 
        # When they're doing a partial update, they can use HTTP PATCH.
        customer_json = request.get_json()
        customer = CustomerModel.find_by_id(id)

        if customer:
            # Dynamically setting attributes of the object 'customer' from 'customer_json' dict
            for attribute in customer_json.keys():
                setattr(customer, attribute, customer_json[attribute])
            customer.save_to_db()
        else:
            return {"message": gettext("customer_not_found")}, 404

        return customer_schema.dump(customer), 200


class CustomerList(Resource):
    # GET /customers
    @classmethod
    def get(cls):
        return get_paginated_list(
            customer_list_schema.dump(CustomerModel.find_all()),
            request.url, 
            start=request.args.get('start', default=1), 
            limit=request.args.get('limit')
        ), 200


    # POST /customers
    @classmethod
    def post(cls):
        customer_json = request.get_json()
        customer_name = customer_json["name"]

        if CustomerModel.find_by_name(customer_name):
            return {"message": gettext("customer_exists").format(customer_name)}, 400

        customer = customer_schema.load(customer_json)

        try:
            customer.save_to_db()
        except:
            return {"message": gettext("customer_error_inserting")}, 500

        return customer_schema.dump(customer), 201


class CustomerListByCity(Resource):
    # GET /customers/<string:city>
    @classmethod
    def get(cls, city: str):
        return get_paginated_list(
            customer_list_schema.dump(CustomerModel.filter_by_city(city)),
            request.url, 
            start=request.args.get('start', default=1), 
            limit=request.args.get('limit')
        ), 200