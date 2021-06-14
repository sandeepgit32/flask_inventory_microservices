from flask_restful import Resource
from flask import request
from models.transaction import TransactionModel
from schemas.transaction import TransactionSchema
from libs.strings import gettext
from libs.pagination import get_paginated_list

transaction_schema = TransactionSchema()
transaction_list_schema = TransactionSchema(many=True)


class TransactionList(Resource):
    # GET /customertransactions
    @classmethod
    def get(cls):
        return get_paginated_list(
            transaction_list_schema.dump(TransactionModel.find_all()),
            request.url, 
            start=request.args.get('start', default=1), 
            limit=request.args.get('limit')
        ), 200


    # POST /customertransactions
    @classmethod
    def post(cls):
        # This request will not be used in practice. This is defined only to insert dummy data for testing
        # through 'upload.py' script.
        transaction_json = request.get_json()
        transaction = transaction_schema.load(transaction_json)
        try:
            transaction.save_to_db()
        except:
            return {"message": gettext("transaction_error_inserting")}, 500

        return transaction_schema.dump(transaction), 201


class TransactionListByProduct(Resource):
    # GET /customertransactions/product/<string:product_code>
    @classmethod
    def get(cls, product_code: str):
        return get_paginated_list(
            transaction_list_schema.dump(TransactionModel.filter_by_product(product_code)),
            request.url, 
            start=request.args.get('start', default=1), 
            limit=request.args.get('limit')
        ), 200


class TransactionListByCustomer(Resource):
    # GET /customertransactions/customer/<string:customer_name>
    @classmethod
    def get(cls, customer_name: str):
        return get_paginated_list(
            transaction_list_schema.dump(TransactionModel.filter_by_supplier(customer_name)),
            request.url,
            start=request.args.get('start', default=1), 
            limit=request.args.get('limit')
        ), 200


class TransactionListByProductAndCustomer(Resource):
    # GET /customertransactions/<string:product_code>/<string:customer_name>
    @classmethod
    def get(cls, product_code: str, customer_name: str):
        print(product_code, customer_name)
        transaction = TransactionModel.filter_by_product_and_supplier(product_code, customer_name)
        if transaction:
            return get_paginated_list(
                transaction_list_schema.dump(transaction),
                request.url, 
                start=request.args.get('start', default=1), 
                limit=request.args.get('limit')
            ), 200

        return {"message": gettext("transaction_not_found").format(product_code, customer_name)}, 404