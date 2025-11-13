import React from 'react'

function DeviceList({ devices, onFlash }) {
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
      case 'authorized': return 'Ready'
      case 'unauthorized': return 'Unauthorized'
      case 'disabled': return 'Disabled'
      default: return 'Unknown'
    }
  }

  return (
    <div className="device-list">
      <table>
        <thead>
          <tr>
            <th>Bus</th>
            <th>Device</th>
            <th>Serial Number</th>
            <th>Vendor ID</th>
            <th>Product ID</th>
            <th>Description</th>
            <th>ADB Status</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {devices.map((device) => (
            <tr key={device.id}>
              <td>{device.bus}</td>
              <td>{device.device}</td>
              <td>{device.serial || 'N/A'}</td>
              <td>{device.vendor_id}</td>
              <td>{device.product_id}</td>
              <td>{device.description}</td>
              <td>
                <span
                  className="adb-status-badge-small"
                  style={{
                    backgroundColor: `${getADBStatusColor(device.adb_status)}20`,
                    color: getADBStatusColor(device.adb_status),
                    border: `1px solid ${getADBStatusColor(device.adb_status)}`
                  }}
                  title={!device.adb_ready ? 'USB debugging must be enabled' : 'Device is ready for flashing'}
                >
                  {getADBStatusIcon(device.adb_status)} {getADBStatusText(device.adb_status)}
                </span>
              </td>
              <td>
                <span className={`status ${device.status}`}>
                  {device.status}
                </span>
              </td>
              <td>
                <button
                  className="flash-btn"
                  onClick={() => onFlash(device.id)}
                  disabled={device.status === 'flashing' || !device.adb_ready}
                  title={!device.adb_ready ? 'USB debugging must be enabled first' : 'Flash LineageOS'}
                >
                  {device.status === 'flashing' ? 'Flashing...' : 'Flash Device'}
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default DeviceList
