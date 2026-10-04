import { useState } from 'react'
import { Link } from 'react-router-dom'
import { CategoryPie } from '../components/Charts.jsx'
import EndOfDayCheck from '../components/EndOfDayCheck.jsx'
import SetupWizard from '../components/SetupWizard.jsx'
import { Alert, Field, ProgressBar, Spinner, StatCard, StatusBadge } from '../components/ui.jsx'
import { useLoad } from '../hooks/useLoad.js'
import { api } from '../services/api.js'
import { fmtDate, greeting, inr, numOrNull, statusClass } from '../utils/format.js'

function SafeSpending({ safe, onChanged }) {
  const [editing, setEditing] = useState(false)
  const [form, setForm] = useState({ reserve: '', target: '' })
  const [error, setError] = useState(null)

  const open = () => {
    setForm({ reserve: String(safe.emergency_reserve ?? 0), target: String(safe.savings_target ?? 0) })
    setEditing(true)
  }
  const save = async (e) => {
    e.preventDefault()
    setError(null)
    try {
      await api.profile.update({
        emergency_reserve: numOrNull(form.reserve),
        monthly_savings_target: numOrNull(form.target),
      })
      setEditing(false)
      onChanged()
    } catch (err) {
      setError(err)
    }
  }

  return (
    <section className="panel">
      <h2>Safe daily spending</h2>
      {!safe ? (
        <p className="muted">I don't have enough information to calculate that. Please enter your current balance.</p>
      ) : (
        <>
          <p className="big">≈ {inr(safe.safe_daily_amount)}<span className="muted small"> per day</span></p>
          <p className="small">{safe.explanation}</p>
          {safe.assumptions.map((a) => <p key={a} className="muted small">{a}</p>)}
          {!editing ? (
            <button className="btn secondary small" onClick={open}>Change reserve / savings target</button>
          ) : (
            <form className="inline-form wrap" onSubmit={save}>
              <Field label="Emergency reserve to hold back (₹)">
                <input type="number" min="0" step="0.01" value={form.reserve} onChange={(e) => setForm({ ...form, reserve: e.target.value })} />
              </Field>
              <Field label="Monthly savings target (₹)">
                <input type="number" min="0" step="0.01" value={form.target} onChange={(e) => setForm({ ...form, target: e.target.value })} />
              </Field>
              <button className="btn small">Save</button>
              <button type="button" className="btn secondary small" onClick={() => setEditing(false)}>Cancel</button>
            </form>
          )}
          <Alert error={error} />
        </>
      )}
    </section>
  )
}

export default function Dashboard() {
  const { data, error, loading, reload } = useLoad(() => api.dashboard(), [])

  if (loading && !data) return <Spinner />
  if (error) return <Alert error={error} />
  if (data.missing_fields.length > 0) return <SetupWizard initialName={data.name} onDone={reload} />

  const health = data.financial_health
  const emergency = data.emergency_fund

  return (
    <>
      <h1>{greeting()}, {data.name}</h1>

      <div className="grid stats">
        <StatCard label="Current balance" value={inr(data.current_balance)} tone={data.current_balance < 0 ? 'critical' : ''} />
        <StatCard label="Monthly income" value={inr(data.monthly_income)} />
        <StatCard label="Spent this month" value={inr(data.month_spending)} hint={`Today ${inr(data.today_spending)} · This week ${inr(data.week_spending)}`} />
        <StatCard label="Savings logged" value={inr(data.total_savings)} hint={`EMIs ${inr(data.emi_total)}/mo · Fixed ${inr(data.monthly_fixed_expenses)}/mo`} />
      </div>

      <div className="grid two">
        <SafeSpending safe={data.safe_daily_spending} onChanged={reload} />

        <section className="panel">
          <h2>Financial health</h2>
          <StatusBadge status={health.status} />
          <p>{health.reason}</p>
          <p className="muted small">{data.disclaimer}</p>
        </section>
      </div>

      <div className="grid two">
        <section className="panel">
          <h2>Upcoming expenses</h2>
          {data.upcoming_expenses.length === 0 ? (
            <p className="muted">Nothing due for the rest of this month. Add recurring bills and EMIs in Settings.</p>
          ) : (
            <ul className="list">
              {data.upcoming_expenses.map((u, i) => (
                <li key={`${u.name}-${i}`}>
                  <span>{u.name} <span className="muted small">({u.kind === 'emi' ? 'EMI' : 'bill'} · due {fmtDate(u.due_date)})</span></span>
                  <strong>{inr(u.amount)}</strong>
                </li>
              ))}
              <li className="total"><span>Total still due</span><strong>{inr(data.upcoming_total)}</strong></li>
            </ul>
          )}
        </section>

        <section className="panel">
          <h2>Spending breakdown</h2>
          <CategoryPie data={data.spending_breakdown} />
        </section>
      </div>

      <div className="grid two">
        <section className="panel">
          <h2>Forecast <span className="tag">estimate</span></h2>
          {data.forecast?.available ? (
            <>
              <p>{data.forecast.message}</p>
              <ul className="list">
                <li><span>Estimated remaining balance</span><strong>{inr(data.forecast.estimated_remaining_balance)}</strong></li>
                <li><span>Estimated savings</span><strong>{inr(data.forecast.estimated_savings)}</strong></li>
              </ul>
            </>
          ) : (
            <p className="muted">{data.forecast?.message || 'Enter your balance to see an estimate.'}</p>
          )}
        </section>

        <section className="panel">
          <h2>Emergency fund</h2>
          {emergency.target === null ? (
            <>
              <p className="muted">{emergency.message}</p>
              <Link to="/emergency-fund" className="btn secondary small">Set it up</Link>
            </>
          ) : (
            <>
              <p>{emergency.message}</p>
              <ProgressBar percent={emergency.progress_percent} tone="safe" />
              <p className="muted small">{inr(emergency.remaining)} remaining</p>
            </>
          )}
        </section>
      </div>

      <EndOfDayCheck />

      <section className={`panel butler-card ${statusClass(health.status)}`}>
        <h2>AI Butler says</h2>
        <p>{data.butler_message}</p>
        <Link to="/butler" className="btn small">Ask the Butler a question</Link>
      </section>
    </>
  )
}