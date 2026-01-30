from flask import request
from flask_restful import Resource
from pydantic import ValidationError
from models.customer import CustomerModel
from schemas.customer import CustomerCreate, CustomerUpdate, CustomerResponse
from libs.strings import gettext
from libs.pagination import get_paginated_list
from libs.pydantic_helpers import serialize_model, serialize_models, validate_request_data


class Customer(Resource):
    # GET /customer/<int:id>
    @classmethod
    def get(cls, id: str):
        customer = CustomerModel.find_by_id(id)
        if customer:
            return serialize_model(customer, CustomerResponse), 200

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
            try:
                validated_data = validate_request_data(customer_json, CustomerUpdate)
                # Dynamically setting attributes of the object 'customer' from validated data
                for field, value in validated_data.model_dump(exclude_unset=True).items():
                    setattr(customer, field, value)
                customer.save_to_db()
            except ValidationError as e:
                return {"errors": e.errors()}, 400
        else:
            return {"message": gettext("customer_not_found")}, 404

        return serialize_model(customer, CustomerResponse), 200


class CustomerList(Resource):
    # GET /customers
    @classmethod
    def get(cls):
        return get_paginated_list(
            serialize_models(CustomerModel.find_all(), CustomerResponse),
            request.url, 
            start=request.args.get('start', default=1), 
            limit=request.args.get('limit')
        ), 200


    # POST /customers
    @classmethod
    def post(cls):
        customer_json = request.get_json()
        customer_name = customer_json.get("name")

        if CustomerModel.find_by_name(customer_name):
            return {"message": gettext("customer_exists").format(customer_name)}, 400

        try:
            validated_data = validate_request_data(customer_json, CustomerCreate)
            customer = CustomerModel(**validated_data.model_dump())
            customer.save_to_db()
        except ValidationError as e:
            return {"errors": e.errors()}, 400
        except:
            return {"message": gettext("customer_error_inserting")}, 500

        return serialize_model(customer, CustomerResponse), 201


class CustomerListByCity(Resource):
    # GET /customers/<string:city>
    @classmethod
    def get(cls, city: str):
        return get_paginated_list(
            serialize_models(CustomerModel.filter_by_city(city), CustomerResponse),
            request.url, 
            start=request.args.get('start', default=1), 
            limit=request.args.get('limit')
        ), 200