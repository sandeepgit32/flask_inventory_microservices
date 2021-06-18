import os
import sys
import pika
import json
import time
from dotenv import load_dotenv
load_dotenv('.env', verbose=True)
from app import create_app
from models.storage import StorageModel
from schemas.storage import StorageSchema

# The followimg models need to be imported as StorageModel has foreignkey
# relationship with these two ProductModel and WarehouseModel. Similarly
# ProductModel has relationship with SupplyModel and so on.
from models.product import ProductModel
from models.warehouse import WarehouseModel
from models.supplier import SupplierModel
from models.customer import CustomerModel

storage_schema = StorageSchema()

# class MessageQueue:
#     def __init__(self):
#         pass

def callback(ch, method, properties, body):
    storage_json = json.loads(body) # Contains product code and warehouse_name
    product_code = storage_json['product_code']
    warehouse_name = storage_json['warehouse_name']

    app = create_app(os.environ.get("FLASK_ENV"))
    with app.app_context():
        storage = StorageModel.find_by_product_code_and_warehouse_name(product_code, warehouse_name)

        if storage:
            storage.quantity += storage_json["quantity"]
        else:
            storage = storage_schema.load(storage_json)
        storage.save_to_db()
    print(storage_json)


def receive_message():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()

    channel.queue_declare(queue='hello')
    channel.basic_consume(
        queue='hello', 
        on_message_callback=callback, 
        auto_ack=True)

    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()


receive_message()
