<template>
  <div>
    <PageHeader title="Orders" subtitle="Track sales to customers">
      <template #actions>
        <button @click="openCreateModal" class="btn btn-primary flex items-center gap-2">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
          </svg>
          New Order
        </button>
      </template>
    </PageHeader>

    <LoadingSpinner v-if="loading" message="Loading orders..." />

    <EmptyState 
      v-else-if="orders.length === 0" 
      title="No orders yet"
      message="Record your first sale to a customer."
    >
      <button @click="openCreateModal" class="btn btn-primary">New Order</button>
    </EmptyState>

    <div v-else class="card">
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="border-b border-gray-100">
              <th class="table-header">ID</th>
              <th class="table-header">Date</th>
              <th class="table-header">Customer</th>
              <th class="table-header">Product</th>
              <th class="table-header">Quantity</th>
              <th class="table-header">Unit Price</th>
              <th class="table-header">Total Amount</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">
            <tr v-for="order in orders" :key="order.id" class="hover:bg-gray-50 transition-colors">
              <td class="table-cell font-medium text-gray-500">#{{ order.id }}</td>
              <td class="table-cell">{{ formatDate(order.timestamp) }}</td>
              <td class="table-cell">
                <div>
                  <p class="font-medium text-gray-900">{{ order.customer?.name || order.customer_name }}</p>
                  <p class="text-xs text-gray-500">{{ order.customer?.city || 'N/A' }}</p>
                </div>
              </td>
              <td class="table-cell">
                <div>
                  <span class="px-2.5 py-1 bg-blue-50 text-blue-700 rounded-full text-xs font-medium">
                    {{ order.product?.code || order.product_code }}
                  </span>
                  <p class="text-sm text-gray-600 mt-1">{{ order.product?.name || order.product_name }}</p>
                </div>
              </td>
              <td class="table-cell font-medium">{{ order.quantity }} {{ order.product?.measure_unit || order.measure_unit || '' }}</td>
              <td class="table-cell">${{ order.unit_price?.toFixed(2) }}</td>
              <td class="table-cell">
                <span class="font-semibold text-blue-600">${{ order.total_amount?.toFixed(2) }}</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <Modal 
      :show="showModal" 
      title="New Order"
      :loading="saving"
      @close="closeModal"
      @submit="createOrder"
    >
      <form @submit.prevent="createOrder" class="space-y-4">
        <div class="border-b border-gray-100 pb-4 mb-4">
          <h4 class="font-medium text-gray-900 mb-3">Order Information</h4>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="label">Customer *</label>
              <select v-model="form.customer_id" class="input" required @change="onCustomerChange">
                <option value="">Select customer</option>
                <option v-for="customer in customers" :key="customer.id" :value="customer.id">
                  {{ customer.name }} ({{ customer.city }})
                </option>
              </select>
            </div>
            <div>
              <label class="label">Product *</label>
              <select v-model="form.product_id" class="input" required @change="onProductChange">
                <option value="">Select product</option>
                <option v-for="product in products" :key="product.id" :value="product.id">
                  {{ product.code }} - {{ product.name }}
                </option>
              </select>
            </div>
          </div>
        </div>

        <div class="border-b border-gray-100 pb-4 mb-4">
          <h4 class="font-medium text-gray-900 mb-3">Transaction Details</h4>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="label">Quantity *</label>
              <input 
                v-model.number="form.quantity" 
                type="number" 
                min="1" 
                class="input" 
                required 
                @input="calculateTotal"
              />
            </div>
            <div>
              <label class="label">Unit Price *</label>
              <input 
                v-model.number="form.unit_price" 
                type="number" 
                step="0.01" 
                min="0.01" 
                class="input" 
                required
                @input="calculateTotal"
              />
            </div>
          </div>
          <div class="mt-4">
            <div class="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
              <span class="font-medium text-gray-700">Total Amount:</span>
              <span class="text-xl font-bold text-blue-600">${{ totalAmount.toFixed(2) }}</span>
            </div>
          </div>
        </div>
      </form>
    </Modal>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { orderService, customerService, productService } from '@/services/api'
import PageHeader from '@/components/PageHeader.vue'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import EmptyState from '@/components/EmptyState.vue'
import Modal from '@/components/Modal.vue'

export default {
  name: 'OrdersView',
  components: { PageHeader, LoadingSpinner, EmptyState, Modal },
  setup() {
    const orders = ref([])
    const customers = ref([])
    const products = ref([])
    const loading = ref(false)
    const saving = ref(false)
    const showModal = ref(false)
    
    const form = ref({
      customer_id: '',
      product_id: '',
      quantity: 1,
      unit_price: 0
    })

    const totalAmount = computed(() => {
      return form.value.quantity * form.value.unit_price
    })

    const formatDate = (timestamp) => {
      return new Date(timestamp).toLocaleString()
    }

    const loadOrders = async () => {
      loading.value = true
      try {
        const response = await orderService.getAll()
        orders.value = response.data.orders || response.data
      } catch (error) {
        console.error('Error loading orders:', error)
      } finally {
        loading.value = false
      }
    }

    const loadCustomers = async () => {
      try {
        const response = await customerService.getAll()
        customers.value = response.data.customers || response.data
      } catch (error) {
        console.error('Error loading customers:', error)
      }
    }

    const loadProducts = async () => {
      try {
        const response = await productService.getAll()
        products.value = response.data.products || response.data
      } catch (error) {
        console.error('Error loading products:', error)
      }
    }

    const openCreateModal = () => {
      showModal.value = true
      if (customers.value.length === 0) loadCustomers()
      if (products.value.length === 0) loadProducts()
    }

    const closeModal = () => {
      showModal.value = false
      form.value = {
        customer_id: '',
        product_id: '',
        quantity: 1,
        unit_price: 0
      }
    }

    const calculateTotal = () => {
      // Computed property handles this automatically
    }

    const onCustomerChange = () => {
      // Could filter products by customer preferences if needed
    }

    const onProductChange = () => {
      // Could auto-fill unit price from product if available
    }

    const createOrder = async () => {
      saving.value = true
      try {
        await orderService.create({
          customer_id: parseInt(form.value.customer_id),
          product_id: parseInt(form.value.product_id),
          quantity: form.value.quantity,
          unit_price: form.value.unit_price
        })
        closeModal()
        loadOrders()
      } catch (error) {
        console.error('Error creating order:', error)
        alert('Failed to create order. Please try again.')
      } finally {
        saving.value = false
      }
    }

    onMounted(() => {
      loadOrders()
    })

    return {
      orders,
      customers,
      products,
      loading,
      saving,
      showModal,
      form,
      totalAmount,
      formatDate,
      openCreateModal,
      closeModal,
      createOrder,
      calculateTotal,
      onCustomerChange,
      onProductChange
    }
  }
}
</script>
