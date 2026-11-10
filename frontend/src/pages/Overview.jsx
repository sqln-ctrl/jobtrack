import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useApplications, useInterviews, usePlatformDistribution, useRecentActivity, useStats, useStatusDistribution } from '../hooks/useData'
import { STATUS_BY_VALUE, CATEGORY_TONE, DEFAULT_CATEGORY_TONE } from '../utils/constants'
import { fmtDateTime, timeAgo } from '../utils/format'
import ApplicationForm from '../components/ApplicationForm'
import SyncButton from '../components/SyncButton'
import { Empty, Icon, Loading, PageHeader, PlatformMark, StatusBadge } from '../components/ui'

const TILES = [
  ['total', 'Total applications'], ['this_week', 'This week'], ['interviews', 'Interviews'],
  ['rejected', 'Rejected'], ['offers', 'Offers'], ['awaiting_response', 'Awaiting response'],
]

function Pipeline({ items }) {
  const active = items.filter((s) => s.count > 0)
  return (
    <section aria-label="Application pipeline" className="panel p-5">
      <h2 className="text-base font-semibold">Where your applications stand</h2>
      <div className="mt-4 flex h-14 gap-1">
        {active.map((s) => (
          <Link key={s.status} to={`/applications?status=${s.status}`} style={{ flexGrow: s.count }} title={`${s.label}: ${s.count}`}
            className={`group flex min-w-[3rem] items-end rounded-md p-2 text-white transition-opacity hover:opacity-85 ${STATUS_BY_VALUE[s.status].bar}`}>
            <span className="font-display text-xl font-bold leading-none">{s.count}</span>
          </Link>
        ))}
      </div>
      <div className="mt-2 flex gap-1 text-xs text-muted">
        {active.map((s) => <span key={s.status} style={{ flexGrow: s.count }} className="min-w-[3rem] truncate">{s.label}</span>)}
      </div>
    </section>
  )
}

