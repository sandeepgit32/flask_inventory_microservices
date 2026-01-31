<template>
  <div v-if="!isAuthPage" class="min-h-screen bg-gray-50">
    <!-- Navigation -->
    <nav class="bg-white shadow-sm border-b border-gray-100 sticky top-0 z-50">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between h-16">
          <div class="flex items-center">
            <router-link to="/" class="flex items-center gap-3">
              <div class="w-10 h-10 bg-primary-600 rounded-lg flex items-center justify-center">
                <svg class="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M3.375 3C2.339 3 1.5 3.84 1.5 4.875v.75c0 1.036.84 1.875 1.875 1.875h17.25c1.035 0 1.875-.84 1.875-1.875v-.75C22.5 3.839 21.66 3 20.625 3H3.375z"/>
                  <path fill-rule="evenodd" d="M3.087 9l.54 9.176A3 3 0 006.62 21h10.757a3 3 0 002.995-2.824L20.913 9H3.087zm6.163 3.75A.75.75 0 0110 12h4a.75.75 0 010 1.5h-4a.75.75 0 01-.75-.75z" clip-rule="evenodd"/>
                </svg>
              </div>
              <span class="text-xl font-bold text-gray-900">Inventory</span>
            </router-link>
          </div>
          
          <!-- Desktop Navigation -->
          <div class="hidden md:flex items-center gap-1">
            <router-link 
              v-for="item in navItems" 
              :key="item.path" 
              :to="item.path"
              class="px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200"
              :class="$route.path === item.path ? 'bg-primary-50 text-primary-700' : 'text-gray-600 hover:bg-gray-100'"
            >
              {{ item.name }}
            </router-link>
            
            <!-- User Menu -->
            <div class="ml-4 flex items-center gap-3 pl-4 border-l border-gray-200">
              <span class="text-sm text-gray-600">{{ currentUser?.username }}</span>
              <button 
                @click="handleLogout" 
                class="px-4 py-2 rounded-lg text-sm font-medium text-gray-600 hover:bg-red-50 hover:text-red-600 transition-all duration-200"
              >
                Logout
              </button>
            </div>
          </div>

          <!-- Mobile menu button -->
          <div class="md:hidden flex items-center">
            <button @click="mobileMenuOpen = !mobileMenuOpen" class="p-2 rounded-lg text-gray-600 hover:bg-gray-100">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path v-if="!mobileMenuOpen" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/>
                <path v-else stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
              </svg>
            </button>
          </div>
        </div>
      </div>

      <!-- Mobile menu -->
      <div v-if="mobileMenuOpen" class="md:hidden border-t border-gray-100">
        <div class="px-2 pt-2 pb-3 space-y-1">
          <router-link 
            v-for="item in navItems" 
            :key="item.path" 
            :to="item.path"
            @click="mobileMenuOpen = false"
            class="block px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200"
            :class="$route.path === item.path ? 'bg-primary-50 text-primary-700' : 'text-gray-600 hover:bg-gray-100'"
          >
            {{ item.name }}
          </router-link>
          <button 
            @click="handleLogout"
            class="w-full text-left px-4 py-2 rounded-lg text-sm font-medium text-red-600 hover:bg-red-50 transition-all duration-200"
          >
            Logout
          </button>
        </div>
      </div>
    </nav>

    <!-- Main Content -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <router-view />
    </main>

    <!-- Footer -->
    <footer class="bg-white border-t border-gray-100 mt-auto">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <p class="text-center text-sm text-gray-500">
          © 2025 Inventory Management System. Built with Vue 3 & Tailwind CSS.
        </p>
      </div>
    </footer>
  </div>
  
  <!-- Auth pages without navigation -->
  <div v-else class="min-h-screen">
    <router-view />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { authService } from '@/services/api'

const router = useRouter()
const route = useRoute()
const mobileMenuOpen = ref(false)
const currentUser = ref(null)

const isAuthPage = computed(() => {
  return route.path === '/login' || route.path === '/register'
})

const navItems = [
  { name: 'Products', path: '/products' },
  { name: 'Suppliers', path: '/suppliers' },
  { name: 'Customers', path: '/customers' },
  { name: 'Inventory', path: '/inventory' },
  { name: 'Procurements', path: '/procurements' },
  { name: 'Orders', path: '/orders' },
]

const handleLogout = () => {
  authService.logout()
  router.push('/login')
}

onMounted(() => {
  currentUser.value = authService.getCurrentUser()
})
</script>
