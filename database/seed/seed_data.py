#!/usr/bin/env python3
"""
Database Seed Script for Inventory Microservices

This script populates the inventory_db database with sample/fake data
for testing and development purposes.

Usage:
    python seed_data.py [--host HOST] [--port PORT] [--user USER] [--password PASSWORD] [--database DATABASE]

Environment Variables (optional):
    MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE

Requirements:
    pip install mysql-connector-python faker
"""

import argparse
import os
import sys
from datetime import datetime, timedelta
import random

try:
    import mysql.connector
    from mysql.connector import Error
except ImportError:
    print("Error: mysql-connector-python is required. Install it with: pip install mysql-connector-python")
    sys.exit(1)

try:
    from faker import Faker
except ImportError:
    print("Error: faker is required. Install it with: pip install faker")
    sys.exit(1)

fake = Faker('en_IN')  # Use Indian locale for realistic data

# ============================================
# Sample Data
# ============================================

WAREHOUSES = [
    {"name": "Main_Warehouse", "city": "Mumbai"},
    {"name": "WS1", "city": "Nashik"},
    {"name": "WS2", "city": "Mumbai"},
    {"name": "WS3", "city": "Pune"},
    {"name": "WS4", "city": "Pune"},
]

SUPPLIERS = [
    {
        "name": "Sen Sports",
        "city": "Mumbai",
        "zipcode": "700067",
        "contact_person": "Mr. X",
        "phone": "99999-99999",
        "email": "mr.x@email.com"
    },
    {
        "name": "Ash_Watches",
        "city": "Mumbai",
        "zipcode": "347274",
        "contact_person": "Mr. Y",
        "phone": "99999-99998",
        "email": "mr.y@email.com"
    },
    {
        "name": "Ash_Motors",
        "city": "Mumbai",
        "zipcode": "347274",
        "contact_person": "Mr. Z",
        "phone": "99999-99998",
        "email": "mr.z@email.com"
    },
    {
        "name": "TechGadgets Ltd",
        "city": "Bangalore",
        "zipcode": "560001",
        "contact_person": "Raj Kumar",
        "phone": "98765-43210",
        "email": "raj@techgadgets.com"
    },
    {
        "name": "FashionHub",
        "city": "Delhi",
        "zipcode": "110001",
        "contact_person": "Priya Sharma",
        "phone": "98765-12345",
        "email": "priya@fashionhub.in"
    },
]

PRODUCTS = [
    {
        "product_code": "nb_bat",
        "name": "NB cricket bat",
        "category": "sports",
        "price_buy": 899,
        "price_sell": 1099,
        "measure_unit": "qty",
        "supplier_name": "Sen Sports"
    },
    {
        "product_code": "dc_ball",
        "name": "DUCE Ball",
        "category": "sports",
        "price_buy": 199,
        "price_sell": 299,
        "measure_unit": "qty",
        "supplier_name": "Sen Sports"
    },
    {
        "product_code": "foss_ch_men",
        "name": "Fossil Chronograph Mens Watch",
        "category": "watches",
        "price_buy": 4199,
        "price_sell": 4599,
        "measure_unit": "qty",
        "supplier_name": "Ash_Watches"
    },
    {
        "product_code": "ss_gloves",
        "name": "SS Batting Gloves",
        "category": "sports",
        "price_buy": 450,
        "price_sell": 599,
        "measure_unit": "qty",
        "supplier_name": "Sen Sports"
    },
    {
        "product_code": "casio_gshock",
        "name": "Casio G-Shock Watch",
        "category": "watches",
        "price_buy": 6500,
        "price_sell": 7999,
        "measure_unit": "qty",
        "supplier_name": "Ash_Watches"
    },
    {
        "product_code": "helmet_pro",
        "name": "Pro Cricket Helmet",
        "category": "sports",
        "price_buy": 1200,
        "price_sell": 1599,
        "measure_unit": "qty",
        "supplier_name": "Sen Sports"
    },
    {
        "product_code": "bt_speaker",
        "name": "Bluetooth Speaker",
        "category": "electronics",
        "price_buy": 800,
        "price_sell": 1199,
        "measure_unit": "qty",
        "supplier_name": "TechGadgets Ltd"
    },
    {
        "product_code": "usb_cable",
        "name": "USB-C Cable 2m",
        "category": "electronics",
        "price_buy": 150,
        "price_sell": 299,
        "measure_unit": "qty",
        "supplier_name": "TechGadgets Ltd"
    },
]

