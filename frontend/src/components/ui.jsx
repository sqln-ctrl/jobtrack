import { useEffect, useRef } from 'react'
import { STATUS_BY_VALUE } from '../utils/constants'

const ICONS = {
  overview: 'M4 13h6V4H4v9zm0 7h6v-5H4v5zm10 0h6V11h-6v9zm0-16v5h6V4h-6z',
  list: 'M8 6h12M8 12h12M8 18h12M4 6h.01M4 12h.01M4 18h.01',
  platforms: 'M4 7l8-4 8 4-8 4-8-4zm0 5l8 4 8-4M4 17l8 4 8-4',
  mail: 'M4 6h16v12H4V6zm0 0l8 7 8-7',
  bell: 'M18 9a6 6 0 00-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4',
  calendar: 'M5 5h14v15H5V5zm0 5h14M9 3v4m6-4v4',
  settings: 'M12 15a3 3 0 100-6 3 3 0 000 6zm7-3l2-1-2-4-2 .5a7 7 0 00-1.5-1L15 4h-4l-.5 2.5a7 7 0 00-1.5 1L7 7l-2 4 2 1a7 7 0 000 2l-2 1 2 4 2-.5a7 7 0 001.5 1L11 20h4l.5-2.5a7 7 0 001.5-1l2 .5 2-4-2-1a7 7 0 000-2z',
  plus: 'M12 5v14M5 12h14',
  sync: 'M20 11a8 8 0 00-14.5-4M4 4v4h4M4 13a8 8 0 0014.5 4M20 20v-4h-4',
  sun: 'M12 16a4 4 0 100-8 4 4 0 000 8zm0-13v2m0 14v2M3 12h2m14 0h2M5.6 5.6l1.4 1.4m10 10l1.4 1.4m0-12.8L17 7M7 17l-1.4 1.4',
  moon: 'M20 14.5A8 8 0 019.5 4 8 8 0 1020 14.5z',
  search: 'M11 18a7 7 0 100-14 7 7 0 000 14zm9 3l-4.5-4.5',
  x: 'M6 6l12 12M18 6L6 18',
  external: 'M14 4h6v6m0-6L10 14M18 14v6H4V6h6',
}

export function Icon({ name, className = 'h-4 w-4' }) {
  return (
    <svg viewBox="0 0 24 24" className={className} fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d={ICONS[name]} />
    </svg>
  )
}

export function Spinner({ className = 'h-5 w-5' }) {
  return <span role="status" aria-label="Loading" className={`inline-block animate-spin rounded-full border-2 border-line border-t-accent ${className}`} />
}

export function Loading({ label = 'Loading' }) {
  return <div className="flex items-center justify-center gap-3 py-16 text-sm text-muted"><Spinner />{label}</div>
}

export function ErrorNote({ children }) {
  return children ? <p role="alert" className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700 dark:bg-rose-500/10 dark:text-rose-300">{children}</p> : null
}

export function Empty({ title, children, action }) {
  return (
    <div className="px-6 py-14 text-center">
      <h3 className="text-base font-semibold">{title}</h3>
      {children && <p className="mx-auto mt-1 max-w-sm text-sm text-muted">{children}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  )
}

export function PageHeader({ title, children, actions }) {
  return (
    <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
      <div>
        <h1 className="text-2xl font-bold">{title}</h1>
        {children && <p className="mt-1 text-sm text-muted">{children}</p>}
      </div>
      {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
    </div>
  )
}

export function Field({ label, error, hint, children, className = '' }) {
  return (
    <label className={`block ${className}`}>
      <span className="mb-1 block text-sm font-medium">{label}</span>
      {children}
      {hint && !error && <span className="mt-1 block text-xs text-muted">{hint}</span>}
      {error && <span role="alert" className="mt-1 block text-xs text-rose-600 dark:text-rose-400">{error}</span>}
    </label>
  )
}

export function Modal({ title, onClose, children, wide = false }) {
  const ref = useRef(null)
  useEffect(() => {
    const previous = document.activeElement
    ref.current?.querySelector('input, select, textarea, button')?.focus()
    const onKey = (e) => e.key === 'Escape' && onClose()
    document.addEventListener('keydown', onKey)
    document.body.style.overflow = 'hidden'
    return () => {
      document.removeEventListener('keydown', onKey)
      document.body.style.overflow = ''
      previous?.focus?.()
    }
  }, [onClose])
  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-ink/40 p-0 sm:items-center sm:p-6" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <div ref={ref} role="dialog" aria-modal="true" aria-label={title} className={`panel flex max-h-[92vh] w-full flex-col rounded-b-none shadow-xl sm:rounded-b-xl ${wide ? 'sm:max-w-2xl' : 'sm:max-w-md'}`}>
        <div className="flex items-center justify-between border-b border-line px-5 py-3.5">
          <h2 className="text-lg font-semibold">{title}</h2>
          <button className="btn btn-ghost !p-1.5" onClick={onClose} aria-label="Close"><Icon name="x" /></button>
        </div>
        <div className="overflow-y-auto px-5 py-4">{children}</div>
      </div>
    </div>
  )
}

export function ConfirmModal({ title, message, confirmLabel = 'Delete', busy, error, onConfirm, onClose, children }) {
  return (
    <Modal title={title} onClose={onClose}>
      <p className="text-sm text-muted">{message}</p>
      {children}
      <ErrorNote>{error}</ErrorNote>
      <div className="mt-5 flex justify-end gap-2">
        <button className="btn btn-secondary" onClick={onClose}>Cancel</button>
        <button className="btn btn-danger" disabled={busy} onClick={onConfirm}>{busy ? 'Working…' : confirmLabel}</button>
      </div>
    </Modal>
  )
}

export function StatusBadge({ status }) {
  const s = STATUS_BY_VALUE[status]
  return <span className={`inline-flex items-center whitespace-nowrap rounded-full px-2.5 py-0.5 text-xs font-semibold ${s?.badge}`}>{s?.label ?? status}</span>
}

const MARK_TONES = ['bg-blue-600', 'bg-emerald-600', 'bg-amber-600', 'bg-rose-600', 'bg-violet-600', 'bg-teal-600', 'bg-orange-600', 'bg-cyan-700']
const KNOWN = { linkedin: 'bg-[#0A66C2]', indeed: 'bg-[#2557A7]', glassdoor: 'bg-[#0CAA41]', 'rozee.pk': 'bg-[#E0212C]' }

export function PlatformMark({ name = '', size = 'h-6 w-6 text-[10px]' }) {
  const tone = KNOWN[name.toLowerCase()] ?? MARK_TONES[[...name].reduce((n, c) => n + c.charCodeAt(0), 0) % MARK_TONES.length]
  const initials = name.split(/[\s.]+/).filter(Boolean).slice(0, 2).map((w) => w[0].toUpperCase()).join('')
  return <span aria-hidden="true" className={`inline-grid shrink-0 place-items-center rounded-md font-bold text-white ${tone} ${size}`}>{initials}</span>
}

export function Pagination({ page, pageSize, total, onPage }) {
  const pages = Math.max(1, Math.ceil(total / pageSize))
  if (pages <= 1) return null
  return (
    <div className="flex items-center justify-between border-t border-line px-4 py-3 text-sm text-muted">
      <span>Page {page} of {pages} · {total} results</span>
      <div className="flex gap-2">
        <button className="btn btn-secondary" disabled={page <= 1} onClick={() => onPage(page - 1)}>Previous</button>
        <button className="btn btn-secondary" disabled={page >= pages} onClick={() => onPage(page + 1)}>Next</button>
      </div>
    </div>
  )
}
