import os
from flask import jsonify
from app import create_app

from marshmallow import ValidationError
# from resources.transaction import TransactionList, TransactionListByProduct, TransactionListByCustomer, TransactionListByProductAndCustomer

app = create_app(os.environ.get("FLASK_ENV"))

@app.errorhandler(ValidationError)
def handle_marshmallow_validation(err):
    return jsonify(err.messages), 400


if __name__ == "__main__":
    # print(app.config)
    app.run(port=5000, debug=True)