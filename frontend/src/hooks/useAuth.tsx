import { createContext, useContext, useState, useCallback, ReactNode } from 'react'
import { authApi, User } from '../api/client'

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
}

interface AuthContextValue extends AuthState {
  login: (email: string, password: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

function loadStoredAuth(): AuthState {
  try {
    const token = localStorage.getItem('access_token')
    const raw = localStorage.getItem('user')
    if (token && raw) {
      return { token, user: JSON.parse(raw), isAuthenticated: true }
    }
  } catch {
    /* ignore parse errors */
  }
  return { token: null, user: null, isAuthenticated: false }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>(loadStoredAuth)

  const login = useCallback(async (email: string, password: string) => {
    const { data } = await authApi.login(email, password)
    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('user', JSON.stringify(data.user))
    setState({ token: data.access_token, user: data.user, isAuthenticated: true })
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('user')
    setState({ token: null, user: null, isAuthenticated: false })
  }, [])

  return (
    <AuthContext.Provider value={{ ...state, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
