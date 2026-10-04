const rupees = new Intl.NumberFormat('en-IN', {
  style: 'currency',
  currency: 'INR',
  maximumFractionDigits: 0,
})

export const inr = (value) =>
  value === null || value === undefined || Number.isNaN(Number(value)) ? '—' : rupees.format(Number(value))

export function todayISO() {
  const d = new Date()
  return new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 10)
}

export const fmtDate = (iso) =>
  new Date(`${iso}T00:00:00`).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })

export function greeting() {
  const h = new Date().getHours()
  if (h < 12) return 'Good morning'
  if (h < 17) return 'Good afternoon'
  return 'Good evening'
}

export const statusClass = (status) =>
  ({ Safe: 'safe', Watch: 'watch', Warning: 'warning', Critical: 'critical' })[status] || 'unknown'

/** Number if the field has a value, otherwise null. */
export const numOrNull = (v) => (v === '' || v === null || v === undefined ? null : Number(v))