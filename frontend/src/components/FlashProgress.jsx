import React from 'react'

function FlashProgress({ deviceId, status, onClose, onConfirm }) {
  const getStatusColor = () => {
    switch (status.status) {
      case 'completed': return '#22c55e'
      case 'error': return '#ef4444'
      case 'downloading':
      case 'download_complete':
      case 'awaiting_confirmation':
      case 'cached':
      case 'rebooting':
      case 'pushing':
      case 'flashing':
      case 'flashing_started': return '#3b82f6'
      default: return '#6b7280'
    }
  }

  const getStatusIcon = () => {
    switch (status.status) {
      case 'completed': return '✓'
      case 'error': return '✕'
      case 'awaiting_confirmation': return '?'
      case 'cached': return '✓'
      default: return '⟳'
    }
  }

  const formatBytes = (bytes) => {
    if (!bytes) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
  }

  const isAwaitingConfirmation = status.status === 'awaiting_confirmation' || status.status === 'download_complete' || status.status === 'cached'
  const isDownloading = status.status === 'downloading'

  return (
    <div className="flash-progress-overlay">
      <div className="flash-progress-modal">
        <div className="progress-header">
          <h3>
            {isAwaitingConfirmation ? 'Ready to Flash' : 'Flashing Device'}: {deviceId}
          </h3>
          {(status.status === 'completed' || status.status === 'error') && (
            <button className="close-btn" onClick={onClose}>×</button>
          )}
        </div>

        <div className="progress-content">
          <div className="status-icon" style={{ color: getStatusColor() }}>
            {getStatusIcon()}
          </div>

          {isDownloading && status.download_progress !== undefined && (
            <>
              <div className="download-info">
                <span className="download-label">Downloading OS Image</span>
                <span className="download-size">
                  {formatBytes(status.download_size)} / {formatBytes(status.total_size)}
                </span>
              </div>
              <div className="progress-bar-container">
                <div
                  className="progress-bar"
                  style={{
                    width: `${status.download_progress || 0}%`,
                    backgroundColor: getStatusColor()
                  }}
                />
              </div>
              <div className="progress-text">
                <span className="progress-percentage">{status.download_progress || 0}%</span>
                <span className="progress-message">{status.message || 'Downloading...'}</span>
              </div>
            </>
          )}

          {!isDownloading && !isAwaitingConfirmation && (
            <>
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
            </>
          )}

          {isAwaitingConfirmation && (
            <div className="confirmation-box">
              <p className="confirmation-message">
                {status.os_cached ?
                  '✓ OS image is already downloaded and ready to flash.' :
                  '✓ OS image has been downloaded successfully.'}
              </p>
              {status.os_size && (
                <p className="os-info">Size: {formatBytes(status.os_size)}</p>
              )}
              <p className="warning-message">
                ⚠ Warning: This will erase all data on the device. Make sure you have a backup.
              </p>
            </div>
          )}

          <div className="status-details">
            <div className="status-item">
              <span className="status-label">Status:</span>
              <span className="status-value" style={{ color: getStatusColor() }}>
                {status.status || 'idle'}
              </span>
            </div>
          </div>

          {status.status === 'error' && status.error_detail && (
            <div className="error-details">
              <h4>Error Details</h4>
              <p className="error-message">{status.error_detail}</p>
              {status.error_trace && (
                <details className="error-trace">
                  <summary>Technical Details (Click to expand)</summary>
                  <pre>{status.error_trace}</pre>
                </details>
              )}
            </div>
          )}
        </div>

        {isAwaitingConfirmation && (
          <div className="progress-footer">
            <button className="cancel-btn" onClick={onClose}>Cancel</button>
            <button className="confirm-btn" onClick={onConfirm}>
              Confirm & Flash Device
            </button>
          </div>
        )}

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
