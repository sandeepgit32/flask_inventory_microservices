import os
from flask import jsonify
from app import create_app
from flask_restful import Api
from pydantic import ValidationError
from libs.pydantic_helpers import handle_validation_error
from resources.transaction import TransactionList, TransactionListByProduct, TransactionListBySupplier, TransactionListByProductAndSupplier

app = create_app(os.environ.get("FLASK_ENV"))

api = Api(app)

# supply transaction endpoints
api.add_resource(TransactionList, "/supplytransactions")
api.add_resource(TransactionListByProduct, "/supplytransactions/product/<string:product_code>")
api.add_resource(TransactionListBySupplier, "/supplytransactions/supplier/<string:supplier_name>")
api.add_resource(TransactionListByProductAndSupplier, "/supplytransactions/product_suplier/<string:product_code>/<string:supplier_name>")


@app.errorhandler(ValidationError)
def handle_marshmallow_validation(err):
    return handle_validation_error(err)


if __name__ == "__main__":
    # The host='0.0.0.0' must be mentioned, otherwise docker networking wont work.
    app.run(host='0.0.0.0', port=5000, debug=True)
