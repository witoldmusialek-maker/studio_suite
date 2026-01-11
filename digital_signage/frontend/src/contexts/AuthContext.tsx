import React, { createContext, useContext, useState, useEffect } from 'react'
import { api } from '../services/api'
import { User } from '../types'

interface AuthContextType {
  user: User | null
  login: (username: string, password: string) => Promise<void>
  logout: () => void
  loading: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Sprawdzenie czy użytkownik jest zalogowany
    const token = localStorage.getItem('token')
    if (token) {
      // Pobranie danych użytkownika z tokena (można dodać endpoint /me)
      // Na razie tylko sprawdzamy czy token istnieje
      setLoading(false)
    } else {
      setLoading(false)
    }
  }, [])

  const login = async (username: string, password: string) => {
    try {
      const response = await api.post('/auth/login', { username, password })
      const { access_token } = response.data
      localStorage.setItem('token', access_token)
      
      // Pobranie danych użytkownika (można dodać endpoint /me)
      // Na razie używamy danych z odpowiedzi lub domyślnych
      setUser({ username, role: 'admin' } as User)
    } catch (error) {
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