export default function Overview() {
  const { user } = useAuth()
  const [adding, setAdding] = useState(false)
  const stats = useStats()
  const dist = useStatusDistribution()
  const platforms = usePlatformDistribution()
  const recent = useApplications({ sort: 'updated', page_size: 6 })
  const activity = useRecentActivity()
  const upcoming = useInterviews({ upcoming: true, limit: 5 })

  const empty = stats.data && stats.data.total === 0
  const maxPlatform = Math.max(1, ...(platforms.data ?? []).map((p) => p.count))

  return (
    <>
      <PageHeader title={`Welcome back, ${user?.name?.split(' ')[0] ?? ''}`} actions={<>
        <SyncButton />
        <button className="btn btn-primary" onClick={() => setAdding(true)}><Icon name="plus" />Add application</button>
      </>}>
        {stats.data ? `${stats.data.awaiting_response} waiting to hear back${stats.data.emails_needing_review ? ` · ${stats.data.emails_needing_review} emails need your review` : ''}` : 'Your job search at a glance'}
      </PageHeader>

      {!stats.data ? <Loading /> : empty ? (
        <div className="panel"><Empty title="Add your first application" action={<button className="btn btn-primary" onClick={() => setAdding(true)}><Icon name="plus" />Add application</button>}>
          Track where you applied and what happened next. Connect Gmail in Settings and replies will update your applications for you.
        </Empty></div>
      ) : (
        <div className="space-y-6">
          {dist.data && <Pipeline items={dist.data} />}
          <section aria-label="Statistics" className="grid grid-cols-2 gap-px overflow-hidden rounded-xl border border-line bg-line sm:grid-cols-3 lg:grid-cols-6">
            {TILES.map(([key, label]) => (
              <div key={key} className="bg-surface p-4"><p className="font-display text-3xl font-bold">{stats.data[key]}</p><p className="mt-1 text-xs text-muted">{label}</p></div>
            ))}
          </section>

          <div className="grid gap-6 lg:grid-cols-[1.6fr_1fr]">
            <section className="panel">
              <div className="flex items-center justify-between px-5 py-4"><h2 className="text-base font-semibold">Recent applications</h2><Link to="/applications" className="text-sm font-medium text-accent hover:underline">View all</Link></div>
              <div className="overflow-x-auto"><table className="w-full text-left text-sm">
                <thead className="border-y border-line text-xs text-muted"><tr><th className="px-5 py-2 font-medium">Company</th><th className="px-3 py-2 font-medium">Position</th><th className="px-3 py-2 font-medium">Platform</th><th className="px-3 py-2 font-medium">Status</th><th className="px-5 py-2 font-medium">Activity</th></tr></thead>
                <tbody className="divide-y divide-line">
                  {recent.data?.items.map((a) => (
                    <tr key={a.id} className="hover:bg-bg/60">
                      <td className="px-5 py-3 font-medium"><Link to={`/applications/${a.id}`} className="hover:text-accent">{a.company_name}</Link></td>
                      <td className="px-3 py-3">{a.job_title}</td>
                      <td className="px-3 py-3"><span className="flex items-center gap-2"><PlatformMark name={a.platform.name} />{a.platform.name}</span></td>
                      <td className="px-3 py-3"><StatusBadge status={a.status} /></td>
                      <td className="whitespace-nowrap px-5 py-3 text-muted">{timeAgo(a.updated_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table></div>
            </section>

            <div className="space-y-6">
              <section className="panel p-5">
                <h2 className="text-base font-semibold">Upcoming interviews</h2>
                {upcoming.data?.length ? (
                  <ul className="mt-3 space-y-3">{upcoming.data.map((i) => (
                    <li key={i.id}><Link to={`/applications/${i.application_id}`} className="block hover:text-accent"><p className="text-sm font-semibold">{i.job_title} · {i.company_name}</p><p className="text-xs text-muted">{fmtDateTime(i.interview_date)}{i.interview_type ? ` · ${i.interview_type}` : ''}</p></Link></li>
                  ))}</ul>
                ) : <p className="mt-2 text-sm text-muted">Nothing scheduled. <Link to="/interviews" className="font-medium text-accent hover:underline">Schedule an interview</Link></p>}
              </section>
              <section className="panel p-5">
                <h2 className="text-base font-semibold">Applications by platform</h2>
                <ul className="mt-3 space-y-3">
                  {platforms.data?.map((p) => (
                    <li key={p.platform_id}>
                      <div className="flex items-center justify-between text-sm"><span className="flex items-center gap-2"><PlatformMark name={p.name} />{p.name}</span><span className="font-semibold">{p.count}</span></div>
                      <div className="mt-1.5 h-1.5 rounded-full bg-line"><div className="h-full rounded-full bg-accent" style={{ width: `${(p.count / maxPlatform) * 100}%` }} /></div>
                    </li>
                  ))}
                </ul>
              </section>
            </div>
          </div>

          <section className="panel">
            <div className="flex items-center justify-between px-5 py-4"><h2 className="text-base font-semibold">Recent Gmail notifications</h2><Link to="/emails" className="text-sm font-medium text-accent hover:underline">Email activity</Link></div>
            {activity.data?.emails.length ? (
              <ul className="divide-y divide-line border-t border-line">{activity.data.emails.slice(0, 5).map((e) => (
                <li key={e.id} className="flex flex-wrap items-center gap-x-4 gap-y-1 px-5 py-3">
                  <span className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${CATEGORY_TONE[e.classification] ?? DEFAULT_CATEGORY_TONE}`}>{e.classification_label}</span>
                  <span className="min-w-0 flex-1 truncate text-sm font-medium">{e.subject || '(no subject)'}</span>
                  <span className="text-xs text-muted">{e.applications[0] ? `${e.applications[0].company_name}` : 'Needs review'} · {timeAgo(e.received_at)}</span>
                </li>
              ))}</ul>
            ) : <p className="border-t border-line px-5 py-6 text-sm text-muted">No job emails yet. Connect Gmail in Settings, then choose Sync Gmail.</p>}
          </section>
        </div>
      )}
      {adding && <ApplicationForm onClose={() => setAdding(false)} />}
    </>
  )
}
