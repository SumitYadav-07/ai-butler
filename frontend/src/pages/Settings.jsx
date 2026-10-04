import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import CrudList from '../components/CrudList.jsx'
import { Alert, Field, PageHeader, Spinner } from '../components/ui.jsx'
import { useAuth } from '../context/AuthContext.jsx'
import { useLoad } from '../hooks/useLoad.js'
import { api } from '../services/api.js'
import { EXPENSE_CATEGORIES, PRIVACY_TEXT } from '../utils/constants.js'
import { inr, numOrNull, todayISO } from '../utils/format.js'

function ProfileForm() {
  const { refreshUser } = useAuth()
  const { data, error, loading } = useLoad(() => api.profile.get(), [])
  const [form, setForm] = useState(null)
  const [formError, setFormError] = useState(null)
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    if (!data) return
    const show = (v) => (v === null || v === undefined ? '' : v)
    setForm({
      name: data.name,
      monthly_income: show(data.monthly_income),
      opening_balance: show(data.opening_balance),
      monthly_fixed_expenses: show(data.monthly_fixed_expenses),
      monthly_savings_target: show(data.monthly_savings_target),
      emergency_fund_target: show(data.emergency_fund_target),
      emergency_reserve: show(data.emergency_reserve),
    })
  }, [data])

  const set = (key) => (e) => setForm({ ...form, [key]: e.target.value })

  const submit = async (e) => {
    e.preventDefault()
    setFormError(null)
    setSaved(false)
    try {
      await api.profile.update({
        name: form.name.trim() || undefined,
        monthly_income: numOrNull(form.monthly_income),
        opening_balance: numOrNull(form.opening_balance),
        monthly_fixed_expenses: numOrNull(form.monthly_fixed_expenses),
        monthly_savings_target: numOrNull(form.monthly_savings_target),
        emergency_fund_target: numOrNull(form.emergency_fund_target),
        emergency_reserve: numOrNull(form.emergency_reserve),
      })
      await refreshUser()
      setSaved(true)
    } catch (err) {
      setFormError(err)
    }
  }

  if (loading || !form) return error ? <Alert error={error} /> : <Spinner />

  return (
    <section className="panel">
      <h2>Your financial profile</h2>
      <Alert error={formError} />
      {saved && <Alert kind="success">Profile saved.</Alert>}
      <form className="form-grid" onSubmit={submit}>
        <Field label="Name"><input value={form.name} onChange={set('name')} required /></Field>
        <Field label="Monthly income (₹)"><input type="number" min="0" step="0.01" value={form.monthly_income} onChange={set('monthly_income')} /></Field>
        <Field label="Starting balance (₹)" hint="Your balance before the first transaction you logged. Changing it changes your current balance.">
          <input type="number" min="0" step="0.01" value={form.opening_balance} onChange={set('opening_balance')} />
        </Field>
        <Field label="Monthly fixed expenses (₹)"><input type="number" min="0" step="0.01" value={form.monthly_fixed_expenses} onChange={set('monthly_fixed_expenses')} /></Field>
        <Field label="Monthly savings target (₹)"><input type="number" min="0" step="0.01" value={form.monthly_savings_target} onChange={set('monthly_savings_target')} /></Field>
        <Field label="Emergency fund target (₹)"><input type="number" min="0" step="0.01" value={form.emergency_fund_target} onChange={set('emergency_fund_target')} /></Field>
        <Field label="Emergency reserve to hold back (₹)" hint="Kept out of your safe daily spending.">
          <input type="number" min="0" step="0.01" value={form.emergency_reserve} onChange={set('emergency_reserve')} />
        </Field>
        <div className="span-2"><button className="btn">Save profile</button></div>
      </form>
    </section>
  )
}

export default function Settings() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  return (
    <>
      <PageHeader title="Settings" subtitle={`Signed in as ${user?.email}`} />
      <section className="panel privacy-panel">
        <h2>Privacy</h2>
        <p>{PRIVACY_TEXT}</p>
        <p className="muted small">
          This app never asks for bank usernames, passwords, OTPs, card details or UPI PINs, and it cannot make
          payments or transfers.
        </p>
      </section>

      <ProfileForm />

      <CrudList
        title="Recurring bills"
        help="Regular expenses with a due day. These feed the 'upcoming expenses' list and safe daily spending."
        path="recurring-expenses"
        fields={[
          { name: 'name', label: 'Name', required: true },
          { name: 'category', label: 'Category', options: EXPENSE_CATEGORIES, default: 'Bills' },
          { name: 'amount', label: 'Amount (₹)', type: 'number', min: 1, required: true },
          { name: 'due_day', label: 'Due day (1-31)', type: 'number', min: 1, max: 31, required: true },
        ]}
        describe={(i) => `${i.name} · ${inr(i.amount)} · due on day ${i.due_day}`}
      />

      <CrudList
        title="EMIs"
        help="Your existing EMIs. The EMI check and safe daily spending use these."
        path="emis"
        fields={[
          { name: 'name', label: 'Name', required: true },
          { name: 'monthly_amount', label: 'Monthly amount (₹)', type: 'number', min: 1, required: true },
          { name: 'due_day', label: 'Due day (1-31)', type: 'number', min: 1, max: 31, required: true },
          { name: 'remaining_months', label: 'Months remaining (optional)', type: 'number', min: 0 },
        ]}
        describe={(i) => `${i.name} · ${inr(i.monthly_amount)}/month · due on day ${i.due_day}${i.remaining_months != null ? ` · ${i.remaining_months} months left` : ''}`}
      />

      <CrudList
        title="Savings entries"
        help="Money you've set aside. The total appears on your dashboard."
        path="savings"
        fields={[
          { name: 'amount', label: 'Amount (₹)', type: 'number', min: 1, required: true },
          { name: 'saved_on', label: 'Date', type: 'date', default: todayISO(), required: true },
          { name: 'note', label: 'Note (optional)' },
        ]}
        describe={(i) => `${inr(i.amount)} on ${i.saved_on}${i.note ? ` · ${i.note}` : ''}`}
      />

      <section className="panel">
        <h2>Account</h2>
        <button className="btn secondary" onClick={async () => { await logout(); navigate('/login', { replace: true }) }}>
          Log out
        </button>
      </section>
    </>
  )
}