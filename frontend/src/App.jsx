import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import Devices from './pages/Devices'
import OsStatus from './pages/OsStatus'
import RegisteredNodes from './pages/RegisteredNodes'
import AdminCentre from './pages/AdminCentre'
import SystemLogs from './pages/SystemLogs'

function App() {
  return (
    <Router>
      <div className="app">
        <Sidebar />
        <div className="main-content">
          <Routes>
            <Route path="/" element={<Devices />} />
            <Route path="/os-status" element={<OsStatus />} />
            <Route path="/registered-nodes" element={<RegisteredNodes />} />
            <Route path="/admin-centre" element={<AdminCentre />} />
            <Route path="/system-logs" element={<SystemLogs />} />
          </Routes>
        </div>
      </div>
    </Router>
  )
}

export default App
