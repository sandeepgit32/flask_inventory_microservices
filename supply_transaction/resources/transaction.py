from flask_restful import Resource
from flask import request
from models.transaction import TransactionModel
from schemas.transaction import TransactionSchema
from libs.strings import gettext
from libs.pagination import get_paginated_list
from producer import send_message

transaction_schema = TransactionSchema()
transaction_list_schema = TransactionSchema(many=True)


class TransactionList(Resource):
    # GET /supplytransactions
    @classmethod
    def get(cls):
        return get_paginated_list(
            transaction_list_schema.dump(TransactionModel.find_all()),
            request.url, 
            start=request.args.get('start', default=1), 
            limit=request.args.get('limit')
        ), 200


    # POST /supplytransactions
    @classmethod
    def post(cls):
        # This request will not be used in practice. This is defined only to insert dummy data for testing
        # through 'upload.py' script.
        transaction_json = request.get_json()
        transaction = transaction_schema.load(transaction_json)
        try:
            transaction.save_to_db()
            # Send message to message queue in order to update the quantity in inventory
            MESSAGE_BODY = {
                "product_code": transaction_json["product_code"],
                "warehouse_name": "Main_Warehouse",
                "quantity": transaction_json["quantity"]
            }
            send_message(MESSAGE_BODY)
        except:
            return {"message": gettext("transaction_error_inserting")}, 500

        return transaction_schema.dump(transaction), 201


class TransactionListByProduct(Resource):
    # GET /supplytransactions/product/<string:product_code>
    @classmethod
    def get(cls, product_code: str):
        return get_paginated_list(
            transaction_list_schema.dump(TransactionModel.filter_by_product(product_code)),
            request.url, 
            start=request.args.get('start', default=1), 
            limit=request.args.get('limit')
        ), 200


class TransactionListBySupplier(Resource):
    # GET /supplytransactions/supplier/<string:supplier_name>
    @classmethod
    def get(cls, supplier_name: str):
        return get_paginated_list(
            transaction_list_schema.dump(TransactionModel.filter_by_supplier(supplier_name)),
            request.url,
            start=request.args.get('start', default=1), 
            limit=request.args.get('limit')
        ), 200


class TransactionListByProductAndSupplier(Resource):
    # GET /supplytransactions/product_suplier/<string:product_code>/<string:supplier_name>
    @classmethod
    def get(cls, product_code: str, supplier_name: str):
        transaction = TransactionModel.filter_by_product_and_supplier(product_code, supplier_name)
        if transaction:
            return get_paginated_list(
                transaction_list_schema.dump(transaction),
                request.url, 
                start=request.args.get('start', default=1), 
                limit=request.args.get('limit')
            ), 200

        return {"message": gettext("transaction_not_found").format(product_code, supplier_name)}, 404