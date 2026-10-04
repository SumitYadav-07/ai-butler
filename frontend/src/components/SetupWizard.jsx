import { useState } from 'react'
import { useAuth } from '../context/AuthContext.jsx'
import { api } from '../services/api.js'
import { numOrNull } from '../utils/format.js'
import { PRIVACY_TEXT } from '../utils/constants.js'
import { Alert, Field } from './ui.jsx'

export default function SetupWizard({ initialName, onDone }) {
  const { refreshUser } = useAuth()
  const [form, setForm] = useState({
    name: initialName || '',
    monthly_income: '',
    opening_balance: '',
    monthly_fixed_expenses: '',
    emi_amount: '',
    emi_due_day: '1',
    monthly_savings_target: '',
    emergency_fund_target: '',
    goal_name: '',
    goal_target: '',
    goal_date: '',
  })
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)
  const set = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }))

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      await api.profile.update({
        name: form.name.trim() || undefined,
        monthly_income: numOrNull(form.monthly_income),
        opening_balance: numOrNull(form.opening_balance),
        monthly_fixed_expenses: numOrNull(form.monthly_fixed_expenses),
        monthly_savings_target: numOrNull(form.monthly_savings_target),
        emergency_fund_target: numOrNull(form.emergency_fund_target),
      })
      if (Number(form.emi_amount) > 0) {
        await api.recurring('emis').create({
          name: 'Existing EMI',
          monthly_amount: Number(form.emi_amount),
          due_day: Number(form.emi_due_day) || 1,
        })
      }
      if (form.goal_name.trim() && form.goal_target && form.goal_date) {
        await api.goals.create({
          name: form.goal_name.trim(),
          target_amount: Number(form.goal_target),
          saved_amount: 0,
          target_date: form.goal_date,
        })
      }
      await refreshUser()
      onDone()
    } catch (err) {
      setError(err)
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="panel wizard">
      <h1>Welcome! Let's set up your profile</h1>
      <p className="muted">{PRIVACY_TEXT} Everything below is typed in by you, and you can change it later in Settings.</p>
      <Alert error={error} />
      <form onSubmit={submit} className="form-grid">
        <Field label="Your name"><input value={form.name} onChange={set('name')} required /></Field>
        <Field label="Monthly income (₹) *"><input type="number" min="0" step="0.01" value={form.monthly_income} onChange={set('monthly_income')} required /></Field>
        <Field label="Current balance (₹) *" hint="How much money you have right now.">
          <input type="number" min="0" step="0.01" value={form.opening_balance} onChange={set('opening_balance')} required />
        </Field>
        <Field label="Monthly fixed expenses (₹)" hint="Rent, bills and other regular costs, not counting EMIs.">
          <input type="number" min="0" step="0.01" value={form.monthly_fixed_expenses} onChange={set('monthly_fixed_expenses')} />
        </Field>
        <Field label="Existing EMI per month (₹)" hint="Leave blank if you have none.">
          <input type="number" min="0" step="0.01" value={form.emi_amount} onChange={set('emi_amount')} />
        </Field>
        <Field label="EMI due day of month">
          <input type="number" min="1" max="31" value={form.emi_due_day} onChange={set('emi_due_day')} />
        </Field>
        <Field label="Monthly savings target (₹)"><input type="number" min="0" step="0.01" value={form.monthly_savings_target} onChange={set('monthly_savings_target')} /></Field>
        <Field label="Emergency fund target (₹)"><input type="number" min="0" step="0.01" value={form.emergency_fund_target} onChange={set('emergency_fund_target')} /></Field>

        <h3 className="span-2">Optional: one financial goal</h3>
        <Field label="Goal name"><input value={form.goal_name} onChange={set('goal_name')} placeholder="e.g. New laptop" /></Field>
        <Field label="Target amount (₹)"><input type="number" min="1" step="0.01" value={form.goal_target} onChange={set('goal_target')} /></Field>
        <Field label="Target date"><input type="date" value={form.goal_date} onChange={set('goal_date')} /></Field>

        <div className="span-2">
          <button className="btn" disabled={busy}>{busy ? 'Saving…' : 'Create my profile'}</button>
        </div>
      </form>
    </section>
  )
}