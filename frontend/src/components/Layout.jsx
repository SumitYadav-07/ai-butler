import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'
import { PRIVACY_TEXT } from '../utils/constants.js'

const LINKS = [
  ['/dashboard', 'Dashboard'],
  ['/transactions', 'Transactions'],
  ['/analytics', 'Analytics'],
  ['/emi', 'EMI check'],
  ['/goals', 'Goals'],
  ['/emergency-fund', 'Emergency fund'],
  ['/butler', 'AI Butler'],
  ['/settings', 'Settings'],
]

export default function Layout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = async () => {
    await logout()
    navigate('/login', { replace: true })
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">AI Butler</div>
        <nav>
          {LINKS.map(([to, label]) => (
            <NavLink key={to} to={to} className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}>
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-footer">
          <span className="muted small">{user?.name}</span>
          <button className="btn secondary small" onClick={handleLogout}>Log out</button>
        </div>
      </aside>
      <div className="main">
        <div className="privacy-strip">🔒 {PRIVACY_TEXT}</div>
        <main className="content">
          <Outlet />
        </main>
      </div>
    </div>
  )
}