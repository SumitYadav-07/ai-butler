import { Navigate, Route, Routes } from 'react-router-dom'
import Layout from './components/Layout.jsx'
import ProtectedRoute from './components/ProtectedRoute.jsx'
import { Spinner } from './components/ui.jsx'
import { useAuth } from './context/AuthContext.jsx'
import Analytics from './pages/Analytics.jsx'
import Butler from './pages/Butler.jsx'
import Dashboard from './pages/Dashboard.jsx'
import EmergencyFund from './pages/EmergencyFund.jsx'
import Emi from './pages/Emi.jsx'
import Goals from './pages/Goals.jsx'
import Login from './pages/Login.jsx'
import Register from './pages/Register.jsx'
import Settings from './pages/Settings.jsx'
import Transactions from './pages/Transactions.jsx'

function PublicOnly({ children }) {
  const { user, loading } = useAuth()
  if (loading) return <Spinner />
  return user ? <Navigate to="/dashboard" replace /> : children
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<PublicOnly><Login /></PublicOnly>} />
      <Route path="/register" element={<PublicOnly><Register /></PublicOnly>} />
      <Route element={<ProtectedRoute><Layout /></ProtectedRoute>}>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/transactions" element={<Transactions />} />
        <Route path="/analytics" element={<Analytics />} />
        <Route path="/emi" element={<Emi />} />
        <Route path="/goals" element={<Goals />} />
        <Route path="/emergency-fund" element={<EmergencyFund />} />
        <Route path="/butler" element={<Butler />} />
        <Route path="/settings" element={<Settings />} />
      </Route>
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  )
}