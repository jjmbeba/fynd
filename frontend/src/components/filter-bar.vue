<script setup lang="ts">
import type { StoreRead } from '@/api/model';

import type { DealFilters } from './filters';

const props = defineProps<{
  stores: StoreRead[]
  modelValue: DealFilters
}>()

const emit = defineEmits<{
  'update:modelValue': [filters: DealFilters]
}>()

function update(patch: Partial<DealFilters>) {
  emit('update:modelValue', { ...props.modelValue, ...patch })
}

function onStoreToggle(slug: string, checked: boolean) {
  const store = checked
    ? props.modelValue.store.includes(slug)
      ? props.modelValue.store
      : [...props.modelValue.store, slug]
    : props.modelValue.store.filter((item) => item !== slug)
  update({ store })
}
</script>

<template>
  <form class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4" @submit.prevent>
    <fieldset v-if="stores.length > 0" class="flex flex-col gap-2">
      <legend class="text-sm font-medium">Stores</legend>
      <label
        v-for="store in stores"
        :key="store.slug"
        class="flex items-center gap-2 text-sm"
      >
        <input
          type="checkbox"
          class="size-4 rounded-lg border-line accent-sale"
          :name="`store-${store.slug}`"
          :checked="modelValue.store.includes(store.slug)"
          @change="onStoreToggle(store.slug, ($event.target as HTMLInputElement).checked)"
        />
        {{ store.display_name }}
      </label>
    </fieldset>

    <label class="flex flex-col gap-2 text-sm font-medium">
      Max price
      <input
        :value="modelValue.maxKesPrice"
        name="max_kes_price"
        type="number"
        min="0"
        inputmode="numeric"
        class="rounded-lg border border-line bg-card px-3 py-2 font-normal text-ink outline-none focus-visible:ring-2 focus-visible:ring-sale dark:border-night-line dark:bg-night-card dark:text-mist"
        @input="update({ maxKesPrice: ($event.target as HTMLInputElement).value })"
      />
    </label>

    <label class="flex flex-col gap-2 text-sm font-medium">
      Min discount
      <input
        :value="modelValue.minDiscountPercent"
        name="min_discount_percent"
        type="number"
        min="0"
        max="100"
        inputmode="numeric"
        class="rounded-lg border border-line bg-card px-3 py-2 font-normal text-ink outline-none focus-visible:ring-2 focus-visible:ring-sale dark:border-night-line dark:bg-night-card dark:text-mist"
        @input="update({ minDiscountPercent: ($event.target as HTMLInputElement).value })"
      />
    </label>

    <label class="flex flex-col gap-2 text-sm font-medium">
      Title
      <input
        :value="modelValue.q"
        name="q"
        type="search"
        class="rounded-lg border border-line bg-card px-3 py-2 font-normal text-ink outline-none focus-visible:ring-2 focus-visible:ring-sale dark:border-night-line dark:bg-night-card dark:text-mist"
        @input="update({ q: ($event.target as HTMLInputElement).value })"
      />
    </label>
  </form>
</template>
