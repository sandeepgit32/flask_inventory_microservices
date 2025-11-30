"""
Redis Message Queue Consumer

Consumes messages from Redis queue to update inventory storage.
"""
import os
import sys
from dotenv import load_dotenv

# Add message_queue to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'message_queue'))

load_dotenv('.env', verbose=True)
load_dotenv('message_queue/.env', verbose=True)

from app import create_app
from models.storage import StorageModel
from schemas.storage import StorageSchema

# The following models need to be imported as StorageModel has foreignkey
# relationship with these two ProductModel and WarehouseModel. Similarly
# ProductModel has relationship with SupplyModel and so on.
from models.product import ProductModel
from models.warehouse import WarehouseModel
from models.supplier import SupplierModel
from models.customer import CustomerModel

from message_queue.consumer import create_consumer

storage_schema = StorageSchema()


def process_inventory_update(message_body: dict):
    """
    Process an inventory update message.
    
    Args:
        message_body: Dictionary containing:
            - product_code: The product code
            - warehouse_name: The warehouse name
            - quantity: The quantity to add
    """
    product_code = message_body['product_code']
    warehouse_name = message_body['warehouse_name']

    app = create_app(os.environ.get("FLASK_ENV", "development"))
    with app.app_context():
        storage = StorageModel.find_by_product_code_and_warehouse_name(
            product_code, warehouse_name
        )

        if storage:
            storage.quantity += message_body["quantity"]
        else:
            storage = storage_schema.load(message_body)
        
        storage.save_to_db()
        print(f" [✓] Updated storage: {message_body}")


def main():
    """Start the message queue consumer"""
    print(" [*] Starting Redis message queue consumer...")
    consumer = create_consumer(process_inventory_update)
    consumer.start_consuming()


if __name__ == "__main__":
    main()

