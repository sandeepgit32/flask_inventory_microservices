-- Migration Script: Remove unit_price columns from orders and procurements
-- Description: Remove redundant unit_price storage - price now fetched from product service
-- Date: 2026-02-06
-- Reason: Single source of truth for pricing (price_buy/price_sell in products table)

-- ============================================
-- STEP 1: Remove unit_price from procurements table
-- ============================================

-- Remove the unit_price column from procurements
-- Price will be fetched from products.price_buy when needed
ALTER TABLE procurements 
    DROP COLUMN IF EXISTS unit_price;

-- ============================================
-- STEP 2: Remove unit_price from orders table
-- ============================================

-- Remove the unit_price column from orders
-- Price will be fetched from products.price_sell when needed
ALTER TABLE orders 
    DROP COLUMN IF EXISTS unit_price;

-- ============================================
-- Notes:
-- ============================================
-- - unit_price is now calculated dynamically from product service
-- - Procurements use products.price_buy
-- - Orders use products.price_sell
-- - total_cost column remains for transaction history
-- - Historical total_cost values are preserved
-- ============================================
