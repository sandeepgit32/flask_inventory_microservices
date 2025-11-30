from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import httpx
from typing import Optional
from config import (
    CATALOG_SERVICE_URL,
    SUPPLY_TRANSACTION_SERVICE_URL,
    CUSTOMER_TRANSACTION_SERVICE_URL
)

app = FastAPI(
    title="Inventory Microservices API Gateway",
    description="Single entry point for all inventory microservices",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# HTTP client
client = httpx.AsyncClient(timeout=30.0)


async def proxy_request(service_url: str, path: str, request: Request, params: dict = None):
    """Generic proxy function to forward requests to microservices"""
    url = f"{service_url}{path}"
    try:
        if request.method == "GET":
            response = await client.get(url, params=params)
        elif request.method == "POST":
            body = await request.json()
            response = await client.post(url, json=body, params=params)
        elif request.method == "PUT":
            body = await request.json()
            response = await client.put(url, json=body, params=params)
        elif request.method == "DELETE":
            response = await client.delete(url, params=params)
        else:
            raise HTTPException(status_code=405, detail="Method not allowed")
        
        return response.json()
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")


# ==================== Health Check ====================
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "api_gateway"}


# ==================== Product Endpoints ====================
@app.get("/api/products")
async def get_products(request: Request, start: Optional[int] = 1, limit: Optional[int] = None):
    return await proxy_request(CATALOG_SERVICE_URL, "/products", request, {"start": start, "limit": limit})

@app.post("/api/products")
async def create_product(request: Request):
    return await proxy_request(CATALOG_SERVICE_URL, "/products", request)

@app.get("/api/product/{product_code}")
async def get_product(product_code: str, request: Request):
    return await proxy_request(CATALOG_SERVICE_URL, f"/product/{product_code}", request)

@app.put("/api/product/{product_code}")
async def update_product(product_code: str, request: Request):
    return await proxy_request(CATALOG_SERVICE_URL, f"/product/{product_code}", request)

@app.delete("/api/product/{product_code}")
async def delete_product(product_code: str, request: Request):
    return await proxy_request(CATALOG_SERVICE_URL, f"/product/{product_code}", request)


# ==================== Supplier Endpoints ====================
@app.get("/api/suppliers")
async def get_suppliers(request: Request, start: Optional[int] = 1, limit: Optional[int] = None):
    return await proxy_request(CATALOG_SERVICE_URL, "/suppliers", request, {"start": start, "limit": limit})

@app.post("/api/suppliers")
async def create_supplier(request: Request):
    return await proxy_request(CATALOG_SERVICE_URL, "/suppliers", request)

@app.get("/api/supplier/{id}")
async def get_supplier(id: int, request: Request):
    return await proxy_request(CATALOG_SERVICE_URL, f"/supplier/{id}", request)

@app.put("/api/supplier/{id}")
async def update_supplier(id: int, request: Request):
    return await proxy_request(CATALOG_SERVICE_URL, f"/supplier/{id}", request)

@app.delete("/api/supplier/{id}")
async def delete_supplier(id: int, request: Request):
    return await proxy_request(CATALOG_SERVICE_URL, f"/supplier/{id}", request)

@app.get("/api/suppliers/{city}")
async def get_suppliers_by_city(city: str, request: Request):
    return await proxy_request(CATALOG_SERVICE_URL, f"/suppliers/{city}", request)

@app.get("/api/supplier/{id}/products")
async def get_supplier_products(id: int, request: Request):
    return await proxy_request(CATALOG_SERVICE_URL, f"/supplier/{id}/products", request)


# ==================== Customer Endpoints ====================
@app.get("/api/customers")
async def get_customers(request: Request, start: Optional[int] = 1, limit: Optional[int] = None):
    return await proxy_request(CATALOG_SERVICE_URL, "/customers", request, {"start": start, "limit": limit})

@app.post("/api/customers")
async def create_customer(request: Request):
    return await proxy_request(CATALOG_SERVICE_URL, "/customers", request)

@app.get("/api/customer/{id}")
async def get_customer(id: int, request: Request):
    return await proxy_request(CATALOG_SERVICE_URL, f"/customer/{id}", request)

@app.put("/api/customer/{id}")
async def update_customer(id: int, request: Request):
    return await proxy_request(CATALOG_SERVICE_URL, f"/customer/{id}", request)

@app.delete("/api/customer/{id}")
async def delete_customer(id: int, request: Request):
    return await proxy_request(CATALOG_SERVICE_URL, f"/customer/{id}", request)

@app.get("/api/customers/{city}")
async def get_customers_by_city(city: str, request: Request):
    return await proxy_request(CATALOG_SERVICE_URL, f"/customers/{city}", request)


# ==================== Warehouse Endpoints ====================
@app.get("/api/warehouses")
async def get_warehouses(request: Request, start: Optional[int] = 1, limit: Optional[int] = None):
    return await proxy_request(CATALOG_SERVICE_URL, "/warehouses", request, {"start": start, "limit": limit})

@app.post("/api/warehouses")
async def create_warehouse(request: Request):
    return await proxy_request(CATALOG_SERVICE_URL, "/warehouses", request)

@app.get("/api/warehouse/{id}")
async def get_warehouse(id: int, request: Request):
    return await proxy_request(CATALOG_SERVICE_URL, f"/warehouse/{id}", request)

