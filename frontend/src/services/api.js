import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Products
export const productService = {
  getAll: (start = 1, limit = 100) => api.get('/products', { params: { start, limit } }),
  getOne: (productCode) => api.get(`/product/${productCode}`),
  create: (data) => api.post('/products', data),
  update: (productCode, data) => api.put(`/product/${productCode}`, data),
  delete: (productCode) => api.delete(`/product/${productCode}`)
}

// Suppliers
export const supplierService = {
  getAll: (start = 1, limit = 100) => api.get('/suppliers', { params: { start, limit } }),
  getOne: (id) => api.get(`/supplier/${id}`),
  create: (data) => api.post('/suppliers', data),
  update: (id, data) => api.put(`/supplier/${id}`, data),
  delete: (id) => api.delete(`/supplier/${id}`),
  getByCity: (city) => api.get(`/suppliers/${city}`),
  getProducts: (id) => api.get(`/supplier/${id}/products`)
}

// Customers
export const customerService = {
  getAll: (start = 1, limit = 100) => api.get('/customers', { params: { start, limit } }),
  getOne: (id) => api.get(`/customer/${id}`),
  create: (data) => api.post('/customers', data),
  update: (id, data) => api.put(`/customer/${id}`, data),
  delete: (id) => api.delete(`/customer/${id}`),
  getByCity: (city) => api.get(`/customers/${city}`)
}

// Warehouses
export const warehouseService = {
  getAll: (start = 1, limit = 100) => api.get('/warehouses', { params: { start, limit } }),
  getOne: (id) => api.get(`/warehouse/${id}`),
  create: (data) => api.post('/warehouses', data),
  update: (id, data) => api.put(`/warehouse/${id}`, data),
  delete: (id) => api.delete(`/warehouse/${id}`),
  getByCity: (city) => api.get(`/warehouses/${city}`),
  getCustomers: (id) => api.get(`/warehouse/${id}/customers`)
}

// Storages
export const storageService = {
  getAll: (start = 1, limit = 100) => api.get('/storages', { params: { start, limit } }),
  getOne: (productCode, warehouseName) => api.get(`/storage/${productCode}/${warehouseName}`),
  create: (data) => api.post('/storages', data),
  update: (productCode, warehouseName, type, data) => api.put(`/storage/${productCode}/${warehouseName}/${type}`, data),
  getByProduct: (productCode) => api.get(`/storages/product/${productCode}`),
  getByWarehouse: (warehouseName) => api.get(`/storages/warehouse/${warehouseName}`)
}

// Supply Transactions
export const supplyTransactionService = {
  getAll: (start = 1, limit = 100) => api.get('/supplytransactions', { params: { start, limit } }),
  create: (data) => api.post('/supplytransactions', data),
  getByProduct: (productCode) => api.get(`/supplytransactions/product/${productCode}`),
  getBySupplier: (supplierName) => api.get(`/supplytransactions/supplier/${supplierName}`),
  getByProductAndSupplier: (productCode, supplierName) => api.get(`/supplytransactions/product_supplier/${productCode}/${supplierName}`)
}

// Customer Transactions
export const customerTransactionService = {
  getAll: (start = 1, limit = 100) => api.get('/customertransactions', { params: { start, limit } }),
  create: (data) => api.post('/customertransactions', data),
  getByProduct: (productCode) => api.get(`/customertransactions/product/${productCode}`),
  getByCustomer: (customerName) => api.get(`/customertransactions/customer/${customerName}`),
  getByProductAndCustomer: (productCode, customerName) => api.get(`/customertransactions/product_customer/${productCode}/${customerName}`)
}

export default api
