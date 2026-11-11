import { Link } from 'react-router-dom'
import { useState } from 'react'
import { useGmailStatus, useJobAlerts } from '../hooks/useData'
import { fmtDateTime, timeAgo } from '../utils/format'
import SyncButton from '../components/SyncButton'
import { Empty, ErrorNote, Icon, Loading, PageHeader, Pagination } from '../components/ui'
import { errorMessage } from '../services/api'

export default function JobAlerts() {
  const [page, setPage] = useState(1)
  const { data: gmail } = useGmailStatus()
  const { data, isLoading, isError, error } = useJobAlerts({ page, page_size: 15 })

  return (
    <>
      <PageHeader title="Job alerts" actions={<SyncButton />}>
        {gmail?.connected
          ? `LinkedIn recommendations from ${gmail.gmail_email}${gmail.last_synced_at ? ` · last synced ${timeAgo(gmail.last_synced_at)}` : ''}`
          : 'Connect Gmail to import LinkedIn job alerts.'}
      </PageHeader>
      {gmail?.last_error && <div className="mb-4"><ErrorNote>{gmail.last_error} {gmail.sync_status === 'revoked' && <Link to="/settings" className="font-semibold underline">Reconnect Gmail</Link>}</ErrorNote></div>}

      <div className="panel overflow-hidden">
        {isLoading ? <Loading /> : isError ? <Empty title="Could not load job alerts">{errorMessage(error)}</Empty> : data.items.length === 0 ? (
          <Empty title="No LinkedIn job alerts yet" action={!gmail?.connected && <Link to="/settings" className="btn btn-primary">Connect Gmail</Link>}>
            {gmail?.connected ? 'Select Sync Gmail to check your LinkedIn job-alert emails.' : 'After Gmail is connected, LinkedIn job alerts will appear here.'}
          </Empty>
        ) : (
          <ul className="divide-y divide-line">
            {data.items.map((job) => (
              <li key={job.id} className="flex flex-col gap-4 px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
                <div className="min-w-0">
                  <p className="font-semibold">{job.job_title}</p>
                  {(job.company_name || job.location) && <p className="mt-0.5 text-sm text-muted">{[job.company_name, job.location].filter(Boolean).join(' · ')}</p>}
                  <p className="mt-1 text-xs text-muted" title={fmtDateTime(job.received_at)}>LinkedIn alert · {timeAgo(job.received_at)}</p>
                </div>
                <a href={job.job_url} target="_blank" rel="noreferrer" className="btn btn-primary shrink-0">
                  Apply <Icon name="external" />
                </a>
              </li>
            ))}
          </ul>
        )}
        {data && <Pagination page={page} pageSize={15} total={data.total} onPage={setPage} />}
      </div>
    </>
  )
}
