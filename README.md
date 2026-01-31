# Flask Inventory Microservices

A modern microservices-based inventory management system built with Flask, FastAPI, Vue 3, Redis, and MySQL.

## 📖 Documentation

**⚠️ This project has been restructured into a complete microservices architecture.**

Please refer to **[MICROSERVICES_README.md](./MICROSERVICES_README.md)** for complete documentation including:

- Architecture overview (7 microservices)
- Database schema and migration guide
- Event-driven communication patterns
- API endpoints and authentication
- Docker Compose setup
- Development and deployment guides

## Quick Start

```bash
# 1. Apply database migration
mysql -h localhost -P 32000 -u root -proot inventory_db < database/migration/001_microservices_restructure.sql

# 2. Start all services
docker-compose up --build

# 3. Access the application
# Frontend: http://localhost:8080
# API Gateway: http://localhost:8000
```

## Tech Stack

- **Backend**: Flask 3.0, FastAPI (API Gateway)
- **Frontend**: Vue 3, Tailwind CSS, Vite
- **Database**: MySQL 8.0
- **Message Queue**: Redis 5.0 (Pub/Sub)
- **Authentication**: JWT (PyJWT 2.8.0, bcrypt 4.1.2)
- **Containerization**: Docker, Docker Compose

## Architecture

The system follows a microservices architecture with:

- **7 Independent Services**: Auth, Product, Supplier, Customer, Inventory, Procurement, Order
- **Event-Driven Communication**: Redis pub/sub for eventual consistency
- **Circuit Breaker Pattern**: Prevents cascading failures
- **API Gateway**: Single entry point with JWT authentication
- **Single Warehouse Model**: Simplified inventory management

## Features

✅ JWT authentication with 6-hour token expiry  
✅ Event-driven architecture for stock updates  
✅ Circuit breaker for resilient service calls  
✅ Redis caching with TTL management  
✅ Supervised consumer processes with auto-restart  
✅ Health checks for all services  
✅ Normalized database schema with ID-based relationships  
✅ Modern Vue 3 frontend with authentication  

## Services

| Service | Port | Description |
|---------|------|-------------|
| Frontend | 8080 | Vue 3 web application |
| API Gateway | 8000 | FastAPI reverse proxy with JWT |
| Auth | 5003 | User authentication & JWT tokens |
| Product | 5000 | Product management with suppliers |
| Supplier | 5004 | Supplier CRUD operations |
| Customer | 5005 | Customer CRUD operations |
| Inventory | 5006 | Stock management & alerts |
| Procurement | 5001 | Purchase orders from suppliers |
| Order | 5002 | Sales orders to customers |

## License

MIT
