import { useState } from 'react'
import { Alert, Field, PageHeader } from '../components/ui.jsx'
import { api } from '../services/api.js'

const TONES = { Comfortable: 'safe', Manageable: 'watch', Risky: 'warning' }

export default function Emi() {
  const [form, setForm] = useState({
    new_emi: '', loan_months: '', existing_emi: '', monthly_income: '', fixed_expenses: '', current_savings: '',
  })
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)
  const set = (key) => (e) => setForm({ ...form, [key]: e.target.value })

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true)
    setError(null)
    setResult(null)
    const body = { new_emi: Number(form.new_emi), loan_months: Number(form.loan_months) }
    ;['existing_emi', 'monthly_income', 'fixed_expenses', 'current_savings'].forEach((k) => {
      if (form[k] !== '') body[k] = Number(form[k])
    })
    try {
      setResult(await api.emi.calculate(body))
    } catch (err) {
      setError(err)
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <PageHeader title="EMI affordability" subtitle="Leave the optional boxes empty to use the numbers already saved in your profile." />
      <section className="panel">
        <Alert error={error} />
        <form className="form-grid" onSubmit={submit}>
          <Field label="New EMI per month (₹) *"><input type="number" min="1" step="0.01" value={form.new_emi} onChange={set('new_emi')} required /></Field>
          <Field label="Loan duration (months) *"><input type="number" min="1" max="600" value={form.loan_months} onChange={set('loan_months')} required /></Field>
          <Field label="Existing EMIs per month (₹)"><input type="number" min="0" step="0.01" value={form.existing_emi} onChange={set('existing_emi')} /></Field>
          <Field label="Monthly income (₹)"><input type="number" min="1" step="0.01" value={form.monthly_income} onChange={set('monthly_income')} /></Field>
          <Field label="Monthly fixed expenses (₹)"><input type="number" min="0" step="0.01" value={form.fixed_expenses} onChange={set('fixed_expenses')} /></Field>
          <Field label="Current savings (₹)"><input type="number" min="0" step="0.01" value={form.current_savings} onChange={set('current_savings')} /></Field>
          <div className="span-2"><button className="btn" disabled={busy}>{busy ? 'Calculating…' : 'Check affordability'}</button></div>
        </form>
      </section>

      {result && (
        <section className="panel">
          <h2>Result</h2>
          <span className={`badge ${TONES[result.category] || 'critical'}`}>{result.category}</span>
          <h3>How I worked it out</h3>
          <ul className="plain">{result.explanation.map((line) => <li key={line}>{line}</li>)}</ul>
          <p className="small muted">Categories: {result.rules_used}</p>
          <p className="small muted">{result.disclaimer}</p>
        </section>
      )}
    </>
  )
}