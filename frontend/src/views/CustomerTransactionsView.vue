<template>
  <div>
    <PageHeader title="Customer Transactions" subtitle="Track sales to customers">
      <template #actions>
        <button @click="openCreateModal" class="btn btn-primary flex items-center gap-2">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
          </svg>
          New Transaction
        </button>
      </template>
    </PageHeader>

    <LoadingSpinner v-if="loading" message="Loading transactions..." />

    <EmptyState 
      v-else-if="transactions.length === 0" 
      title="No customer transactions yet"
      message="Record your first sale to a customer."
    >
      <button @click="openCreateModal" class="btn btn-primary">New Transaction</button>
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
              <th class="table-header">Total</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">
            <tr v-for="tx in transactions" :key="tx.id" class="hover:bg-gray-50 transition-colors">
              <td class="table-cell font-medium text-gray-500">#{{ tx.id }}</td>
              <td class="table-cell">{{ formatDate(tx.timestamp) }}</td>
              <td class="table-cell">
                <div>
                  <p class="font-medium text-gray-900">{{ tx.customer_name }}</p>
                  <p class="text-xs text-gray-500">{{ tx.city || 'N/A' }}</p>
                </div>
              </td>
              <td class="table-cell">
                <div>
                  <span class="px-2.5 py-1 bg-primary-50 text-primary-700 rounded-full text-xs font-medium">
                    {{ tx.product_code }}
                  </span>
                  <p class="text-sm text-gray-600 mt-1">{{ tx.product_name }}</p>
                </div>
              </td>
              <td class="table-cell font-medium">{{ tx.quantity }} {{ tx.measure_unit || '' }}</td>
              <td class="table-cell">${{ tx.unit_price?.toFixed(2) }}</td>
              <td class="table-cell">
                <span class="font-semibold text-primary-600">${{ tx.total_cost?.toFixed(2) }}</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <Modal 
      :show="showModal" 
      title="New Customer Transaction"
      :loading="saving"
      @close="closeModal"
      @submit="createTransaction"
    >
      <form @submit.prevent="createTransaction" class="space-y-4">
        <div class="border-b border-gray-100 pb-4 mb-4">
          <h4 class="font-medium text-gray-900 mb-3">Customer Information</h4>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="label">Customer Name *</label>
              <input v-model="form.customer_name" type="text" class="input" required />
            </div>
            <div>
              <label class="label">City</label>
              <input v-model="form.city" type="text" class="input" />
            </div>
          </div>
          <div class="grid grid-cols-2 gap-4 mt-4">
            <div>
              <label class="label">Contact Person</label>
              <input v-model="form.contact_person" type="text" class="input" />
            </div>
            <div>
              <label class="label">Phone</label>
              <input v-model="form.phone" type="text" class="input" />
            </div>
          </div>
        </div>

        <div class="border-b border-gray-100 pb-4 mb-4">
          <h4 class="font-medium text-gray-900 mb-3">Product Information</h4>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="label">Product Code *</label>
              <input v-model="form.product_code" type="text" class="input" required />
            </div>
            <div>
              <label class="label">Product Name *</label>
              <input v-model="form.product_name" type="text" class="input" required />
            </div>
          </div>
          <div class="grid grid-cols-2 gap-4 mt-4">
            <div>
              <label class="label">Category</label>
              <input v-model="form.product_category" type="text" class="input" />
            </div>
            <div>
              <label class="label">Measure Unit</label>
              <input v-model="form.measure_unit" type="text" class="input" placeholder="e.g., kg, pcs" />
            </div>
          </div>
        </div>

        <div>
          <h4 class="font-medium text-gray-900 mb-3">Transaction Details</h4>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="label">Quantity *</label>
              <input v-model.number="form.quantity" type="number" class="input" required />
            </div>
            <div>
              <label class="label">Unit Price *</label>
              <input v-model.number="form.unit_price" type="number" step="0.01" class="input" required />
            </div>
          </div>
          <div class="mt-4 p-4 bg-gray-50 rounded-lg">
            <div class="flex justify-between items-center">
              <span class="text-gray-600">Total Amount</span>
              <span class="text-xl font-bold text-primary-600">${{ totalCost.toFixed(2) }}</span>
            </div>
          </div>
        </div>
      </form>
    </Modal>

    <Toast :show="toast.show" :message="toast.message" :type="toast.type" @close="toast.show = false" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { customerTransactionService } from '../services/api'
import PageHeader from '../components/PageHeader.vue'
import Modal from '../components/Modal.vue'
import LoadingSpinner from '../components/LoadingSpinner.vue'
import EmptyState from '../components/EmptyState.vue'
import Toast from '../components/Toast.vue'

const transactions = ref([])
const loading = ref(true)
const saving = ref(false)
const showModal = ref(false)

const form = ref({
  customer_name: '',
  city: '',
  zipcode: '',
  contact_person: '',
  phone: '',
  email: '',
  product_code: '',
  product_name: '',
  product_category: '',
  unit_price: 0,
  quantity: 0,
  measure_unit: ''
})

const totalCost = computed(() => form.value.quantity * form.value.unit_price)

const toast = ref({ show: false, message: '', type: 'success' })

const showToast = (message, type = 'success') => {
  toast.value = { show: true, message, type }
  setTimeout(() => toast.value.show = false, 3000)
}

const formatDate = (date) => {
  if (!date) return 'N/A'
  return new Date(date).toLocaleDateString('en-US', { 
    year: 'numeric', 
    month: 'short', 
    day: 'numeric' 
  })
}

const fetchTransactions = async () => {
  try {
    loading.value = true
    const response = await customerTransactionService.getAll()
    transactions.value = response.data.transactions || response.data || []
  } catch (error) {
    showToast('Failed to load transactions', 'error')
  } finally {
    loading.value = false
  }
}

const openCreateModal = () => {
  form.value = {
    customer_name: '',
    city: '',
    zipcode: '',
    contact_person: '',
    phone: '',
    email: '',
    product_code: '',
    product_name: '',
    product_category: '',
    unit_price: 0,
    quantity: 0,
    measure_unit: ''
  }
  showModal.value = true
}

const closeModal = () => {
  showModal.value = false
}

const createTransaction = async () => {
  try {
    saving.value = true
    const payload = {
      ...form.value,
      total_cost: totalCost.value
    }
    await customerTransactionService.create(payload)
    showToast('Transaction created successfully')
    closeModal()
    fetchTransactions()
  } catch (error) {
    showToast(error.response?.data?.message || 'Failed to create transaction', 'error')
  } finally {
    saving.value = false
  }
}

onMounted(fetchTransactions)
</script>
