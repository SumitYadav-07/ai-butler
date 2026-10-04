import { useMemo, useState } from 'react'
import { useLoad } from '../hooks/useLoad.js'
import { api } from '../services/api.js'
import { Alert, Field, Spinner } from './ui.jsx'

/** Generic add/list/delete panel for recurring-expenses, emis and savings. */
export default function CrudList({ title, help, path, fields, describe }) {
  const resource = useMemo(() => api.recurring(path), [path])
  const { data, error, loading, reload } = useLoad(() => resource.list(), [resource])
  const blank = () => Object.fromEntries(fields.map((f) => [f.name, f.default ?? '']))
  const [form, setForm] = useState(blank)
  const [formError, setFormError] = useState(null)
  const [busy, setBusy] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true)
    setFormError(null)
    const body = {}
    fields.forEach((f) => {
      const v = form[f.name]
      if (v === '') return
      body[f.name] = f.type === 'number' ? Number(v) : v
    })
    try {
      await resource.create(body)
      setForm(blank())
      reload()
    } catch (err) {
      setFormError(err)
    } finally {
      setBusy(false)
    }
  }

  const remove = async (id) => {
    if (!window.confirm('Delete this item?')) return
    try {
      await resource.remove(id)
      reload()
    } catch (err) {
      setFormError(err)
    }
  }

  return (
    <section className="panel">
      <h2>{title}</h2>
      {help && <p className="muted small">{help}</p>}
      <Alert error={error || formError} />
      {loading && !data ? <Spinner /> : (
        <ul className="list">
          {(data || []).map((item) => (
            <li key={item.id}>
              <span>{describe(item)}</span>
              <button className="btn danger small" onClick={() => remove(item.id)}>Delete</button>
            </li>
          ))}
          {data?.length === 0 && <li className="muted">Nothing added yet.</li>}
        </ul>
      )}
      <form className="form-grid" onSubmit={submit}>
        {fields.map((f) => (
          <Field key={f.name} label={f.label}>
            {f.options ? (
              <select value={form[f.name]} onChange={(e) => setForm({ ...form, [f.name]: e.target.value })}>
                {f.options.map((o) => <option key={o}>{o}</option>)}
              </select>
            ) : (
              <input
                type={f.type || 'text'}
                min={f.min}
                max={f.max}
                step={f.type === 'number' ? '0.01' : undefined}
                required={f.required}
                value={form[f.name]}
                onChange={(e) => setForm({ ...form, [f.name]: e.target.value })}
              />
            )}
          </Field>
        ))}
        <div className="span-2"><button className="btn" disabled={busy}>{busy ? 'Adding…' : 'Add'}</button></div>
      </form>
    </section>
  )
}