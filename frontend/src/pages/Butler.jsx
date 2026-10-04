import { useEffect, useRef, useState } from 'react'
import { Alert, PageHeader } from '../components/ui.jsx'
import { api } from '../services/api.js'
import { SUGGESTED_QUESTIONS } from '../utils/constants.js'

function RichText({ text }) {
  return text.split(/(\*\*[^*]+\*\*)/g).map((part, i) =>
    part.startsWith('**') && part.endsWith('**')
      ? <strong key={i}>{part.slice(2, -2)}</strong>
      : <span key={i}>{part}</span>,
  )
}

export default function Butler() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const [error, setError] = useState(null)
  const endRef = useRef(null)

  useEffect(() => {
    api.butler
      .history()
      .then((rows) => setMessages(rows.map((r) => ({ role: r.role, text: r.message }))))
      .catch(setError)
  }, [])

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, sending])

  const send = async (text) => {
    const question = text.trim()
    if (!question || sending) return
    setError(null)
    setInput('')
    setMessages((m) => [...m, { role: 'user', text: question }])
    setSending(true)
    try {
      const res = await api.butler.chat(question)
      setMessages((m) => [...m, { role: 'assistant', text: res.reply, notice: res.notice }])
    } catch (err) {
      setError(err)
    } finally {
      setSending(false)
    }
  }

  const clear = async () => {
    if (!window.confirm('Clear your chat history?')) return
    try {
      await api.butler.clear()
      setMessages([])
    } catch (err) {
      setError(err)
    }
  }

  return (
    <>
      <PageHeader title="AI Butler" subtitle="Ask about your money. I only use the numbers you've entered in this app." />
      <section className="panel chat">
        <div className="chat-log">
          {messages.length === 0 && (
            <div className="bubble assistant">
              Hi! I can help you understand your spending, safe daily amount, EMIs and savings. I analyse and explain,
              but I never move money, and I'm not a financial advisor. Try one of the questions below.
            </div>
          )}
          {messages.map((m, i) => (
            <div key={i} className={`bubble ${m.role}`}>
              <RichText text={m.text} />
              {m.notice && <div className="muted small">{m.notice}</div>}
            </div>
          ))}
          {sending && <div className="bubble assistant typing">Thinking…</div>}
          <div ref={endRef} />
        </div>

        <Alert error={error} />

        <div className="chips">
          {SUGGESTED_QUESTIONS.map((q) => (
            <button key={q} className="chip" onClick={() => send(q)} disabled={sending}>{q}</button>
          ))}
        </div>

        <form className="inline-form" onSubmit={(e) => { e.preventDefault(); send(input) }}>
          <input value={input} maxLength={500} placeholder="Ask the Butler…" onChange={(e) => setInput(e.target.value)} />
          <button className="btn" disabled={sending || !input.trim()}>Send</button>
        </form>
        <div className="row-between">
          <span className="muted small">Please don't type PINs, OTPs or passwords here. I never need them.</span>
          <button className="btn secondary small" onClick={clear}>Clear chat</button>
        </div>
      </section>
    </>
  )
}