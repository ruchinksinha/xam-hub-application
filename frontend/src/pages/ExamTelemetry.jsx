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
  const [viewMode, setViewMode] = useState('filter')
  const [allDevices, setAllDevices] = useState([])
  const [filterDevice, setFilterDevice] = useState('')
  const [deviceSessions, setDeviceSessions] = useState([])
  const [filterSession, setFilterSession] = useState('')
  const [activeDataType, setActiveDataType] = useState('exam_sessions')

  useEffect(() => {
    fetchStats()
    fetchSessions()
    fetchAllDevices()
  }, [])

  useEffect(() => {
    if (deviceTelemetry && deviceTelemetry.data) {
      const dataTypes = Object.keys(deviceTelemetry.data)
      if (dataTypes.length > 0 && !dataTypes.includes(activeDataType)) {
        setActiveDataType(dataTypes[0])
      }
    }
  }, [deviceTelemetry])

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
      <div className="page-header" style={{
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        padding: '32px',
        borderRadius: '12px',
        marginBottom: '32px',
        boxShadow: '0 8px 20px rgba(102, 126, 234, 0.25)',
        color: 'white'
      }}>
        <h1 style={{ fontSize: '32px', fontWeight: '800', marginBottom: '8px', color: 'white' }}>
          Exam Telemetry Dashboard
        </h1>
        <p style={{ fontSize: '16px', opacity: 0.95, color: 'white', fontWeight: '400' }}>
          Track exam sessions and device activity
        </p>
      </div>

      {stats && (
        <div className="stats-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '20px', marginBottom: '32px' }}>
          <div style={{
            background: 'linear-gradient(135deg, #5a67d8 0%, #6b46c1 100%)',
            padding: '24px',
            borderRadius: '12px',
            color: 'white',
            boxShadow: '0 4px 6px rgba(90, 103, 216, 0.25)'
          }}>
            <h3 style={{ fontSize: '14px', fontWeight: '500', marginBottom: '12px', opacity: 0.9 }}>Total Exams</h3>
            <div style={{ fontSize: '36px', fontWeight: '700' }}>{stats.totalExams}</div>
          </div>
          <div style={{
            background: 'linear-gradient(135deg, #d946a8 0%, #dc2626 100%)',
            padding: '24px',
            borderRadius: '12px',
            color: 'white',
            boxShadow: '0 4px 6px rgba(217, 70, 168, 0.25)'
          }}>
            <h3 style={{ fontSize: '14px', fontWeight: '500', marginBottom: '12px', opacity: 0.9 }}>Distinct Devices</h3>
            <div style={{ fontSize: '36px', fontWeight: '700' }}>{stats.totalDevices}</div>
          </div>
          <div style={{
            background: 'linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%)',
            padding: '24px',
            borderRadius: '12px',
            color: 'white',
            boxShadow: '0 4px 6px rgba(14, 165, 233, 0.25)'
          }}>
            <h3 style={{ fontSize: '14px', fontWeight: '500', marginBottom: '12px', opacity: 0.9 }}>Total Sessions</h3>
            <div style={{ fontSize: '36px', fontWeight: '700' }}>{stats.totalSessions}</div>
          </div>
          <div style={{
            background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
            padding: '24px',
            borderRadius: '12px',
            color: 'white',
            boxShadow: '0 4px 6px rgba(16, 185, 129, 0.25)'
          }}>
            <h3 style={{ fontSize: '14px', fontWeight: '500', marginBottom: '12px', opacity: 0.9 }}>Data Files</h3>
            <div style={{ fontSize: '36px', fontWeight: '700' }}>
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
        background: 'linear-gradient(135deg, #f6f8fb 0%, #ffffff 100%)',
        padding: '20px',
        borderRadius: '12px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.08)'
      }}>
        <label style={{ fontWeight: '600', marginRight: '8px', color: '#1f2937', fontSize: '15px' }}>View Mode:</label>
        <button
          onClick={() => {
            setViewMode('session')
            setFilterDevice('')
            setFilterSession('')
            setDeviceTelemetry(null)
          }}
          style={{
            padding: '10px 20px',
            borderRadius: '8px',
            border: 'none',
            background: viewMode === 'session' ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' : 'white',
            color: viewMode === 'session' ? 'white' : '#6b7280',
            fontWeight: '600',
            cursor: 'pointer',
            boxShadow: viewMode === 'session' ? '0 4px 12px rgba(102, 126, 234, 0.3)' : '0 2px 4px rgba(0,0,0,0.05)',
            transition: 'all 0.3s ease',
            fontSize: '14px'
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
            padding: '10px 20px',
            borderRadius: '8px',
            border: 'none',
            background: viewMode === 'filter' ? 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)' : 'white',
            color: viewMode === 'filter' ? 'white' : '#6b7280',
            fontWeight: '600',
            cursor: 'pointer',
            boxShadow: viewMode === 'filter' ? '0 4px 12px rgba(79, 172, 254, 0.3)' : '0 2px 4px rgba(0,0,0,0.05)',
            transition: 'all 0.3s ease',
            fontSize: '14px'
          }}
        >
          Device Filter
        </button>
      </div>

      {viewMode === 'filter' && (
        <div style={{
          background: 'white',
          padding: '28px',
          borderRadius: '12px',
          boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
          marginBottom: '28px',
          border: '1px solid #e5e7eb'
        }}>
          <h3 style={{
            marginBottom: '20px',
            fontSize: '18px',
            fontWeight: '700',
            color: '#1f2937',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}>
            <span style={{
              width: '4px',
              height: '24px',
              background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
              borderRadius: '4px'
            }}></span>
            Filter by Device and Session
          </h3>
          <div style={{ display: 'flex', gap: '20px', alignItems: 'flex-end' }}>
            <div style={{ flex: 1 }}>
              <label style={{
                display: 'block',
                marginBottom: '10px',
                fontSize: '14px',
                fontWeight: '600',
                color: '#374151'
              }}>
                Select Device
              </label>
              <select
                value={filterDevice}
                onChange={(e) => handleFilterDeviceChange(e.target.value)}
                style={{
                  width: '100%',
                  padding: '12px 14px',
                  borderRadius: '8px',
                  border: '2px solid #e5e7eb',
                  fontSize: '14px',
                  background: 'white',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                  outline: 'none'
                }}
                onFocus={(e) => e.target.style.borderColor = '#4facfe'}
                onBlur={(e) => e.target.style.borderColor = '#e5e7eb'}
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
                marginBottom: '10px',
                fontSize: '14px',
                fontWeight: '600',
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
                  padding: '12px 14px',
                  borderRadius: '8px',
                  border: '2px solid #e5e7eb',
                  fontSize: '14px',
                  background: 'white',
                  opacity: !filterDevice || deviceSessions.length === 0 ? 0.5 : 1,
                  cursor: !filterDevice || deviceSessions.length === 0 ? 'not-allowed' : 'pointer',
                  transition: 'all 0.2s ease',
                  outline: 'none'
                }}
                onFocus={(e) => !e.target.disabled && (e.target.style.borderColor = '#4facfe')}
                onBlur={(e) => e.target.style.borderColor = '#e5e7eb'}
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
        <div className="device-telemetry" style={{
          background: 'white',
          padding: '28px',
          borderRadius: '12px',
          boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
          border: '1px solid #e5e7eb'
        }}>
          <h2 style={{
            fontSize: '24px',
            fontWeight: '700',
            color: '#1f2937',
            marginBottom: '20px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}>
            <span style={{
              width: '6px',
              height: '28px',
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              borderRadius: '4px'
            }}></span>
            Device Telemetry
          </h2>
          <div style={{
            background: 'linear-gradient(135deg, #f6f8fb 0%, #ffffff 100%)',
            padding: '16px 20px',
            borderRadius: '10px',
            marginBottom: '24px',
            border: '1px solid #e5e7eb'
          }}>
            <div style={{ display: 'flex', gap: '24px', flexWrap: 'wrap' }}>
              <p style={{ margin: 0 }}>
                <strong style={{ color: '#6b7280', fontSize: '13px', fontWeight: '600' }}>Device ID:</strong>{' '}
                <span style={{ color: '#1f2937', fontSize: '14px', fontWeight: '600' }}>{deviceTelemetry.deviceId}</span>
              </p>
              <p style={{ margin: 0 }}>
                <strong style={{ color: '#6b7280', fontSize: '13px', fontWeight: '600' }}>Exam ID:</strong>{' '}
                <span style={{ color: '#1f2937', fontSize: '14px', fontWeight: '600' }}>{deviceTelemetry.examId}</span>
              </p>
              <p style={{ margin: 0 }}>
                <strong style={{ color: '#6b7280', fontSize: '13px', fontWeight: '600' }}>Session ID:</strong>{' '}
                <span style={{ color: '#1f2937', fontSize: '14px', fontWeight: '600' }}>{deviceTelemetry.sessionId}</span>
              </p>
            </div>
          </div>

          <div style={{ marginTop: '24px' }}>
            <div style={{
              display: 'flex',
              gap: '8px',
              borderBottom: '3px solid #f3f4f6',
              marginBottom: '24px',
              flexWrap: 'wrap',
              background: '#fafbfc',
              padding: '8px',
              borderRadius: '12px 12px 0 0'
            }}>
              {Object.entries(deviceTelemetry.data).map(([dataType, items]) => (
                <button
                  key={dataType}
                  onClick={() => setActiveDataType(dataType)}
                  style={{
                    padding: '14px 24px',
                    border: 'none',
                    background: activeDataType === dataType
                      ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
                      : 'white',
                    color: activeDataType === dataType ? 'white' : '#6b7280',
                    fontWeight: '700',
                    fontSize: '13px',
                    cursor: 'pointer',
                    borderRadius: '8px',
                    transition: 'all 0.3s ease',
                    boxShadow: activeDataType === dataType
                      ? '0 4px 12px rgba(102, 126, 234, 0.4)'
                      : '0 2px 4px rgba(0,0,0,0.05)',
                    transform: activeDataType === dataType ? 'translateY(-2px)' : 'translateY(0)',
                    letterSpacing: '0.5px'
                  }}
                >
                  {dataType.replace(/_/g, ' ').toUpperCase()} ({items.length})
                </button>
              ))}
            </div>

            <div className="telemetry-tab-content">
              {deviceTelemetry.data[activeDataType] && (
                <>
                  {deviceTelemetry.data[activeDataType].length === 0 ? (
                    <div style={{
                      textAlign: 'center',
                      padding: '60px 40px',
                      background: 'linear-gradient(135deg, #f9fafb 0%, #ffffff 100%)',
                      borderRadius: '12px',
                      border: '2px dashed #e5e7eb'
                    }}>
                      <div style={{
                        fontSize: '48px',
                        marginBottom: '16px',
                        opacity: 0.5
                      }}>📭</div>
                      <p style={{
                        color: '#9ca3af',
                        fontSize: '16px',
                        fontWeight: '600',
                        margin: 0
                      }}>
                        No data available
                      </p>
                    </div>
                  ) : (
                    <div className="data-list">
                      {deviceTelemetry.data[activeDataType].map((item, index) => (
                        <div key={index} className="data-item" style={{
                          background: 'white',
                          border: '2px solid #f3f4f6',
                          borderRadius: '12px',
                          padding: '20px',
                          marginBottom: '20px',
                          boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
                          transition: 'all 0.3s ease'
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.boxShadow = '0 8px 20px rgba(0,0,0,0.12)';
                          e.currentTarget.style.transform = 'translateY(-2px)';
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.06)';
                          e.currentTarget.style.transform = 'translateY(0)';
                        }}>
                          <div className="data-header" style={{
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                            marginBottom: '16px',
                            paddingBottom: '16px',
                            borderBottom: '2px solid #f3f4f6'
                          }}>
                            <span className="file-name" style={{
                              fontWeight: '700',
                              color: '#1f2937',
                              fontSize: '15px',
                              display: 'flex',
                              alignItems: 'center',
                              gap: '8px'
                            }}>
                              <span style={{
                                width: '8px',
                                height: '8px',
                                background: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
                                borderRadius: '50%',
                                display: 'inline-block'
                              }}></span>
                              {item._filename}
                            </span>
                            {item.received_at && (
                              <span className="timestamp" style={{
                                color: '#9ca3af',
                                fontSize: '13px',
                                fontWeight: '500',
                                background: '#f9fafb',
                                padding: '4px 12px',
                                borderRadius: '6px'
                              }}>
                                {new Date(item.received_at).toLocaleString()}
                              </span>
                            )}
                          </div>
                          <pre className="data-content" style={{
                            background: '#1e1e1e',
                            color: '#d4d4d4',
                            padding: '16px',
                            borderRadius: '8px',
                            fontSize: '12px',
                            overflow: 'auto',
                            maxHeight: '500px',
                            whiteSpace: 'pre-wrap',
                            wordWrap: 'break-word',
                            wordBreak: 'break-word',
                            border: '1px solid #333',
                            fontFamily: 'ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, "Liberation Mono", monospace',
                            lineHeight: '1.6'
                          }}>
                            {JSON.stringify(item, null, 2)}
                          </pre>
                        </div>
                      ))}
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default ExamTelemetry
