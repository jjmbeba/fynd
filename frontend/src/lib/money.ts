import type { DealRead } from '@/api/model'

const kes = new Intl.NumberFormat('en-KE', {
  style: 'currency',
  currency: 'KES',
  currencyDisplay: 'code',
  minimumFractionDigits: 0,
  maximumFractionDigits: 2,
})

export function formatKes(amount: number): string {
  return kes.format(amount)
}

export function kesBaseAmount(deal: DealRead): number | null {
  const native = Number(deal.native_amount)
  if (!Number.isFinite(native) || native === 0) return null

  const base = (Number(deal.base_amount) / native) * Number(deal.kes_amount)
  if (!Number.isFinite(base)) return null
  return base
}
