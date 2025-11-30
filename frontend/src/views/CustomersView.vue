<template>
  <div>
    <PageHeader title="Customers" subtitle="Manage your customers">
      <template #actions>
        <button @click="openCreateModal" class="btn btn-primary flex items-center gap-2">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
          </svg>
          Add Customer
        </button>
      </template>
    </PageHeader>

    <LoadingSpinner v-if="loading" message="Loading customers..." />

    <EmptyState 
      v-else-if="customers.length === 0" 
      title="No customers yet"
      message="Get started by adding your first customer."
    >
      <button @click="openCreateModal" class="btn btn-primary">Add Customer</button>
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
              <th class="table-header">Warehouse</th>
              <th class="table-header text-right">Actions</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">
            <tr v-for="customer in customers" :key="customer.id" class="hover:bg-gray-50 transition-colors">
              <td class="table-cell font-medium text-primary-600">#{{ customer.id }}</td>
              <td class="table-cell font-medium text-gray-900">{{ customer.name }}</td>
              <td class="table-cell">{{ customer.city || 'N/A' }}</td>
              <td class="table-cell">{{ customer.zipcode || 'N/A' }}</td>
              <td class="table-cell">{{ customer.contact_person || 'N/A' }}</td>
              <td class="table-cell">{{ customer.phone || 'N/A' }}</td>
              <td class="table-cell">{{ customer.email || 'N/A' }}</td>
              <td class="table-cell">
                <span v-if="customer.warehouse_id" class="px-2.5 py-1 bg-primary-50 text-primary-700 rounded-full text-xs font-medium">
                  #{{ customer.warehouse_id }}
                </span>
                <span v-else class="text-gray-400">N/A</span>
              </td>
              <td class="table-cell text-right">
                <div class="flex items-center justify-end gap-2">
                  <button @click="openEditModal(customer)" class="p-2 text-gray-400 hover:text-primary-600 hover:bg-primary-50 rounded-lg transition-colors">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
                    </svg>
                  </button>
                  <button @click="confirmDelete(customer)" class="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors">
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
      :title="isEditing ? 'Edit Customer' : 'Add Customer'"
      :loading="saving"
      @close="closeModal"
      @submit="saveCustomer"
    >
      <form @submit.prevent="saveCustomer" class="space-y-4">
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
        <div>
          <label class="label">Warehouse ID</label>
          <input v-model.number="form.warehouse_id" type="number" class="input" />
        </div>
      </form>
    </Modal>

    <ConfirmDialog
      :show="showDeleteDialog"
      :loading="deleting"
      title="Delete Customer"
      :message="`Are you sure you want to delete '${customerToDelete?.name}'? This action cannot be undone.`"
      @close="showDeleteDialog = false"
      @confirm="deleteCustomer"
    />

    <Toast :show="toast.show" :message="toast.message" :type="toast.type" @close="toast.show = false" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { customerService } from '../services/api'
import PageHeader from '../components/PageHeader.vue'
import Modal from '../components/Modal.vue'
import ConfirmDialog from '../components/ConfirmDialog.vue'
import LoadingSpinner from '../components/LoadingSpinner.vue'
import EmptyState from '../components/EmptyState.vue'
import Toast from '../components/Toast.vue'

const customers = ref([])
const loading = ref(true)
const saving = ref(false)
const deleting = ref(false)
const showModal = ref(false)
const showDeleteDialog = ref(false)
const isEditing = ref(false)
const customerToDelete = ref(null)

const form = ref({
  name: '',
  city: '',
  zipcode: '',
  contact_person: '',
  phone: '',
  email: '',
  warehouse_id: null
})

const toast = ref({ show: false, message: '', type: 'success' })

const showToast = (message, type = 'success') => {
  toast.value = { show: true, message, type }
  setTimeout(() => toast.value.show = false, 3000)
}

const fetchCustomers = async () => {
  try {
    loading.value = true
    const response = await customerService.getAll()
    customers.value = response.data.results || response.data || []
  } catch (error) {
    showToast('Failed to load customers', 'error')
  } finally {
    loading.value = false
  }
}

const openCreateModal = () => {
  isEditing.value = false
  form.value = { name: '', city: '', zipcode: '', contact_person: '', phone: '', email: '', warehouse_id: null }
  showModal.value = true
}

const openEditModal = (customer) => {
  isEditing.value = true
  form.value = { ...customer }
  showModal.value = true
}

const closeModal = () => {
  showModal.value = false
}

const saveCustomer = async () => {
  try {
    saving.value = true
    if (isEditing.value) {
      await customerService.update(form.value.id, form.value)
      showToast('Customer updated successfully')
    } else {
      await customerService.create(form.value)
      showToast('Customer created successfully')
    }
    closeModal()
    fetchCustomers()
  } catch (error) {
    showToast(error.response?.data?.message || 'Failed to save customer', 'error')
  } finally {
    saving.value = false
  }
}

const confirmDelete = (customer) => {
  customerToDelete.value = customer
  showDeleteDialog.value = true
}

const deleteCustomer = async () => {
  try {
    deleting.value = true
    await customerService.delete(customerToDelete.value.id)
    showToast('Customer deleted successfully')
    showDeleteDialog.value = false
    fetchCustomers()
  } catch (error) {
    showToast('Failed to delete customer', 'error')
  } finally {
    deleting.value = false
  }
}

onMounted(fetchCustomers)
</script>
