import { fmtDate, fmtDateTime } from '../utils/format'
import { STATUS_BY_VALUE } from '../utils/constants'

const DOT = { submitted: 'bg-accent', status: 'bg-teal-500', email: 'bg-amber-500', interview: 'bg-emerald-500' }
const SOURCE = { gmail: 'Detected from Gmail', manual: 'Added by you', system: 'System' }

export default function Timeline({ events }) {
  if (!events.length) return <p className="text-sm text-muted">Nothing has happened yet.</p>
  return (
    <ol className="relative ml-2 border-l border-line">
      {events.map((e, i) => (
        <li key={i} className="relative pb-6 pl-6 last:pb-0">
          <span className={`absolute -left-[5px] top-1.5 h-2.5 w-2.5 rounded-full ring-4 ring-surface ${DOT[e.kind] ?? 'bg-muted'}`} />
          <p className="text-xs text-muted">{e.kind === 'submitted' ? fmtDate(e.at.slice(0, 10)) : fmtDateTime(e.at)}{e.source ? ` · ${SOURCE[e.source] ?? e.source}` : ''}</p>
          <p className="text-sm font-semibold">{e.kind === 'email' ? `Email: ${e.title}` : e.title}</p>
          {e.description && <p className="text-sm text-muted">{e.description}</p>}
          {e.kind === 'status' && e.status && <p className="sr-only">New status {STATUS_BY_VALUE[e.status]?.label}</p>}
        </li>
      ))}
    </ol>
  )
}
