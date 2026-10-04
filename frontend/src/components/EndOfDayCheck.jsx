import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useLoad } from '../hooks/useLoad.js'
import { api } from '../services/api.js'
import { inr } from '../utils/format.js'
import { Alert } from './ui.jsx'

export default function EndOfDayCheck() {
  const { data, loading } = useLoad(() => api.dailyBalance.prompt(), [])
  const [value, setValue] = useState('')
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      setResult(await api.dailyBalance.submit({ reported_balance: Number(value) }))
    } catch (err) {
      setError(err)
    } finally {
      setBusy(false)
    }
  }

  if (loading) return null
  const hint = result?.possible_missing_transaction

  return (
    <section className="panel">
      <h2>End-of-day check</h2>
      <p className="butler-q">“{data?.question}”</p>
      {data?.already_submitted && !result && (
        <p className="muted small">You reported {inr(data.reported_balance)} today. You can submit again to update it.</p>
      )}
      <form className="inline-form" onSubmit={submit}>
        <input type="number" min="0" step="0.01" placeholder="Money left today (₹)" value={value} onChange={(e) => setValue(e.target.value)} required />
        <button className="btn" disabled={busy}>{busy ? 'Checking…' : 'Check'}</button>
      </form>
      <Alert error={error} />
      {result && (
        <div className={`alert ${result.matches ? 'success' : 'warn'}`}>
          <p>{result.message}</p>
          {hint && (
            <>
              <p className="small">{hint.note}</p>
              <Link className="btn secondary small" to={`/transactions?type=${hint.type}&amount=${hint.amount}`}>
                Add a missing transaction
              </Link>
            </>
          )}
          {result.transactions_for_day.length > 0 && (
            <ul className="small">
              {result.transactions_for_day.map((t) => (
                <li key={t.id}>
                  {t.type === 'income' ? '+' : '−'}{inr(t.amount)} · {t.category}{t.description ? ` · ${t.description}` : ''}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </section>
  )
}