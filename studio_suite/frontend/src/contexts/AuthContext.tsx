import React, { createContext, useContext, useEffect, useMemo, useState } from 'react'

import { api } from '../services/api'
import { User } from '../types'

interface AuthContextType {
  user: User | null
  login: (username: string, password: string) => Promise<void>
  logout: () => void
  loading: boolean
}

const TOKEN_KEY = 'token'
const USER_KEY = 'booking_user'

const AuthContext = createContext<AuthContextType | undefined>(undefined)

const mapRole = (role: string): User['role'] => {
  if (role === 'admin' || role === 'manager' || role === 'receptionist' || role === 'operator_displays' || role === 'operator_bells' || role === 'operator') {
    return role
  }
  return 'manager'
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
        const mappedUser: User = {
          id: payload.id,
          username: payload.username,
          role: mapRole(payload.role),
          full_name: payload.username,
          assigned_salon_ids: [1],
        }
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

  const login = async (username: string, password: string) => {
    const loginRes = await api.post('/auth/login', { username, password })
    const token = loginRes.data.access_token as string
    localStorage.setItem(TOKEN_KEY, token)

    const me = await api.get('/auth/me')
    const payload = me.data
    const mappedUser: User = {
      id: payload.id,
      username: payload.username,
      role: mapRole(payload.role),
      full_name: payload.username,
      assigned_salon_ids: [1],
    }
    localStorage.setItem(USER_KEY, JSON.stringify(mappedUser))
    setUser(mappedUser)
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
