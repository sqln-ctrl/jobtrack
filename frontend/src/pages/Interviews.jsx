import { useState } from 'react'
import { Link } from 'react-router-dom'
import { api, errorMessage } from '../services/api'
import { useApiMutation, useInterviews } from '../hooks/useData'
import { fmtDateTime } from '../utils/format'
import InterviewForm from '../components/InterviewForm'
import { ConfirmModal, Empty, Icon, Loading, PageHeader } from '../components/ui'

function List({ items, onEdit, onDelete }) {
  return (
    <ul className="divide-y divide-line">{items.map((i) => (
      <li key={i.id} className="flex flex-wrap items-center gap-x-6 gap-y-1 px-5 py-4">
        <div className="w-44 shrink-0"><p className="text-sm font-semibold">{fmtDateTime(i.interview_date)}</p><p className="text-xs text-muted">{i.interview_type ?? 'Interview'}</p></div>
        <div className="min-w-0 flex-1">
          <Link to={`/applications/${i.application_id}`} className="text-sm font-semibold hover:text-accent">{i.job_title} · {i.company_name}</Link>
          {i.notes && <p className="line-clamp-1 text-sm text-muted">{i.notes}</p>}
        </div>
        {i.meeting_link && <a href={i.meeting_link} target="_blank" rel="noopener noreferrer" className="btn btn-secondary !py-1">Join link</a>}
        <button className="btn btn-ghost !py-1" onClick={() => onEdit(i)}>Edit</button>
        <button className="btn btn-ghost !py-1 hover:!text-rose-600" onClick={() => onDelete(i)}>Delete</button>
      </li>
    ))}</ul>
  )
}

export default function Interviews() {
  const all = useInterviews({ limit: 200 })
  const [editing, setEditing] = useState(null)
  const [deleting, setDeleting] = useState(null)
  const remove = useApiMutation((id) => api.delete(`/interviews/${id}`), { onSuccess: () => setDeleting(null) })
  const now = Date.now()
  const upcoming = (all.data ?? []).filter((i) => new Date(i.interview_date).getTime() >= now).sort((a, b) => new Date(a.interview_date) - new Date(b.interview_date))
  const past = (all.data ?? []).filter((i) => new Date(i.interview_date).getTime() < now)

  return (
    <>
      <PageHeader title="Interviews" actions={<button className="btn btn-primary" onClick={() => setEditing('new')}><Icon name="plus" />Schedule interview</button>}>Keep track of every call, test and on-site</PageHeader>
      {all.isLoading ? <Loading /> : (
        <div className="space-y-6">
          <section className="panel"><h2 className="px-5 py-4 text-base font-semibold">Upcoming</h2>
            {upcoming.length ? <div className="border-t border-line"><List items={upcoming} onEdit={setEditing} onDelete={setDeleting} /></div> : <Empty title="No upcoming interviews">Schedule one when an invitation arrives. A confirmed time shows up on your overview.</Empty>}
          </section>
          {past.length > 0 && <section className="panel"><h2 className="px-5 py-4 text-base font-semibold">Past</h2><div className="border-t border-line"><List items={past} onEdit={setEditing} onDelete={setDeleting} /></div></section>}
        </div>
      )}
      {editing && <InterviewForm interview={editing === 'new' ? null : editing} onClose={() => setEditing(null)} />}
      {deleting && <ConfirmModal title="Delete interview" message={`Delete the interview for ${deleting.job_title} at ${deleting.company_name}?`} busy={remove.isPending}
        error={remove.isError ? errorMessage(remove.error) : ''} onConfirm={() => remove.mutate(deleting.id)} onClose={() => setDeleting(null)} />}
    </>
  )
}
