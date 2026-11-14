import { useState } from 'react'
import { Link } from 'react-router-dom'
import { errorMessage } from '../services/api'
import { useEmails, useGmailStatus } from '../hooks/useData'
import { CATEGORY_TONE, DEFAULT_CATEGORY_TONE } from '../utils/constants'
import { fmtDateTime, timeAgo } from '../utils/format'
import SyncButton from '../components/SyncButton'
import { Empty, ErrorNote, Icon, Loading, PageHeader, Pagination } from '../components/ui'

const TABS = [['matched', 'Matched'], ['needs_review', 'Unmatched'], ['', 'All']]

function emailSummary(excerpt, subject) {
  const cleaned = (excerpt ?? '')
    .replace(/https?:\/\/\S+/gi, ' ')
    .replace(/[|_=-]{4,}/g, ' ')
    .replace(/\b(?:this email was intended for|learn why we included this|you are receiving .*?notification emails|unsubscribe|manage your email preferences|email preferences|privacy policy|terms of service)\b[\s\S]*$/i, '')
    .replace(/\s+/g, ' ')
    .trim()

  if (cleaned.length < 24) return subject || 'No message summary available.'
  if (cleaned.length <= 260) return cleaned
  const shortened = cleaned.slice(0, 260)
  return `${shortened.slice(0, Math.max(0, shortened.lastIndexOf(' '))) || shortened}...`
}

function gmailMessageUrl(email) {
  return `https://mail.google.com/mail/u/0/#all/${email.gmail_thread_id || email.gmail_message_id}`
}

export default function EmailActivity() {
  const [tab, setTab] = useState('matched')
  const [page, setPage] = useState(1)
  const { data: gmail } = useGmailStatus()
  const { data, isLoading, isError, error } = useEmails({ processing_status: tab, page, page_size: 15 })

  return (
    <>
      <PageHeader title="Email activity" actions={<SyncButton />}>
        {gmail?.connected ? `Connected as ${gmail.gmail_email}${gmail.last_synced_at ? ` - last synced ${timeAgo(gmail.last_synced_at)}` : ''}` : 'Connect Gmail to detect replies automatically'}
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
          <Empty title={tab === 'needs_review' ? 'No unmatched emails' : 'No emails here'}>
            {gmail?.connected ? 'Job-related emails are matched automatically after a sync. Choose Sync Gmail to check now.' : 'Connect Gmail in Settings to start detecting replies.'}
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
              <p className="mt-2 max-w-3xl text-sm leading-6 text-muted"><span className="font-semibold text-ink">Summary:</span> {emailSummary(e.excerpt, e.subject)}</p>
              {(e.extracted_company || e.extracted_job_title) && <p className="mt-1 text-xs text-muted">Detected: {[e.extracted_job_title, e.extracted_company].filter(Boolean).join(' at ')}</p>}
              <div className="mt-3 flex flex-wrap items-center gap-2">
                {e.applications.map((a) => <Link key={a.id} to={`/applications/${a.id}`} className="rounded-md bg-accent/10 px-2.5 py-1 text-xs font-semibold text-accent">Linked to {a.job_title} - {a.company_name}</Link>)}
                {e.processing_status === 'needs_review' && <span className="text-xs text-amber-700 dark:text-amber-300">No matching application was found yet. It will be retried after a later sync.</span>}
                <span className="flex-1" />
                <a href={gmailMessageUrl(e)} target="_blank" rel="noopener noreferrer" className="btn btn-secondary !py-1"><Icon name="external" />View in Gmail</a>
              </div>
            </li>
          ))}</ul>
        )}
        {data && <Pagination page={page} pageSize={15} total={data.total} onPage={setPage} />}
      </div>
    </>
  )
}
