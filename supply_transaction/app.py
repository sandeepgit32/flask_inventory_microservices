import os

from db import db
from flask import Flask, jsonify
from flask_restful import Api
from ma import ma
from marshmallow import ValidationError
from resources.transaction import (
    TransactionList,
    TransactionListByProduct,
    TransactionListByProductAndSupplier,
    TransactionListBySupplier,
)

app = Flask(__name__)
flask_env = os.environ.get("FLASK_ENV")

if flask_env == "dev":
    app.config.from_object("config.DevConfig")
elif flask_env == "test":
    app.config.from_object("config.TestConfig")
elif flask_env == "prod":
    app.config.from_object("config.ProdConfig")

api = Api(app)


@app.before_first_request
def create_tables():
    db.create_all()


@app.errorhandler(ValidationError)
def handle_marshmallow_validation(err):
    return jsonify(err.messages), 400


# supply transaction endpoints
api.add_resource(TransactionList, "/supplytransactions")
api.add_resource(
    TransactionListByProduct, "/supplytransactions/product/<string:product_code>"
)
api.add_resource(
    TransactionListBySupplier, "/supplytransactions/supplier/<string:supplier_name>"
)
api.add_resource(
    TransactionListByProductAndSupplier,
    "/supplytransactions/product_suplier/<string:product_code>/<string:supplier_name>",
)


if __name__ == "__main__":
    db.init_app(app)
    ma.init_app(app)
    app.run(host="0.0.0.0", port=5000, debug=True)
