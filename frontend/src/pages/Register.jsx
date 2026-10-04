import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Alert, Field } from '../components/ui.jsx'
import { useAuth } from '../context/AuthContext.jsx'
import { PRIVACY_TEXT } from '../utils/constants.js'

export default function Register() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ name: '', email: '', password: '', confirm: '' })
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)
  const set = (key) => (e) => setForm({ ...form, [key]: e.target.value })

  const submit = async (e) => {
    e.preventDefault()
    setError(null)
    if (form.password !== form.confirm) {
      setError({ message: 'The two passwords do not match.' })
      return
    }
    setBusy(true)
    try {
      await register(form.name, form.email, form.password)
      navigate('/dashboard', { replace: true })
    } catch (err) {
      setError(err)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="auth-page">
      <form className="auth-card" onSubmit={submit}>
        <h1>Create your account</h1>
        <Alert error={error} />
        <Field label="Name"><input value={form.name} onChange={set('name')} required /></Field>
        <Field label="Email"><input type="email" autoComplete="email" value={form.email} onChange={set('email')} required /></Field>
        <Field label="Password" hint="At least 8 characters.">
          <input type="password" autoComplete="new-password" minLength={8} value={form.password} onChange={set('password')} required />
        </Field>
        <Field label="Confirm password">
          <input type="password" autoComplete="new-password" value={form.confirm} onChange={set('confirm')} required />
        </Field>
        <button className="btn" disabled={busy}>{busy ? 'Creating…' : 'Register'}</button>
        <p className="small">Already registered? <Link to="/login">Log in</Link></p>
        <p className="privacy-note">🔒 {PRIVACY_TEXT} We never ask for banking credentials.</p>
      </form>
    </div>
  )
}