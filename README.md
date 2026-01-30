# Flask Inventory Microservices

A microservices-based inventory management system built with Flask, featuring three independent services communicating via Redis message queue.

## Architecture Overview

```
                                    ┌─────────────────────┐
                                    │   Nginx Reverse     │
                                    │   Proxy (:8080)     │
                                    └──────────┬──────────┘
                                               │
              ┌────────────────────────────────┼────────────────────────────────┐
              │                                │                                │
              ▼                                ▼                                ▼
┌─────────────────────────┐    ┌─────────────────────────┐    ┌─────────────────────────┐
│   Catalog Service       │    │  Supply Transaction     │    │  Customer Transaction   │
│       (:5000)           │    │     Service (:5001)     │    │     Service (:5002)     │
│                         │    │                         │    │                         │
│  - Products             │    │  - Supply Transactions  │    │  - Customer             │
│  - Suppliers            │◄───│                         │    │    Transactions         │
│  - Customers            │    └───────────┬─────────────┘    └─────────────────────────┘
│  - Warehouses           │                │
│  - Storage              │                │ (Redis Queue)
│                         │◄───────────────┘
└─────────────────────────┘
         ▲
         │ (Consumer)
         │
┌─────────────────────────┐
│     Redis Queue         │
│       (:6379)           │
└─────────────────────────┘
```

The system consists of three microservices:

1. **Catalog Service** (`catalog/`) - Core catalog management
   - Manages Products, Suppliers, Customers, Warehouses, and Storage
   - Consumes messages from Redis queue to update storage quantities

2. **Supply Transaction Service** (`supply_transaction/`) - Supplier transactions
   - Records supply/purchase transactions from suppliers
   - Publishes messages to Redis queue when new supplies arrive to update inventory

3. **Customer Transaction Service** (`customer_transaction/`) - Customer transactions
   - Records customer sales transactions

## Tech Stack

- **Framework**: Flask, Flask-RESTful
- **Database**: SQLAlchemy (SQLite for development, MySQL for production)
- **Serialization**: Pydantic
- **Message Queue**: Redis (using Redis Lists)
- **Containerization**: Docker, Docker Compose
- **Reverse Proxy**: Nginx

## Project Structure

```
├── catalog/                      # Catalog microservice
│   ├── models/                   # SQLAlchemy models
│   │   ├── product.py           # Product model
│   │   ├── supplier.py          # Supplier model
│   │   ├── customer.py          # Customer model
│   │   ├── warehouse.py         # Warehouse model
│   │   └── storage.py           # Storage model
│   ├── resources/               # REST API endpoints
│   ├── schemas/                 # Pydantic schemas
│   ├── libs/                    # Utilities (pagination, strings)
│   ├── dummy_data/              # Sample data for testing
│   ├── consumer.py              # Redis queue consumer
│   ├── main.py                  # Application entry point
│   └── config.py                # Configuration settings
├── supply_transaction/           # Supply transaction microservice
│   ├── models/                  # Transaction model
│   ├── resources/               # REST API endpoints
│   ├── schemas/                 # Pydantic schemas
│   ├── producer.py              # Redis queue producer
│   └── app.py                   # Application entry point
├── customer_transaction/         # Customer transaction microservice
│   ├── models/                  # Transaction model
│   ├── resources/               # REST API endpoints
│   ├── schemas/                 # Pydantic schemas
│   └── main.py                  # Application entry point
├── message_queue/                # Message queue service (Redis)
│   ├── Dockerfile               # Redis Docker configuration
│   ├── redis.conf               # Redis server configuration
│   ├── config.py                # Python Redis configuration
│   ├── producer.py              # Message producer module
│   ├── consumer.py              # Message consumer module
│   └── .env                     # Environment variables
├── docker-compose.yml            # Main Docker Compose (all services)
├── nginx.conf                    # Nginx reverse proxy configuration
├── dockerrun.sh                  # Docker orchestration script
└── Inventory_microservices.postman_collection.json  # Postman API collection
```

## API Endpoints

### Catalog Service

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/products` | GET | List all products (paginated) |
| `/products` | POST | Create a new product |
| `/product/<product_code>` | GET | Get product by code |
| `/product/<product_code>` | PUT | Update product |
| `/product/<product_code>` | DELETE | Delete product |
| `/suppliers` | GET | List all suppliers (paginated) |
| `/suppliers` | POST | Create a new supplier |
| `/suppliers/<city>` | GET | Filter suppliers by city |
| `/supplier/<id>` | GET | Get supplier by ID |
| `/supplier/<id>` | PUT | Update supplier |
| `/supplier/<id>` | DELETE | Delete supplier |
| `/supplier/<id>/products` | GET | List products by supplier |
| `/customers` | GET | List all customers (paginated) |
| `/customers` | POST | Create a new customer |
| `/customers/<city>` | GET | Filter customers by city |
| `/customer/<id>` | GET | Get customer by ID |
| `/customer/<id>` | PUT | Update customer |
| `/customer/<id>` | DELETE | Delete customer |
| `/warehouses` | GET | List all warehouses (paginated) |
| `/warehouses` | POST | Create a new warehouse |
| `/warehouses/<city>` | GET | Filter warehouses by city |
| `/warehouse/<id>` | GET | Get warehouse by ID |
| `/warehouse/<id>` | PUT | Update warehouse |
| `/warehouse/<id>` | DELETE | Delete warehouse |
| `/warehouse/<id>/customers` | GET | List customers by warehouse |
| `/storages` | GET | List all storage records (paginated) |
| `/storages` | POST | Create a storage record |
| `/storage/<product_code>/<warehouse_name>` | GET | Get storage by product and warehouse |
| `/storage/<product_code>/<warehouse_name>/<type>` | PUT | Update storage (type: insert/update) |
| `/storages/product/<product_code>` | GET | Filter storage by product |
| `/storages/warehouse/<warehouse_name>` | GET | Filter storage by warehouse |

### Supply Transaction Service

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/supplytransactions` | GET | List all supply transactions (paginated) |
| `/supplytransactions` | POST | Create a supply transaction |
| `/supplytransactions/product/<product_code>` | GET | Filter by product |
| `/supplytransactions/supplier/<supplier_name>` | GET | Filter by supplier |
| `/supplytransactions/product_suplier/<product_code>/<supplier_name>` | GET | Filter by product and supplier |

