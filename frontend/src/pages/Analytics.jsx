import { CategoryPie, DailyLine, MonthlyBars, WeeklyBars } from '../components/Charts.jsx'
import { Alert, PageHeader, Spinner } from '../components/ui.jsx'
import { useLoad } from '../hooks/useLoad.js'
import { api } from '../services/api.js'
import { inr } from '../utils/format.js'

export default function Analytics() {
  const { data, error, loading } = useLoad(() => api.analytics(), [])
  if (loading && !data) return <Spinner />
  if (error) return <Alert error={error} />

  const cmp = data.comparison
  return (
    <>
      <PageHeader title="Spending analytics" subtitle="Based only on the transactions you've entered." />

      <section className="panel">
        <h2>What stands out</h2>
        <ul className="plain">{data.insights.map((line) => <li key={line}>{line}</li>)}</ul>
      </section>

      <div className="grid two">
        <section className="panel">
          <h2>This month by category</h2>
          <CategoryPie data={data.category_breakdown} />
          {data.highest_category && (
            <p className="small">Highest: <strong>{data.highest_category.category}</strong> ({inr(data.highest_category.total)})</p>
          )}
        </section>
        <section className="panel">
          <h2>Daily spending (last 30 days)</h2>
          <DailyLine data={data.daily} />
        </section>
      </div>

      <div className="grid two">
        <section className="panel">
          <h2>Weekly spending</h2>
          <WeeklyBars data={data.weekly} />
        </section>
        <section className="panel">
          <h2>Monthly: income vs spending</h2>
          <MonthlyBars data={data.monthly} />
        </section>
      </div>

      <section className="panel">
        <h2>Compared with the same point last month</h2>
        {!cmp.has_previous_data && <p className="muted">There are no entries from last month yet, so there's nothing to compare.</p>}
        <div className="table-wrap">
          <table>
            <thead><tr><th>Category</th><th className="right">This month</th><th className="right">Last month</th><th className="right">Change</th></tr></thead>
            <tbody>
              {cmp.rows.map((r) => (
                <tr key={r.category}>
                  <td>{r.category}</td>
                  <td className="right">{inr(r.this_month)}</td>
                  <td className="right">{inr(r.last_month)}</td>
                  <td className={`right ${r.change > 0 ? 'neg' : r.change < 0 ? 'pos' : ''}`}>{r.change > 0 ? '+' : ''}{inr(r.change)}</td>
                </tr>
              ))}
              <tr className="total">
                <td>Total</td>
                <td className="right">{inr(cmp.this_month_total)}</td>
                <td className="right">{inr(cmp.last_month_total)}</td>
                <td className="right">{inr(cmp.this_month_total - cmp.last_month_total)}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </>
  )
}