CUSTOMERS = [
    {
        "name": "Ligula Nullam Feugiat LLP",
        "city": "Mumbai",
        "zipcode": "046211",
        "contact_person": "Macy Merritt",
        "phone": "9180739405",
        "email": "ornare.ligula@elitpretiumet.net",
        "warehouse_id": 1
    },
    {
        "name": "Lorem Ipsum Sodales Corporation",
        "city": "Mumbai",
        "zipcode": "43761",
        "contact_person": "Sage Gonzalez",
        "phone": "9278695929",
        "email": "at.augue.id@felisrviverra.ca",
        "warehouse_id": 2
    },
    {
        "name": "Mattis Velit Ltd",
        "city": "Pune",
        "zipcode": "45336",
        "contact_person": "Kirk Schwartz",
        "phone": "9598843913",
        "email": "consectetuer@Quisque.net",
        "warehouse_id": 3
    },
    {
        "name": "Parturient Montes Corp.",
        "city": "Nashik",
        "zipcode": "59-422",
        "contact_person": "Chastity Lancaster",
        "phone": "9797403307",
        "email": "orci.luctus.et@Seddictum.org",
        "warehouse_id": 4
    },
    {
        "name": "Bibendum Sed Est Limited",
        "city": "Pune",
        "zipcode": "18596",
        "contact_person": "Serina Whitney",
        "phone": "9687916010",
        "email": "a@loremvehicula.edu",
        "warehouse_id": 5
    },
    {
        "name": "Lectus Convallis LLP",
        "city": "Mumbai",
        "zipcode": "08106-343",
        "contact_person": "MacKensie Peck",
        "phone": "9405748872",
        "email": "non.enim.Mauris@leo.net",
        "warehouse_id": 1
    },
    {
        "name": "In Tempus PC",
        "city": "Nashik",
        "zipcode": "325288",
        "contact_person": "Hu Byrd",
        "phone": "9214864824",
        "email": "aliquam.iaculis@fringugiat.org",
        "warehouse_id": 2
    },
    {
        "name": "Ipsum Incorporated",
        "city": "Pune",
        "zipcode": "411001",
        "contact_person": "Zephania Mccray",
        "phone": "9014572562",
        "email": "inceptos@arcuimperdiet.co.uk",
        "warehouse_id": 3
    },
    {
        "name": "Eu PC",
        "city": "Pune",
        "zipcode": "78-951",
        "contact_person": "Idona Walton",
        "phone": "9394713019",
        "email": "sit@ligulaelit.co.uk",
        "warehouse_id": 4
    },
    {
        "name": "Curae Ltd",
        "city": "Mumbai",
        "zipcode": "8868",
        "contact_person": "Burke Eaton",
        "phone": "9522609142",
        "email": "Nunc@molestieSedid.ca",
        "warehouse_id": 5
    },
]

