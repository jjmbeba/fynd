<script setup lang="ts">
import type { DealRead } from '@/api/model'
import { formatKes, kesBaseAmount } from '@/lib/money'
import { computed } from 'vue'

const props = defineProps<{
  deal: DealRead
}>()

const price = computed(() => formatKes(Number(props.deal.kes_amount)))
const basePrice = computed(() => {
  const base = kesBaseAmount(props.deal)
  if (base === null) return null
  if (Math.abs(base - Number(props.deal.kes_amount)) < 0.5) return null
  return formatKes(base)
})
</script>

<template>
  <article class="overflow-hidden rounded-lg border border-line bg-card dark:border-night-line dark:bg-night-card">
    <div class="aspect-[460/215] bg-line dark:bg-night-line">
      <img
        v-if="deal.image_url"
        :src="deal.image_url"
        :alt="deal.title"
        class="h-full w-full object-cover"
      />
    </div>
    <div class="flex flex-col gap-2 p-4">
      <h3 class="text-base font-medium leading-snug">{{ deal.title }}</h3>
      <p class="text-sm text-muted dark:text-night-muted">{{ deal.store_display_name }}</p>
      <p class="font-mono text-lg font-medium text-sale">
        <span class="sr-only">Current price</span>
        {{ price }}
      </p>
      <p v-if="basePrice" class="font-mono text-sm text-muted line-through dark:text-night-muted">
        <span class="sr-only">Original price</span>
        {{ basePrice }}
      </p>
      <p v-if="deal.discount_percent != null" class="text-sm font-medium text-sale">
        {{ deal.discount_percent }}% off
      </p>
    </div>
  </article>
</template>
