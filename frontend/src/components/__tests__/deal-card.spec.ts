import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import type { DealRead } from '@/api/model'

import DealCard from '../deal-card.vue'

const deal: DealRead = {
  title: 'Hades',
  listing_id: 1,
  image_url: null,
  store_slug: 'steam',
  store_display_name: 'Steam',
  base_amount: '20',
  native_amount: '10',
  kes_amount: '1300',
  currency: 'USD',
  discount_percent: 50,
  observed_at: '2026-06-01T00:00:00Z',
}

describe('DealCard', () => {
  it('renders the KES price', () => {
    const wrapper = mount(DealCard, { props: { deal } })
    const text = wrapper.text().replace(/\u00a0/g, ' ')

    expect(text).toContain('KES 1,300')
  })
})