STORAGES = [
    {"product_code": "nb_bat", "warehouse_name": "WS1", "quantity": 10},
    {"product_code": "dc_ball", "warehouse_name": "WS1", "quantity": 40},
    {"product_code": "foss_ch_men", "warehouse_name": "WS1", "quantity": 5},
    {"product_code": "nb_bat", "warehouse_name": "WS2", "quantity": 7},
    {"product_code": "dc_ball", "warehouse_name": "WS2", "quantity": 27},
    {"product_code": "foss_ch_men", "warehouse_name": "WS2", "quantity": 12},
    {"product_code": "nb_bat", "warehouse_name": "WS3", "quantity": 15},
    {"product_code": "dc_ball", "warehouse_name": "WS3", "quantity": 22},
    {"product_code": "foss_ch_men", "warehouse_name": "WS4", "quantity": 5},
    {"product_code": "nb_bat", "warehouse_name": "WS4", "quantity": 8},
    {"product_code": "dc_ball", "warehouse_name": "WS4", "quantity": 15},
    {"product_code": "foss_ch_men", "warehouse_name": "WS4", "quantity": 4},
    {"product_code": "nb_bat", "warehouse_name": "Main_Warehouse", "quantity": 50},
    {"product_code": "dc_ball", "warehouse_name": "Main_Warehouse", "quantity": 100},
    {"product_code": "foss_ch_men", "warehouse_name": "Main_Warehouse", "quantity": 25},
    {"product_code": "ss_gloves", "warehouse_name": "Main_Warehouse", "quantity": 30},
    {"product_code": "casio_gshock", "warehouse_name": "Main_Warehouse", "quantity": 15},
    {"product_code": "helmet_pro", "warehouse_name": "Main_Warehouse", "quantity": 20},
    {"product_code": "bt_speaker", "warehouse_name": "Main_Warehouse", "quantity": 40},
    {"product_code": "usb_cable", "warehouse_name": "Main_Warehouse", "quantity": 100},
    {"product_code": "ss_gloves", "warehouse_name": "WS1", "quantity": 12},
    {"product_code": "casio_gshock", "warehouse_name": "WS2", "quantity": 8},
    {"product_code": "helmet_pro", "warehouse_name": "WS3", "quantity": 6},
    {"product_code": "bt_speaker", "warehouse_name": "WS4", "quantity": 18},
]


def get_connection(host, port, user, password, database):
    """Create and return a MySQL database connection."""
    try:
        connection = mysql.connector.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )
        if connection.is_connected():
            print(f"✓ Connected to MySQL database: {database}@{host}:{port}")
            return connection
    except Error as e:
        print(f"✗ Error connecting to MySQL: {e}")
        sys.exit(1)


def clear_tables(cursor):
    """Clear all data from tables in correct order (respecting foreign keys)."""
    print("\n🗑️  Clearing existing data...")
    
    # Disable foreign key checks temporarily
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
    
    tables = [
        "orders",
        "procurements", 
        "storages",
        "products",
        "customers",
        "suppliers",
        "warehouses"
    ]
    
    for table in tables:
        try:
            cursor.execute(f"TRUNCATE TABLE {table}")
            print(f"  ✓ Cleared {table}")
        except Error as e:
            print(f"  ⚠ Warning clearing {table}: {e}")
    
    # Re-enable foreign key checks
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")


def seed_warehouses(cursor):
    """Insert warehouse data."""
    print("\n📦 Seeding warehouses...")
    sql = "INSERT INTO warehouses (name, city) VALUES (%s, %s)"
    for w in WAREHOUSES:
        cursor.execute(sql, (w['name'], w['city']))
    print(f"  ✓ Inserted {len(WAREHOUSES)} warehouses")


def seed_suppliers(cursor):
    """Insert supplier data."""
    print("\n🏭 Seeding suppliers...")
    sql = """INSERT INTO suppliers (name, city, zipcode, contact_person, phone, email) 
             VALUES (%s, %s, %s, %s, %s, %s)"""
    for s in SUPPLIERS:
        cursor.execute(sql, (s['name'], s['city'], s['zipcode'], 
                            s['contact_person'], s['phone'], s['email']))
    print(f"  ✓ Inserted {len(SUPPLIERS)} suppliers")


def seed_customers(cursor):
    """Insert customer data."""
    print("\n👥 Seeding customers...")
    sql = """INSERT INTO customers (name, city, zipcode, contact_person, phone, email, warehouse_id) 
             VALUES (%s, %s, %s, %s, %s, %s, %s)"""
    for c in CUSTOMERS:
        cursor.execute(sql, (c['name'], c['city'], c['zipcode'], 
                            c['contact_person'], c['phone'], c['email'], c['warehouse_id']))
    print(f"  ✓ Inserted {len(CUSTOMERS)} customers")


def seed_products(cursor):
    """Insert product data."""
    print("\n📱 Seeding products...")
    sql = """INSERT INTO products (product_code, name, category, price_buy, price_sell, measure_unit, supplier_name) 
             VALUES (%s, %s, %s, %s, %s, %s, %s)"""
    for p in PRODUCTS:
        cursor.execute(sql, (p['product_code'], p['name'], p['category'], 
                            p['price_buy'], p['price_sell'], p['measure_unit'], p['supplier_name']))
    print(f"  ✓ Inserted {len(PRODUCTS)} products")


