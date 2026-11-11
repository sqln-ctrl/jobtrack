import { useSearchParams } from 'react-router-dom'
import { StatusBadge } from '../components/ui'

const ERRORS = {
  cancelled: 'Sign-in was cancelled. Try again when you are ready.',
  invalid_state: 'That sign-in link expired. Start again.',
  google_unavailable: 'Google could not be reached. Try again in a moment.',
  unverified_email: 'Your Google email address is not verified. Verify it with Google, then try again.',
}

export default function Login() {
  const [params] = useSearchParams()
  const error = ERRORS[params.get('error')]
  return (
    <div className="mx-auto grid min-h-screen max-w-5xl items-center gap-12 px-6 py-12 md:grid-cols-[1.2fr_1fr]">
      <div>
        <p className="font-display text-lg font-bold text-accent">JobTrack</p>
        <h1 className="mt-4 text-4xl font-bold leading-[1.05] sm:text-6xl">Apply for jobs. Let your inbox update the tracker.</h1>
        <p className="mt-5 max-w-md text-base text-muted">Keep every application from LinkedIn, Indeed, Rozee.pk and company sites in one list, and see replies land on the right job automatically.</p>
        <div className="mt-8 flex flex-wrap items-center gap-2" aria-label="Example application journey">
          {['sent', 'viewed', 'interview_call', 'accepted'].map((s, i) => (
            <span key={s} className="flex items-center gap-2"><StatusBadge status={s} />{i < 3 && <span className="text-line">—</span>}</span>
          ))}
        </div>
      </div>
      <div className="panel p-7">
        <h2 className="text-xl font-semibold">Sign in</h2>
        <p className="mt-1 text-sm text-muted">Use your Google account. Connecting Gmail is a separate, optional step after you sign in.</p>
        {error && <p role="alert" className="mt-4 rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700 dark:bg-rose-500/10 dark:text-rose-300">{error}</p>}
        <a href="/api/v1/auth/google" className="btn btn-primary mt-6 w-full !py-2.5">
          <span aria-hidden="true" className="grid h-5 w-5 place-items-center rounded-full bg-accent-ink/90 text-xs font-bold text-accent">G</span>
          Continue with Google
        </a>
      </div>
    </div>
  )
}
