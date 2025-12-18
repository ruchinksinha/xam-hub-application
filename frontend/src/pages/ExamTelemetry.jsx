import React, { useState, useEffect } from 'react'

function ExamTelemetry() {
  const [stats, setStats] = useState(null)
  const [sessions, setSessions] = useState([])
  const [selectedSession, setSelectedSession] = useState(null)
  const [sessionDetails, setSessionDetails] = useState(null)
  const [selectedDevice, setSelectedDevice] = useState(null)
  const [deviceTelemetry, setDeviceTelemetry] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [viewMode, setViewMode] = useState('session')
  const [allDevices, setAllDevices] = useState([])
  const [filterDevice, setFilterDevice] = useState('')
  const [deviceSessions, setDeviceSessions] = useState([])
  const [filterSession, setFilterSession] = useState('')

  useEffect(() => {
    fetchStats()
    fetchSessions()
    fetchAllDevices()
  }, [])

  const fetchStats = async () => {
    try {
      const response = await fetch('http://localhost/api/telemetry/stats')
      const data = await response.json()
      setStats(data)
    } catch (err) {
      console.error('Error fetching stats:', err)
    }
  }

  const fetchSessions = async () => {
    try {
      setLoading(true)
      const response = await fetch('http://localhost/api/telemetry/sessions')
      const data = await response.json()
      setSessions(data.sessions || [])
    } catch (err) {
      setError('Failed to load exam sessions')
    } finally {
      setLoading(false)
    }
  }

  const fetchAllDevices = async () => {
    try {
      const response = await fetch('http://localhost/api/telemetry/devices')
      const data = await response.json()
      setAllDevices(data.devices || [])
    } catch (err) {
      console.error('Failed to load devices:', err)
    }
  }

  const handleFilterDeviceChange = async (deviceId) => {
    setFilterDevice(deviceId)
    setFilterSession('')
    setDeviceSessions([])
    setDeviceTelemetry(null)

    if (!deviceId) return

    try {
      const response = await fetch(`http://localhost/api/telemetry/device/${deviceId}/sessions`)
      const data = await response.json()
      setDeviceSessions(data.sessions || [])
    } catch (err) {
      console.error('Failed to load device sessions:', err)
    }
  }

  const handleFilterSessionChange = async (sessionKey) => {
    setFilterSession(sessionKey)
    setDeviceTelemetry(null)

    if (!sessionKey || !filterDevice) return

    const [examId, sessionId] = sessionKey.split('/')

    try {
      setLoading(true)
      const response = await fetch(
        `http://localhost/api/telemetry/device/${examId}/${sessionId}/${filterDevice}`
      )
      const data = await response.json()
      setDeviceTelemetry(data)
    } catch (err) {
      setError('Failed to load device telemetry')
    } finally {
      setLoading(false)
    }
  }

  const handleSessionClick = async (session) => {
    try {
      setLoading(true)
      setSelectedSession(session)
      setSelectedDevice(null)
      setDeviceTelemetry(null)

      const response = await fetch(
        `http://localhost/api/telemetry/session/${session.examId}/${session.sessionId}`
      )
      const data = await response.json()
      setSessionDetails(data)
    } catch (err) {
      setError('Failed to load session details')
    } finally {
      setLoading(false)
    }
  }

  const handleDeviceClick = async (device) => {
    try {
      setLoading(true)
      setSelectedDevice(device)

      const response = await fetch(
        `http://localhost/api/telemetry/device/${selectedSession.examId}/${selectedSession.sessionId}/${device.deviceId}`
      )
      const data = await response.json()
      setDeviceTelemetry(data)
    } catch (err) {
      setError('Failed to load device telemetry')
    } finally {
      setLoading(false)
    }
  }

  const goBack = () => {
    if (selectedDevice) {
      setSelectedDevice(null)
      setDeviceTelemetry(null)
    } else if (selectedSession) {
      setSelectedSession(null)
      setSessionDetails(null)
    }
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>Exam Telemetry Dashboard</h1>
        <p>Track exam sessions and device activity</p>
      </div>

      {stats && (
        <div className="stats-grid">
          <div className="stat-card">
            <h3>Total Exams</h3>
            <div className="stat-value">{stats.totalExams}</div>
          </div>
          <div className="stat-card">
            <h3>Total Sessions</h3>
            <div className="stat-value">{stats.totalSessions}</div>
          </div>
          <div className="stat-card">
            <h3>Total Devices</h3>
            <div className="stat-value">{stats.totalDevices}</div>
          </div>
          <div className="stat-card">
            <h3>Data Files</h3>
            <div className="stat-value">
              {Object.values(stats.dataTypes).reduce((sum, val) => sum + val, 0)}
            </div>
          </div>
        </div>
      )}

      <div style={{
        display: 'flex',
        gap: '12px',
        marginBottom: '24px',
        alignItems: 'center',
        background: 'white',
        padding: '16px',
        borderRadius: '8px',
        border: '1px solid #e5e7eb'
      }}>
        <label style={{ fontWeight: '600', marginRight: '8px' }}>View Mode:</label>
        <button
          onClick={() => {
            setViewMode('session')
            setFilterDevice('')
            setFilterSession('')
            setDeviceTelemetry(null)
          }}
          style={{
            padding: '8px 16px',
            borderRadius: '6px',
            border: viewMode === 'session' ? '2px solid #3b82f6' : '1px solid #d1d5db',
            background: viewMode === 'session' ? '#eff6ff' : 'white',
            color: viewMode === 'session' ? '#3b82f6' : '#6b7280',
            fontWeight: viewMode === 'session' ? '600' : '400',
            cursor: 'pointer'
          }}
        >
          Session View
        </button>
        <button
          onClick={() => {
            setViewMode('filter')
            setSelectedSession(null)
            setSessionDetails(null)
            setSelectedDevice(null)
          }}
          style={{
            padding: '8px 16px',
            borderRadius: '6px',
            border: viewMode === 'filter' ? '2px solid #3b82f6' : '1px solid #d1d5db',
            background: viewMode === 'filter' ? '#eff6ff' : 'white',
            color: viewMode === 'filter' ? '#3b82f6' : '#6b7280',
            fontWeight: viewMode === 'filter' ? '600' : '400',
            cursor: 'pointer'
          }}
        >
          Device Filter
        </button>
      </div>

      {viewMode === 'filter' && (
        <div style={{
          background: 'white',
          padding: '20px',
          borderRadius: '8px',
          border: '1px solid #e5e7eb',
          marginBottom: '24px'
        }}>
          <h3 style={{ marginBottom: '16px', fontSize: '16px', fontWeight: '600' }}>
            Filter by Device and Session
          </h3>
          <div style={{ display: 'flex', gap: '16px', alignItems: 'flex-end' }}>
            <div style={{ flex: 1 }}>
              <label style={{
                display: 'block',
                marginBottom: '8px',
                fontSize: '14px',
                fontWeight: '500',
                color: '#374151'
              }}>
                Select Device
              </label>
              <select
                value={filterDevice}
                onChange={(e) => handleFilterDeviceChange(e.target.value)}
                style={{
                  width: '100%',
                  padding: '10px 12px',
                  borderRadius: '6px',
                  border: '1px solid #d1d5db',
                  fontSize: '14px'
                }}
              >
                <option value="">-- Select Device --</option>
                {allDevices.map((device) => (
                  <option key={device.deviceId} value={device.deviceId}>
                    {device.deviceId} ({device.sessionCount} sessions)
                  </option>
                ))}
              </select>
            </div>
            <div style={{ flex: 1 }}>
              <label style={{
                display: 'block',
                marginBottom: '8px',
                fontSize: '14px',
                fontWeight: '500',
                color: '#374151'
              }}>
                Select Session
              </label>
              <select
                value={filterSession}
                onChange={(e) => handleFilterSessionChange(e.target.value)}
                disabled={!filterDevice || deviceSessions.length === 0}
                style={{
                  width: '100%',
                  padding: '10px 12px',
                  borderRadius: '6px',
                  border: '1px solid #d1d5db',
                  fontSize: '14px',
                  opacity: !filterDevice || deviceSessions.length === 0 ? 0.5 : 1,
                  cursor: !filterDevice || deviceSessions.length === 0 ? 'not-allowed' : 'pointer'
                }}
              >
                <option value="">-- Select Session --</option>
                {deviceSessions.map((session) => (
                  <option
                    key={`${session.examId}/${session.sessionId}`}
                    value={`${session.examId}/${session.sessionId}`}
                  >
                    Exam: {session.examId} | Session: {session.sessionId}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>
      )}

      {(selectedSession || selectedDevice) && viewMode === 'session' && (
        <button className="back-button" onClick={goBack}>
          ← Back
        </button>
      )}

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      {viewMode === 'session' && !selectedSession && !selectedDevice && (
        <div className="sessions-list">
          <h2>Exam Sessions</h2>
          {loading ? (
            <div className="loading">Loading sessions...</div>
          ) : sessions.length === 0 ? (
            <div className="empty-state">No exam sessions found</div>
          ) : (
            <div className="session-cards">
              {sessions.map((session, index) => (
                <div
                  key={index}
                  className="session-card"
                  onClick={() => handleSessionClick(session)}
                >
                  <div className="session-header">
                    <h3>Exam: {session.examId}</h3>
                    <span className="session-badge">{session.deviceCount} devices</span>
                  </div>
                  <div className="session-info">
                    <p>Session ID: {session.sessionId}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {viewMode === 'session' && selectedSession && !selectedDevice && sessionDetails && (
        <div className="session-details">
          <h2>Session Details</h2>
          <div className="detail-info">
            <p><strong>Exam ID:</strong> {sessionDetails.examId}</p>
            <p><strong>Session ID:</strong> {sessionDetails.sessionId}</p>
            <p><strong>Devices:</strong> {sessionDetails.devices.length}</p>
          </div>

          <h3>Devices</h3>
          <div className="device-grid">
            {sessionDetails.devices.map((device, index) => (
              <div
                key={index}
                className="device-card"
                onClick={() => handleDeviceClick(device)}
              >
                <h4>{device.deviceId}</h4>
                <div className="device-stats">
                  <div>
                    <span className="label">Sessions:</span>
                    <span className="value">{device.exam_sessions.length}</span>
                  </div>
                  <div>
                    <span className="label">Actions:</span>
                    <span className="value">{device.question_actions.length}</span>
                  </div>
                  <div>
                    <span className="label">Snapshots:</span>
                    <span className="value">{device.snapshot_actions.length}</span>
                  </div>
                  <div>
                    <span className="label">Submissions:</span>
                    <span className="value">{device.final_submissions.length}</span>
                  </div>
                  <div>
                    <span className="label">Answer Sheets:</span>
                    <span className="value">{device.answer_sheets.length}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {((viewMode === 'session' && selectedDevice) || (viewMode === 'filter' && filterDevice && filterSession)) && deviceTelemetry && (
        <div className="device-telemetry">
          <h2>Device Telemetry</h2>
          <div className="detail-info">
            <p><strong>Device ID:</strong> {deviceTelemetry.deviceId}</p>
            <p><strong>Exam ID:</strong> {deviceTelemetry.examId}</p>
            <p><strong>Session ID:</strong> {deviceTelemetry.sessionId}</p>
          </div>

          <div className="telemetry-sections">
            {Object.entries(deviceTelemetry.data).map(([dataType, items]) => (
              <div key={dataType} className="telemetry-section">
                <h3>{dataType.replace(/_/g, ' ').toUpperCase()} ({items.length})</h3>
                {items.length === 0 ? (
                  <p className="empty-data">No data available</p>
                ) : (
                  <div className="data-list">
                    {items.map((item, index) => (
                      <div key={index} className="data-item">
                        <div className="data-header">
                          <span className="file-name">{item._filename}</span>
                          {item.received_at && (
                            <span className="timestamp">{new Date(item.received_at).toLocaleString()}</span>
                          )}
                        </div>
                        <pre className="data-content">
                          {JSON.stringify(item, null, 2)}
                        </pre>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default ExamTelemetry
