import React, { useState } from 'react'

const API_URL = 'http://localhost';

function DeviceTiles({ devices, onFlash, onRegister }) {
  const [showInstructions, setShowInstructions] = useState(null)
  const [showCaptcha, setShowCaptcha] = useState(null)
  const [captchaInput, setCaptchaInput] = useState('')
  const [captchaCode, setCaptchaCode] = useState('')

  const handleRegister = async (device) => {
    if (!device.serial || device.serial === 'N/A') {
      alert('Cannot register device without a valid serial number. Please enable USB debugging first.')
      return
    }

    try {
      const response = await fetch(`${API_URL}/api/registered-devices`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          serial: device.serial,
          name: device.description || device.serial,
          model: device.description || '',
          manufacturer: '',
          usb_bus: device.bus || '',
          usb_device: device.device || ''
        })
      })

      if (response.ok) {
        alert('Device registered successfully!')
        if (onRegister) onRegister()
      } else {
        alert('Failed to register device')
      }
    } catch (error) {
      console.error('Failed to register device:', error)
      alert('Error registering device')
    }
  }

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

  const generateCaptcha = () => {
    const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
    let result = ''
    for (let i = 0; i < 6; i++) {
      result += chars.charAt(Math.floor(Math.random() * chars.length))
    }
    return result
  }

  const handleFlashClick = (deviceId) => {
    const code = generateCaptcha()
    setCaptchaCode(code)
    setShowCaptcha(deviceId)
    setCaptchaInput('')
  }

  const handleCaptchaSubmit = (deviceId) => {
    if (captchaInput.toUpperCase() === captchaCode) {
      setShowCaptcha(null)
      setCaptchaInput('')
      setCaptchaCode('')
      onFlash(deviceId)
    } else {
      alert('Incorrect captcha. Please try again.')
      const newCode = generateCaptcha()
      setCaptchaCode(newCode)
      setCaptchaInput('')
    }
  }

  const handlePublishApp = async (device) => {
    if (!device.serial || device.serial === 'N/A') {
      alert('Cannot publish app without a valid serial number.')
      return
    }

    if (!confirm(`Publish app to ${device.description}?`)) {
      return
    }

    try {
      const response = await fetch(`${API_URL}/api/devices/${device.serial}/publish-app`, {
        method: 'POST'
      })

      const data = await response.json()

      if (response.ok) {
        alert(`App published successfully to ${device.description}!`)
      } else {
        alert(data.detail || 'Failed to publish app')
      }
    } catch (error) {
      console.error('Failed to publish app:', error)
      alert('Error publishing app')
    }
  }

  const getConnectionType = (device) => {
    // Use connection_type from API if available
    if (device.connection_type) {
      return device.connection_type
    }
    // Fallback logic
    if (!device.serial || device.serial === 'N/A') {
      return 'disconnected'
    }
    if (device.bus && device.device) {
      return 'usb'
    }
    if (device.is_registered) {
      return 'wifi'
    }
    return 'disconnected'
  }

  const getConnectionIcon = (type) => {
    switch (type) {
      case 'usb':
        return (
          <svg className="connection-icon" fill="currentColor" viewBox="0 0 24 24" width="16" height="16">
            <path d="M12 2a1 1 0 011 1v10.586l2.293-2.293a1 1 0 011.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L11 13.586V3a1 1 0 011-1zM6 15a2 2 0 00-2 2v3a2 2 0 002 2h12a2 2 0 002-2v-3a2 2 0 00-2-2h-3.586l-2 2H14a1 1 0 010 2h-4a1 1 0 010-2h1.586l-2-2H6z"/>
          </svg>
        )
      case 'wifi':
        return (
          <svg className="connection-icon" fill="currentColor" viewBox="0 0 24 24" width="16" height="16">
            <path d="M1 9l2 2c4.97-4.97 13.03-4.97 18 0l2-2C16.93 2.93 7.08 2.93 1 9zm8 8l3 3 3-3c-1.65-1.66-4.34-1.66-6 0zm-4-4l2 2c2.76-2.76 7.24-2.76 10 0l2-2C15.14 9.14 8.87 9.14 5 13z"/>
          </svg>
        )
      default:
        return (
          <svg className="connection-icon" fill="currentColor" viewBox="0 0 24 24" width="16" height="16">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 15h2v2h-2v-2zm0-10h2v8h-2V7z"/>
          </svg>
        )
    }
  }

  const getConnectionBadgeClass = (type) => {
    switch (type) {
      case 'usb': return 'usb-connection-badge'
      case 'wifi': return 'wifi-connection-badge'
      default: return 'disconnected-connection-badge'
    }
  }

  const getConnectionText = (type) => {
    switch (type) {
      case 'usb': return 'USB'
      case 'wifi': return 'WiFi'
      default: return 'Disconnected'
    }
  }

  return (
    <div className="device-tiles">
      {devices.map((device) => (
        <div key={device.id} className="device-tile">
          <div className="device-tile-header">
            <div className="device-icon">💻</div>
            <div className={getConnectionBadgeClass(getConnectionType(device))} title={`Connected via ${getConnectionText(getConnectionType(device))}`}>
              {getConnectionIcon(getConnectionType(device))}
              {getConnectionText(getConnectionType(device))}
            </div>
          </div>
          <h3>{device.description}</h3>
          {device.connection_type === 'usb' && (
            <>
              <p className="device-id">Bus {device.bus} - Device {device.device}</p>
              <p className="device-vendor">Vendor: {device.vendor_id} | Product: {device.product_id}</p>
            </>
          )}
          <p className="device-serial">Serial: {device.serial || 'N/A'}</p>
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

          {showCaptcha === device.id && (
            <div className="captcha-panel">
              <h4>Confirm Flash Operation</h4>
              <p>Enter the code below to proceed:</p>
              <div className="captcha-code">{captchaCode}</div>
              <input
                type="text"
                className="captcha-input"
                value={captchaInput}
                onChange={(e) => setCaptchaInput(e.target.value)}
                placeholder="Enter captcha"
                maxLength={6}
              />
              <div className="captcha-actions">
                <button
                  className="captcha-submit-btn"
                  onClick={() => handleCaptchaSubmit(device.id)}
                >
                  Confirm
                </button>
                <button
                  className="captcha-cancel-btn"
                  onClick={() => {
                    setShowCaptcha(null)
                    setCaptchaInput('')
                    setCaptchaCode('')
                  }}
                >
                  Cancel
                </button>
              </div>
            </div>
          )}

          <div className="device-actions">
            {!device.is_registered && device.serial && device.serial !== 'N/A' && (
              <button
                className="register-btn"
                onClick={() => handleRegister(device)}
                title="Register this device for tracking"
              >
                Register Device
              </button>
            )}
            {device.is_registered && device.serial && device.serial !== 'N/A' && (
              <button
                className="publish-btn"
                onClick={() => handlePublishApp(device)}
                title="Publish app to this device"
              >
                Publish App
              </button>
            )}
            <button
              className="flash-btn"
              onClick={() => handleFlashClick(device.id)}
              disabled={device.status === 'flashing' || !device.adb_ready}
              title={!device.adb_ready ? 'USB debugging must be enabled first' : 'Flash LineageOS'}
            >
              {device.status === 'flashing' ? 'Flashing...' : 'Flash Device'}
            </button>
          </div>
        </div>
      ))}
    </div>
  )
}

export default DeviceTiles
