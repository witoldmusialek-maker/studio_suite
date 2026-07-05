import React, { createContext, useContext, useEffect, useMemo, useState } from 'react'

import { api } from '../services/api'
import { User } from '../types'

interface AuthContextType {
  user: User | null
  login: (username: string, password: string, totpCode?: string) => Promise<void>
  logout: () => void
  loading: boolean
}

type TenantContextResponse = {
  licenses?: Array<{
    module_code?: string
    is_enabled?: boolean
  }>
}

const TOKEN_KEY = 'token'
const USER_KEY = 'booking_user'

const AuthContext = createContext<AuthContextType | undefined>(undefined)

const mapRole = (role: string): User['role'] => {
  if (
    role === 'admin' ||
    role === 'manager' ||
    role === 'manager_main' ||
    role === 'manager_salon' ||
    role === 'employee' ||
    role === 'receptionist'
  ) {
    return role
  }
  return 'manager'
}

const resolveAssignedSalonIds = (role: User['role'], salonIds: number[]) => {
  if (salonIds.length === 0) return [1]
  if (role === 'receptionist' || role === 'manager_salon') return [salonIds[0]]
  return salonIds
}

const buildMappedUser = (
  payload: any,
  fallbackSalonIds: number[],
  licensedModules: string[],
): User => {
  const role = mapRole(payload.role)
  const isSuperadmin = Boolean(payload.is_superadmin)
  const linkedSalonId = typeof payload.linked_salon_id === 'number' ? payload.linked_salon_id : undefined
  const effectiveSalonIds = isSuperadmin
    ? []
    : linkedSalonId
    ? [linkedSalonId]
    : resolveAssignedSalonIds(role, fallbackSalonIds)

  return {
    id: payload.id,
    username: payload.username,
    role,
    full_name: payload.username,
    assigned_salon_ids: effectiveSalonIds,
    linked_staff_id: payload.linked_staff_id,
    linked_staff_name: payload.linked_staff_name,
    linked_salon_id: payload.linked_salon_id,
    linked_salon_name: payload.linked_salon_name,
    totp_enabled: Boolean(payload.totp_enabled),
    tenant_id: typeof payload.tenant_id === 'number' ? payload.tenant_id : undefined,
    is_superadmin: isSuperadmin,
    licensed_modules: licensedModules,
    legacy_caisse_enabled: Boolean(payload.legacy_caisse_enabled),
  }
}

const fetchLicensedModules = async (isSuperadmin: boolean): Promise<string[]> => {
  if (isSuperadmin) return []
  const res = await api.get<TenantContextResponse>('/auth/tenant-context')
  const rows = res.data?.licenses || []
  return rows
    .filter((row) => Boolean(row?.is_enabled))
    .map((row) => String(row?.module_code || '').trim().toUpperCase())
    .filter((code) => code.length > 0)
}

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const bootstrap = async () => {
      const token = localStorage.getItem(TOKEN_KEY)
      if (!token) {
        setLoading(false)
        return
      }
      try {
        const me = await api.get('/auth/me')
        const payload = me.data
        const licensedModules = await fetchLicensedModules(Boolean(payload?.is_superadmin))
        let salonIds: number[] = []
        if (!payload?.is_superadmin) {
          const salonsRes = await api.get<Array<{ id: number }>>('/resources/salons')
          salonIds = (salonsRes.data || []).map((salon) => salon.id)
        }
        const mappedUser = buildMappedUser(payload, salonIds, licensedModules)
        localStorage.setItem(USER_KEY, JSON.stringify(mappedUser))
        setUser(mappedUser)
      } catch {
        localStorage.removeItem(TOKEN_KEY)
        localStorage.removeItem(USER_KEY)
        setUser(null)
      } finally {
        setLoading(false)
      }
    }
    bootstrap()
  }, [])

  const login = async (username: string, password: string, totpCode?: string) => {
    try {
      const loginRes = await api.post('/auth/login', { username, password, totp_code: totpCode || undefined })
      const token = loginRes.data.access_token as string
      localStorage.setItem(TOKEN_KEY, token)

      const me = await api.get('/auth/me')
      const payload = me.data
      const licensedModules = await fetchLicensedModules(Boolean(payload?.is_superadmin))
      let salonIds: number[] = []
      if (!payload?.is_superadmin) {
        const salonsRes = await api.get<Array<{ id: number }>>('/resources/salons')
        salonIds = (salonsRes.data || []).map((salon) => salon.id)
      }
      const mappedUser = buildMappedUser(payload, salonIds, licensedModules)
      localStorage.setItem(USER_KEY, JSON.stringify(mappedUser))
      setUser(mappedUser)
    } catch (err: any) {
      const detail = err?.response?.data?.detail
      if (typeof detail === 'string' && detail.length > 0) {
        throw new Error(detail)
      }
      throw new Error('Blad logowania')
    }
  }

  const logout = () => {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
    setUser(null)
  }

  const value = useMemo(() => ({ user, login, logout, loading }), [loading, user])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used within AuthProvider')
  return context
}
