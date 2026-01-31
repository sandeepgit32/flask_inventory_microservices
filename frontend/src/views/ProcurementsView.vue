<template>
  <div>
    <PageHeader title="Procurements" subtitle="Track purchases from suppliers">
      <template #actions>
        <button @click="openCreateModal" class="btn btn-primary flex items-center gap-2">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
          </svg>
          New Procurement
        </button>
      </template>
    </PageHeader>

    <LoadingSpinner v-if="loading" message="Loading procurements..." />

    <EmptyState 
      v-else-if="procurements.length === 0" 
      title="No procurements yet"
      message="Record your first purchase from a supplier."
    >
      <button @click="openCreateModal" class="btn btn-primary">New Procurement</button>
    </EmptyState>

    <div v-else class="card">
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="border-b border-gray-100">
              <th class="table-header">ID</th>
              <th class="table-header">Date</th>
              <th class="table-header">Supplier</th>
              <th class="table-header">Product</th>
              <th class="table-header">Quantity</th>
              <th class="table-header">Unit Price</th>
              <th class="table-header">Total Cost</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">
            <tr v-for="proc in procurements" :key="proc.id" class="hover:bg-gray-50 transition-colors">
              <td class="table-cell font-medium text-gray-500">#{{ proc.id }}</td>
              <td class="table-cell">{{ formatDate(proc.timestamp) }}</td>
              <td class="table-cell">
                <div>
                  <p class="font-medium text-gray-900">{{ proc.supplier?.name || proc.supplier_name }}</p>
                  <p class="text-xs text-gray-500">{{ proc.supplier?.city || 'N/A' }}</p>
                </div>
              </td>
              <td class="table-cell">
                <div>
                  <span class="px-2.5 py-1 bg-primary-50 text-primary-700 rounded-full text-xs font-medium">
                    {{ proc.product?.code || proc.product_code }}
                  </span>
                  <p class="text-sm text-gray-600 mt-1">{{ proc.product?.name || proc.product_name }}</p>
                </div>
              </td>
              <td class="table-cell font-medium">{{ proc.quantity }} {{ proc.product?.measure_unit || proc.measure_unit || '' }}</td>
              <td class="table-cell">${{ proc.unit_price?.toFixed(2) }}</td>
              <td class="table-cell">
                <span class="font-semibold text-emerald-600">${{ proc.total_cost?.toFixed(2) }}</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <Modal 
      :show="showModal" 
      title="New Procurement"
      :loading="saving"
      @close="closeModal"
      @submit="createProcurement"
    >
      <form @submit.prevent="createProcurement" class="space-y-4">
        <div class="border-b border-gray-100 pb-4 mb-4">
          <h4 class="font-medium text-gray-900 mb-3">Procurement Information</h4>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="label">Supplier *</label>
              <select v-model="form.supplier_id" class="input" required @change="onSupplierChange">
                <option value="">Select supplier</option>
                <option v-for="supplier in suppliers" :key="supplier.id" :value="supplier.id">
                  {{ supplier.name }} ({{ supplier.city }})
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
              <span class="font-medium text-gray-700">Total Cost:</span>
              <span class="text-xl font-bold text-emerald-600">${{ totalCost.toFixed(2) }}</span>
            </div>
          </div>
        </div>
      </form>
    </Modal>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { procurementService, supplierService, productService } from '@/services/api'
import PageHeader from '@/components/PageHeader.vue'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import EmptyState from '@/components/EmptyState.vue'
import Modal from '@/components/Modal.vue'

export default {
  name: 'ProcurementsView',
  components: { PageHeader, LoadingSpinner, EmptyState, Modal },
  setup() {
    const procurements = ref([])
    const suppliers = ref([])
    const products = ref([])
    const loading = ref(false)
    const saving = ref(false)
    const showModal = ref(false)
    
    const form = ref({
      supplier_id: '',
      product_id: '',
      quantity: 1,
      unit_price: 0
    })

    const totalCost = computed(() => {
      return form.value.quantity * form.value.unit_price
    })

    const formatDate = (timestamp) => {
      return new Date(timestamp).toLocaleString()
    }

    const loadProcurements = async () => {
      loading.value = true
      try {
        const response = await procurementService.getAll()
        procurements.value = response.data.procurements || response.data
      } catch (error) {
        console.error('Error loading procurements:', error)
      } finally {
        loading.value = false
      }
    }

    const loadSuppliers = async () => {
      try {
        const response = await supplierService.getAll()
        suppliers.value = response.data.suppliers || response.data
      } catch (error) {
        console.error('Error loading suppliers:', error)
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
      if (suppliers.value.length === 0) loadSuppliers()
      if (products.value.length === 0) loadProducts()
    }

    const closeModal = () => {
      showModal.value = false
      form.value = {
        supplier_id: '',
        product_id: '',
        quantity: 1,
        unit_price: 0
      }
    }

    const calculateTotal = () => {
      // Computed property handles this automatically
    }

    const onSupplierChange = () => {
      // Could filter products by supplier if needed
    }

    const onProductChange = () => {
      // Could auto-fill unit price from product if available
    }

    const createProcurement = async () => {
      saving.value = true
      try {
        await procurementService.create({
          supplier_id: parseInt(form.value.supplier_id),
          product_id: parseInt(form.value.product_id),
          quantity: form.value.quantity,
          unit_price: form.value.unit_price
        })
        closeModal()
        loadProcurements()
      } catch (error) {
        console.error('Error creating procurement:', error)
        alert('Failed to create procurement. Please try again.')
      } finally {
        saving.value = false
      }
    }

    onMounted(() => {
      loadProcurements()
    })

    return {
      procurements,
      suppliers,
      products,
      loading,
      saving,
      showModal,
      form,
      totalCost,
      formatDate,
      openCreateModal,
      closeModal,
      createProcurement,
      calculateTotal,
      onSupplierChange,
      onProductChange
    }
  }
}
</script>