def seed_storages(cursor):
    """Insert storage data."""
    print("\n🏪 Seeding storages...")
    sql = """INSERT INTO storages (product_code, warehouse_name, quantity) 
             VALUES (%s, %s, %s)"""
    for s in STORAGES:
        cursor.execute(sql, (s['product_code'], s['warehouse_name'], s['quantity']))
    print(f"  ✓ Inserted {len(STORAGES)} storage records")


def seed_procurements(cursor, num_transactions=20):
    """Insert procurement data using Faker."""
    print(f"\n📥 Seeding procurements ({num_transactions} records)...")
    
    sql = """INSERT INTO procurements 
             (timestamp, supplier_id, product_id, unit_price, quantity, total_cost) 
             VALUES (%s, %s, %s, %s, %s, %s)"""
    
    # Create a mapping of supplier to their products
    supplier_products = {}
    for p in PRODUCTS:
        supplier = p['supplier_name']
        if supplier not in supplier_products:
            supplier_products[supplier] = []
        supplier_products[supplier].append(p)
    
    count = 0
    for _ in range(num_transactions):
        supplier = random.choice(SUPPLIERS)
        
        # Get products for this supplier
        products_for_supplier = supplier_products.get(supplier['name'], [])
        if not products_for_supplier:
            continue
            
        product = random.choice(products_for_supplier)
        quantity = random.randint(5, 50)
        
        # Lookup supplier_id and product_id in DB
        cursor.execute("SELECT id FROM suppliers WHERE name=%s LIMIT 1", (supplier['name'],))
        sup_row = cursor.fetchone()
        if not sup_row:
            continue
        supplier_id = sup_row[0]

        cursor.execute("SELECT id, price_buy FROM products WHERE product_code=%s LIMIT 1", (product['product_code'],))
        prod_row = cursor.fetchone()
        if not prod_row:
            continue
        product_id, unit_price = prod_row

        total_cost = unit_price * quantity
        
        # Random date in the last 6 months
        days_ago = random.randint(1, 180)
        transaction_date = datetime.now() - timedelta(days=days_ago)
        
        cursor.execute(sql, (
            transaction_date.strftime('%Y-%m-%d'),
            supplier_id,
            product_id,
            unit_price,
            quantity,
            total_cost
        ))
        count += 1
    
    print(f"  ✓ Inserted {count} procurements")


def seed_orders(cursor, num_orders=30):
    """Insert order data using Faker."""
    print(f"\n📤 Seeding orders ({num_orders} records)...")
    
    sql = """INSERT INTO orders 
             (timestamp, customer_id, product_id, unit_price, quantity, total_cost) 
             VALUES (%s, %s, %s, %s, %s, %s)"""
    
    count = 0
    for _ in range(num_orders):
        # Pick a random existing customer id
        cursor.execute("SELECT id FROM customers ORDER BY RAND() LIMIT 1")
        cid_row = cursor.fetchone()
        customer_id = cid_row[0] if cid_row else None

        # Pick a random existing product id and its price
        cursor.execute("SELECT id, price_sell FROM products ORDER BY RAND() LIMIT 1")
        pid_row = cursor.fetchone()
        product_id = pid_row[0] if pid_row else None
        unit_price = pid_row[1] if pid_row and len(pid_row) > 1 else 0

        quantity = random.randint(1, 10)
        total_cost = unit_price * quantity

        # Random date in the last 6 months
        days_ago = random.randint(1, 180)
        transaction_date = datetime.now() - timedelta(days=days_ago)

        cursor.execute(sql, (
            transaction_date.strftime('%Y-%m-%d'),
            customer_id,
            product_id,
            unit_price,
            quantity,
            total_cost
        ))
        count += 1
    
    print(f"  ✓ Inserted {count} orders")


