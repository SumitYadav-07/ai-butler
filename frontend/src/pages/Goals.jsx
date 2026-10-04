import { useState } from 'react'
import { Alert, Field, PageHeader, ProgressBar, Spinner } from '../components/ui.jsx'
import { useLoad } from '../hooks/useLoad.js'
import { api } from '../services/api.js'
import { inr, todayISO } from '../utils/format.js'

function GoalCard({ goal, onChanged }) {
  const [extra, setExtra] = useState('')
  const [error, setError] = useState(null)

  const addSaved = async (e) => {
    e.preventDefault()
    setError(null)
    try {
      await api.goals.update(goal.id, {
        name: goal.name,
        target_amount: goal.target_amount,
        saved_amount: goal.saved_amount + Number(extra),
        target_date: goal.target_date,
      })
      setExtra('')
      onChanged()
    } catch (err) {
      setError(err)
    }
  }

  const remove = async () => {
    if (!window.confirm(`Delete the goal "${goal.name}"?`)) return
    try {
      await api.goals.remove(goal.id)
      onChanged()
    } catch (err) {
      setError(err)
    }
  }

  return (
    <section className="panel">
      <div className="row-between">
        <h2>{goal.name}</h2>
        <button className="btn danger small" onClick={remove}>Delete</button>
      </div>
      <ProgressBar percent={goal.progress_percent} tone="safe" />
      <p>{inr(goal.saved_amount)} of {inr(goal.target_amount)} ({goal.progress_percent}%)</p>
      <ul className="list">
        <li><span>Remaining</span><strong>{inr(goal.remaining)}</strong></li>
        <li><span>Target date</span><strong>{goal.target_date}</strong></li>
        <li><span>Suggested monthly saving</span><strong>{inr(goal.suggested_monthly_saving)}</strong></li>
      </ul>
      {goal.note && <p className="muted small">{goal.note}</p>}
      <Alert error={error} />
      <form className="inline-form" onSubmit={addSaved}>
        <input type="number" min="1" step="0.01" placeholder="Add to saved (₹)" value={extra} onChange={(e) => setExtra(e.target.value)} required />
        <button className="btn secondary small">Add</button>
      </form>
    </section>
  )
}

export default function Goals() {
  const { data, error, loading, reload } = useLoad(() => api.goals.list(), [])
  const [form, setForm] = useState({ name: '', target_amount: '', saved_amount: '', target_date: '' })
  const [formError, setFormError] = useState(null)
  const [busy, setBusy] = useState(false)
  const set = (key) => (e) => setForm({ ...form, [key]: e.target.value })

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true)
    setFormError(null)
    try {
      await api.goals.create({
        name: form.name.trim(),
        target_amount: Number(form.target_amount),
        saved_amount: form.saved_amount === '' ? 0 : Number(form.saved_amount),
        target_date: form.target_date,
      })
      setForm({ name: '', target_amount: '', saved_amount: '', target_date: '' })
      reload()
    } catch (err) {
      setFormError(err)
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <PageHeader title="Financial goals" subtitle="Track what you're saving for. The monthly suggestion is a simple calculation, not a promise." />
      <section className="panel">
        <h2>New goal</h2>
        <Alert error={formError} />
        <form className="form-grid" onSubmit={submit}>
          <Field label="Goal name"><input value={form.name} onChange={set('name')} placeholder="e.g. Bike, vacation, college fees" required /></Field>
          <Field label="Target amount (₹)"><input type="number" min="1" step="0.01" value={form.target_amount} onChange={set('target_amount')} required /></Field>
          <Field label="Already saved (₹)"><input type="number" min="0" step="0.01" value={form.saved_amount} onChange={set('saved_amount')} /></Field>
          <Field label="Target date"><input type="date" min={todayISO()} value={form.target_date} onChange={set('target_date')} required /></Field>
          <div className="span-2"><button className="btn" disabled={busy}>{busy ? 'Saving…' : 'Create goal'}</button></div>
        </form>
      </section>

      <Alert error={error} />
      {loading && !data ? <Spinner /> : (
        <div className="grid two">
          {data?.map((g) => <GoalCard key={g.id} goal={g} onChanged={reload} />)}
          {data?.length === 0 && <p className="muted">No goals yet. Create your first one above.</p>}
        </div>
      )}
    </>
  )
}