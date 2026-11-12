import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { api, errorMessage } from '../services/api'
import { useApiMutation, useApplication } from '../hooks/useData'
import { CATEGORY_TONE, DEFAULT_CATEGORY_TONE, EMPLOYMENT_LABEL, STATUSES } from '../utils/constants'
import { fmtDate, fmtDateTime } from '../utils/format'
import ApplicationForm from '../components/ApplicationForm'
import InterviewForm from '../components/InterviewForm'
import Timeline from '../components/Timeline'
import { ConfirmModal, Empty, ErrorNote, Loading, PlatformMark } from '../components/ui'

const Row = ({ label, children }) => (children ? <div><dt className="text-xs text-muted">{label}</dt><dd className="mt-0.5 break-words text-sm">{children}</dd></div> : null)
const ExtLink = ({ href }) => <a href={href} target="_blank" rel="noopener noreferrer" className="text-accent hover:underline">{href.replace(/^https?:\/\/(www\.)?/, '').slice(0, 48)}</a>

export default function ApplicationDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { data, isLoading, isError, error } = useApplication(id)
  const [editing, setEditing] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [scheduling, setScheduling] = useState(false)

  const setStatus = useApiMutation((status) => api.patch(`/applications/${id}/status`, { status }).then((r) => r.data))
  const remove = useApiMutation(() => api.delete(`/applications/${id}`), { onSuccess: () => navigate('/applications') })
  const removeInterview = useApiMutation((iid) => api.delete(`/interviews/${iid}`))

  if (isLoading) return <Loading />
  if (isError) return <div className="panel"><Empty title="Application not found" action={<Link to="/applications" className="btn btn-secondary">Back to applications</Link>}>{errorMessage(error, 'It may have been deleted.')}</Empty></div>
  const { application: a, timeline, emails, interviews } = data

  return (
    <>
      <Link to="/applications" className="text-sm text-muted hover:text-ink">← All applications</Link>
      <div className="mb-6 mt-2 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold">{a.job_title}</h1>
          <p className="mt-1 flex items-center gap-2 text-muted"><PlatformMark name={a.platform.name} />{a.company_name} · {a.platform.name}</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <label className="sr-only" htmlFor="status">Status</label>
          <select id="status" className="!w-auto font-semibold" value={a.status} disabled={setStatus.isPending} onChange={(e) => setStatus.mutate(e.target.value)}>
            {STATUSES.map((s) => <option key={s.value} value={s.value}>{s.label}</option>)}
          </select>
          <button className="btn btn-secondary" onClick={() => setEditing(true)}>Edit</button>
          <button className="btn btn-secondary hover:!text-rose-600" onClick={() => setDeleting(true)}>Delete</button>
        </div>
      </div>
      <ErrorNote>{setStatus.isError ? errorMessage(setStatus.error) : ''}</ErrorNote>

      <div className="space-y-6">
        <section className="panel p-5">
          <h2 className="text-base font-semibold">Details</h2>
          <dl className="mt-4 grid grid-cols-2 gap-x-6 gap-y-4 sm:grid-cols-3">
            <Row label="Applied on">{fmtDate(a.application_date)}</Row>
            <Row label="Location">{a.location}</Row>
            <Row label="Employment type">{EMPLOYMENT_LABEL[a.employment_type]}</Row>
            <Row label="Salary range">{a.salary_range}</Row>
            <Row label="Contact person">{a.contact_person}</Row>
            <Row label="Job link">{a.job_url && <ExtLink href={a.job_url} />}</Row>
            <Row label="Company website">{a.company_website && <ExtLink href={a.company_website} />}</Row>
          </dl>
          {a.job_description && <div className="mt-5 border-t border-line pt-4"><h3 className="text-sm font-semibold">Job description</h3><p className="mt-1 max-w-prose whitespace-pre-wrap text-sm text-muted">{a.job_description}</p></div>}
          {a.notes && <div className="mt-5 border-t border-line pt-4"><h3 className="text-sm font-semibold">Notes</h3><p className="mt-1 max-w-prose whitespace-pre-wrap text-sm text-muted">{a.notes}</p></div>}
        </section>

        <div className="grid min-w-0 gap-6 lg:grid-cols-[minmax(0,1.25fr)_minmax(16rem,0.9fr)] lg:items-start">
          <section className="panel min-w-0 overflow-hidden">
            <h2 className="px-5 py-4 text-base font-semibold">Gmail conversations</h2>
            {emails.length ? (
              <ul className="max-h-[min(48vh,30rem)] divide-y divide-line overflow-y-auto border-t border-line">{emails.map((e) => (
                <li key={e.id} className="min-w-0 px-5 py-4">
                  <div className="flex flex-wrap items-center gap-2"><span className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${CATEGORY_TONE[e.classification] ?? DEFAULT_CATEGORY_TONE}`}>{e.classification_label}</span><span className="text-xs text-muted">{fmtDateTime(e.received_at)}</span></div>
                  <p className="mt-1.5 truncate text-sm font-semibold" title={e.subject || '(no subject)'}>{e.subject || '(no subject)'}</p>
                  <p className="truncate text-xs text-muted" title={e.sender}>{e.sender}</p>
                  {e.excerpt && <p className="mt-1 line-clamp-2 break-words text-sm text-muted">{e.excerpt}</p>}
                </li>
              ))}</ul>
            ) : <p className="border-t border-line px-5 py-6 text-sm text-muted">No emails linked yet. Matching emails appear here after a Gmail sync.</p>}
          </section>

          <div className="min-w-0 space-y-6">
          <section className="panel p-5"><h2 className="mb-4 text-base font-semibold">Timeline</h2><Timeline events={timeline} /></section>
          <section className="panel p-5">
            <div className="flex items-center justify-between"><h2 className="text-base font-semibold">Interviews</h2><button className="btn btn-secondary !py-1" onClick={() => setScheduling(true)}>Schedule</button></div>
            {interviews.length ? <ul className="mt-3 space-y-3">{interviews.map((i) => (
              <li key={i.id} className="flex items-start justify-between gap-2 text-sm">
                <div><p className="font-semibold">{fmtDateTime(i.interview_date)}</p><p className="text-xs text-muted">{i.interview_type ?? 'Interview'}</p>{i.meeting_link && <ExtLink href={i.meeting_link} />}</div>
                <button className="btn btn-ghost !px-2 !py-1 hover:!text-rose-600" onClick={() => removeInterview.mutate(i.id)}>Remove</button>
              </li>
            ))}</ul> : <p className="mt-2 text-sm text-muted">No interviews scheduled.</p>}
          </section>
        </div>
      </div>
      </div>

      {editing && <ApplicationForm application={a} onClose={() => setEditing(false)} />}
      {scheduling && <InterviewForm applicationId={a.id} onClose={() => setScheduling(false)} />}
      {deleting && <ConfirmModal title="Delete application" busy={remove.isPending} error={remove.isError ? errorMessage(remove.error) : ''}
        message={`Delete ${a.job_title} at ${a.company_name}? Its history and email links are removed too. This can't be undone.`}
        onConfirm={() => remove.mutate()} onClose={() => setDeleting(false)} />}
    </>
  )
}
