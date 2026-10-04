import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Alert, Field, PageHeader, Spinner } from '../components/ui.jsx'
import { useLoad } from '../hooks/useLoad.js'
import { api } from '../services/api.js'
import { EXPENSE_CATEGORIES, INCOME_CATEGORIES, PAYMENT_METHODS } from '../utils/constants.js'
import { fmtDate, inr, todayISO } from '../utils/format.js'

const PAGE_SIZE = 15

export default function Transactions() {
  const [params] = useSearchParams()
  const startType = params.get('type') === 'income' ? 'income' : 'expense'
  const [form, setForm] = useState({
    type: startType,
    amount: params.get('amount') || '',
    category: startType === 'income' ? INCOME_CATEGORIES[0] : EXPENSE_CATEGORIES[0],
    description: '',
    txn_date: todayISO(),
    payment_method: '',
  })
  const [formError, setFormError] = useState(null)
  const [notice, setNotice] = useState(null)
  const [busy, setBusy] = useState(false)
  const [filters, setFilters] = useState({ type: '', category: '' })
  const [page, setPage] = useState(0)

  const { data, error, loading, reload } = useLoad(
    () => api.transactions.list({ ...filters, limit: PAGE_SIZE, offset: page * PAGE_SIZE }),
    [filters.type, filters.category, page],
  )

  const categories = form.type === 'income' ? INCOME_CATEGORIES : EXPENSE_CATEGORIES
  const setType = (type) =>
    setForm((f) => ({ ...f, type, category: type === 'income' ? INCOME_CATEGORIES[0] : EXPENSE_CATEGORIES[0] }))

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true)
    setFormError(null)
    setNotice(null)
    try {
      const res = await api.transactions.create({
        type: form.type,
        amount: Number(form.amount),
        category: form.category,
        description: form.description,
        txn_date: form.txn_date,
        payment_method: form.payment_method || null,
      })
      setNotice({
        kind: res.warning ? 'warn' : 'success',
        text: res.warning || `Saved. Your balance is now ${inr(res.balance)}.`,
      })
      setForm((f) => ({ ...f, amount: '', description: '' }))
      if (page === 0) reload()
      else setPage(0)
    } catch (err) {
      setFormError(err)
    } finally {
      setBusy(false)
    }
  }

  const remove = async (id) => {
    if (!window.confirm('Delete this transaction? Your balance will update.')) return
    try {
      await api.transactions.remove(id)
      reload()
    } catch (err) {
      setFormError(err)
    }
  }

  const totalPages = data ? Math.max(1, Math.ceil(data.total / PAGE_SIZE)) : 1

  return (
    <>
      <PageHeader title="Transactions" subtitle="Everything here is typed in by you. Your balance is updated from these entries." />

      <section className="panel">
        <h2>Add a transaction</h2>
        <Alert error={formError} />
        {notice && <Alert kind={notice.kind === 'warn' ? 'warn' : 'success'}>{notice.text}</Alert>}
        <form className="form-grid" onSubmit={submit}>
          <div className="span-2 toggle">
            <button type="button" className={form.type === 'expense' ? 'active' : ''} onClick={() => setType('expense')}>Expense</button>
            <button type="button" className={form.type === 'income' ? 'active' : ''} onClick={() => setType('income')}>Income</button>
          </div>
          <Field label="Amount (₹)">
            <input type="number" min="0.01" step="0.01" value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} required />
          </Field>
          <Field label="Category">
            <select value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })}>
              {categories.map((c) => <option key={c}>{c}</option>)}
            </select>
          </Field>
          <Field label="Description">
            <input value={form.description} maxLength={255} placeholder="e.g. Lunch" onChange={(e) => setForm({ ...form, description: e.target.value })} />
          </Field>
          <Field label="Date">
            <input type="date" max={todayISO()} value={form.txn_date} onChange={(e) => setForm({ ...form, txn_date: e.target.value })} required />
          </Field>
          <Field label="Payment method (optional)">
            <select value={form.payment_method} onChange={(e) => setForm({ ...form, payment_method: e.target.value })}>
              <option value="">Not specified</option>
              {PAYMENT_METHODS.map((m) => <option key={m}>{m}</option>)}
            </select>
          </Field>
          <div className="span-2"><button className="btn" disabled={busy}>{busy ? 'Saving…' : 'Add transaction'}</button></div>
        </form>
      </section>

      <section className="panel">
        <h2>History</h2>
        <div className="inline-form wrap">
          <select value={filters.type} onChange={(e) => { setFilters({ type: e.target.value, category: '' }); setPage(0) }}>
            <option value="">All types</option>
            <option value="expense">Expenses</option>
            <option value="income">Income</option>
          </select>
          <select value={filters.category} onChange={(e) => { setFilters({ ...filters, category: e.target.value }); setPage(0) }}>
            <option value="">All categories</option>
            {[...EXPENSE_CATEGORIES, ...INCOME_CATEGORIES].map((c) => <option key={c}>{c}</option>)}
          </select>
        </div>
        <Alert error={error} />
        {loading && !data ? <Spinner /> : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr><th>Date</th><th>Category</th><th>Description</th><th>Method</th><th className="right">Amount</th><th /></tr>
              </thead>
              <tbody>
                {data?.items.map((t) => (
                  <tr key={t.id}>
                    <td>{fmtDate(t.txn_date)}</td>
                    <td>{t.category}</td>
                    <td>{t.description || '—'}</td>
                    <td>{t.payment_method || '—'}</td>
                    <td className={`right ${t.type === 'income' ? 'pos' : 'neg'}`}>{t.type === 'income' ? '+' : '−'}{inr(t.amount)}</td>
                    <td className="right"><button className="btn danger small" onClick={() => remove(t.id)}>Delete</button></td>
                  </tr>
                ))}
                {data?.items.length === 0 && <tr><td colSpan="6" className="muted">No transactions match yet.</td></tr>}
              </tbody>
            </table>
          </div>
        )}
        <div className="pager">
          <button className="btn secondary small" disabled={page === 0} onClick={() => setPage(page - 1)}>Previous</button>
          <span className="muted small">Page {page + 1} of {totalPages}</span>
          <button className="btn secondary small" disabled={page + 1 >= totalPages} onClick={() => setPage(page + 1)}>Next</button>
        </div>
      </section>
    </>
  )
}