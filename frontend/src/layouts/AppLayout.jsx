import { useState } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useTheme } from '../hooks/useTheme'
import { Icon } from '../components/ui'

const NAV = [
  { to: '/', label: 'Overview', icon: 'overview', end: true },
  { to: '/applications', label: 'All applications', icon: 'list' },
  { to: '/platforms', label: 'Platforms', icon: 'platforms' },
  { to: '/emails', label: 'Email activity', icon: 'mail' },
  { to: '/interviews', label: 'Interviews', icon: 'calendar' },
  { to: '/settings', label: 'Settings', icon: 'settings' },
]

export default function AppLayout() {
  const { user } = useAuth()
  const { dark, toggle } = useTheme()
  const navigate = useNavigate()
  const [q, setQ] = useState('')

  const search = (e) => {
    e.preventDefault()
    navigate(q.trim() ? `/applications?q=${encodeURIComponent(q.trim())}` : '/applications')
  }

  return (
    <div className="min-h-screen md:flex">
      <aside className="border-b border-line bg-surface md:sticky md:top-0 md:h-screen md:w-60 md:shrink-0 md:border-b-0 md:border-r">
        <div className="flex items-center gap-2.5 px-5 py-4">
          <span className="grid h-8 w-8 place-items-center rounded-lg bg-accent text-accent-ink"><Icon name="list" className="h-4 w-4" /></span>
          <span className="font-display text-lg font-bold">JobTrack</span>
        </div>
        <nav aria-label="Main" className="flex gap-1 overflow-x-auto px-3 pb-3 md:flex-col md:pb-0">
          {NAV.map((item) => (
            <NavLink key={item.to} to={item.to} end={item.end}
              className={({ isActive }) => `flex shrink-0 items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${isActive ? 'bg-accent/10 text-accent' : 'text-muted hover:bg-bg hover:text-ink'}`}>
              <Icon name={item.icon} />{item.label}
            </NavLink>
          ))}
        </nav>
      </aside>

      <div className="min-w-0 flex-1">
        <header className="flex items-center gap-3 border-b border-line bg-bg/90 px-4 py-3 backdrop-blur sm:px-8">
          <form onSubmit={search} role="search" className="relative max-w-md flex-1">
            <Icon name="search" className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted" />
            <input aria-label="Search applications" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search company, job title or platform" className="!pl-9" />
          </form>
          <button className="btn btn-ghost !p-2" onClick={toggle} aria-label={dark ? 'Switch to light mode' : 'Switch to dark mode'}><Icon name={dark ? 'sun' : 'moon'} className="h-5 w-5" /></button>
          <NavLink to="/settings" className="flex items-center gap-2" aria-label="Your profile">
            {user?.profile_picture
              ? <img src={user.profile_picture} alt="" referrerPolicy="no-referrer" className="h-8 w-8 rounded-full" />
              : <span className="grid h-8 w-8 place-items-center rounded-full bg-accent/15 text-sm font-semibold text-accent">{user?.name?.[0]?.toUpperCase()}</span>}
          </NavLink>
        </header>
        <main className="mx-auto max-w-6xl px-4 py-8 sm:px-8"><Outlet /></main>
      </div>
    </div>
  )
}
