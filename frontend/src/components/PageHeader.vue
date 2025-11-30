<template>
  <div class="flex items-center justify-between mb-6">
    <div>
      <h1 class="text-2xl font-bold text-gray-900">{{ title }}</h1>
      <p v-if="subtitle" class="text-gray-500 mt-1">{{ subtitle }}</p>
    </div>
    <slot name="actions"></slot>
  </div>
</template>

<script setup>
defineProps({
  title: String,
  subtitle: String
})
</script>