### Customer Transaction Service

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/customertransactions` | GET | List all customer transactions (paginated) |
| `/customertransactions` | POST | Create a customer transaction |
| `/customertransactions/product/<product_code>` | GET | Filter by product |
| `/customertransactions/customer/<customer_name>` | GET | Filter by customer |
| `/customertransactions/product_customer/<product_code>/<customer_name>` | GET | Filter by product and customer |

### Pagination

All list endpoints support pagination with query parameters:
- `start`: Starting index (default: 1)
- `limit`: Number of results per page

Example: `/products?start=1&limit=10`

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Python 3.8+ (for local development)

### Running with Docker

All services are managed through a single `docker-compose.yml` file.

1. **Build and start all services:**
   ```bash
   ./dockerrun.sh up --build
   ```

   Or using docker-compose directly:
   ```bash
   docker-compose up --build -d
   ```

2. **View service status:**
   ```bash
   ./dockerrun.sh status
   ```

3. **View logs:**
   ```bash
   # All services
   ./dockerrun.sh logs
   
   # Specific service
   ./dockerrun.sh logs inventory_api
   ```

4. **Stop all services:**
   ```bash
   ./dockerrun.sh down
   ```

5. **Stop and remove volumes (clean):**
   ```bash
   ./dockerrun.sh clean
   ```

### Running Locally (Development)

1. **Install dependencies for each service:**
   ```bash
   cd catalog && pip install -r requirements.txt
   cd ../supply_transaction && pip install -r requirements.txt
   cd ../customer_transaction && pip install -r requirements.txt
   ```

2. **Start Redis:**
   ```bash
   docker run -d --name redis_queue -p 6379:6379 redis:7-alpine
   ```

3. **Run each service in separate terminals:**
   ```bash
   # Terminal 1: Catalog Service
   cd catalog && python main.py
   
   # Terminal 2: Supply Transaction Service
   cd supply_transaction && python app.py
   
   # Terminal 3: Customer Transaction Service
   cd customer_transaction && python main.py
   
   # Terminal 4: Redis Queue Consumer (for catalog updates)
   cd catalog && python consumer.py
   ```

### Loading Sample Data

Each service includes dummy data that can be loaded using the upload scripts:

```bash
cd catalog/dummy_data && ./upload.sh
cd supply_transaction/dummy_data && ./upload.sh
cd customer_transaction/dummy_data && ./upload.sh
```

## Service Ports

| Service | Internal Port | External Port (via Nginx) |
|---------|--------------|---------------------------|
| Nginx Reverse Proxy | 80 | 8080 |
| Redis Queue | 6379 | 6379 |
| Catalog API | 5000 | Via Nginx |
| Supply Transaction API | 5000 | Via Nginx |
| Customer Transaction API | 5000 | Via Nginx |

## Message Queue Flow

When a supply transaction is created:
1. The Supply Transaction Service records the transaction in its database
2. It publishes a message to Redis queue with product code, warehouse name, and quantity
3. The Catalog Service's consumer picks up the message from the Redis list
4. The storage quantity is updated in the Catalog database

### Message Queue Configuration

The message queue service is configured via `message_queue/.env`:

| Variable | Description | Default |
|----------|-------------|---------|
| `REDIS_HOST` | Redis server hostname | `redis_queue` |
| `REDIS_PORT` | Redis server port | `6379` |
| `REDIS_PASSWORD` | Redis password (optional) | `None` |
| `REDIS_QUEUE_NAME` | Name of the queue | `catalog_updates` |

## Environment Configuration

Each service supports development and production configurations via `config.py`:
- **Development**: SQLite database, debug mode enabled
- **Production**: MySQL database, debug mode disabled

Set the environment using the `FLASK_ENV` environment variable.

## API Testing

Import the Postman collection `Inventory_microservices.postman_collection.json` to test all API endpoints.

## References

- [Docker Compose Nginx Reverse Proxy Multiple Containers](https://www.bogotobogo.com/DevOps/Docker/Docker-Compose-Nginx-Reverse-Proxy-Multiple-Containers.php)

## License

This project is open source and available under the MIT License.
