import { useEffect, useRef } from 'react'
import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../services/api'
import { clean } from '../utils/format'

const get = (url, params) => api.get(url, { params: clean(params) }).then((r) => r.data)
const LIVE = 30_000 // dashboards refresh on their own so new emails and statuses show up without a reload
const GMAIL_AUTO_SYNC = 5 * 60_000

export const usePlatforms = () => useQuery({ queryKey: ['platforms'], queryFn: () => get('/platforms'), staleTime: 60_000 })
export const useApplications = (params) =>
  useQuery({ queryKey: ['applications', params], queryFn: () => get('/applications', params), placeholderData: keepPreviousData, refetchInterval: LIVE })
export const useApplication = (id) => useQuery({ queryKey: ['application', id], queryFn: () => get(`/applications/${id}`), refetchInterval: LIVE })
export const useStats = () => useQuery({ queryKey: ['dashboard', 'stats'], queryFn: () => get('/dashboard/stats'), refetchInterval: LIVE })
export const useStatusDistribution = () => useQuery({ queryKey: ['dashboard', 'status'], queryFn: () => get('/dashboard/status-distribution'), refetchInterval: LIVE })
export const usePlatformDistribution = () => useQuery({ queryKey: ['dashboard', 'platforms'], queryFn: () => get('/dashboard/platforms'), refetchInterval: LIVE })
export const useRecentActivity = () => useQuery({ queryKey: ['dashboard', 'activity'], queryFn: () => get('/dashboard/recent-activity'), refetchInterval: LIVE })
export const useInterviews = (params) => useQuery({ queryKey: ['interviews', params], queryFn: () => get('/interviews', params), refetchInterval: LIVE })
export const useEmails = (params) =>
  useQuery({ queryKey: ['emails', params], queryFn: () => get('/emails', params), placeholderData: keepPreviousData, refetchInterval: LIVE })
export const useJobAlerts = (params) =>
  useQuery({ queryKey: ['job-alerts', params], queryFn: () => get('/job-alerts', params), placeholderData: keepPreviousData, refetchInterval: LIVE })
export const useGmailStatus = () =>
  useQuery({
    queryKey: ['gmail', 'status'],
    queryFn: () => get('/gmail/status'),
    refetchInterval: (query) => (query.state.data?.sync_status === 'syncing' ? 2000 : LIVE),
  })

export function useRefreshAll() {
  const qc = useQueryClient()
  return () => ['applications', 'application', 'dashboard', 'emails', 'job-alerts', 'interviews'].forEach((key) => qc.invalidateQueries({ queryKey: [key] }))
}

/** Generic mutation that refreshes the data every screen depends on. */
export function useApiMutation(fn, { refresh = true, onSuccess } = {}) {
  const refreshAll = useRefreshAll()
  const qc = useQueryClient()
  return useMutation({
    mutationFn: fn,
    onSuccess: (data, vars) => {
      if (refresh) refreshAll()
      qc.invalidateQueries({ queryKey: ['platforms'] })
      qc.invalidateQueries({ queryKey: ['gmail'] })
      onSuccess?.(data, vars)
    },
  })
}

export const useSyncGmail = () => useApiMutation(() => api.post('/gmail/sync').then((r) => r.data), { refresh: false })

/** Keep Gmail-sourced application statuses current while the overview is open. */
export function useAutoSyncGmail(enabled = true) {
  const { data: status } = useGmailStatus()
  const sync = useSyncGmail()
  const refreshAll = useRefreshAll()
  const mutate = useRef(sync.mutate)
  const previousStatus = useRef(null)
  const started = useRef(false)
  mutate.current = sync.mutate

  useEffect(() => {
    if (previousStatus.current === 'syncing' && status?.sync_status && status.sync_status !== 'syncing') refreshAll()
    previousStatus.current = status?.sync_status
  }, [status?.sync_status, refreshAll])

  useEffect(() => {
    if (!enabled || !status?.connected) {
      started.current = false
      return undefined
    }
    if (status.sync_status === 'syncing') return undefined
    const syncIfVisible = () => {
      if (document.visibilityState === 'visible') mutate.current()
    }
    if (!started.current) {
      started.current = true
      syncIfVisible()
    }
    const interval = window.setInterval(syncIfVisible, GMAIL_AUTO_SYNC)
    return () => window.clearInterval(interval)
  }, [enabled, status?.connected, status?.sync_status])

  return status
}
