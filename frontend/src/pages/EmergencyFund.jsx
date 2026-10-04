import { useEffect, useState } from 'react'
import { Alert, Field, PageHeader, ProgressBar, Spinner } from '../components/ui.jsx'
import { useLoad } from '../hooks/useLoad.js'
import { api } from '../services/api.js'
import { inr, numOrNull } from '../utils/format.js'

export default function EmergencyFund() {
  const { data, error, loading, reload } = useLoad(() => api.emergency.get(), [])
  const [form, setForm] = useState({ current_amount: '', monthly_essential_expenses: '', target_months: '' })
  const [formError, setFormError] = useState(null)
  const [saved, setSaved] = useState(false)
  const set = (key) => (e) => setForm({ ...form, [key]: e.target.value })

  useEffect(() => {
    if (!data) return
    setForm({
      current_amount: data.current_amount ?? '',
      monthly_essential_expenses: data.monthly_essential_expenses ?? '',
      target_months: data.target_months ?? '',
    })
  }, [data])

  const submit = async (e) => {
    e.preventDefault()
    setFormError(null)
    setSaved(false)
    try {
      await api.emergency.update({
        current_amount: numOrNull(form.current_amount),
        monthly_essential_expenses: numOrNull(form.monthly_essential_expenses),
        target_months: numOrNull(form.target_months),
      })
      setSaved(true)
      reload()
    } catch (err) {
      setFormError(err)
    }
  }

  if (loading && !data) return <Spinner />

  return (
    <>
      <PageHeader title="Emergency fund" subtitle="Money set aside for the unexpected, based on your essential monthly costs." />
      <Alert error={error} />
      {data && (
        <section className="panel">
          <h2>Progress</h2>
          {data.target === null ? (
            <p className="muted">{data.message}</p>
          ) : (
            <>
              <ProgressBar percent={data.progress_percent} tone="safe" />
              <ul className="list">
                <li><span>Current emergency fund</span><strong>{inr(data.current_amount)}</strong></li>
                <li><span>Target ({data.target_source})</span><strong>{inr(data.target)}</strong></li>
                <li><span>Remaining</span><strong>{inr(data.remaining)}</strong></li>
                <li><span>Progress</span><strong>{data.progress_percent}%</strong></li>
              </ul>
            </>
          )}
        </section>
      )}

      <section className="panel">
        <h2>Update your numbers</h2>
        <Alert error={formError} />
        {saved && <Alert kind="success">Saved.</Alert>}
        <form className="form-grid" onSubmit={submit}>
          <Field label="Current emergency savings (₹)"><input type="number" min="0" step="0.01" value={form.current_amount} onChange={set('current_amount')} /></Field>
          <Field label="Monthly essential expenses (₹)"><input type="number" min="0" step="0.01" value={form.monthly_essential_expenses} onChange={set('monthly_essential_expenses')} /></Field>
          <Field label="Months to cover" hint="For example 6 months of essential expenses.">
            <input type="number" min="1" max="60" value={form.target_months} onChange={set('target_months')} />
          </Field>
          <div className="span-2"><button className="btn">Save</button></div>
        </form>
      </section>
    </>
  )
}