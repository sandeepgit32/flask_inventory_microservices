<template>
  <div>
    <PageHeader title="Products" subtitle="Manage your product inventory">
      <template #actions>
        <button @click="openCreateModal" class="btn btn-primary flex items-center gap-2">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
          </svg>
          Add Product
        </button>
      </template>
    </PageHeader>

    <!-- Loading -->
    <LoadingSpinner v-if="loading" message="Loading products..." />

    <!-- Empty State -->
    <EmptyState 
      v-else-if="products.length === 0" 
      title="No products yet"
      message="Get started by adding your first product."
    >
      <button @click="openCreateModal" class="btn btn-primary">Add Product</button>
    </EmptyState>

    <!-- Products Table -->
    <div v-else class="card">
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="border-b border-gray-100">
              <th class="table-header">Code</th>
              <th class="table-header">Name</th>
              <th class="table-header">Category</th>
              <th class="table-header">Buy Price</th>
              <th class="table-header">Sell Price</th>
              <th class="table-header">Unit</th>
              <th class="table-header">Supplier</th>
              <th class="table-header text-right">Actions</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">
            <tr v-for="product in products" :key="product.product_code" class="hover:bg-gray-50 transition-colors">
              <td class="table-cell font-medium text-primary-600">{{ product.product_code }}</td>
              <td class="table-cell font-medium text-gray-900">{{ product.name }}</td>
              <td class="table-cell">
                <span class="px-2.5 py-1 bg-gray-100 text-gray-700 rounded-full text-xs font-medium">
                  {{ product.category || 'N/A' }}
                </span>
              </td>
              <td class="table-cell">${{ product.price_buy?.toFixed(2) }}</td>
              <td class="table-cell">${{ product.price_sell?.toFixed(2) }}</td>
              <td class="table-cell">{{ product.measure_unit || 'N/A' }}</td>
              <td class="table-cell">{{ product.supplier_name }}</td>
              <td class="table-cell text-right">
                <div class="flex items-center justify-end gap-2">
                  <button @click="openEditModal(product)" class="p-2 text-gray-400 hover:text-primary-600 hover:bg-primary-50 rounded-lg transition-colors">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
                    </svg>
                  </button>
                  <button @click="confirmDelete(product)" class="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                    </svg>
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Create/Edit Modal -->
    <Modal 
      :show="showModal" 
      :title="isEditing ? 'Edit Product' : 'Add Product'"
      :loading="saving"
      @close="closeModal"
      @submit="saveProduct"
    >
      <form @submit.prevent="saveProduct" class="space-y-4">
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="label">Product Code *</label>
            <input v-model="form.product_code" type="text" class="input" :disabled="isEditing" required />
          </div>
          <div>
            <label class="label">Name *</label>
            <input v-model="form.name" type="text" class="input" required />
          </div>
        </div>
        <div>
          <label class="label">Category</label>
          <input v-model="form.category" type="text" class="input" />
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="label">Buy Price *</label>
            <input v-model.number="form.price_buy" type="number" step="0.01" class="input" required />
          </div>
          <div>
            <label class="label">Sell Price *</label>
            <input v-model.number="form.price_sell" type="number" step="0.01" class="input" required />
          </div>
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="label">Measure Unit</label>
            <input v-model="form.measure_unit" type="text" class="input" placeholder="e.g., kg, pcs, ltr" />
          </div>
          <div>
            <label class="label">Supplier Name *</label>
            <input v-model="form.supplier_name" type="text" class="input" required />
          </div>
        </div>
      </form>
    </Modal>

    <!-- Delete Confirmation -->
    <ConfirmDialog
      :show="showDeleteDialog"
      :loading="deleting"
      title="Delete Product"
      :message="`Are you sure you want to delete '${productToDelete?.name}'? This action cannot be undone.`"
      @close="showDeleteDialog = false"
      @confirm="deleteProduct"
    />

    <!-- Toast -->
    <Toast :show="toast.show" :message="toast.message" :type="toast.type" @close="toast.show = false" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { productService } from '../services/api'
import PageHeader from '../components/PageHeader.vue'
import Modal from '../components/Modal.vue'
import ConfirmDialog from '../components/ConfirmDialog.vue'
import LoadingSpinner from '../components/LoadingSpinner.vue'
import EmptyState from '../components/EmptyState.vue'
import Toast from '../components/Toast.vue'

const products = ref([])
const loading = ref(true)
const saving = ref(false)
const deleting = ref(false)
const showModal = ref(false)
const showDeleteDialog = ref(false)
const isEditing = ref(false)
const productToDelete = ref(null)

const form = ref({
  product_code: '',
  name: '',
  category: '',
  price_buy: 0,
  price_sell: 0,
  measure_unit: '',
  supplier_name: ''
})

const toast = ref({ show: false, message: '', type: 'success' })

const showToast = (message, type = 'success') => {
  toast.value = { show: true, message, type }
  setTimeout(() => toast.value.show = false, 3000)
}

const fetchProducts = async () => {
  try {
    loading.value = true
    const response = await productService.getAll()
    products.value = response.data.products || response.data || []
  } catch (error) {
    showToast('Failed to load products', 'error')
  } finally {
    loading.value = false
  }
}

const openCreateModal = () => {
  isEditing.value = false
  form.value = { product_code: '', name: '', category: '', price_buy: 0, price_sell: 0, measure_unit: '', supplier_name: '' }
  showModal.value = true
}

const openEditModal = (product) => {
  isEditing.value = true
  form.value = { ...product }
  showModal.value = true
}

const closeModal = () => {
  showModal.value = false
}

const saveProduct = async () => {
  try {
    saving.value = true
    if (isEditing.value) {
      await productService.update(form.value.product_code, form.value)
      showToast('Product updated successfully')
    } else {
      await productService.create(form.value)
      showToast('Product created successfully')
    }
    closeModal()
    fetchProducts()
  } catch (error) {
    showToast(error.response?.data?.message || 'Failed to save product', 'error')
  } finally {
    saving.value = false
  }
}

const confirmDelete = (product) => {
  productToDelete.value = product
  showDeleteDialog.value = true
}

const deleteProduct = async () => {
  try {
    deleting.value = true
    await productService.delete(productToDelete.value.product_code)
    showToast('Product deleted successfully')
    showDeleteDialog.value = false
    fetchProducts()
  } catch (error) {
    showToast('Failed to delete product', 'error')
  } finally {
    deleting.value = false
  }
}

onMounted(fetchProducts)
</script>
