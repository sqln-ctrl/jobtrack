import { useNavigate } from 'react-router-dom'

const done = () => { try { localStorage.setItem('jt_onboarded', '1') } catch { /* ignore */ } }

export default function Onboarding() {
  const navigate = useNavigate()
  return (
    <div className="mx-auto grid min-h-screen max-w-2xl content-center px-6 py-12">
      <h1 className="text-3xl font-bold sm:text-4xl">Let JobTrack read your job emails</h1>
      <p className="mt-3 text-muted">Connect Gmail and JobTrack will spot confirmations, interview invitations, assessments, rejections and offers, then update the matching application for you.</p>
      <dl className="panel mt-8 divide-y divide-line">
        <div className="p-5"><dt className="font-semibold">What JobTrack can do</dt><dd className="mt-1 text-sm text-muted">Read-only access to your mailbox. It looks at messages from the last 90 days that look job-related, and ignores and never stores the rest.</dd></div>
        <div className="p-5"><dt className="font-semibold">What it can never do</dt><dd className="mt-1 text-sm text-muted">Send, delete or change any email. Your access tokens stay encrypted on the server and are never sent to your browser.</dd></div>
        <div className="p-5"><dt className="font-semibold">You stay in control</dt><dd className="mt-1 text-sm text-muted">When a message could belong to more than one job, JobTrack asks you instead of guessing. Disconnect any time in Settings to revoke access and delete the stored tokens.</dd></div>
      </dl>
      <div className="mt-8 flex flex-wrap gap-3">
        <a href="/api/v1/gmail/connect" className="btn btn-primary !py-2.5" onClick={done}>Connect Gmail</a>
        <button className="btn btn-secondary !py-2.5" onClick={() => { done(); navigate('/') }}>Skip for now</button>
      </div>
      <p className="mt-3 text-xs text-muted">You can connect later from Settings. Everything except automatic email updates works without Gmail.</p>
    </div>
  )
}
