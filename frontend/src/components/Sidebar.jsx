import React from 'react'
import { Link, useLocation } from 'react-router-dom'

function Sidebar() {
  const location = useLocation()

  const menuItems = [
    { path: '/', label: 'Home', icon: '🏠' },
    { path: '/os-status', label: 'Node OS Status', icon: '💾' }
  ]

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <h2>LineageOS Flash</h2>
      </div>
      <nav className="sidebar-nav">
        {menuItems.map((item) => (
          <Link
            key={item.path}
            to={item.path}
            className={`nav-item ${location.pathname === item.path ? 'active' : ''}`}
          >
            <span className="nav-icon">{item.icon}</span>
            <span className="nav-label">{item.label}</span>
          </Link>
        ))}
      </nav>
    </div>
  )
}

export default Sidebar
