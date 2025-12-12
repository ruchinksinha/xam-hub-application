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

  useEffect(() => {
    fetchStats()
    fetchSessions()
  }, [])

  const fetchStats = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/telemetry/stats')
      const data = await response.json()
      setStats(data)
    } catch (err) {
      console.error('Error fetching stats:', err)
    }
  }

  const fetchSessions = async () => {
    try {
      setLoading(true)
      const response = await fetch('http://localhost:8000/api/telemetry/sessions')
      const data = await response.json()
      setSessions(data.sessions || [])
    } catch (err) {
      setError('Failed to load exam sessions')
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
        `http://localhost:8000/api/telemetry/session/${session.examId}/${session.sessionId}`
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
        `http://localhost:8000/api/telemetry/device/${selectedSession.examId}/${selectedSession.sessionId}/${device.deviceId}`
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

      {(selectedSession || selectedDevice) && (
        <button className="back-button" onClick={goBack}>
          ← Back
        </button>
      )}

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      {!selectedSession && !selectedDevice && (
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

      {selectedSession && !selectedDevice && sessionDetails && (
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

      {selectedDevice && deviceTelemetry && (
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