def generate_additional_fake_data(cursor, num_customers=10, num_suppliers=5):
    """Generate additional fake customers and suppliers using Faker."""
    print(f"\n🎲 Generating additional fake data...")
    
    cities = ["Mumbai", "Pune", "Nashik", "Bangalore", "Delhi", "Chennai", "Kolkata", "Hyderabad"]
    
    # Generate fake suppliers
    print(f"  Generating {num_suppliers} additional suppliers...")
    sql = """INSERT INTO suppliers (name, city, zipcode, contact_person, phone, email) 
             VALUES (%s, %s, %s, %s, %s, %s)"""
    for i in range(num_suppliers):
        cursor.execute(sql, (
            fake.company()[:100],
            random.choice(cities),
            fake.postcode()[:20],
            fake.name()[:80],
            fake.phone_number()[:20],
            fake.company_email()[:80]
        ))
    print(f"    ✓ Inserted {num_suppliers} additional suppliers")
    
    # Generate fake customers
    print(f"  Generating {num_customers} additional customers...")
    sql = """INSERT INTO customers (name, city, zipcode, contact_person, phone, email, warehouse_id) 
             VALUES (%s, %s, %s, %s, %s, %s, %s)"""
    for i in range(num_customers):
        cursor.execute(sql, (
            fake.company()[:80],
            random.choice(cities),
            fake.postcode()[:20],
            fake.name()[:80],
            fake.phone_number()[:20],
            fake.company_email()[:80],
            random.randint(1, len(WAREHOUSES))
        ))
    print(f"    ✓ Inserted {num_customers} additional customers")


def main():
    parser = argparse.ArgumentParser(
        description='Seed the inventory database with sample data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python seed_data.py
  python seed_data.py --host localhost --port 32000
  python seed_data.py --clear-only
  python seed_data.py --extra-customers 20 --extra-suppliers 10
        """
    )
    
    parser.add_argument('--host', default=os.getenv('MYSQL_HOST', 'localhost'),
                        help='MySQL host (default: localhost or MYSQL_HOST env)')
    parser.add_argument('--port', type=int, default=int(os.getenv('MYSQL_PORT', '32000')),
                        help='MySQL port (default: 32000 or MYSQL_PORT env)')
    parser.add_argument('--user', default=os.getenv('MYSQL_USER', 'admin'),
                        help='MySQL user (default: admin or MYSQL_USER env)')
    parser.add_argument('--password', default=os.getenv('MYSQL_PASSWORD', '123456'),
                        help='MySQL password (default: 123456 or MYSQL_PASSWORD env)')
    parser.add_argument('--database', default=os.getenv('MYSQL_DATABASE', 'inventory_db'),
                        help='MySQL database (default: inventory_db or MYSQL_DATABASE env)')
    parser.add_argument('--clear-only', action='store_true',
                        help='Only clear data without seeding')
    parser.add_argument('--no-clear', action='store_true',
                        help='Do not clear existing data before seeding')
    parser.add_argument('--extra-customers', type=int, default=0,
                        help='Number of additional fake customers to generate')
    parser.add_argument('--extra-suppliers', type=int, default=0,
                        help='Number of additional fake suppliers to generate')
    parser.add_argument('--procurements', type=int, default=20,
                        help='Number of procurements to generate (default: 20)')
    parser.add_argument('--orders', type=int, default=30,
                        help='Number of orders to generate (default: 30)')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🌱 Inventory Database Seed Script")
    print("=" * 60)
    
    connection = get_connection(args.host, args.port, args.user, args.password, args.database)
    cursor = connection.cursor()
    
    try:
        if not args.no_clear:
            clear_tables(cursor)
        
        if not args.clear_only:
            seed_warehouses(cursor)
            seed_suppliers(cursor)
            seed_customers(cursor)
            seed_products(cursor)
            seed_storages(cursor)
            seed_procurements(cursor, args.procurements)
            seed_orders(cursor, args.orders)
            
            if args.extra_customers > 0 or args.extra_suppliers > 0:
                generate_additional_fake_data(cursor, args.extra_customers, args.extra_suppliers)
        
        connection.commit()
        print("\n" + "=" * 60)
        print("✅ Database seeding completed successfully!")
        print("=" * 60)
        
    except Error as e:
        print(f"\n✗ Error during seeding: {e}")
        connection.rollback()
        sys.exit(1)
    finally:
        cursor.close()
        connection.close()
        print("🔌 Database connection closed")


if __name__ == "__main__":
    main()
