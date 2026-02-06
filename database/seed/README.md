# Database Seed Scripts

This folder contains scripts to populate the inventory database with sample/fake data for testing and development.

## Files

- `seed_data.py` - Main Python script that inserts sample data
- `seed.sh` - Bash wrapper script that checks dependencies and runs the seeder
- `requirements.txt` - Python package dependencies

## Prerequisites

```bash
pip install -r requirements.txt
```

Or install manually:
```bash
pip install mysql-connector-python faker
```

## Usage

### Using the Bash Script (Recommended)

```bash
# Make the script executable
chmod +x seed.sh

# Run with default settings (localhost:32000)
./seed.sh

# Clear data only (no seeding)
./seed.sh --clear-only

# Generate extra fake data
./seed.sh --extra-customers 20 --extra-suppliers 10

# Custom connection
./seed.sh --host localhost --port 32000 --user admin --password 123456
```

### Using Python Directly

```bash
# Default settings
python seed_data.py

# Custom connection
python seed_data.py --host localhost --port 32000 --database inventory_db

# Show help
python seed_data.py --help
```

## Options

| Option | Default | Description |
|--------|---------|-------------|
| `--host` | localhost | MySQL host |
| `--port` | 32000 | MySQL port |
| `--user` | admin | MySQL user |
| `--password` | 123456 | MySQL password |
| `--database` | inventory_db | Database name |
| `--clear-only` | false | Only clear data, don't seed |
| `--no-clear` | false | Don't clear existing data |
| `--extra-customers` | 0 | Generate additional fake customers |
| `--extra-suppliers` | 0 | Generate additional fake suppliers |
| `--procurements` | 20 | Number of procurements |
| `--orders` | 30 | Number of orders |

## Environment Variables

The script also reads from environment variables (can be set in `../env`):

- `MYSQL_HOST`
- `MYSQL_PORT`
- `MYSQL_USER`
- `MYSQL_PASSWORD`
- `MYSQL_DATABASE`

## Sample Data

The script inserts:

### Core Data
- 5 warehouses (Main_Warehouse, WS1-WS4)
- 5 suppliers
- 10 customers
- 8 products (sports, watches, electronics categories)
- 24 storage records (product inventory in warehouses)

### Transactions
- 20 procurements (purchases from suppliers)
- 30 customer transactions (sales to customers)

### Generated with Faker
- Additional random customers and suppliers can be generated using `--extra-customers` and `--extra-suppliers`

## Example Output

```
============================================================
🌱 Inventory Database Seed Script
============================================================
✓ Connected to MySQL database: inventory_db@localhost:32000

🗑️  Clearing existing data...
  ✓ Cleared orders
  ✓ Cleared procurements
  ✓ Cleared storages
  ✓ Cleared products
  ✓ Cleared customers
  ✓ Cleared suppliers
  ✓ Cleared warehouses

📦 Seeding warehouses...
  ✓ Inserted 5 warehouses

🏭 Seeding suppliers...
  ✓ Inserted 5 suppliers

👥 Seeding customers...
  ✓ Inserted 10 customers

📱 Seeding products...
  ✓ Inserted 8 products

🏪 Seeding storages...
  ✓ Inserted 24 storage records

📥 Seeding procurements (20 records)...
  ✓ Inserted 20 procurements

📤 Seeding orders (30 records)...
  ✓ Inserted 30 orders

============================================================
✅ Database seeding completed successfully!
============================================================
🔌 Database connection closed
```
