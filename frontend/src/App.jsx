import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import Devices from './pages/Devices'
import OsStatus from './pages/OsStatus'

function App() {
  return (
    <Router>
      <div className="app">
        <Sidebar />
        <div className="main-content">
          <Routes>
            <Route path="/" element={<Devices />} />
            <Route path="/os-status" element={<OsStatus />} />
          </Routes>
        </div>
      </div>
    </Router>
  )
}

export default App
