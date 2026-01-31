-- Migration Script: Microservices Restructuring
-- Description: Transform monolithic catalog service into 7 microservices
-- Author: System
-- Date: 2026-01-31

-- ============================================
-- STEP 1: Drop warehouses table (single warehouse architecture)
-- ============================================

-- First, drop foreign keys that reference warehouses
ALTER TABLE customers DROP FOREIGN KEY IF EXISTS customers_ibfk_1;
ALTER TABLE storages DROP FOREIGN KEY IF EXISTS storages_ibfk_2;

-- Drop the warehouses table
DROP TABLE IF EXISTS warehouses;

-- ============================================
-- STEP 2: Modify storages table for single warehouse
-- ============================================

-- Remove warehouse_name column (no longer needed with single warehouse)
ALTER TABLE storages DROP COLUMN IF EXISTS warehouse_name;

-- Add product_id foreign key column (instead of product_code string)
ALTER TABLE storages 
    ADD COLUMN product_id INT AFTER id;

-- Update product_id from product_code (backfill existing data)
UPDATE storages s
INNER JOIN products p ON s.product_code = p.product_code
SET s.product_id = p.id;

-- Make product_id NOT NULL after backfill
ALTER TABLE storages 
    MODIFY COLUMN product_id INT NOT NULL;

-- Drop old product_code column
ALTER TABLE storages DROP COLUMN IF EXISTS product_code;

-- Add foreign key constraint
ALTER TABLE storages
    ADD CONSTRAINT fk_storages_product 
    FOREIGN KEY (product_id) REFERENCES products(id) 
    ON DELETE CASCADE;

-- Add index for performance
CREATE INDEX idx_storages_product ON storages(product_id);

-- ============================================
-- STEP 3: Modify products table to use supplier_id FK
-- ============================================

-- Add supplier_id column
ALTER TABLE products 
    ADD COLUMN supplier_id INT AFTER id;

-- Backfill supplier_id from supplier_name
UPDATE products p
INNER JOIN suppliers s ON p.supplier_name = s.name
SET p.supplier_id = s.id;

-- Drop the old supplier_name column
ALTER TABLE products DROP FOREIGN KEY IF EXISTS products_ibfk_1;
ALTER TABLE products DROP COLUMN IF EXISTS supplier_name;

-- Add foreign key constraint
ALTER TABLE products
    ADD CONSTRAINT fk_products_supplier 
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id) 
    ON DELETE SET NULL;

-- Add index for performance
CREATE INDEX idx_products_supplier ON products(supplier_id);

-- ============================================
-- STEP 4: Normalize supply_transactions table
-- ============================================

-- Add foreign key columns for supplier and product
ALTER TABLE supply_transactions 
    ADD COLUMN supplier_id INT AFTER id,
    ADD COLUMN product_id INT AFTER supplier_id;

-- Backfill supplier_id from supplier_name
UPDATE supply_transactions st
INNER JOIN suppliers s ON st.supplier_name = s.name
SET st.supplier_id = s.id;

-- Backfill product_id from product_code
UPDATE supply_transactions st
INNER JOIN products p ON st.product_code = p.product_code
SET st.product_id = p.id;

-- Add foreign key constraints
ALTER TABLE supply_transactions
    ADD CONSTRAINT fk_supply_transactions_supplier 
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id) 
    ON DELETE SET NULL;

ALTER TABLE supply_transactions
    ADD CONSTRAINT fk_supply_transactions_product 
    FOREIGN KEY (product_id) REFERENCES products(id) 
    ON DELETE SET NULL;

-- Add indexes for performance
CREATE INDEX idx_supply_tx_supplier ON supply_transactions(supplier_id);
CREATE INDEX idx_supply_tx_product ON supply_transactions(product_id);

-- Note: Keep denormalized columns for historical data integrity
-- (supplier_name, city, zipcode, product_name, etc.)

-- ============================================
-- STEP 5: Normalize customer_transactions table
-- ============================================

-- Add foreign key columns for customer and product
ALTER TABLE customer_transactions 
    ADD COLUMN customer_id INT AFTER id,
    ADD COLUMN product_id INT AFTER customer_id;

-- Backfill customer_id from customer_name
UPDATE customer_transactions ct
INNER JOIN customers c ON ct.customer_name = c.name
SET ct.customer_id = c.id;

-- Backfill product_id from product_code
UPDATE customer_transactions ct
INNER JOIN products p ON ct.product_code = p.product_code
SET ct.product_id = p.id;

-- Add foreign key constraints
ALTER TABLE customer_transactions
    ADD CONSTRAINT fk_customer_transactions_customer 
    FOREIGN KEY (customer_id) REFERENCES customers(id) 
    ON DELETE SET NULL;

ALTER TABLE customer_transactions
    ADD CONSTRAINT fk_customer_transactions_product 
    FOREIGN KEY (product_id) REFERENCES products(id) 
    ON DELETE SET NULL;

-- Add indexes for performance
CREATE INDEX idx_customer_tx_customer ON customer_transactions(customer_id);
CREATE INDEX idx_customer_tx_product ON customer_transactions(product_id);

-- Note: Keep denormalized columns for historical data integrity
-- (customer_name, city, zipcode, product_name, etc.)

-- ============================================
-- STEP 6: Remove warehouse_id from customers table
-- ============================================

-- Drop warehouse_id column (no longer needed with single warehouse)
ALTER TABLE customers DROP COLUMN IF EXISTS warehouse_id;

-- ============================================
-- STEP 7: Create users table for Auth Service
-- ============================================

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    role VARCHAR(20) DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_users_username (username),
    INDEX idx_users_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Insert default admin user (password: admin123)
-- Password hash generated with bcrypt for "admin123"
INSERT INTO users (username, password_hash, email, role) 
VALUES ('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYq7X8kVe5u', 'admin@example.com', 'admin')
ON DUPLICATE KEY UPDATE username=username;

-- ============================================
-- VERIFICATION QUERIES (commented out for safety)
-- ============================================

-- Verify storages table structure
-- SELECT * FROM storages LIMIT 5;

-- Verify products with suppliers
-- SELECT p.id, p.name, p.supplier_id, s.name as supplier_name 
-- FROM products p 
-- LEFT JOIN suppliers s ON p.supplier_id = s.id 
-- LIMIT 5;

-- Verify supply_transactions with FKs
-- SELECT st.id, st.supplier_id, s.name as supplier_name, st.product_id, p.name as product_name
-- FROM supply_transactions st
-- LEFT JOIN suppliers s ON st.supplier_id = s.id
-- LEFT JOIN products p ON st.product_id = p.id
-- LIMIT 5;

-- Verify customer_transactions with FKs
-- SELECT ct.id, ct.customer_id, c.name as customer_name, ct.product_id, p.name as product_name
-- FROM customer_transactions ct
-- LEFT JOIN customers c ON ct.customer_id = c.id
-- LEFT JOIN products p ON ct.product_id = p.id
-- LIMIT 5;

-- ============================================
-- MIGRATION COMPLETE
-- ============================================
