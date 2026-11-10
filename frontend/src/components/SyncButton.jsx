import { useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import { errorMessage } from '../services/api'
import { useGmailStatus, useRefreshAll, useSyncGmail } from '../hooks/useData'
import { Icon } from './ui'

/** Starts a sync, then refreshes every screen once the backend reports it is finished. */
export default function SyncButton({ className = 'btn btn-secondary' }) {
  const { data: status } = useGmailStatus()
  const sync = useSyncGmail()
  const refreshAll = useRefreshAll()
  const was = useRef(null)

  useEffect(() => {
    if (was.current === 'syncing' && status?.sync_status && status.sync_status !== 'syncing') refreshAll()
    was.current = status?.sync_status
  }, [status?.sync_status]) // eslint-disable-line react-hooks/exhaustive-deps

  if (!status?.connected) return <Link to="/settings" className={className}><Icon name="mail" />Connect Gmail</Link>
  const busy = status.sync_status === 'syncing' || sync.isPending
  return (
    <button className={className} disabled={busy} onClick={() => sync.mutate()} title={sync.isError ? errorMessage(sync.error) : undefined}>
      <Icon name="sync" className={`h-4 w-4 ${busy ? 'animate-spin' : ''}`} />{busy ? 'Syncing…' : 'Sync Gmail'}
    </button>
  )
}
