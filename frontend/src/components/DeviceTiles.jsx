import React, { useState } from 'react'
import ProgressModal from './ProgressModal'

const API_URL = 'http://localhost';

function DeviceTiles({ devices, onFlash, onRegister }) {
  const [showCaptcha, setShowCaptcha] = useState(null)
  const [captchaInput, setCaptchaInput] = useState('')
  const [captchaCode, setCaptchaCode] = useState('')
  const [progressModal, setProgressModal] = useState({
    isOpen: false,
    title: '',
    message: '',
    steps: []
  })

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

  const handlePushProfile = async (device) => {
    if (!device.serial || device.serial === 'N/A') {
      alert('Cannot push profile without a valid serial number.')
      return
    }

    if (!confirm(`Push device profile to ${device.description}?`)) {
      return
    }

    setProgressModal({
      isOpen: true,
      title: 'Pushing Device Profile',
      message: 'Processing...',
      steps: []
    })

    try {
      const response = await fetch(`${API_URL}/api/devices/${device.serial}/push-profile`, {
        method: 'POST'
      })

      const data = await response.json()

      if (response.ok && data.success) {
        setProgressModal({
          isOpen: true,
          title: 'Push Device Profile',
          message: data.message,
          steps: data.steps || []
        })
      } else {
        setProgressModal({
          isOpen: true,
          title: 'Push Device Profile',
          message: data.message || data.detail || 'Failed to push profile',
          steps: data.steps || []
        })
      }
    } catch (error) {
      console.error('Failed to push profile:', error)
      setProgressModal({
        isOpen: true,
        title: 'Push Device Profile',
        message: `Error: ${error.message}`,
        steps: []
      })
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

  const getConnectionText = (device) => {
    const type = getConnectionType(device)
    switch (type) {
      case 'usb':
        return device.wifi_connected ? 'USB + WiFi' : 'USB'
      case 'wifi':
        return 'WiFi Connected'
      default:
        return 'Disconnected'
    }
  }

  return (
    <div className="device-tiles">
      {devices.map((device) => (
        <div key={device.id} className="device-tile">
          <div className="device-tile-header">
            <div className="device-icon">💻</div>
            <div className={getConnectionBadgeClass(getConnectionType(device))} title={`Connected via ${getConnectionText(device)}`}>
              {getConnectionIcon(getConnectionType(device))}
              {getConnectionText(device)}
            </div>
          </div>
          <h3>{device.serial || 'N/A'}</h3>
          {device.connection_type === 'usb' && (
            <>
              <p className="device-id">Bus {device.bus} - Device {device.device}</p>
              <p className="device-vendor">Vendor: {device.vendor_id} | Product: {device.product_id}</p>
            </>
          )}
          <p className="device-serial">Name: {device.description}</p>
          {device.is_registered && (
            <p className="device-registered-name" title="Registered name">📋 {device.registered_name}</p>
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
            {!device.is_registered && device.serial && device.serial !== 'N/A' && device.connection_type === 'usb' && (
              <button
                className="register-btn"
                onClick={() => handleRegister(device)}
                title="Register this device for tracking"
              >
                Register Device
              </button>
            )}
            {device.is_registered && device.serial && device.serial !== 'N/A' && device.connection_type === 'usb' && (
              <button
                className="push-profile-btn"
                onClick={() => handlePushProfile(device)}
                title="Push device profile to this device"
                disabled={device.connection_type !== 'usb'}
              >
                Push Device Profile
              </button>
            )}
            {device.connection_type === 'wifi' && (
              <p className="wifi-only-message">WiFi connected - USB required for operations</p>
            )}
            {device.connection_type === 'disconnected' && device.is_registered && (
              <p className="disconnected-message">Device disconnected</p>
            )}
          </div>
        </div>
      ))}

      <ProgressModal
        isOpen={progressModal.isOpen}
        title={progressModal.title}
        message={progressModal.message}
        steps={progressModal.steps}
        onClose={() => setProgressModal({ isOpen: false, title: '', message: '', steps: [] })}
      />
    </div>
  )
}

export default DeviceTiles
