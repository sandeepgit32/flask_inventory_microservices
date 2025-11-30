import os

# Service URLs - use container names in Docker network
CATALOG_SERVICE_URL = os.getenv("CATALOG_SERVICE_URL", "http://catalog_api:5000")
SUPPLY_TRANSACTION_SERVICE_URL = os.getenv("SUPPLY_TRANSACTION_SERVICE_URL", "http://supplytransaction_api:5000")
CUSTOMER_TRANSACTION_SERVICE_URL = os.getenv("CUSTOMER_TRANSACTION_SERVICE_URL", "http://customertransaction_api:5000")
