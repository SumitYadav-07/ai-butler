import {
  Bar, BarChart, CartesianGrid, Cell, Legend, Line, LineChart, Pie, PieChart,
  ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts'
import { CHART_COLORS } from '../utils/constants.js'
import { fmtDate, inr } from '../utils/format.js'

const money = (v) => inr(v)
const Empty = ({ text }) => <p className="muted">{text}</p>

export function CategoryPie({ data }) {
  if (!data?.length) return <Empty text="No expenses to chart yet." />
  return (
    <div className="chart-box">
      <ResponsiveContainer width="100%" height={260}>
        <PieChart>
          <Pie data={data} dataKey="total" nameKey="category" innerRadius={55} outerRadius={95} paddingAngle={2}>
            {data.map((d, i) => <Cell key={d.category} fill={CHART_COLORS[i % CHART_COLORS.length]} />)}
          </Pie>
          <Tooltip formatter={money} />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </div>
  )
}

export function DailyLine({ data }) {
  if (!data?.some((d) => d.spent > 0)) return <Empty text="No daily spending in the last 30 days." />
  return (
    <div className="chart-box">
      <ResponsiveContainer width="100%" height={260}>
        <LineChart data={data} margin={{ left: 0, right: 12, top: 8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e4e7ee" />
          <XAxis dataKey="date" tickFormatter={fmtDate} minTickGap={24} fontSize={12} />
          <YAxis tickFormatter={(v) => `₹${v}`} fontSize={12} width={60} />
          <Tooltip formatter={money} labelFormatter={fmtDate} />
          <Line type="monotone" dataKey="spent" name="Spent" stroke="#3b5bdb" strokeWidth={2} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

export function WeeklyBars({ data }) {
  if (!data?.some((d) => d.spent > 0)) return <Empty text="No weekly spending to show yet." />
  return (
    <div className="chart-box">
      <ResponsiveContainer width="100%" height={240}>
        <BarChart data={data} margin={{ left: 0, right: 12, top: 8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e4e7ee" />
          <XAxis dataKey="week_start" tickFormatter={fmtDate} fontSize={12} />
          <YAxis tickFormatter={(v) => `₹${v}`} fontSize={12} width={60} />
          <Tooltip formatter={money} labelFormatter={(l) => `Week of ${fmtDate(l)}`} />
          <Bar dataKey="spent" name="Spent" fill="#3b5bdb" radius={[6, 6, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

export function MonthlyBars({ data }) {
  if (!data?.some((d) => d.spent > 0 || d.income > 0)) return <Empty text="No monthly data to show yet." />
  return (
    <div className="chart-box">
      <ResponsiveContainer width="100%" height={240}>
        <BarChart data={data} margin={{ left: 0, right: 12, top: 8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e4e7ee" />
          <XAxis dataKey="month" fontSize={12} />
          <YAxis tickFormatter={(v) => `₹${v}`} fontSize={12} width={60} />
          <Tooltip formatter={money} />
          <Legend />
          <Bar dataKey="income" name="Income logged" fill="#12b886" radius={[6, 6, 0, 0]} />
          <Bar dataKey="spent" name="Spent" fill="#3b5bdb" radius={[6, 6, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}