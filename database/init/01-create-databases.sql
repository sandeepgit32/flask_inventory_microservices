-- Create the main inventory database
CREATE DATABASE IF NOT EXISTS inventory_db;

-- Grant privileges to the admin user
GRANT ALL PRIVILEGES ON inventory_db.* TO 'admin'@'%';
FLUSH PRIVILEGES;

-- Use the inventory database
USE inventory_db;

-- ============================================
-- Catalog Service Tables
-- ============================================

-- Warehouses table
CREATE TABLE IF NOT EXISTS warehouses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(80) NOT NULL UNIQUE,
    city VARCHAR(50)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Suppliers table
CREATE TABLE IF NOT EXISTS suppliers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    city VARCHAR(50),
    zipcode VARCHAR(20),
    contact_person VARCHAR(80),
    phone VARCHAR(20),
    email VARCHAR(80)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Customers table
CREATE TABLE IF NOT EXISTS customers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(80) NOT NULL UNIQUE,
    city VARCHAR(50),
    zipcode VARCHAR(20),
    contact_person VARCHAR(80),
    phone VARCHAR(20),
    email VARCHAR(80),
    warehouse_id INT,
    FOREIGN KEY (warehouse_id) REFERENCES warehouses(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Products table
CREATE TABLE IF NOT EXISTS products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_code VARCHAR(80) NOT NULL UNIQUE,
    name VARCHAR(80) NOT NULL UNIQUE,
    category VARCHAR(50),
    price_buy FLOAT NOT NULL,
    price_sell FLOAT NOT NULL,
    measure_unit VARCHAR(10),
    supplier_name VARCHAR(100) NOT NULL,
    FOREIGN KEY (supplier_name) REFERENCES suppliers(name) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Storages table (product inventory in warehouses)
CREATE TABLE IF NOT EXISTS storages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_code VARCHAR(80) NOT NULL,
    warehouse_name VARCHAR(80) NOT NULL,
    quantity INT NOT NULL,
    FOREIGN KEY (product_code) REFERENCES products(product_code) ON DELETE CASCADE,
    FOREIGN KEY (warehouse_name) REFERENCES warehouses(name) ON DELETE CASCADE,
    UNIQUE KEY unique_product_warehouse (product_code, warehouse_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- Supply Transaction Service Tables
-- ============================================

CREATE TABLE IF NOT EXISTS supply_transactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATE,
    supplier_name VARCHAR(100) NOT NULL,
    city VARCHAR(50),
    zipcode INT,
    contact_person VARCHAR(80),
    phone VARCHAR(20),
    email VARCHAR(80),
    product_code VARCHAR(80) NOT NULL,
    product_name VARCHAR(80) NOT NULL,
    product_category VARCHAR(50),
    unit_price FLOAT NOT NULL,
    quantity INT,
    total_cost FLOAT NOT NULL,
    measure_unit VARCHAR(10)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- Customer Transaction Service Tables
-- ============================================

CREATE TABLE IF NOT EXISTS customer_transactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATE,
    customer_name VARCHAR(100) NOT NULL,
    city VARCHAR(50),
    zipcode INT,
    contact_person VARCHAR(80),
    phone VARCHAR(20),
    email VARCHAR(80),
    product_code VARCHAR(80) NOT NULL,
    product_name VARCHAR(80) NOT NULL,
    product_category VARCHAR(50),
    unit_price FLOAT NOT NULL,
    quantity INT,
    total_cost FLOAT NOT NULL,
    measure_unit VARCHAR(10)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- Create indexes for better query performance
-- ============================================

CREATE INDEX idx_products_supplier ON products(supplier_name);
CREATE INDEX idx_storages_product ON storages(product_code);
CREATE INDEX idx_storages_warehouse ON storages(warehouse_name);
CREATE INDEX idx_supply_transactions_product ON supply_transactions(product_code);
CREATE INDEX idx_supply_transactions_supplier ON supply_transactions(supplier_name);
CREATE INDEX idx_supply_transactions_date ON supply_transactions(timestamp);
CREATE INDEX idx_customer_transactions_product ON customer_transactions(product_code);
CREATE INDEX idx_customer_transactions_customer ON customer_transactions(customer_name);
CREATE INDEX idx_customer_transactions_date ON customer_transactions(timestamp);
