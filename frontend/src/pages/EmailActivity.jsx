import { useState } from 'react'
import { Link } from 'react-router-dom'
import { api, errorMessage } from '../services/api'
import { useApiMutation, useApplications, useEmails, useGmailStatus } from '../hooks/useData'
import { CATEGORY_TONE, DEFAULT_CATEGORY_TONE } from '../utils/constants'
import { fmtDateTime, timeAgo } from '../utils/format'
import SyncButton from '../components/SyncButton'
import { Empty, ErrorNote, Field, Loading, Modal, PageHeader, Pagination } from '../components/ui'

const TABS = [['needs_review', 'Needs review'], ['matched', 'Matched'], ['ignored', 'Ignored'], ['', 'All']]

function MatchModal({ email, onClose }) {
  const { data } = useApplications({ sort: 'updated', page_size: 200 })
  const suggested = data?.items.find((a) => email.extracted_company && a.company_name.toLowerCase().includes(email.extracted_company.toLowerCase()))
  const [appId, setAppId] = useState(email.applications[0]?.id ?? suggested?.id ?? '')
  const match = useApiMutation((id) => api.post(`/emails/${email.id}/match`, { application_id: Number(id) }), { onSuccess: onClose })
  return (
    <Modal title="Match email to application" onClose={onClose}>
      <p className="text-sm font-semibold">{email.subject || '(no subject)'}</p>
      <p className="mb-4 text-xs text-muted">{email.sender}</p>
      <Field label="Application" hint="Matching can update the application's status, for example to Interview if this is an invitation.">
        <select value={appId} onChange={(e) => setAppId(e.target.value)}>
          <option value="">Choose an application</option>
          {data?.items.map((a) => <option key={a.id} value={a.id}>{a.job_title} — {a.company_name}</option>)}
        </select>
      </Field>
      <ErrorNote>{match.isError ? errorMessage(match.error) : ''}</ErrorNote>
      <div className="mt-5 flex justify-end gap-2">
        <button className="btn btn-secondary" onClick={onClose}>Cancel</button>
        <button className="btn btn-primary" disabled={!appId || match.isPending} onClick={() => match.mutate(appId)}>{match.isPending ? 'Matching…' : 'Match email'}</button>
      </div>
    </Modal>
  )
}

export default function EmailActivity() {
  const [tab, setTab] = useState('needs_review')
  const [page, setPage] = useState(1)
  const [matching, setMatching] = useState(null)
  const { data: gmail } = useGmailStatus()
  const { data, isLoading, isError, error } = useEmails({ processing_status: tab, page, page_size: 15 })
  const ignore = useApiMutation((id) => api.post(`/emails/${id}/ignore`))

  return (
    <>
      <PageHeader title="Email activity" actions={<SyncButton />}>
        {gmail?.connected ? `Connected as ${gmail.gmail_email}${gmail.last_synced_at ? ` · last synced ${timeAgo(gmail.last_synced_at)}` : ''}` : 'Connect Gmail to detect replies automatically'}
      </PageHeader>
      {gmail?.last_error && <div className="mb-4"><ErrorNote>{gmail.last_error} {gmail.sync_status === 'revoked' && <Link to="/settings" className="font-semibold underline">Reconnect Gmail</Link>}</ErrorNote></div>}

      <div role="tablist" className="mb-4 flex gap-1 border-b border-line">
        {TABS.map(([value, label]) => (
          <button key={label} role="tab" aria-selected={tab === value} onClick={() => { setTab(value); setPage(1) }}
            className={`-mb-px border-b-2 px-4 py-2 text-sm font-medium ${tab === value ? 'border-accent text-accent' : 'border-transparent text-muted hover:text-ink'}`}>{label}</button>
        ))}
      </div>

      <div className="panel overflow-hidden">
        {isLoading ? <Loading /> : isError ? <Empty title="Could not load emails">{errorMessage(error)}</Empty> : data.items.length === 0 ? (
          <Empty title={tab === 'needs_review' ? 'Nothing needs your review' : 'No emails here'}>
            {gmail?.connected ? 'Job-related emails show up here after a sync. Choose Sync Gmail to check now.' : 'Connect Gmail in Settings to start detecting replies.'}
          </Empty>
        ) : (
          <ul className="divide-y divide-line">{data.items.map((e) => (
            <li key={e.id} className="px-5 py-4">
              <div className="flex flex-wrap items-center gap-2">
                <span className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${CATEGORY_TONE[e.classification] ?? DEFAULT_CATEGORY_TONE}`}>{e.classification_label}</span>
                <span className="text-xs text-muted">{fmtDateTime(e.received_at)}</span>
              </div>
              <p className="mt-1.5 text-sm font-semibold">{e.subject || '(no subject)'}</p>
              <p className="text-xs text-muted">{e.sender}</p>
              {e.excerpt && <p className="mt-1 line-clamp-2 max-w-3xl text-sm text-muted">{e.excerpt}</p>}
              {(e.extracted_company || e.extracted_job_title) && <p className="mt-1 text-xs text-muted">Detected: {[e.extracted_job_title, e.extracted_company].filter(Boolean).join(' at ')}</p>}
              <div className="mt-3 flex flex-wrap items-center gap-2">
                {e.applications.map((a) => <Link key={a.id} to={`/applications/${a.id}`} className="rounded-md bg-accent/10 px-2.5 py-1 text-xs font-semibold text-accent">Linked to {a.job_title} · {a.company_name}</Link>)}
                {e.processing_status !== 'matched' && e.processing_status !== 'ignored' && <span className="text-xs text-amber-700 dark:text-amber-300">Could belong to more than one job, or none yet.</span>}
                <span className="flex-1" />
                {e.processing_status !== 'ignored' && <button className="btn btn-secondary !py-1" onClick={() => setMatching(e)}>{e.applications.length ? 'Change match' : 'Match to application'}</button>}
                {e.processing_status === 'needs_review' && <button className="btn btn-ghost !py-1" disabled={ignore.isPending} onClick={() => ignore.mutate(e.id)}>Ignore</button>}
              </div>
            </li>
          ))}</ul>
        )}
        {data && <Pagination page={page} pageSize={15} total={data.total} onPage={setPage} />}
      </div>
      {matching && <MatchModal email={matching} onClose={() => setMatching(null)} />}
    </>
  )
}
