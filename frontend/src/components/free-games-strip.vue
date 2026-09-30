<script setup lang="ts">
import type { FreeGameRead } from '@/api/model'

defineProps<{
  games: FreeGameRead[]
  pending: boolean
  failed: boolean
}>()
</script>

<template>
  <section class="pt-8">
    <h2 class="text-2xl font-semibold tracking-tight">Free</h2>
    <p v-if="failed" class="mt-4 text-base text-ink dark:text-mist" role="alert">
      Free games did not load. Refresh to try again.
    </p>
    <div
      v-else-if="pending"
      class="mt-4 flex gap-4 overflow-hidden"
      aria-busy="true"
    >
      <p class="sr-only">Loading free games</p>
      <div
        v-for="slot in 3"
        :key="slot"
        class="w-64 shrink-0 overflow-hidden rounded-lg border border-line dark:border-night-line"
      >
        <div class="aspect-[460/215] bg-line dark:bg-night-line" />
      </div>
    </div>
    <p v-else-if="games.length === 0" class="mt-4 text-base text-muted dark:text-night-muted">
      Nothing is free right now.
    </p>
    <ul
      v-else
      class="mt-4 flex gap-4 overflow-x-auto pb-2"
    >
      <li
        v-for="game in games"
        :key="game.listing_id"
        class="w-64 shrink-0 snap-start overflow-hidden rounded-lg border border-line bg-card dark:border-night-line dark:bg-night-card"
      >
        <div class="aspect-[460/215] bg-line dark:bg-night-line">
          <img
            v-if="game.image_url"
            :src="game.image_url"
            :alt="game.title"
            class="h-full w-full object-cover"
          />
        </div>
        <div class="p-3">
          <p class="text-sm font-medium leading-snug">{{ game.title }}</p>
          <p class="mt-1 text-sm text-muted dark:text-night-muted">{{ game.store_display_name }}</p>
        </div>
      </li>
    </ul>
  </section>
</template>
