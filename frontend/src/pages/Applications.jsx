import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { api, errorMessage } from '../services/api'
import { useApiMutation, useApplications, usePlatforms } from '../hooks/useData'
import { EMPLOYMENT_TYPES, STATUSES } from '../utils/constants'
import { fmtDate, timeAgo } from '../utils/format'
import ApplicationForm from '../components/ApplicationForm'
import { ConfirmModal, Empty, Icon, Loading, PageHeader, PlatformMark, Pagination, StatusBadge } from '../components/ui'

const PAGE_SIZE = 15

export default function Applications() {
  const [params, setParams] = useSearchParams()
  const [editing, setEditing] = useState(null) // application | 'new' | null
  const [deleting, setDeleting] = useState(null)
  const [q, setQ] = useState(params.get('q') ?? '')
  const { data: platforms = [] } = usePlatforms()

  const get = (k, d = '') => params.get(k) ?? d
  const page = Number(get('page', 1))
  const query = { q: get('q'), platform_id: get('platform_id'), status: get('status'), employment_type: get('employment_type'), date_from: get('date_from'), date_to: get('date_to'), sort: get('sort', 'newest'), page, page_size: PAGE_SIZE }
  const { data, isLoading, isError, error } = useApplications(query)

  const set = (patch) => {
    const next = new URLSearchParams(params)
    Object.entries({ page: '', ...patch }).forEach(([k, v]) => (v ? next.set(k, v) : next.delete(k)))
    setParams(next, { replace: true })
  }
  useEffect(() => { setQ(params.get('q') ?? '') }, [params.get('q')]) // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => {
    if (q === get('q')) return undefined
    const t = setTimeout(() => set({ q }), 300)
    return () => clearTimeout(t)
  }, [q]) // eslint-disable-line react-hooks/exhaustive-deps

  const remove = useApiMutation((id) => api.delete(`/applications/${id}`), { onSuccess: () => setDeleting(null) })
  const filtered = ['q', 'platform_id', 'status', 'employment_type', 'date_from', 'date_to'].some((k) => get(k))

  return (
    <>
      <PageHeader title="All applications" actions={<button className="btn btn-primary" onClick={() => setEditing('new')}><Icon name="plus" />Add application</button>}>
        {data ? `${data.total} ${data.total === 1 ? 'application' : 'applications'}${filtered ? ' match your filters' : ''}` : 'Search, filter and update everything you have applied for'}
      </PageHeader>

      <div className="panel mb-4 grid gap-3 p-4 sm:grid-cols-2 lg:grid-cols-4">
        <input aria-label="Search" placeholder="Search company, title or platform" value={q} onChange={(e) => setQ(e.target.value)} className="lg:col-span-2" />
        <select aria-label="Platform" value={get('platform_id')} onChange={(e) => set({ platform_id: e.target.value })}><option value="">All platforms</option>{platforms.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}</select>
        <select aria-label="Status" value={get('status')} onChange={(e) => set({ status: e.target.value })}><option value="">All statuses</option>{STATUSES.map((s) => <option key={s.value} value={s.value}>{s.label}</option>)}</select>
        <select aria-label="Employment type" value={get('employment_type')} onChange={(e) => set({ employment_type: e.target.value })}><option value="">Any employment type</option>{EMPLOYMENT_TYPES.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}</select>
        <input aria-label="Applied from" type="date" value={get('date_from')} onChange={(e) => set({ date_from: e.target.value })} title="Applied from" />
        <input aria-label="Applied until" type="date" value={get('date_to')} onChange={(e) => set({ date_to: e.target.value })} title="Applied until" />
        <select aria-label="Sort" value={get('sort', 'newest')} onChange={(e) => set({ sort: e.target.value })}><option value="newest">Newest first</option><option value="oldest">Oldest first</option><option value="updated">Recently updated</option></select>
      </div>

      <div className="panel overflow-hidden">
        {isLoading ? <Loading /> : isError ? <Empty title="Could not load applications">{errorMessage(error)}</Empty> : data.items.length === 0 ? (
          filtered ? <Empty title="No applications match" action={<button className="btn btn-secondary" onClick={() => { setQ(''); setParams({}) }}>Clear filters</button>}>Try removing a filter or searching for something else.</Empty>
            : <Empty title="No applications yet" action={<button className="btn btn-primary" onClick={() => setEditing('new')}><Icon name="plus" />Add application</button>}>Add a job you applied for, or one you want to remember for later.</Empty>
        ) : (
          <div className="overflow-x-auto"><table className="w-full text-left text-sm">
            <thead className="border-b border-line text-xs text-muted"><tr>
              {['Company', 'Job position', 'Platform', 'Applied', 'Status', 'Last activity'].map((h) => <th key={h} className="px-4 py-3 font-medium">{h}</th>)}<th className="px-4 py-3 text-right font-medium">Actions</th>
            </tr></thead>
            <tbody className="divide-y divide-line">
              {data.items.map((a) => (
                <tr key={a.id} className="hover:bg-bg/60">
                  <td className="px-4 py-3 font-semibold"><Link to={`/applications/${a.id}`} className="hover:text-accent">{a.company_name}</Link></td>
                  <td className="px-4 py-3">{a.job_title}</td>
                  <td className="px-4 py-3"><span className="flex items-center gap-2 whitespace-nowrap"><PlatformMark name={a.platform.name} />{a.platform.name}</span></td>
                  <td className="whitespace-nowrap px-4 py-3 text-muted">{fmtDate(a.application_date)}</td>
                  <td className="px-4 py-3"><StatusBadge status={a.status} /></td>
                  <td className="whitespace-nowrap px-4 py-3 text-muted">{timeAgo(a.updated_at)}</td>
                  <td className="whitespace-nowrap px-4 py-3 text-right">
                    <button className="btn btn-ghost !px-2 !py-1" onClick={() => setEditing(a)}>Edit</button>
                    <button className="btn btn-ghost !px-2 !py-1 hover:!text-rose-600" onClick={() => setDeleting(a)}>Delete</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table></div>
        )}
        {data && <Pagination page={page} pageSize={PAGE_SIZE} total={data.total} onPage={(p) => set({ page: String(p) })} />}
      </div>

      {editing && <ApplicationForm application={editing === 'new' ? null : editing} onClose={() => setEditing(null)} />}
      {deleting && <ConfirmModal title="Delete application" busy={remove.isPending} error={remove.isError ? errorMessage(remove.error) : ''}
        message={`Delete ${deleting.job_title} at ${deleting.company_name}? Its history and email links are removed too. This can't be undone.`}
        onConfirm={() => remove.mutate(deleting.id)} onClose={() => setDeleting(null)} />}
    </>
  )
}
