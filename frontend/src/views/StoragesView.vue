<template>
  <div>
    <PageHeader title="Storage" subtitle="View product storage across warehouses">
      <template #actions>
        <button @click="openCreateModal" class="btn btn-primary flex items-center gap-2">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
          </svg>
          Add Storage
        </button>
      </template>
    </PageHeader>

    <LoadingSpinner v-if="loading" message="Loading storage records..." />

    <EmptyState 
      v-else-if="storages.length === 0" 
      title="No storage records yet"
      message="Storage records are created when products are added to warehouses."
    >
      <button @click="openCreateModal" class="btn btn-primary">Add Storage</button>
    </EmptyState>

    <div v-else class="card">
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="border-b border-gray-100">
              <th class="table-header">ID</th>
              <th class="table-header">Product Code</th>
              <th class="table-header">Warehouse</th>
              <th class="table-header">Quantity</th>
              <th class="table-header text-right">Actions</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">
            <tr v-for="storage in storages" :key="storage.id" class="hover:bg-gray-50 transition-colors">
              <td class="table-cell font-medium text-gray-500">#{{ storage.id }}</td>
              <td class="table-cell">
                <span class="px-2.5 py-1 bg-primary-50 text-primary-700 rounded-full text-xs font-medium">
                  {{ storage.product_code }}
                </span>
              </td>
              <td class="table-cell font-medium text-gray-900">{{ storage.warehouse_name }}</td>
              <td class="table-cell">
                <span 
                  class="px-3 py-1 rounded-full text-sm font-medium"
                  :class="storage.quantity > 10 ? 'bg-emerald-50 text-emerald-700' : storage.quantity > 0 ? 'bg-amber-50 text-amber-700' : 'bg-red-50 text-red-700'"
                >
                  {{ storage.quantity }}
                </span>
              </td>
              <td class="table-cell text-right">
                <button @click="openUpdateModal(storage)" class="p-2 text-gray-400 hover:text-primary-600 hover:bg-primary-50 rounded-lg transition-colors">
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
                  </svg>
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Create Modal -->
    <Modal 
      :show="showCreateModal" 
      title="Add Storage"
      :loading="saving"
      @close="showCreateModal = false"
      @submit="createStorage"
    >
      <form @submit.prevent="createStorage" class="space-y-4">
        <div>
          <label class="label">Product Code *</label>
          <input v-model="createForm.product_code" type="text" class="input" required />
        </div>
        <div>
          <label class="label">Warehouse Name *</label>
          <input v-model="createForm.warehouse_name" type="text" class="input" required />
        </div>
        <div>
          <label class="label">Quantity *</label>
          <input v-model.number="createForm.quantity" type="number" class="input" required />
        </div>
      </form>
    </Modal>

    <!-- Update Modal -->
    <Modal 
      :show="showUpdateModal" 
      title="Update Storage Quantity"
      :loading="saving"
      @close="showUpdateModal = false"
      @submit="updateStorage"
    >
      <form @submit.prevent="updateStorage" class="space-y-4">
        <div class="bg-gray-50 rounded-lg p-4 mb-4">
          <p class="text-sm text-gray-500">Product: <span class="font-medium text-gray-900">{{ updateForm.product_code }}</span></p>
          <p class="text-sm text-gray-500">Warehouse: <span class="font-medium text-gray-900">{{ updateForm.warehouse_name }}</span></p>
          <p class="text-sm text-gray-500">Current Quantity: <span class="font-medium text-gray-900">{{ updateForm.current_quantity }}</span></p>
        </div>
        <div>
          <label class="label">Update Type *</label>
          <select v-model="updateForm.type" class="input">
            <option value="insert">Insert (Add to quantity)</option>
            <option value="update">Update (Replace quantity)</option>
          </select>
        </div>
        <div>
          <label class="label">Quantity *</label>
          <input v-model.number="updateForm.quantity" type="number" class="input" required />
        </div>
      </form>
    </Modal>

    <Toast :show="toast.show" :message="toast.message" :type="toast.type" @close="toast.show = false" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { storageService } from '../services/api'
import PageHeader from '../components/PageHeader.vue'
import Modal from '../components/Modal.vue'
import LoadingSpinner from '../components/LoadingSpinner.vue'
import EmptyState from '../components/EmptyState.vue'
import Toast from '../components/Toast.vue'

const storages = ref([])
const loading = ref(true)
const saving = ref(false)
const showCreateModal = ref(false)
const showUpdateModal = ref(false)

const createForm = ref({
  product_code: '',
  warehouse_name: '',
  quantity: 0
})

const updateForm = ref({
  product_code: '',
  warehouse_name: '',
  current_quantity: 0,
  quantity: 0,
  type: 'insert'
})

const toast = ref({ show: false, message: '', type: 'success' })

const showToast = (message, type = 'success') => {
  toast.value = { show: true, message, type }
  setTimeout(() => toast.value.show = false, 3000)
}

const fetchStorages = async () => {
  try {
    loading.value = true
    const response = await storageService.getAll()
    storages.value = response.data.results || response.data || []
  } catch (error) {
    showToast('Failed to load storage records', 'error')
  } finally {
    loading.value = false
  }
}

const openCreateModal = () => {
  createForm.value = { product_code: '', warehouse_name: '', quantity: 0 }
  showCreateModal.value = true
}

const openUpdateModal = (storage) => {
  updateForm.value = {
    product_code: storage.product_code,
    warehouse_name: storage.warehouse_name,
    current_quantity: storage.quantity,
    quantity: 0,
    type: 'insert'
  }
  showUpdateModal.value = true
}

const createStorage = async () => {
  try {
    saving.value = true
    await storageService.create(createForm.value)
    showToast('Storage record created successfully')
    showCreateModal.value = false
    fetchStorages()
  } catch (error) {
    showToast(error.response?.data?.message || 'Failed to create storage record', 'error')
  } finally {
    saving.value = false
  }
}

const updateStorage = async () => {
  try {
    saving.value = true
    await storageService.update(
      updateForm.value.product_code, 
      updateForm.value.warehouse_name, 
      updateForm.value.type,
      { quantity: updateForm.value.quantity }
    )
    showToast('Storage updated successfully')
    showUpdateModal.value = false
    fetchStorages()
  } catch (error) {
    showToast(error.response?.data?.message || 'Failed to update storage', 'error')
  } finally {
    saving.value = false
  }
}

onMounted(fetchStorages)
</script>
