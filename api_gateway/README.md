# API Gateway

FastAPI-based API Gateway that provides a single entry point for all inventory microservices.

## Features
- Unified API endpoint for all microservices
- CORS support for frontend integration
- Automatic OpenAPI documentation at `/docs`
- Health check endpoint

## Endpoints

All endpoints are prefixed with `/api`:

- **Products**: `/api/products`, `/api/product/{code}`
- **Suppliers**: `/api/suppliers`, `/api/supplier/{id}`
- **Customers**: `/api/customers`, `/api/customer/{id}`
- **Warehouses**: `/api/warehouses`, `/api/warehouse/{id}`
- **Storages**: `/api/storages`, `/api/storage/{product_code}/{warehouse_name}`
- **Supply Transactions**: `/api/supplytransactions`
- **Customer Transactions**: `/api/customertransactions`

## Running

```bash
docker-compose up api_gateway
```

Access documentation at: `http://localhost:8000/docs`
