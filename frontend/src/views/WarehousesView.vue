<template>
  <div>
    <PageHeader title="Warehouses" subtitle="Manage your warehouses">
      <template #actions>
        <button @click="openCreateModal" class="btn btn-primary flex items-center gap-2">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
          </svg>
          Add Warehouse
        </button>
      </template>
    </PageHeader>

    <LoadingSpinner v-if="loading" message="Loading warehouses..." />

    <EmptyState 
      v-else-if="warehouses.length === 0" 
      title="No warehouses yet"
      message="Get started by adding your first warehouse."
    >
      <button @click="openCreateModal" class="btn btn-primary">Add Warehouse</button>
    </EmptyState>

    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <div v-for="warehouse in warehouses" :key="warehouse.id" class="card p-6">
        <div class="flex items-start justify-between mb-4">
          <div class="w-12 h-12 bg-primary-100 rounded-xl flex items-center justify-center">
            <svg class="w-6 h-6 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/>
            </svg>
          </div>
          <div class="flex items-center gap-1">
            <button @click="openEditModal(warehouse)" class="p-2 text-gray-400 hover:text-primary-600 hover:bg-primary-50 rounded-lg transition-colors">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
              </svg>
            </button>
            <button @click="confirmDelete(warehouse)" class="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
              </svg>
            </button>
          </div>
        </div>
        
        <h3 class="text-lg font-semibold text-gray-900 mb-1">{{ warehouse.name }}</h3>
        <div class="flex items-center gap-2 text-gray-500">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/>
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"/>
          </svg>
          <span class="text-sm">{{ warehouse.city || 'No city specified' }}</span>
        </div>
        
        <div class="mt-4 pt-4 border-t border-gray-100">
          <span class="text-xs font-medium text-gray-400 uppercase">Warehouse ID</span>
          <p class="text-primary-600 font-semibold">#{{ warehouse.id }}</p>
        </div>
      </div>
    </div>

    <Modal 
      :show="showModal" 
      :title="isEditing ? 'Edit Warehouse' : 'Add Warehouse'"
      :loading="saving"
      @close="closeModal"
      @submit="saveWarehouse"
    >
      <form @submit.prevent="saveWarehouse" class="space-y-4">
        <div>
          <label class="label">Name *</label>
          <input v-model="form.name" type="text" class="input" required />
        </div>
        <div>
          <label class="label">City</label>
          <input v-model="form.city" type="text" class="input" />
        </div>
      </form>
    </Modal>

    <ConfirmDialog
      :show="showDeleteDialog"
      :loading="deleting"
      title="Delete Warehouse"
      :message="`Are you sure you want to delete '${warehouseToDelete?.name}'? This action cannot be undone.`"
      @close="showDeleteDialog = false"
      @confirm="deleteWarehouse"
    />

    <Toast :show="toast.show" :message="toast.message" :type="toast.type" @close="toast.show = false" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { warehouseService } from '../services/api'
import PageHeader from '../components/PageHeader.vue'
import Modal from '../components/Modal.vue'
import ConfirmDialog from '../components/ConfirmDialog.vue'
import LoadingSpinner from '../components/LoadingSpinner.vue'
import EmptyState from '../components/EmptyState.vue'
import Toast from '../components/Toast.vue'

const warehouses = ref([])
const loading = ref(true)
const saving = ref(false)
const deleting = ref(false)
const showModal = ref(false)
const showDeleteDialog = ref(false)
const isEditing = ref(false)
const warehouseToDelete = ref(null)

const form = ref({
  name: '',
  city: ''
})

const toast = ref({ show: false, message: '', type: 'success' })

const showToast = (message, type = 'success') => {
  toast.value = { show: true, message, type }
  setTimeout(() => toast.value.show = false, 3000)
}

const fetchWarehouses = async () => {
  try {
    loading.value = true
    const response = await warehouseService.getAll()
    warehouses.value = response.data.results || response.data || []
  } catch (error) {
    showToast('Failed to load warehouses', 'error')
  } finally {
    loading.value = false
  }
}

const openCreateModal = () => {
  isEditing.value = false
  form.value = { name: '', city: '' }
  showModal.value = true
}

const openEditModal = (warehouse) => {
  isEditing.value = true
  form.value = { ...warehouse }
  showModal.value = true
}

const closeModal = () => {
  showModal.value = false
}

const saveWarehouse = async () => {
  try {
    saving.value = true
    if (isEditing.value) {
      await warehouseService.update(form.value.id, form.value)
      showToast('Warehouse updated successfully')
    } else {
      await warehouseService.create(form.value)
      showToast('Warehouse created successfully')
    }
    closeModal()
    fetchWarehouses()
  } catch (error) {
    showToast(error.response?.data?.message || 'Failed to save warehouse', 'error')
  } finally {
    saving.value = false
  }
}

const confirmDelete = (warehouse) => {
  warehouseToDelete.value = warehouse
  showDeleteDialog.value = true
}

const deleteWarehouse = async () => {
  try {
    deleting.value = true
    await warehouseService.delete(warehouseToDelete.value.id)
    showToast('Warehouse deleted successfully')
    showDeleteDialog.value = false
    fetchWarehouses()
  } catch (error) {
    showToast('Failed to delete warehouse', 'error')
  } finally {
    deleting.value = false
  }
}

onMounted(fetchWarehouses)
</script>
