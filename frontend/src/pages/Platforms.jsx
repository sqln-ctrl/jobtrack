import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, errorMessage } from '../services/api'
import { useApiMutation, useApplications, usePlatformDistribution, usePlatforms } from '../hooks/useData'
import { STATUSES } from '../utils/constants'
import { fmtDate } from '../utils/format'
import { ConfirmModal, Empty, ErrorNote, Field, Loading, Modal, PageHeader, PlatformMark, StatusBadge } from '../components/ui'

function NameModal({ platform, onClose }) {
  const [name, setName] = useState(platform?.name ?? '')
  const save = useApiMutation((n) => (platform ? api.put(`/platforms/${platform.id}`, { name: n }) : api.post('/platforms', { name: n })), { refresh: false, onSuccess: onClose })
  return (
    <Modal title={platform ? 'Rename platform' : 'Add platform'} onClose={onClose}>
      <form onSubmit={(e) => { e.preventDefault(); if (name.trim()) save.mutate(name.trim()) }} className="space-y-4">
        <Field label="Platform name"><input value={name} onChange={(e) => setName(e.target.value)} placeholder="Wellfound" maxLength={80} /></Field>
        <ErrorNote>{save.isError ? errorMessage(save.error) : ''}</ErrorNote>
        <div className="flex justify-end gap-2"><button type="button" className="btn btn-secondary" onClick={onClose}>Cancel</button><button className="btn btn-primary" disabled={!name.trim() || save.isPending}>Save</button></div>
      </form>
    </Modal>
  )
}

export default function Platforms() {
  const { data: platforms = [], isLoading } = usePlatforms()
  const { data: counts = [] } = usePlatformDistribution()
  const [selected, setSelected] = useState(null)
  const [status, setStatus] = useState('')
  const [naming, setNaming] = useState(null) // platform | 'new'
  const [deleting, setDeleting] = useState(null)

  const countOf = (id) => counts.find((c) => c.platform_id === id)?.count ?? 0
  useEffect(() => {
    if (selected === null && platforms.length) setSelected((counts[0]?.platform_id) ?? platforms[0].id)
  }, [platforms, counts, selected])
  const current = platforms.find((p) => p.id === selected)
  const { data } = useApplications({ platform_id: selected, status, sort: 'newest', page_size: 100 })
  const remove = useApiMutation((id) => api.delete(`/platforms/${id}`), { refresh: false, onSuccess: () => { setDeleting(null); setSelected(null) } })

  if (isLoading) return <Loading />
  return (
    <>
      <PageHeader title="Platforms" actions={<button className="btn btn-secondary" onClick={() => setNaming('new')}>Add platform</button>}>Applications grouped by where you found the job</PageHeader>
      <div className="grid gap-6 md:grid-cols-[16rem_1fr]">
        <nav aria-label="Platforms" className="panel h-fit p-2">
          {platforms.map((p) => (
            <button key={p.id} onClick={() => { setSelected(p.id); setStatus('') }} aria-current={selected === p.id}
              className={`flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-left text-sm font-medium ${selected === p.id ? 'bg-accent/10 text-accent' : 'text-ink hover:bg-bg'}`}>
              <PlatformMark name={p.name} /><span className="flex-1 truncate">{p.name}</span><span className="text-xs text-muted">{countOf(p.id)}</span>
            </button>
          ))}
        </nav>

        <section className="panel">
          {current && (
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-line px-5 py-4">
              <h2 className="flex items-center gap-2.5 text-lg font-semibold"><PlatformMark name={current.name} size="h-7 w-7 text-xs" />{current.name}</h2>
              <div className="flex items-center gap-2">
                <select aria-label="Filter by status" className="!w-auto" value={status} onChange={(e) => setStatus(e.target.value)}><option value="">All statuses</option>{STATUSES.map((s) => <option key={s.value} value={s.value}>{s.label}</option>)}</select>
                {!current.is_default && <>
                  <button className="btn btn-ghost" onClick={() => setNaming(current)}>Rename</button>
                  <button className="btn btn-ghost hover:!text-rose-600" onClick={() => setDeleting(current)}>Delete</button>
                </>}
              </div>
            </div>
          )}
          {!data ? <Loading /> : data.items.length === 0 ? <Empty title={status ? 'No applications with this status' : 'Nothing here yet'}>{status ? 'Pick another status to see more.' : 'Applications you add from this platform will be listed here.'}</Empty> : (
            <ul className="divide-y divide-line">{data.items.map((a) => (
              <li key={a.id}><Link to={`/applications/${a.id}`} className="flex flex-wrap items-center gap-x-4 gap-y-1 px-5 py-3.5 hover:bg-bg/60">
                <span className="min-w-0 flex-1"><span className="block truncate text-sm font-semibold">{a.job_title}</span><span className="block truncate text-sm text-muted">{a.company_name}</span></span>
                <span className="text-xs text-muted">{fmtDate(a.application_date)}</span><StatusBadge status={a.status} />
              </Link></li>
            ))}</ul>
          )}
        </section>
      </div>
      {naming && <NameModal platform={naming === 'new' ? null : naming} onClose={() => setNaming(null)} />}
      {deleting && <ConfirmModal title="Delete platform" message={`Delete ${deleting.name}? This only works when no applications use it.`} busy={remove.isPending}
        error={remove.isError ? errorMessage(remove.error) : ''} onConfirm={() => remove.mutate(deleting.id)} onClose={() => setDeleting(null)} />}
    </>
  )
}
