<script setup lang="ts">
import type { DealRead } from '@/api/model'

import DealCard from './deal-card.vue'

defineProps<{
  deals: DealRead[]
  pending: boolean
  failed: boolean
  filtered: boolean
}>()
</script>

<template>
  <p v-if="failed" class="text-base text-ink dark:text-mist" role="alert">
    The catalog did not load. Refresh to try again.
  </p>
  <div
    v-else-if="pending"
    class="grid grid-cols-1 gap-4 min-[641px]:grid-cols-[repeat(auto-fill,minmax(280px,1fr))]"
    aria-busy="true"
  >
    <p class="sr-only">Loading deals</p>
    <div
      v-for="slot in 6"
      :key="slot"
      class="overflow-hidden rounded-lg border border-line dark:border-night-line"
    >
      <div class="aspect-[460/215] bg-line dark:bg-night-line" />
      <div class="flex flex-col gap-2 p-4">
        <div class="h-5 w-3/4 rounded-lg bg-line dark:bg-night-line" />
        <div class="h-4 w-1/3 rounded-lg bg-line dark:bg-night-line" />
        <div class="h-6 w-1/2 rounded-lg bg-line dark:bg-night-line" />
      </div>
    </div>
  </div>
  <p v-else-if="deals.length === 0" class="max-w-[65ch] text-base text-muted dark:text-night-muted">
    {{
      filtered
        ? 'No deals match these filters.'
        : 'No deals yet. Refresh to pull the latest prices.'
    }}
  </p>
  <div
    v-else
    class="grid grid-cols-1 gap-4 min-[641px]:grid-cols-[repeat(auto-fill,minmax(280px,1fr))]"
  >
    <deal-card v-for="deal in deals" :key="deal.listing_id" :deal="deal" />
  </div>
</template>
