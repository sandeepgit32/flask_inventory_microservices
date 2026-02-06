-- Create the main inventory database
CREATE DATABASE IF NOT EXISTS inventory_db;

-- Grant privileges to the admin user
GRANT ALL PRIVILEGES ON inventory_db.* TO 'admin'@'%';
FLUSH PRIVILEGES;

-- Use the inventory database
USE inventory_db;

-- ============================================
-- Auth Service Tables
-- ============================================

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    role VARCHAR(20) DEFAULT 'user',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_username (username),
    INDEX idx_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- Supplier Service Tables
-- ============================================

CREATE TABLE IF NOT EXISTS suppliers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    city VARCHAR(100),
    zipcode VARCHAR(20),
    contact_person VARCHAR(100),
    phone VARCHAR(20),
    email VARCHAR(100)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- Customer Service Tables
-- ============================================

CREATE TABLE IF NOT EXISTS customers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    city VARCHAR(100),
    zipcode VARCHAR(20),
    contact_person VARCHAR(100),
    phone VARCHAR(20),
    email VARCHAR(100)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- Product Service Tables
-- ============================================

CREATE TABLE IF NOT EXISTS products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_code VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(200) NOT NULL UNIQUE,
    category VARCHAR(100),
    price_buy FLOAT,
    price_sell FLOAT,
    measure_unit VARCHAR(20),
    supplier_id INT,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id) ON DELETE SET NULL,
    INDEX idx_product_code (product_code),
    INDEX idx_supplier_id (supplier_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- Inventory Service Tables
-- ============================================

CREATE TABLE IF NOT EXISTS storages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    quantity INT DEFAULT 0,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    UNIQUE KEY unique_product (product_id),
    INDEX idx_product_id (product_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- Procurement Service Tables (Procurements)
-- ============================================

CREATE TABLE IF NOT EXISTS procurements (
    id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign keys (normalized)
    supplier_id INT,
    product_id INT,
    
    unit_price FLOAT,
    quantity INT,
    total_cost FLOAT,
    
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id) ON DELETE SET NULL,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL,
    INDEX idx_supplier_id (supplier_id),
    INDEX idx_product_id (product_id),
    INDEX idx_timestamp (timestamp)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- Order Service Tables (Orders)
-- ============================================

CREATE TABLE IF NOT EXISTS orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign keys (normalized)
    customer_id INT,
    product_id INT,
    
    unit_price FLOAT,
    quantity INT,
    total_cost FLOAT,
    
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE SET NULL,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL,
    INDEX idx_orders_customer (customer_id),
    INDEX idx_orders_product (product_id),
    INDEX idx_timestamp (timestamp)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- Seed Data
-- ============================================

-- Insert default admin user (password: admin123)
INSERT INTO users (username, password_hash, email, role) VALUES
('admin', '$2b$12$cfMHRLM/LqxaAHQrDkWDReQ8mCpldd7dyeUIivc5ybk.xXz5PTT5W', 'admin@inventory.local', 'admin')
ON DUPLICATE KEY UPDATE username=username;

-- Insert sample suppliers
INSERT INTO suppliers (name, city, zipcode, contact_person, phone, email) VALUES
('Tech Supplies Co', 'San Francisco', '94102', 'John Smith', '555-0101', 'john@techsupplies.com'),
('Office Depot', 'Los Angeles', '90001', 'Jane Doe', '555-0102', 'jane@officedepot.com'),
('Industrial Parts Inc', 'Chicago', '60601', 'Bob Wilson', '555-0103', 'bob@indparts.com'),
('Electronics World', 'New York', '10001', 'Alice Brown', '555-0104', 'alice@electronicsworld.com'),
('Global Supplies', 'Seattle', '98101', 'Charlie Davis', '555-0105', 'charlie@globalsupplies.com')
ON DUPLICATE KEY UPDATE name=name;

-- Insert sample customers
INSERT INTO customers (name, city, zipcode, contact_person, phone, email) VALUES
('Acme Corp', 'Boston', '02101', 'Mike Johnson', '555-0201', 'mike@acme.com'),
('Beta Industries', 'Denver', '80201', 'Sarah Lee', '555-0202', 'sarah@beta.com'),
('Gamma Solutions', 'Austin', '78701', 'Tom Harris', '555-0203', 'tom@gamma.com'),
('Delta Services', 'Miami', '33101', 'Lisa Chen', '555-0204', 'lisa@delta.com'),
('Epsilon Tech', 'Portland', '97201', 'David Kim', '555-0205', 'david@epsilon.com'),
('Zeta Holdings', 'Phoenix', '85001', 'Emma White', '555-0206', 'emma@zeta.com'),
('Eta Manufacturing', 'Dallas', '75201', 'James Brown', '555-0207', 'james@eta.com'),
('Theta Corp', 'Atlanta', '30301', 'Olivia Green', '555-0208', 'olivia@theta.com'),
('Iota Innovations', 'San Diego', '92101', 'William Black', '555-0209', 'william@iota.com'),
('Kappa Enterprises', 'Minneapolis', '55401', 'Sophia Gray', '555-0210', 'sophia@kappa.com')
ON DUPLICATE KEY UPDATE name=name;

-- Insert sample products
INSERT INTO products (product_code, name, category, price_buy, price_sell, measure_unit, supplier_id) VALUES
('PROD-001', 'Laptop Computer', 'Electronics', 800.00, 1200.00, 'unit', 1),
('PROD-002', 'Office Chair', 'Furniture', 150.00, 250.00, 'unit', 2),
('PROD-003', 'Industrial Motor', 'Machinery', 500.00, 750.00, 'unit', 3),
('PROD-004', 'LED Monitor', 'Electronics', 200.00, 350.00, 'unit', 4),
('PROD-005', 'Printer Paper', 'Supplies', 20.00, 35.00, 'ream', 5),
('PROD-006', 'Wireless Mouse', 'Electronics', 15.00, 30.00, 'unit', 1),
('PROD-007', 'Desk Lamp', 'Furniture', 25.00, 45.00, 'unit', 2),
('PROD-008', 'Safety Gloves', 'Safety', 10.00, 18.00, 'pair', 3),
('PROD-009', 'USB Hub', 'Electronics', 12.00, 25.00, 'unit', 4),
('PROD-010', 'Stapler', 'Supplies', 5.00, 12.00, 'unit', 5)
ON DUPLICATE KEY UPDATE product_code=product_code;

-- Insert sample inventory (storages)
INSERT INTO storages (product_id, quantity) VALUES
(1, 50),
(2, 100),
(3, 25),
(4, 75),
(5, 500),
(6, 200),
(7, 150),
(8, 300),
(9, 125),
(10, 400)
ON DUPLICATE KEY UPDATE quantity=VALUES(quantity);
