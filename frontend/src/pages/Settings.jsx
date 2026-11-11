import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'
import { api, errorMessage } from '../services/api'
import { useAuth } from '../context/AuthContext'
import { useApiMutation, useGmailStatus } from '../hooks/useData'
import { useTheme } from '../hooks/useTheme'
import { timeAgo } from '../utils/format'
import SyncButton from '../components/SyncButton'
import { ConfirmModal, PageHeader } from '../components/ui'

const NOTICES = {
  connected: ['ok', 'Gmail connected. Your first sync is running now.'],
  cancelled: ['warn', 'Gmail access was not granted, so nothing was connected.'],
  scope_denied: ['warn', 'JobTrack needs read-only Gmail access to detect replies. Allow it on the Google screen to continue.'],
  invalid_state: ['warn', 'That connection link expired. Start again.'],
  failed: ['warn', 'Gmail could not be connected. Try again in a moment.'],
}
const STATE_LABEL = { idle: 'Up to date', syncing: 'Syncing', error: 'Last sync failed', revoked: 'Access revoked' }

export default function Settings() {
  const { user, logout } = useAuth()
  const { dark, toggle } = useTheme()
  const qc = useQueryClient()
  const { data: gmail } = useGmailStatus()
  const [params, setParams] = useSearchParams()
  const [disconnecting, setDisconnecting] = useState(false)
  const [deleteEmails, setDeleteEmails] = useState(false)
  const notice = NOTICES[params.get('gmail')]

  useEffect(() => {
    if (params.get('gmail')) qc.invalidateQueries({ queryKey: ['me'] })
  }, [params, qc])

  const disconnect = useApiMutation(() => api.post('/gmail/disconnect', null, { params: { delete_emails: deleteEmails } }), {
    onSuccess: () => { setDisconnecting(false); qc.invalidateQueries({ queryKey: ['me'] }) },
  })

  return (
    <>
      <PageHeader title="Settings">Your account, Gmail connection and appearance</PageHeader>
      {notice && <p role="status" className={`mb-4 rounded-lg px-4 py-3 text-sm ${notice[0] === 'ok' ? 'bg-emerald-50 text-emerald-800 dark:bg-emerald-500/10 dark:text-emerald-300' : 'bg-amber-50 text-amber-800 dark:bg-amber-500/10 dark:text-amber-300'}`}>{notice[1]} <button className="font-semibold underline" onClick={() => setParams({})}>Dismiss</button></p>}

      <div className="max-w-2xl space-y-6">
        <section className="panel p-5">
          <h2 className="text-base font-semibold">Profile</h2>
          <div className="mt-4 flex items-center gap-4">
            {user?.profile_picture ? <img src={user.profile_picture} alt="" referrerPolicy="no-referrer" className="h-12 w-12 rounded-full" /> : <span className="grid h-12 w-12 place-items-center rounded-full bg-accent/15 text-lg font-semibold text-accent">{user?.name?.[0]}</span>}
            <div className="flex-1"><p className="font-semibold">{user?.name}</p><p className="text-sm text-muted">{user?.email}</p></div>
            <button className="btn btn-secondary" onClick={logout}>Sign out</button>
          </div>
        </section>

        <section className="panel p-5">
          <h2 className="text-base font-semibold">Gmail</h2>
          {gmail?.connected ? (
            <div className="mt-3">
              <p className="text-sm"><span className="font-semibold">{gmail.gmail_email}</span> · {STATE_LABEL[gmail.sync_status] ?? gmail.sync_status}{gmail.last_synced_at ? ` · last synced ${timeAgo(gmail.last_synced_at)}` : ''}</p>
              {gmail.last_error && <p role="alert" className="mt-2 rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700 dark:bg-rose-500/10 dark:text-rose-300">{gmail.last_error}</p>}
              <p className="mt-2 text-sm text-muted">JobTrack has read-only access. It cannot send, delete or change email.</p>
              <div className="mt-4 flex flex-wrap gap-2">
                <SyncButton />
                {['revoked', 'error'].includes(gmail.sync_status) && <a href="/api/v1/gmail/connect" className="btn btn-primary">Reconnect Gmail</a>}
                <button className="btn btn-ghost hover:!text-rose-600" onClick={() => setDisconnecting(true)}>Disconnect</button>
              </div>
            </div>
          ) : (
            <div className="mt-3">
              <p className="text-sm text-muted">Connect Gmail so JobTrack can find confirmations, review updates, interview invitations and acceptance emails, and update the matching application. Access is read-only and limited to job-related messages from the last 90 days.</p>
              <a href="/api/v1/gmail/connect" className="btn btn-primary mt-4">Connect Gmail</a>
            </div>
          )}
        </section>

        <section className="panel flex items-center justify-between p-5">
          <div><h2 className="text-base font-semibold">Appearance</h2><p className="text-sm text-muted">{dark ? 'Dark' : 'Light'} mode</p></div>
          <button className="btn btn-secondary" onClick={toggle}>Switch to {dark ? 'light' : 'dark'}</button>
        </section>
      </div>

      {disconnecting && (
        <ConfirmModal title="Disconnect Gmail" confirmLabel="Disconnect" busy={disconnect.isPending} error={disconnect.isError ? errorMessage(disconnect.error) : ''}
          message="JobTrack will revoke its access with Google and delete the stored tokens. Your applications and history stay as they are."
          onConfirm={() => disconnect.mutate()} onClose={() => setDisconnecting(false)}>
          <label className="mt-4 flex items-center gap-2 text-sm"><input type="checkbox" checked={deleteEmails} onChange={(e) => setDeleteEmails(e.target.checked)} />Also delete the emails JobTrack imported</label>
        </ConfirmModal>
      )}
    </>
  )
}
