import React, { useState, useEffect } from 'react'
import DeviceList from '../components/DeviceList'
import DeviceTiles from '../components/DeviceTiles'
import FlashProgress from '../components/FlashProgress'

function Devices() {
  const [devices, setDevices] = useState([])
  const [viewMode, setViewMode] = useState('tiles')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [flashingDevice, setFlashingDevice] = useState(null)
  const [flashStatus, setFlashStatus] = useState(null)
  const [osAvailable, setOsAvailable] = useState(false)

  useEffect(() => {
    fetchDevices()
    checkOsAvailability()
    const interval = setInterval(fetchDevices, 5000)
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    let statusInterval
    if (flashingDevice) {
      statusInterval = setInterval(() => {
        fetchFlashStatus(flashingDevice)
      }, 2000)
    }
    return () => {
      if (statusInterval) clearInterval(statusInterval)
    }
  }, [flashingDevice])

  const checkOsAvailability = async () => {
    try {
      const response = await fetch('/api/devices/os/check')
      if (response.ok) {
        const data = await response.json()
        setOsAvailable(data.available || false)
      }
    } catch (err) {
      console.error('Error checking OS availability:', err)
    }
  }

  const fetchDevices = async () => {
    try {
      const response = await fetch('/api/devices')
      if (!response.ok) throw new Error('Failed to fetch devices')
      const data = await response.json()
      setDevices(data.devices || [])
      setError(null)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const fetchFlashStatus = async (deviceId) => {
    try {
      const response = await fetch(`/api/devices/${deviceId}/flash/status`)
      if (!response.ok) return
      const data = await response.json()
      setFlashStatus(data)

      if (data.status === 'completed' || data.status === 'error') {
        setTimeout(() => {
          if (data.status === 'completed') {
            fetchDevices()
          }
        }, 1000)
      }
    } catch (err) {
      console.error('Error fetching flash status:', err)
    }
  }

  const handleFlashDevice = async (deviceId) => {
    try {
      const response = await fetch(`/api/devices/${deviceId}/flash/prepare`, {
        method: 'POST'
      })
      if (!response.ok) {
        const data = await response.json()
        throw new Error(data.detail || 'Failed to start flashing')
      }
      const data = await response.json()
      setFlashingDevice(deviceId)
      setFlashStatus({ status: 'starting', progress: 0, message: 'Preparing flash process...' })
    } catch (err) {
      alert(`Error: ${err.message}`)
    }
  }

  const handleConfirmFlash = async () => {
    if (!flashingDevice) return

    try {
      const response = await fetch(`/api/devices/${flashingDevice}/flash/confirm`, {
        method: 'POST'
      })
      if (!response.ok) {
        const data = await response.json()
        throw new Error(data.detail || 'Failed to confirm flash')
      }
      setFlashStatus({ status: 'flashing_started', progress: 30, message: 'Flash confirmed. Starting process...' })
    } catch (err) {
      alert(`Error: ${err.message}`)
      setFlashStatus({ status: 'error', progress: 0, message: err.message })
    }
  }

  const handleCloseProgress = () => {
    setFlashingDevice(null)
    setFlashStatus(null)
    fetchDevices()
  }

  return (
    <div className="devices-page">
      <div className="devices-header">
        <h1>Connected Devices</h1>
        <div className="view-toggle">
          <button
            className={viewMode === 'list' ? 'active' : ''}
            onClick={() => setViewMode('list')}
          >
            List View
          </button>
          <button
            className={viewMode === 'tiles' ? 'active' : ''}
            onClick={() => setViewMode('tiles')}
          >
            Tile View
          </button>
        </div>
      </div>

      {loading && <p>Loading devices...</p>}
      {error && <p className="error">Error: {error}</p>}

      {!loading && !error && devices.length === 0 && (
        <p className="no-devices">No devices connected</p>
      )}

      {!loading && !error && devices.length > 0 && (
        <>
          {osAvailable && (
            <div className="os-available-banner">
              ✓ LineageOS image is available and ready for flashing
            </div>
          )}
          {viewMode === 'list' ? (
            <DeviceList devices={devices} onFlash={handleFlashDevice} />
          ) : (
            <DeviceTiles devices={devices} onFlash={handleFlashDevice} />
          )}
        </>
      )}

      {flashingDevice && flashStatus && (
        <FlashProgress
          deviceId={flashingDevice}
          status={flashStatus}
          onClose={handleCloseProgress}
          onConfirm={handleConfirmFlash}
        />
      )}
    </div>
  )
}

export default Devices
