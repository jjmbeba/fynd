<script setup lang="ts">
import {
  getListDealsApiV1CatalogDealsGetQueryKey,
  getListFreeGamesApiV1CatalogFreeGamesGetQueryKey,
  getListStoresApiV1CatalogStoresGetQueryKey,
  useTriggerRefreshApiV1CatalogRefreshPost,
} from '@/api/catalog/catalog'
import type { StoreRead } from '@/api/model'
import { useQueryClient } from '@tanstack/vue-query'
import { computed } from 'vue'

const props = defineProps<{
  stores: StoreRead[]
}>()

const queryClient = useQueryClient()

const refresh = useTriggerRefreshApiV1CatalogRefreshPost({
  mutation: {
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: getListStoresApiV1CatalogStoresGetQueryKey(),
      })
      void queryClient.invalidateQueries({
        queryKey: getListFreeGamesApiV1CatalogFreeGamesGetQueryKey(),
      })
      void queryClient.invalidateQueries({
        queryKey: getListDealsApiV1CatalogDealsGetQueryKey(),
      })
    },
  },
})

const lines = computed(() => {
  const result = refresh.data.value
  if (!result) return []
  return result.data.stores.map((store) => {
    const name =
      props.stores.find((item) => item.slug === store.store_slug)?.display_name ?? store.store_slug
    if (store.status === 'error') return `${name} failed.`
    const noun = store.listings_observed === 1 ? 'listing' : 'listings'
    return `${name}: ${store.listings_observed} ${noun}`
  })
})

const pending = refresh.isPending
const failed = refresh.isError
</script>

<template>
  <div>
    <button
      type="button"
      class="rounded-lg bg-sale px-4 py-2 text-sm font-medium text-white active:scale-[0.98] motion-reduce:active:scale-100"
      :disabled="pending"
      @click="refresh.mutate()"
    >
      {{ pending ? 'Refreshing' : 'Refresh' }}
    </button>
    <p v-if="failed" class="pb-3 text-sm text-ink dark:text-mist" role="alert">Refresh failed.</p>
    <ul
      v-else-if="lines.length > 0"
      class="pb-3 text-right text-sm text-muted dark:text-night-muted"
    >
      <li v-for="line in lines" :key="line">{{ line }}</li>
    </ul>
  </div>
</template>
