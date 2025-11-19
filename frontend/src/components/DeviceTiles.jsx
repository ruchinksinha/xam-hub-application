import React, { useState } from 'react'

function DeviceTiles({ devices, onFlash }) {
  const [showInstructions, setShowInstructions] = useState(null)

  const getADBStatusIcon = (adbStatus) => {
    switch (adbStatus) {
      case 'authorized': return '✓'
      case 'unauthorized': return '⚠'
      case 'disabled': return '✕'
      default: return '?'
    }
  }

  const getADBStatusColor = (adbStatus) => {
    switch (adbStatus) {
      case 'authorized': return '#22c55e'
      case 'unauthorized': return '#f59e0b'
      case 'disabled': return '#ef4444'
      default: return '#6b7280'
    }
  }

  const getADBStatusText = (adbStatus) => {
    switch (adbStatus) {
      case 'authorized': return 'ADB Ready'
      case 'unauthorized': return 'ADB Unauthorized'
      case 'disabled': return 'ADB Disabled'
      default: return 'Unknown'
    }
  }

  return (
    <div className="device-tiles">
      {devices.map((device) => (
        <div key={device.id} className="device-tile">
          <div className="device-tile-header">
            <div className="device-icon">💻</div>
            <div className="usb-connection-badge" title="Connected via USB">
              <svg className="usb-icon" fill="currentColor" viewBox="0 0 24 24" width="16" height="16">
                <path d="M12 2a1 1 0 011 1v10.586l2.293-2.293a1 1 0 011.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L11 13.586V3a1 1 0 011-1zM6 15a2 2 0 00-2 2v3a2 2 0 002 2h12a2 2 0 002-2v-3a2 2 0 00-2-2h-3.586l-2 2H14a1 1 0 010 2h-4a1 1 0 010-2h1.586l-2-2H6z"/>
              </svg>
              USB
            </div>
          </div>
          <h3>{device.description}</h3>
          <p className="device-id">Bus {device.bus} - Device {device.device}</p>
          <p className="device-serial">Serial: {device.serial || 'N/A'}</p>
          <p className="device-vendor">Vendor: {device.vendor_id} | Product: {device.product_id}</p>
          {device.is_registered && (
            <p className="device-registered-name" title="Registered name">📋 {device.registered_name}</p>
          )}

          <div className="adb-status-container">
            <span
              className="adb-status-badge"
              style={{
                backgroundColor: `${getADBStatusColor(device.adb_status)}20`,
                color: getADBStatusColor(device.adb_status),
                border: `1px solid ${getADBStatusColor(device.adb_status)}`
              }}
            >
              <span className="adb-icon">{getADBStatusIcon(device.adb_status)}</span>
              {getADBStatusText(device.adb_status)}
            </span>

            {!device.adb_ready && (
              <button
                className="help-btn"
                onClick={() => setShowInstructions(showInstructions === device.id ? null : device.id)}
              >
                ?
              </button>
            )}
          </div>

          {showInstructions === device.id && !device.adb_ready && (
            <div className="instructions-panel">
              <h4>Enable USB Debugging</h4>
              <ol>
                <li>Open <strong>Settings</strong> on your device</li>
                <li>Go to <strong>About Tablet</strong></li>
                <li>Tap <strong>Build Number</strong> 7 times to enable Developer Options</li>
                <li>Go back to <strong>Settings</strong> → <strong>Developer Options</strong></li>
                <li>Enable <strong>USB Debugging</strong></li>
                <li>When prompted, tap <strong>Allow</strong> to authorize this computer</li>
              </ol>
              <p className="note">The device will automatically be ready once debugging is enabled.</p>
            </div>
          )}

          <span className={`status ${device.status}`}>
            {device.status}
          </span>

          <button
            className="flash-btn"
            onClick={() => onFlash(device.id)}
            disabled={device.status === 'flashing' || !device.adb_ready}
            title={!device.adb_ready ? 'USB debugging must be enabled first' : 'Flash LineageOS'}
          >
            {device.status === 'flashing' ? 'Flashing...' : 'Flash Device'}
          </button>
        </div>
      ))}
    </div>
  )
}

export default DeviceTiles
