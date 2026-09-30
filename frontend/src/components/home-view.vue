<script setup lang="ts">
import {
  useListDealsApiV1CatalogDealsGet,
  useListFreeGamesApiV1CatalogFreeGamesGet,
  useListStoresApiV1CatalogStoresGet,
} from '@/api/catalog/catalog'
import type { ListDealsApiV1CatalogDealsGetParams } from '@/api/model'
import { computed, ref } from 'vue'

import DealGrid from './deal-grid.vue'
import FilterBar from './filter-bar.vue'
import { emptyFilters, type DealFilters } from './filters'
import FreeGamesStrip from './free-games-strip.vue'
import RefreshButton from './refresh-button.vue'

const filters = ref<DealFilters>(emptyFilters())

const dealParams = computed<ListDealsApiV1CatalogDealsGetParams>(() => {
  const params: ListDealsApiV1CatalogDealsGetParams = {}
  if (filters.value.store.length > 0) params.store = filters.value.store
  if (filters.value.maxKesPrice !== '') params.max_kes_price = filters.value.maxKesPrice
  if (filters.value.minDiscountPercent !== '') {
    params.min_discount_percent = Number(filters.value.minDiscountPercent)
  }
  if (filters.value.q.trim() !== '') params.q = filters.value.q.trim()
  return params
})

const storesQuery = useListStoresApiV1CatalogStoresGet()
const freeQuery = useListFreeGamesApiV1CatalogFreeGamesGet()
const dealsQuery = useListDealsApiV1CatalogDealsGet(dealParams)

const stores = computed(() => storesQuery.data.value?.data ?? [])
const games = computed(() => freeQuery.data.value?.data ?? [])
const deals = computed(() => {
  const data = dealsQuery.data.value?.data
  return Array.isArray(data) ? data : []
})

const storesFailed = storesQuery.isError
const freePending = freeQuery.isPending
const freeFailed = freeQuery.isError
const dealsPending = dealsQuery.isPending
const dealsFailed = dealsQuery.isError

const filtered = computed(
  () =>
    filters.value.store.length > 0 ||
    filters.value.maxKesPrice !== '' ||
    filters.value.minDiscountPercent !== '' ||
    filters.value.q.trim() !== '',
)
</script>

<template>
  <div class="min-h-dvh bg-paper font-sans text-ink dark:bg-night dark:text-mist">
    <header class="border-b border-line dark:border-night-line">
      <div class="mx-auto grid max-w-7xl grid-cols-[1fr_auto] grid-rows-[4rem_auto] px-4">
        <p class="col-start-1 row-start-1 flex items-center text-lg font-semibold tracking-tight">
          Fynd
        </p>
        <refresh-button
          class="col-start-2 row-start-1 row-span-2 flex flex-col items-end justify-center"
          :stores="stores"
        />
      </div>
    </header>
    <main class="mx-auto w-full max-w-7xl px-4 pb-16">
      <free-games-strip :games="games" :pending="freePending" :failed="freeFailed" />
      <section class="mt-10">
        <h1 class="text-2xl font-semibold tracking-tight">Deals</h1>
        <p
          v-if="storesFailed"
          class="mt-4 text-base text-ink dark:text-mist"
          role="alert"
        >
          Stores did not load.
        </p>
        <filter-bar class="mt-4" v-model="filters" :stores="stores" />
        <deal-grid
          class="mt-6"
          :deals="deals"
          :pending="dealsPending"
          :failed="dealsFailed"
          :filtered="filtered"
        />
      </section>
    </main>
  </div>
</template>
