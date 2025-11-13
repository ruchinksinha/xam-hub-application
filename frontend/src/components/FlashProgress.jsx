import React from 'react'

function FlashProgress({ deviceId, status, onClose }) {
  const getStatusColor = () => {
    switch (status.status) {
      case 'completed': return '#22c55e'
      case 'error': return '#ef4444'
      case 'downloading':
      case 'rebooting':
      case 'pushing':
      case 'flashing': return '#3b82f6'
      default: return '#6b7280'
    }
  }

  const getStatusIcon = () => {
    switch (status.status) {
      case 'completed': return '✓'
      case 'error': return '✕'
      default: return '⟳'
    }
  }

  return (
    <div className="flash-progress-overlay">
      <div className="flash-progress-modal">
        <div className="progress-header">
          <h3>Flashing Device: {deviceId}</h3>
          {(status.status === 'completed' || status.status === 'error') && (
            <button className="close-btn" onClick={onClose}>×</button>
          )}
        </div>

        <div className="progress-content">
          <div className="status-icon" style={{ color: getStatusColor() }}>
            {getStatusIcon()}
          </div>

          <div className="progress-bar-container">
            <div
              className="progress-bar"
              style={{
                width: `${status.progress || 0}%`,
                backgroundColor: getStatusColor()
              }}
            />
          </div>

          <div className="progress-text">
            <span className="progress-percentage">{status.progress || 0}%</span>
            <span className="progress-message">{status.message || 'Processing...'}</span>
          </div>

          <div className="status-details">
            <div className="status-item">
              <span className="status-label">Status:</span>
              <span className="status-value" style={{ color: getStatusColor() }}>
                {status.status || 'idle'}
              </span>
            </div>
          </div>
        </div>

        {status.status === 'completed' && (
          <div className="progress-footer">
            <button className="success-btn" onClick={onClose}>Close</button>
          </div>
        )}

        {status.status === 'error' && (
          <div className="progress-footer">
            <button className="error-btn" onClick={onClose}>Close</button>
          </div>
        )}
      </div>
    </div>
  )
}

export default FlashProgress
