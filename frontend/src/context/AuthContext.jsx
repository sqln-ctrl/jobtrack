import { createContext, useContext } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../services/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const qc = useQueryClient()
  const { data, isLoading } = useQuery({
    queryKey: ['me'],
    queryFn: () => api.get('/auth/me').then((r) => r.data).catch((e) => (e.response?.status === 401 ? null : Promise.reject(e))),
    retry: false,
    staleTime: 60_000,
  })
  const logout = async () => {
    await api.post('/auth/logout')
    qc.clear()
    qc.setQueryData(['me'], null)
  }
  const value = { user: data?.user ?? null, gmailConnected: data?.gmail_connected ?? false, loading: isLoading, logout }
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export const useAuth = () => useContext(AuthContext)
