import { useNavigate } from 'react-router-dom'
import { LogOut, BarChart2 } from 'lucide-react'
import { useAuth } from '../hooks/useAuth'

export default function Navbar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <header
      style={{
        background: 'var(--bg-surface)',
        borderBottom: '1px solid var(--border)',
        boxShadow: 'var(--shadow-xs)',
        position: 'sticky',
        top: 0,
        zIndex: 50,
      }}
    >
      <div
        style={{
          maxWidth: 1200,
          margin: '0 auto',
          padding: '0 24px',
          height: 60,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: 16,
        }}
      >
        {/* Logo */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div
            style={{
              width: 32,
              height: 32,
              background: 'var(--primary)',
              borderRadius: 8,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
            }}
          >
            <BarChart2 size={18} color="white" strokeWidth={2.5} />
          </div>
          <span style={{ fontWeight: 700, fontSize: 18, color: 'var(--text-primary)', letterSpacing: '-0.3px' }}>
            Elevate
          </span>
        </div>

        {/* User info + logout */}
        {user && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              {/* Avatar */}
              <div
                style={{
                  width: 36,
                  height: 36,
                  background: 'var(--primary-light)',
                  borderRadius: '50%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontWeight: 600,
                  fontSize: 14,
                  color: 'var(--primary)',
                  flexShrink: 0,
                }}
              >
                {user.name.charAt(0).toUpperCase()}
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                <span style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)', lineHeight: 1.2 }}>
                  {user.name}
                </span>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                    {user.company_name}
                  </span>
                  <span
                    className={`badge ${user.role === 'HR' ? 'badge-hr' : 'badge-employee'}`}
                    style={{ fontSize: 11, padding: '1px 7px' }}
                  >
                    {user.role}
                  </span>
                </div>
              </div>
            </div>
            <button
              id="logout-btn"
              className="btn btn-ghost btn-sm"
              onClick={handleLogout}
              title="Sign out"
              style={{ gap: 6 }}
            >
              <LogOut size={15} />
              <span style={{ display: 'none' }}>Sign out</span>
            </button>
          </div>
        )}
      </div>
    </header>
  )
}
