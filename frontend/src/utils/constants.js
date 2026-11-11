export const STATUSES = [
  { value: 'sent', label: 'Sent', badge: 'bg-sky-100 text-sky-800 dark:bg-sky-500/15 dark:text-sky-300', bar: 'bg-sky-500' },
  { value: 'viewed', label: 'Viewed', badge: 'bg-indigo-100 text-indigo-800 dark:bg-indigo-500/15 dark:text-indigo-300', bar: 'bg-indigo-500' },
  { value: 'interview_call', label: 'Interview call', badge: 'bg-teal-100 text-teal-800 dark:bg-teal-500/15 dark:text-teal-300', bar: 'bg-teal-500' },
  { value: 'accepted', label: 'Accepted', badge: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-500/15 dark:text-emerald-300', bar: 'bg-emerald-500' },
]
export const STATUS_BY_VALUE = Object.fromEntries(STATUSES.map((s) => [s.value, s]))

export const EMPLOYMENT_TYPES = [
  { value: 'full_time', label: 'Full-time' },
  { value: 'part_time', label: 'Part-time' },
  { value: 'contract', label: 'Contract' },
  { value: 'internship', label: 'Internship' },
  { value: 'freelance', label: 'Freelance' },
  { value: 'temporary', label: 'Temporary' },
  { value: 'other', label: 'Other' },
]
export const EMPLOYMENT_LABEL = Object.fromEntries(EMPLOYMENT_TYPES.map((t) => [t.value, t.label]))

export const CATEGORY_TONE = {
  rejection: 'bg-rose-100 text-rose-800 dark:bg-rose-500/15 dark:text-rose-300',
  job_offer: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-500/15 dark:text-emerald-300',
  interview_invitation: 'bg-teal-100 text-teal-800 dark:bg-teal-500/15 dark:text-teal-300',
  assessment_invitation: 'bg-amber-100 text-amber-800 dark:bg-amber-500/15 dark:text-amber-300',
  under_review: 'bg-indigo-100 text-indigo-800 dark:bg-indigo-500/15 dark:text-indigo-300',
}
export const DEFAULT_CATEGORY_TONE = 'bg-sky-100 text-sky-800 dark:bg-sky-500/15 dark:text-sky-300'
