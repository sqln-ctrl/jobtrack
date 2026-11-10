const dateOnly = (value) => {
  // 'YYYY-MM-DD' must be read as a local date, otherwise it shifts a day in some timezones.
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value)
  return m ? new Date(+m[1], +m[2] - 1, +m[3]) : new Date(value)
}

export const fmtDate = (value) =>
  value ? dateOnly(value).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' }) : '—'

export const fmtDateTime = (value) =>
  value ? new Date(value).toLocaleString(undefined, { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' }) : '—'

export const timeAgo = (value) => {
  if (!value) return '—'
  const iso = /[zZ]|[+-]\d{2}:?\d{2}$/.test(value) ? value : `${value}Z`
  const mins = Math.round((Date.now() - new Date(iso).getTime()) / 60000)
  if (mins < 1) return 'Just now'
  if (mins < 60) return `${mins}m ago`
  if (mins < 60 * 24) return `${Math.round(mins / 60)}h ago`
  if (mins < 60 * 24 * 30) return `${Math.round(mins / 1440)}d ago`
  return fmtDate(value.slice(0, 10))
}

export const todayISO = () => {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

export const toLocalInput = (iso) => {
  const d = new Date(iso)
  const p = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}T${p(d.getHours())}:${p(d.getMinutes())}`
}

export const clean = (params) =>
  Object.fromEntries(Object.entries(params || {}).filter(([, v]) => v !== '' && v !== null && v !== undefined))
