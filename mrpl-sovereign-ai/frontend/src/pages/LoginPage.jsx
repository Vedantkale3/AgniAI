import { useState } from 'react'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'
import { ArrowRight, LockKeyhole, ShieldCheck } from 'lucide-react'

import { useAuth } from '../auth/AuthContext.jsx'


export default function LoginPage() {
  const { login, isAuthenticated, loading } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const destination = location.state?.from?.pathname || '/'

  if (!loading && isAuthenticated) {
    return <Navigate to={destination} replace />
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')
    setSubmitting(true)

    try {
      await login(username.trim(), password)
      navigate(destination, { replace: true })
    } catch (submitError) {
      setError(submitError.message || 'Unable to sign in.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <main className="login-page">
      <div className="login-glow login-glow-one" />
      <div className="login-glow login-glow-two" />

      <section className="login-shell" aria-label="MRPL operator sign-in">
        <div className="login-brand-block">
          <div className="login-brand-mark">
            <ShieldCheck size={27} strokeWidth={2.2} />
          </div>

          <div>
            <div className="login-brand-name">
              Agni AI
            </div>
            <div className="login-brand-product">
              Workbench
            </div>
          </div>
        </div>

        <div className="login-divider" />

        <div className="login-copy">
          <div className="login-eyebrow">
            <span className="login-status-dot" />
            LOCAL SECURE ACCESS
          </div>

          <h1>Welcome back</h1>
          <p>
            Sign in to access your on-premise agentic workspace.
          </p>
        </div>

        <form className="login-form" onSubmit={handleSubmit}>
          <div className="login-field">
            <label htmlFor="username">Username</label>
            <input
              id="username"
              name="username"
              type="text"
              autoComplete="username"
              placeholder="Enter your username"
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              disabled={submitting}
              required
              autoFocus
            />
          </div>

          <div className="login-field">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              name="password"
              type="password"
              autoComplete="current-password"
              placeholder="Enter your password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              disabled={submitting}
              required
            />
          </div>

          {error && (
            <div className="login-error" role="alert">
              <LockKeyhole size={15} />
              <span>{error}</span>
            </div>
          )}

          <button
            className="login-submit"
            type="submit"
            disabled={submitting}
          >
            <span>
              {submitting ? 'Authenticating…' : 'Sign in securely'}
            </span>
            {!submitting && <ArrowRight size={18} />}
          </button>
        </form>

        <div className="login-trust-row">
          <div className="login-trust-item">
            <ShieldCheck size={15} />
            <span>Air-gapped environment</span>
          </div>

          <div className="login-trust-item">
            <span className="login-trust-dot" />
            <span>No external identity provider</span>
          </div>
        </div>

        <p className="login-footer">
          Access is monitored by Network Sentinel.
        </p>
      </section>
    </main>
  )
}
