<template>
  <div class="flex flex-col items-center justify-center py-12">
    <div class="w-16 h-16 border-4 border-primary-200 border-t-primary-600 rounded-full animate-spin"></div>
    <p class="mt-4 text-gray-500 font-medium">{{ message }}</p>
  </div>
</template>

<script setup>
defineProps({
  message: {
    type: String,
    default: 'Loading...'
  }
})
</script>