@app.put("/api/warehouse/{id}")
async def update_warehouse(id: int, request: Request):
    return await proxy_request(CATALOG_SERVICE_URL, f"/warehouse/{id}", request)

@app.delete("/api/warehouse/{id}")
async def delete_warehouse(id: int, request: Request):
    return await proxy_request(CATALOG_SERVICE_URL, f"/warehouse/{id}", request)

@app.get("/api/warehouses/{city}")
async def get_warehouses_by_city(city: str, request: Request):
    return await proxy_request(CATALOG_SERVICE_URL, f"/warehouses/{city}", request)

@app.get("/api/warehouse/{id}/customers")
async def get_warehouse_customers(id: int, request: Request):
    return await proxy_request(CATALOG_SERVICE_URL, f"/warehouse/{id}/customers", request)


# ==================== Storage Endpoints ====================
@app.get("/api/storages")
async def get_storages(request: Request, start: Optional[int] = 1, limit: Optional[int] = None):
    return await proxy_request(CATALOG_SERVICE_URL, "/storages", request, {"start": start, "limit": limit})

@app.post("/api/storages")
async def create_storage(request: Request):
    return await proxy_request(CATALOG_SERVICE_URL, "/storages", request)

@app.get("/api/storage/{product_code}/{warehouse_name}")
async def get_storage(product_code: str, warehouse_name: str, request: Request):
    return await proxy_request(CATALOG_SERVICE_URL, f"/storage/{product_code}/{warehouse_name}", request)

@app.put("/api/storage/{product_code}/{warehouse_name}/{type}")
async def update_storage(product_code: str, warehouse_name: str, type: str, request: Request):
    return await proxy_request(CATALOG_SERVICE_URL, f"/storage/{product_code}/{warehouse_name}/{type}", request)

@app.get("/api/storages/product/{product_code}")
async def get_storages_by_product(product_code: str, request: Request):
    return await proxy_request(CATALOG_SERVICE_URL, f"/storages/product/{product_code}", request)

@app.get("/api/storages/warehouse/{warehouse_name}")
async def get_storages_by_warehouse(warehouse_name: str, request: Request):
    return await proxy_request(CATALOG_SERVICE_URL, f"/storages/warehouse/{warehouse_name}", request)


# ==================== Supply Transaction Endpoints ====================
@app.get("/api/supplytransactions")
async def get_supply_transactions(request: Request, start: Optional[int] = 1, limit: Optional[int] = None):
    return await proxy_request(SUPPLY_TRANSACTION_SERVICE_URL, "/supplytransactions", request, {"start": start, "limit": limit})

@app.post("/api/supplytransactions")
async def create_supply_transaction(request: Request):
    return await proxy_request(SUPPLY_TRANSACTION_SERVICE_URL, "/supplytransactions", request)

@app.get("/api/supplytransactions/product/{product_code}")
async def get_supply_transactions_by_product(product_code: str, request: Request):
    return await proxy_request(SUPPLY_TRANSACTION_SERVICE_URL, f"/supplytransactions/product/{product_code}", request)

@app.get("/api/supplytransactions/supplier/{supplier_name}")
async def get_supply_transactions_by_supplier(supplier_name: str, request: Request):
    return await proxy_request(SUPPLY_TRANSACTION_SERVICE_URL, f"/supplytransactions/supplier/{supplier_name}", request)

@app.get("/api/supplytransactions/product_supplier/{product_code}/{supplier_name}")
async def get_supply_transactions_by_product_and_supplier(product_code: str, supplier_name: str, request: Request):
    return await proxy_request(SUPPLY_TRANSACTION_SERVICE_URL, f"/supplytransactions/product_suplier/{product_code}/{supplier_name}", request)


# ==================== Customer Transaction Endpoints ====================
@app.get("/api/customertransactions")
async def get_customer_transactions(request: Request, start: Optional[int] = 1, limit: Optional[int] = None):
    return await proxy_request(CUSTOMER_TRANSACTION_SERVICE_URL, "/customertransactions", request, {"start": start, "limit": limit})

@app.post("/api/customertransactions")
async def create_customer_transaction(request: Request):
    return await proxy_request(CUSTOMER_TRANSACTION_SERVICE_URL, "/customertransactions", request)

@app.get("/api/customertransactions/product/{product_code}")
async def get_customer_transactions_by_product(product_code: str, request: Request):
    return await proxy_request(CUSTOMER_TRANSACTION_SERVICE_URL, f"/customertransactions/product/{product_code}", request)

@app.get("/api/customertransactions/customer/{customer_name}")
async def get_customer_transactions_by_customer(customer_name: str, request: Request):
    return await proxy_request(CUSTOMER_TRANSACTION_SERVICE_URL, f"/customertransactions/customer/{customer_name}", request)

@app.get("/api/customertransactions/product_customer/{product_code}/{customer_name}")
async def get_customer_transactions_by_product_and_customer(product_code: str, customer_name: str, request: Request):
    return await proxy_request(CUSTOMER_TRANSACTION_SERVICE_URL, f"/customertransactions/product_customer/{product_code}/{customer_name}", request)


# Cleanup on shutdown
@app.on_event("shutdown")
async def shutdown_event():
    await client.aclose()
