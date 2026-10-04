import { statusClass } from '../utils/format.js'

export function Spinner() {
  return (
    <div className="spinner-wrap">
      <div className="spinner" aria-label="Loading" />
    </div>
  )
}

export function Alert({ error, kind = 'error', children }) {
  if (!error && !children) return null
  return (
    <div className={`alert ${kind}`} role={kind === 'error' ? 'alert' : 'status'}>
      {error ? (
        <>
          <strong>{error.message}</strong>
          {Array.isArray(error.details) && error.details.length > 0 && (
            <ul>{error.details.map((d, i) => <li key={i}>{d}</li>)}</ul>
          )}
        </>
      ) : (
        children
      )}
    </div>
  )
}

export function PageHeader({ title, subtitle }) {
  return (
    <header className="page-header">
      <h1>{title}</h1>
      {subtitle && <p className="muted">{subtitle}</p>}
    </header>
  )
}

export function StatCard({ label, value, hint, tone }) {
  return (
    <div className={`stat ${tone || ''}`}>
      <span className="stat-label">{label}</span>
      <span className="stat-value">{value}</span>
      {hint && <span className="stat-hint">{hint}</span>}
    </div>
  )
}

export function ProgressBar({ percent, tone }) {
  const pct = Math.max(0, Math.min(100, Number(percent) || 0))
  return (
    <div className="progress" role="progressbar" aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100}>
      <div className={`progress-fill ${tone || ''}`} style={{ width: `${pct}%` }} />
    </div>
  )
}

export function StatusBadge({ status }) {
  return <span className={`badge ${statusClass(status)}`}>{status}</span>
}

export function Field({ label, hint, children }) {
  return (
    <label className="field">
      <span>{label}</span>
      {children}
      {hint && <small>{hint}</small>}
    </label>
  )
}