import { useState, FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { BarChart2, Mail, Lock, Eye, EyeOff } from 'lucide-react'
import { useAuth } from '../hooks/useAuth'
import Spinner from '../components/Spinner'

const DEMO_ACCOUNTS = [
  { label: 'Priya (Manager + Employee)', email: 'priya@ashoka.com', note: 'Gives & receives feedback' },
  { label: 'Kavita (HR)', email: 'kavita@ashoka.com', note: 'Sees pending submissions' },
  { label: 'Rohan (Top Manager)', email: 'rohan@ashoka.com', note: 'VP Engineering' },
  { label: 'Aditya (Employee)', email: 'aditya@ashoka.com', note: 'Views trends' },
  { label: 'Arjun (Flat-Org Founder)', email: 'arjun@brightpath.com', note: 'Bright Path Consulting' },
  { label: 'HR — Bright Path', email: 'hr@brightpath.com', note: 'People Ops' },
]

export default function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      await login(email.trim(), password)
      navigate('/')
    } catch {
      setError('Invalid email or password. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const quickLogin = async (demoEmail: string) => {
    setEmail(demoEmail)
    setPassword('password123')
    setError(null)
    setLoading(true)
    try {
      await login(demoEmail, 'password123')
      navigate('/')
    } catch {
      setError('Demo login failed. Is the backend running?')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      style={{
        minHeight: '100vh',
        background: 'var(--bg-page)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '24px 16px',
      }}
    >
      <div style={{ width: '100%', maxWidth: 440 }}>
        {/* Logo */}
        <div style={{ textAlign: 'center', marginBottom: 36 }}>
          <div
            style={{
              width: 56,
              height: 56,
              background: 'var(--primary)',
              borderRadius: 16,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 16px',
              boxShadow: '0 4px 16px rgba(42, 157, 143, 0.3)',
            }}
          >
            <BarChart2 size={28} color="white" strokeWidth={2.5} />
          </div>
          <h1 style={{ fontSize: 26, fontWeight: 700, letterSpacing: '-0.5px' }}>
            Elevate
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: 15, marginTop: 6 }}>
            Performance feedback, done right
          </p>
        </div>

        {/* Login Card */}
        <div
          className="card"
          style={{ padding: 32, boxShadow: 'var(--shadow-lg)', borderRadius: 18 }}
        >
          <h2 style={{ fontSize: 18, marginBottom: 24 }}>Sign in to your account</h2>

          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
            {/* Email */}
            <div className="form-group">
              <label className="form-label" htmlFor="email-input">
                Email address
              </label>
              <div style={{ position: 'relative' }}>
                <Mail
                  size={16}
                  style={{
                    position: 'absolute',
                    left: 12,
                    top: '50%',
                    transform: 'translateY(-50%)',
                    color: 'var(--text-muted)',
                  }}
                />
                <input
                  id="email-input"
                  type="email"
                  className="form-input"
                  placeholder="you@company.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  autoComplete="email"
                  style={{ paddingLeft: 38 }}
                />
              </div>
            </div>

            {/* Password */}
            <div className="form-group">
              <label className="form-label" htmlFor="password-input">
                Password
              </label>
              <div style={{ position: 'relative' }}>
                <Lock
                  size={16}
                  style={{
                    position: 'absolute',
                    left: 12,
                    top: '50%',
                    transform: 'translateY(-50%)',
                    color: 'var(--text-muted)',
                  }}
                />
                <input
                  id="password-input"
                  type={showPassword ? 'text' : 'password'}
                  className="form-input"
                  placeholder="Your password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  autoComplete="current-password"
                  style={{ paddingLeft: 38, paddingRight: 40 }}
                />
                <button
                  type="button"
                  id="toggle-password-btn"
                  onClick={() => setShowPassword((s) => !s)}
                  style={{
                    position: 'absolute',
                    right: 10,
                    top: '50%',
                    transform: 'translateY(-50%)',
                    background: 'none',
                    border: 'none',
                    cursor: 'pointer',
                    color: 'var(--text-muted)',
                    padding: 4,
                  }}
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            {error && <div className="alert alert-error">{error}</div>}

            <button
              id="login-submit-btn"
              type="submit"
              className="btn btn-primary btn-full btn-lg"
              disabled={loading}
              style={{ marginTop: 4 }}
            >
              {loading ? <Spinner size="sm" /> : 'Sign in'}
            </button>
          </form>
        </div>

        {/* Demo Accounts */}
        <div style={{ marginTop: 24 }}>
          <div
            style={{
              fontSize: 12,
              fontWeight: 600,
              color: 'var(--text-muted)',
              textTransform: 'uppercase',
              letterSpacing: '0.5px',
              textAlign: 'center',
              marginBottom: 12,
            }}
          >
            Demo accounts — all passwords: password123
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {DEMO_ACCOUNTS.map((acct) => (
              <button
                key={acct.email}
                id={`demo-${acct.email.split('@')[0]}`}
                className="btn btn-secondary"
                onClick={() => quickLogin(acct.email)}
                disabled={loading}
                style={{
                  justifyContent: 'space-between',
                  padding: '10px 14px',
                  fontSize: 13,
                  textAlign: 'left',
                }}
              >
                <div>
                  <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{acct.label}</div>
                  <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 1 }}>{acct.note}</div>
                </div>
                <span style={{ fontSize: 12, color: 'var(--primary)', fontWeight: 500 }}>
                  Login →
                </span>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
