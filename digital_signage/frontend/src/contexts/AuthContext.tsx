import React, { createContext, useContext, useEffect, useMemo, useState } from 'react'
import { mockUsers } from '../mocks/bookingData'
import { User } from '../types'

interface AuthContextType {
  user: User | null
  login: (username: string, password: string) => Promise<void>
  logout: () => void
  loading: boolean
}

const STORAGE_KEY = 'booking_demo_user'

const AuthContext = createContext<AuthContextType | undefined>(undefined)

const findDemoUser = (username: string): User | undefined =>
  mockUsers.find((u) => u.username.toLowerCase() === username.trim().toLowerCase())

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) {
      setLoading(false)
      return
    }

    const restored = findDemoUser(raw)
    setUser(restored ?? null)
    setLoading(false)
  }, [])

  const login = async (username: string, password: string) => {
    const found = findDemoUser(username)
    if (!found || password.length < 3) {
      throw new Error('Nieprawidlowe dane logowania (demo: admin/manager/recepcja).')
    }

    localStorage.setItem(STORAGE_KEY, found.username)
    setUser(found)
  }

  const logout = () => {
    localStorage.removeItem(STORAGE_KEY)
    setUser(null)
  }

  const value = useMemo(() => ({ user, login, logout, loading }), [user, loading])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}
