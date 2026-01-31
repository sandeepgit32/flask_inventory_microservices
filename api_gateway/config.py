import os

# Microservice URLs - use container names in Docker network
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth:5003")
PRODUCT_SERVICE_URL = os.getenv("PRODUCT_SERVICE_URL", "http://product:5000")
SUPPLIER_SERVICE_URL = os.getenv("SUPPLIER_SERVICE_URL", "http://supplier:5004")
CUSTOMER_SERVICE_URL = os.getenv("CUSTOMER_SERVICE_URL", "http://customer:5005")
INVENTORY_SERVICE_URL = os.getenv("INVENTORY_SERVICE_URL", "http://inventory:5006")
PROCUREMENT_SERVICE_URL = os.getenv("PROCUREMENT_SERVICE_URL", "http://procurement:5001")
ORDER_SERVICE_URL = os.getenv("ORDER_SERVICE_URL", "http://order:5002")
