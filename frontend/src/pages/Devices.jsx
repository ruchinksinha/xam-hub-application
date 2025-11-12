import React, { useState, useEffect } from 'react'
import DeviceList from '../components/DeviceList'
import DeviceTiles from '../components/DeviceTiles'

function Devices() {
  const [devices, setDevices] = useState([])
  const [viewMode, setViewMode] = useState('tiles')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchDevices()
    const interval = setInterval(fetchDevices, 5000)
    return () => clearInterval(interval)
  }, [])

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

  const handleFlashDevice = async (deviceId) => {
    if (!confirm(`Are you sure you want to flash device ${deviceId}?`)) return

    try {
      const response = await fetch(`/api/devices/${deviceId}/flash`, {
        method: 'POST'
      })
      if (!response.ok) throw new Error('Failed to start flashing')
      const data = await response.json()
      alert(data.message || 'Flashing started successfully')
      fetchDevices()
    } catch (err) {
      alert(`Error: ${err.message}`)
    }
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
        viewMode === 'list' ? (
          <DeviceList devices={devices} onFlash={handleFlashDevice} />
        ) : (
          <DeviceTiles devices={devices} onFlash={handleFlashDevice} />
        )
      )}
    </div>
  )
}

export default Devices
