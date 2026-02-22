import React, { createContext, useContext, useState, useEffect } from 'react'
import { api } from '../services/api'
import { User } from '../types'

interface AuthContextType {
  user: User | null
  login: (username: string, password: string) => Promise<void>
  logout: () => void
  loading: boolean
}

interface TokenResponse {
  access_token: string
  token_type: string
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  const fetchCurrentUser = async (): Promise<User | null> => {
    try {
      const response = await api.get<User>('/auth/me')
      return response.data
    } catch {
      return null
    }
  }

  useEffect(() => {
    let isMounted = true

    const initAuth = async () => {
      const token = localStorage.getItem('token')
      if (!token) {
        if (isMounted) {
          setUser(null)
          setLoading(false)
        }
        return
      }

      const currentUser = await fetchCurrentUser()

      if (!isMounted) {
        return
      }

      if (currentUser) {
        setUser(currentUser)
      } else {
        localStorage.removeItem('token')
        setUser(null)
      }

      setLoading(false)
    }

    initAuth()

    return () => {
      isMounted = false
    }
  }, [])

  const login = async (username: string, password: string) => {
    try {
      const response = await api.post<TokenResponse>('/auth/login', { username, password })
      localStorage.setItem('token', response.data.access_token)

      const currentUser = await fetchCurrentUser()
      if (!currentUser) {
        localStorage.removeItem('token')
        throw new Error('Nie udało się pobrać danych użytkownika')
      }

      setUser(currentUser)
    } catch (error) {
      setUser(null)
      throw error
    }
  }

  const logout = () => {
    localStorage.removeItem('token')
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
