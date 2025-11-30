import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    redirect: '/products'
  },
  {
    path: '/products',
    name: 'Products',
    component: () => import('../views/ProductsView.vue')
  },
  {
    path: '/suppliers',
    name: 'Suppliers',
    component: () => import('../views/SuppliersView.vue')
  },
  {
    path: '/customers',
    name: 'Customers',
    component: () => import('../views/CustomersView.vue')
  },
  {
    path: '/warehouses',
    name: 'Warehouses',
    component: () => import('../views/WarehousesView.vue')
  },
  {
    path: '/storages',
    name: 'Storages',
    component: () => import('../views/StoragesView.vue')
  },
  {
    path: '/supply-transactions',
    name: 'SupplyTransactions',
    component: () => import('../views/SupplyTransactionsView.vue')
  },
  {
    path: '/customer-transactions',
    name: 'CustomerTransactions',
    component: () => import('../views/CustomerTransactionsView.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
