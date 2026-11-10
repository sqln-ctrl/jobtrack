import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../services/api'
import { clean } from '../utils/format'

const get = (url, params) => api.get(url, { params: clean(params) }).then((r) => r.data)
const LIVE = 30_000 // dashboards refresh on their own so new emails and statuses show up without a reload

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
export const useGmailStatus = () =>
  useQuery({
    queryKey: ['gmail', 'status'],
    queryFn: () => get('/gmail/status'),
    refetchInterval: (query) => (query.state.data?.sync_status === 'syncing' ? 2000 : LIVE),
  })

export function useRefreshAll() {
  const qc = useQueryClient()
  return () => ['applications', 'application', 'dashboard', 'emails', 'interviews'].forEach((key) => qc.invalidateQueries({ queryKey: [key] }))
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
