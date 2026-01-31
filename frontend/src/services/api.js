import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Request interceptor to add JWT token
api.interceptors.request.use(
  (config) => {
    const token = sessionStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor to handle 401 errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      sessionStorage.removeItem('token')
      sessionStorage.removeItem('user')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Auth Service
export const authService = {
  register: (data) => api.post('/auth/register', data),
  login: async (username, password) => {
    const response = await api.post('/auth/login', { username, password })
    if (response.data.token) {
      sessionStorage.setItem('token', response.data.token)
      sessionStorage.setItem('user', JSON.stringify(response.data.user))
    }
    return response
  },
  logout: () => {
    sessionStorage.removeItem('token')
    sessionStorage.removeItem('user')
  },
  getCurrentUser: () => {
    const userStr = sessionStorage.getItem('user')
    return userStr ? JSON.parse(userStr) : null
  },
  isAuthenticated: () => {
    return !!sessionStorage.getItem('token')
  }
}

// Products
export const productService = {
  getAll: (start = 0, limit = 50) => api.get('/products', { params: { start, limit } }),
  getOne: (id) => api.get(`/products/${id}`),
  create: (data) => api.post('/products', data),
  update: (id, data) => api.put(`/products/${id}`, data),
  delete: (id) => api.delete(`/products/${id}`)
}

// Suppliers
export const supplierService = {
  getAll: (start = 0, limit = 50) => api.get('/suppliers', { params: { start, limit } }),
  getOne: (id) => api.get(`/suppliers/${id}`),
  create: (data) => api.post('/suppliers', data),
  update: (id, data) => api.put(`/suppliers/${id}`, data),
  delete: (id) => api.delete(`/suppliers/${id}`),
  getByCity: (city) => api.get(`/suppliers/city/${city}`)
}

// Customers
export const customerService = {
  getAll: (start = 0, limit = 50) => api.get('/customers', { params: { start, limit } }),
  getOne: (id) => api.get(`/customers/${id}`),
  create: (data) => api.post('/customers', data),
  update: (id, data) => api.put(`/customers/${id}`, data),
  delete: (id) => api.delete(`/customers/${id}`),
  getByCity: (city) => api.get(`/customers/city/${city}`)
}

// Inventory/Storage
export const inventoryService = {
  getAll: (start = 0, limit = 50) => api.get('/storages', { params: { start, limit } }),
  getOne: (id) => api.get(`/storages/${id}`),
  create: (data) => api.post('/storages', data),
  update: (id, data) => api.put(`/storages/${id}`, data),
  getByProduct: (productId) => api.get(`/storages/product/${productId}`)
}

// Procurement (Supply Transactions)
export const procurementService = {
  getAll: (start = 0, limit = 50) => api.get('/procurements', { params: { start, limit } }),
  create: (data) => api.post('/procurements', data),
  getByProduct: (productId) => api.get(`/procurements/product/${productId}`),
  getBySupplier: (supplierId) => api.get(`/procurements/supplier/${supplierId}`)
}

// Orders (Customer Transactions)
export const orderService = {
  getAll: (start = 0, limit = 50) => api.get('/orders', { params: { start, limit } }),
  create: (data) => api.post('/orders', data),
  getByProduct: (productId) => api.get(`/orders/product/${productId}`),
  getByCustomer: (customerId) => api.get(`/orders/customer/${customerId}`)
}

export default api
