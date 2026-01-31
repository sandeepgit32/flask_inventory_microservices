from fastapi import FastAPI, HTTPException, Request, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
from typing import Optional
from config import (
    AUTH_SERVICE_URL,
    SUPPLIER_SERVICE_URL,
    CUSTOMER_SERVICE_URL,
    PRODUCT_SERVICE_URL,
    INVENTORY_SERVICE_URL,
    PROCUREMENT_SERVICE_URL,
    ORDER_SERVICE_URL
)

app = FastAPI(
    title="Inventory Microservices API Gateway",
    description="Single entry point for all inventory microservices",
    version="2.0.0"
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


async def verify_token(authorization: Optional[str] = Header(None)):
    """JWT token verification middleware"""
    # Skip auth for public endpoints
    if not authorization:
        return None
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    token = authorization.split(" ")[1]
    
    try:
        # Validate token with auth service
        response = await client.post(
            f"{AUTH_SERVICE_URL}/auth/validate",
            json={"token": token},
            timeout=5.0
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("valid"):
                return result.get("payload")
        
        raise HTTPException(status_code=401, detail="Invalid or expired token")
        
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Auth service unavailable: {str(e)}")


async def proxy_request(service_url: str, path: str, request: Request, params: dict = None):
    """Generic proxy function to forward requests to microservices"""
    url = f"{service_url}{path}"
    
    # Forward Authorization header if present
    headers = {}
    if "authorization" in request.headers:
        headers["Authorization"] = request.headers["authorization"]
    
    try:
        if request.method == "GET":
            response = await client.get(url, params=params, headers=headers)
        elif request.method == "POST":
            body = await request.json()
            response = await client.post(url, json=body, params=params, headers=headers)
        elif request.method == "PUT":
            body = await request.json()
            response = await client.put(url, json=body, params=params, headers=headers)
        elif request.method == "DELETE":
            response = await client.delete(url, params=params, headers=headers)
        else:
            raise HTTPException(status_code=405, detail="Method not allowed")
        
        return JSONResponse(content=response.json(), status_code=response.status_code)
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")


# ==================== Health Check ====================
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "api_gateway", "version": "2.0.0"}


# ==================== Auth Endpoints (Public - No Auth Required) ====================
@app.post("/api/auth/register")
async def register(request: Request):
    return await proxy_request(AUTH_SERVICE_URL, "/auth/register", request)

@app.post("/api/auth/login")
async def login(request: Request):
    return await proxy_request(AUTH_SERVICE_URL, "/auth/login", request)

@app.post("/api/auth/validate")
async def validate_token_endpoint(request: Request):
    return await proxy_request(AUTH_SERVICE_URL, "/auth/validate", request)


# ==================== Product Endpoints ====================
@app.get("/api/products")
async def get_products(request: Request, start: Optional[int] = 0, limit: Optional[int] = 50, user=Depends(verify_token)):
    return await proxy_request(PRODUCT_SERVICE_URL, "/products", request, {"start": start, "limit": limit})

@app.post("/api/products")
async def create_product(request: Request, user=Depends(verify_token)):
    return await proxy_request(PRODUCT_SERVICE_URL, "/products", request)

@app.get("/api/products/{product_id}")
async def get_product(product_id: int, request: Request, user=Depends(verify_token)):
    return await proxy_request(PRODUCT_SERVICE_URL, f"/products/{product_id}", request)

@app.put("/api/products/{product_id}")
async def update_product(product_id: int, request: Request, user=Depends(verify_token)):
    return await proxy_request(PRODUCT_SERVICE_URL, f"/products/{product_id}", request)

@app.delete("/api/products/{product_id}")
async def delete_product(product_id: int, request: Request, user=Depends(verify_token)):
    return await proxy_request(PRODUCT_SERVICE_URL, f"/products/{product_id}", request)


# ==================== Supplier Endpoints ====================
@app.get("/api/suppliers")
async def get_suppliers(request: Request, start: Optional[int] = 0, limit: Optional[int] = 50, user=Depends(verify_token)):
    return await proxy_request(SUPPLIER_SERVICE_URL, "/suppliers", request, {"start": start, "limit": limit})

@app.post("/api/suppliers")
async def create_supplier(request: Request, user=Depends(verify_token)):
    return await proxy_request(SUPPLIER_SERVICE_URL, "/suppliers", request)

@app.get("/api/suppliers/{supplier_id}")
async def get_supplier(supplier_id: int, request: Request, user=Depends(verify_token)):
    return await proxy_request(SUPPLIER_SERVICE_URL, f"/suppliers/{supplier_id}", request)

@app.put("/api/suppliers/{supplier_id}")
async def update_supplier(supplier_id: int, request: Request, user=Depends(verify_token)):
    return await proxy_request(SUPPLIER_SERVICE_URL, f"/suppliers/{supplier_id}", request)

@app.delete("/api/suppliers/{supplier_id}")
async def delete_supplier(supplier_id: int, request: Request, user=Depends(verify_token)):
    return await proxy_request(SUPPLIER_SERVICE_URL, f"/suppliers/{supplier_id}", request)

@app.get("/api/suppliers/city/{city}")
async def get_suppliers_by_city(city: str, request: Request, user=Depends(verify_token)):
    return await proxy_request(SUPPLIER_SERVICE_URL, f"/suppliers/city/{city}", request)


# ==================== Customer Endpoints ====================
@app.get("/api/customers")
async def get_customers(request: Request, start: Optional[int] = 0, limit: Optional[int] = 50, user=Depends(verify_token)):
    return await proxy_request(CUSTOMER_SERVICE_URL, "/customers", request, {"start": start, "limit": limit})

@app.post("/api/customers")
async def create_customer(request: Request, user=Depends(verify_token)):
    return await proxy_request(CUSTOMER_SERVICE_URL, "/customers", request)

@app.get("/api/customers/{customer_id}")
async def get_customer(customer_id: int, request: Request, user=Depends(verify_token)):
    return await proxy_request(CUSTOMER_SERVICE_URL, f"/customers/{customer_id}", request)

@app.put("/api/customers/{customer_id}")
async def update_customer(customer_id: int, request: Request, user=Depends(verify_token)):
    return await proxy_request(CUSTOMER_SERVICE_URL, f"/customers/{customer_id}", request)

@app.delete("/api/customers/{customer_id}")
async def delete_customer(customer_id: int, request: Request, user=Depends(verify_token)):
    return await proxy_request(CUSTOMER_SERVICE_URL, f"/customers/{customer_id}", request)

@app.get("/api/customers/city/{city}")
async def get_customers_by_city(city: str, request: Request, user=Depends(verify_token)):
    return await proxy_request(CUSTOMER_SERVICE_URL, f"/customers/city/{city}", request)


# ==================== Inventory Endpoints ====================
@app.get("/api/inventory")
@app.get("/api/storages")
async def get_inventory(request: Request, start: Optional[int] = 0, limit: Optional[int] = 50, user=Depends(verify_token)):
    return await proxy_request(INVENTORY_SERVICE_URL, "/storages", request, {"start": start, "limit": limit})

@app.post("/api/inventory")
@app.post("/api/storages")
async def create_storage(request: Request, user=Depends(verify_token)):
    return await proxy_request(INVENTORY_SERVICE_URL, "/storages", request)

@app.get("/api/inventory/{storage_id}")
@app.get("/api/storages/{storage_id}")
async def get_storage(storage_id: int, request: Request, user=Depends(verify_token)):
    return await proxy_request(INVENTORY_SERVICE_URL, f"/storages/{storage_id}", request)

@app.put("/api/inventory/{storage_id}")
@app.put("/api/storages/{storage_id}")
async def update_storage(storage_id: int, request: Request, user=Depends(verify_token)):
    return await proxy_request(INVENTORY_SERVICE_URL, f"/storages/{storage_id}", request)

@app.get("/api/inventory/product/{product_id}")
@app.get("/api/storages/product/{product_id}")
async def get_storage_by_product(product_id: int, request: Request, user=Depends(verify_token)):
    return await proxy_request(INVENTORY_SERVICE_URL, f"/storages/product/{product_id}", request)


# ==================== Procurement Endpoints ====================
@app.get("/api/procurements")
@app.get("/api/supplytransactions")
async def get_procurements(request: Request, start: Optional[int] = 0, limit: Optional[int] = 50, user=Depends(verify_token)):
    return await proxy_request(PROCUREMENT_SERVICE_URL, "/procurements", request, {"start": start, "limit": limit})

@app.post("/api/procurements")
@app.post("/api/supplytransactions")
async def create_procurement(request: Request, user=Depends(verify_token)):
    return await proxy_request(PROCUREMENT_SERVICE_URL, "/procurements", request)

@app.get("/api/procurements/product/{product_id}")
@app.get("/api/supplytransactions/product/{product_id}")
async def get_procurements_by_product(product_id: int, request: Request, user=Depends(verify_token)):
    return await proxy_request(PROCUREMENT_SERVICE_URL, f"/procurements/product/{product_id}", request)

@app.get("/api/procurements/supplier/{supplier_id}")
@app.get("/api/supplytransactions/supplier/{supplier_id}")
async def get_procurements_by_supplier(supplier_id: int, request: Request, user=Depends(verify_token)):
    return await proxy_request(PROCUREMENT_SERVICE_URL, f"/procurements/supplier/{supplier_id}", request)


# ==================== Order Endpoints ====================
@app.get("/api/orders")
@app.get("/api/customertransactions")
async def get_orders(request: Request, start: Optional[int] = 0, limit: Optional[int] = 50, user=Depends(verify_token)):
    return await proxy_request(ORDER_SERVICE_URL, "/orders", request, {"start": start, "limit": limit})

@app.post("/api/orders")
@app.post("/api/customertransactions")
async def create_order(request: Request, user=Depends(verify_token)):
    return await proxy_request(ORDER_SERVICE_URL, "/orders", request)

@app.get("/api/orders/product/{product_id}")
@app.get("/api/customertransactions/product/{product_id}")
async def get_orders_by_product(product_id: int, request: Request, user=Depends(verify_token)):
    return await proxy_request(ORDER_SERVICE_URL, f"/orders/product/{product_id}", request)

@app.get("/api/orders/customer/{customer_id}")
@app.get("/api/customertransactions/customer/{customer_id}")
async def get_orders_by_customer(customer_id: int, request: Request, user=Depends(verify_token)):
    return await proxy_request(ORDER_SERVICE_URL, f"/orders/customer/{customer_id}", request)


# Health check endpoint
@app.get("/health")
async def health():
    return {"status": "healthy", "service": "api_gateway"}


# Cleanup on shutdown
@app.on_event("shutdown")
async def shutdown_event():
    await client.aclose()

