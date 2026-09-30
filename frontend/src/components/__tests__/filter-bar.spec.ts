import { mount } from '@vue/test-utils'
import { defineComponent, ref } from 'vue'
import { describe, expect, it } from 'vitest'

import type { StoreRead } from '@/api/model'

import FilterBar from '../filter-bar.vue'
import { emptyFilters, type DealFilters } from '../filters'

const steam: StoreRead = {
  id: 1,
  slug: 'steam',
  display_name: 'Steam',
  is_active: true,
  created_at: '2026-06-01T00:00:00Z',
  updated_at: '2026-06-01T00:00:00Z',
}

const Harness = defineComponent({
  components: { FilterBar },
  setup() {
    const filters = ref<DealFilters>(emptyFilters())
    return { filters, stores: [steam] }
  },
  template: '<filter-bar v-model="filters" :stores="stores" />',
})

describe('FilterBar', () => {
  it('writes filter values through v-model', async () => {
    const wrapper = mount(Harness)

    await wrapper.get('input[name="max_kes_price"]').setValue('2000')
    await wrapper.get('input[name="min_discount_percent"]').setValue('40')
    await wrapper.get('input[name="q"]').setValue('Hades')
    await wrapper.get('input[name="store-steam"]').setValue(true)

    expect(wrapper.vm.filters).toEqual({
      store: ['steam'],
      maxKesPrice: '2000',
      minDiscountPercent: '40',
      q: 'Hades',
    })
  })
})
