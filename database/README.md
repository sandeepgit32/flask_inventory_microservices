# Database Service

This is the centralized database service for the Inventory Microservices application. It provides a single MySQL database instance with separate tables for different services.

## Structure

```
database/
├── Dockerfile          # Docker configuration for MySQL
├── .env               # Environment variables (do not commit to version control)
├── .env.example       # Example environment variables
├── init/              # Initialization scripts
│   └── 01-create-databases.sql  # SQL script to create all tables
├── seed/              # Data seeding scripts
│   ├── seed_data.py   # Python script to populate with sample data
│   ├── seed.sh        # Bash wrapper script
│   ├── requirements.txt
│   └── README.md
└── README.md          # This file
```

## Tables

The database contains tables for three services:

### Catalog Service Tables
- `customers` - Customer information (name, city, contact details, warehouse reference)
- `suppliers` - Supplier information (name, city, contact details)
- `warehouses` - Warehouse locations
- `products` - Product catalog with supplier references (product_code, name, prices, etc.)
- `storages` - Product inventory in warehouses (product_code, warehouse_name, quantity)

### Procurement Service Tables
- `procurements` - Records of supplies received from suppliers

### Order Service Tables
- `orders` - Records of sales to customers

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MYSQL_ROOT_PASSWORD` | MySQL root password | root |
| `MYSQL_USER` | Application database user | admin |
| `MYSQL_PASSWORD` | Application user password | 123456 |
| `MYSQL_HOST` | Database hostname | inventory_db_host |
| `MYSQL_PORT` | Database port | 3306 |
| `MYSQL_DATABASE` | Database name | inventory_db |

## Usage

The database is automatically started with docker-compose:

```bash
docker-compose up -d inventory_db
```

### Connecting to the Database

From host machine:
```bash
mysql -h localhost -P 32000 -u admin -p inventory_db
```

From within Docker network:
```bash
mysql -h inventory_db_host -P 3306 -u admin -p inventory_db
```

## Initialization

The `init/01-create-databases.sql` script runs automatically when the container is first created. It:
1. Creates the `inventory_db` database
2. Grants privileges to the admin user
3. Creates all necessary tables with proper relationships
4. Sets up indexes for query optimization

## Data Persistence

Database data is persisted in the `inventory-db-vol` Docker volume.

## Notes

- The init scripts only run on first container creation
- To re-run init scripts, remove the volume: `docker volume rm flask_inventory_microservices_inventory-db-vol`
- Foreign key constraints are not enforced across microservice boundaries (e.g., transactions reference product_id but don't have FK to products table)

## Seeding Sample Data

After the database is running, you can populate it with sample data:

```bash
cd seed/
pip install -r requirements.txt
python seed_data.py --host localhost --port 32000
```

Or use the convenience script:
```bash
cd seed/
chmod +x seed.sh
./seed.sh
```

See `seed/README.md` for more options.
