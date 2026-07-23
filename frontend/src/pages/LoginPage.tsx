import { useState } from "react"
import { Navigate, useNavigate } from "react-router-dom"
import { GoogleLogin, GoogleOAuthProvider } from "@react-oauth/google"
import type { CredentialResponse } from "@react-oauth/google"
import { useAuth } from "../context/AuthContext"
import { ApiError } from "../services/apiClient"
import { signInWithMicrosoft } from "../services/msalClient"

export function LoginPage() {
  const { isAuthenticated, loginWithGoogle, loginWithMicrosoft } = useAuth()
  const navigate = useNavigate()
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  if (isAuthenticated) {
    return <Navigate to="/workers" replace />
  }

  const handleGoogleSuccess = async (credentialResponse: CredentialResponse) => {
    if (!credentialResponse.credential) {
      setError("Google 로그인에서 자격 증명을 받지 못했습니다.")
      return
    }
    setError(null)
    setIsSubmitting(true)
    try {
      await loginWithGoogle(credentialResponse.credential)
      navigate("/workers")
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Google 로그인에 실패했습니다.")
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleMicrosoftLogin = async () => {
    setError(null)
    setIsSubmitting(true)
    try {
      const idToken = await signInWithMicrosoft()
      await loginWithMicrosoft(idToken)
      navigate("/workers")
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Microsoft 로그인에 실패했습니다.")
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="login-page">
      <div className="login-form">
        <h1>관리자 로그인</h1>

        <GoogleOAuthProvider clientId={import.meta.env.VITE_GOOGLE_CLIENT_ID}>
          <GoogleLogin onSuccess={handleGoogleSuccess} onError={() => setError("Google 로그인에 실패했습니다.")} />
        </GoogleOAuthProvider>

        <button type="button" onClick={handleMicrosoftLogin} disabled={isSubmitting}>
          Microsoft 계정으로 로그인
        </button>

        {error && <p className="form-error">{error}</p>}
      </div>
    </div>
  )
}
