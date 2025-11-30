<template>
  <div>
    <PageHeader title="Suppliers" subtitle="Manage your suppliers">
      <template #actions>
        <button @click="openCreateModal" class="btn btn-primary flex items-center gap-2">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
          </svg>
          Add Supplier
        </button>
      </template>
    </PageHeader>

    <LoadingSpinner v-if="loading" message="Loading suppliers..." />

    <EmptyState 
      v-else-if="suppliers.length === 0" 
      title="No suppliers yet"
      message="Get started by adding your first supplier."
    >
      <button @click="openCreateModal" class="btn btn-primary">Add Supplier</button>
    </EmptyState>

    <div v-else class="card">
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="border-b border-gray-100">
              <th class="table-header">ID</th>
              <th class="table-header">Name</th>
              <th class="table-header">City</th>
              <th class="table-header">Zipcode</th>
              <th class="table-header">Contact Person</th>
              <th class="table-header">Phone</th>
              <th class="table-header">Email</th>
              <th class="table-header text-right">Actions</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">
            <tr v-for="supplier in suppliers" :key="supplier.id" class="hover:bg-gray-50 transition-colors">
              <td class="table-cell font-medium text-primary-600">#{{ supplier.id }}</td>
              <td class="table-cell font-medium text-gray-900">{{ supplier.name }}</td>
              <td class="table-cell">{{ supplier.city || 'N/A' }}</td>
              <td class="table-cell">{{ supplier.zipcode || 'N/A' }}</td>
              <td class="table-cell">{{ supplier.contact_person || 'N/A' }}</td>
              <td class="table-cell">{{ supplier.phone || 'N/A' }}</td>
              <td class="table-cell">{{ supplier.email || 'N/A' }}</td>
              <td class="table-cell text-right">
                <div class="flex items-center justify-end gap-2">
                  <button @click="openEditModal(supplier)" class="p-2 text-gray-400 hover:text-primary-600 hover:bg-primary-50 rounded-lg transition-colors">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
                    </svg>
                  </button>
                  <button @click="confirmDelete(supplier)" class="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors">
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

    <Modal 
      :show="showModal" 
      :title="isEditing ? 'Edit Supplier' : 'Add Supplier'"
      :loading="saving"
      @close="closeModal"
      @submit="saveSupplier"
    >
      <form @submit.prevent="saveSupplier" class="space-y-4">
        <div>
          <label class="label">Name *</label>
          <input v-model="form.name" type="text" class="input" required />
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="label">City</label>
            <input v-model="form.city" type="text" class="input" />
          </div>
          <div>
            <label class="label">Zipcode</label>
            <input v-model="form.zipcode" type="text" class="input" />
          </div>
        </div>
        <div>
          <label class="label">Contact Person</label>
          <input v-model="form.contact_person" type="text" class="input" />
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="label">Phone</label>
            <input v-model="form.phone" type="text" class="input" />
          </div>
          <div>
            <label class="label">Email</label>
            <input v-model="form.email" type="email" class="input" />
          </div>
        </div>
      </form>
    </Modal>

    <ConfirmDialog
      :show="showDeleteDialog"
      :loading="deleting"
      title="Delete Supplier"
      :message="`Are you sure you want to delete '${supplierToDelete?.name}'? This action cannot be undone.`"
      @close="showDeleteDialog = false"
      @confirm="deleteSupplier"
    />

    <Toast :show="toast.show" :message="toast.message" :type="toast.type" @close="toast.show = false" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { supplierService } from '../services/api'
import PageHeader from '../components/PageHeader.vue'
import Modal from '../components/Modal.vue'
import ConfirmDialog from '../components/ConfirmDialog.vue'
import LoadingSpinner from '../components/LoadingSpinner.vue'
import EmptyState from '../components/EmptyState.vue'
import Toast from '../components/Toast.vue'

const suppliers = ref([])
const loading = ref(true)
const saving = ref(false)
const deleting = ref(false)
const showModal = ref(false)
const showDeleteDialog = ref(false)
const isEditing = ref(false)
const supplierToDelete = ref(null)

const form = ref({
  name: '',
  city: '',
  zipcode: '',
  contact_person: '',
  phone: '',
  email: ''
})

const toast = ref({ show: false, message: '', type: 'success' })

const showToast = (message, type = 'success') => {
  toast.value = { show: true, message, type }
  setTimeout(() => toast.value.show = false, 3000)
}

const fetchSuppliers = async () => {
  try {
    loading.value = true
    const response = await supplierService.getAll()
    suppliers.value = response.data.results || response.data || []
  } catch (error) {
    showToast('Failed to load suppliers', 'error')
  } finally {
    loading.value = false
  }
}

const openCreateModal = () => {
  isEditing.value = false
  form.value = { name: '', city: '', zipcode: '', contact_person: '', phone: '', email: '' }
  showModal.value = true
}

const openEditModal = (supplier) => {
  isEditing.value = true
  form.value = { ...supplier }
  showModal.value = true
}

const closeModal = () => {
  showModal.value = false
}

const saveSupplier = async () => {
  try {
    saving.value = true
    if (isEditing.value) {
      await supplierService.update(form.value.id, form.value)
      showToast('Supplier updated successfully')
    } else {
      await supplierService.create(form.value)
      showToast('Supplier created successfully')
    }
    closeModal()
    fetchSuppliers()
  } catch (error) {
    showToast(error.response?.data?.message || 'Failed to save supplier', 'error')
  } finally {
    saving.value = false
  }
}

const confirmDelete = (supplier) => {
  supplierToDelete.value = supplier
  showDeleteDialog.value = true
}

const deleteSupplier = async () => {
  try {
    deleting.value = true
    await supplierService.delete(supplierToDelete.value.id)
    showToast('Supplier deleted successfully')
    showDeleteDialog.value = false
    fetchSuppliers()
  } catch (error) {
    showToast('Failed to delete supplier', 'error')
  } finally {
    deleting.value = false
  }
}

onMounted(fetchSuppliers)
</script>
