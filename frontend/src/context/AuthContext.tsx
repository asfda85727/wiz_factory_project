import { createContext, useContext, useState } from "react"
import type { ReactNode } from "react"
import { api, clearToken, getToken, setToken } from "../services/apiClient"

interface LoginResponse {
  access_token: string
}

interface AuthContextValue {
  isAuthenticated: boolean
  loginWithGoogle: (idToken: string) => Promise<void>
  loginWithMicrosoft: (idToken: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(() => getToken() !== null)

  const loginWithProvider = async (path: string, idToken: string) => {
    const response = await api.post<LoginResponse>(path, { id_token: idToken })
    setToken(response.access_token)
    setIsAuthenticated(true)
  }

  const loginWithGoogle = (idToken: string) => loginWithProvider("/admin/login/google", idToken)
  const loginWithMicrosoft = (idToken: string) => loginWithProvider("/admin/login/microsoft", idToken)

  const logout = () => {
    clearToken()
    setIsAuthenticated(false)
  }

  return (
    <AuthContext.Provider value={{ isAuthenticated, loginWithGoogle, loginWithMicrosoft, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext)
  if (context === null) {
    throw new Error("useAuth는 AuthProvider 내부에서만 사용할 수 있습니다.")
  }
  return context
}
