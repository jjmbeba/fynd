export type DealFilters = {
  store: string[]
  maxKesPrice: string
  minDiscountPercent: string
  q: string
}

export const emptyFilters = (): DealFilters => ({
  store: [],
  maxKesPrice: '',
  minDiscountPercent: '',
  q: '',
})
