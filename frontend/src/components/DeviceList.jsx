import React from 'react'

function DeviceList({ devices, onFlash }) {
  return (
    <div className="device-list">
      <table>
        <thead>
          <tr>
            <th>Device ID</th>
            <th>Model</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {devices.map((device) => (
            <tr key={device.id}>
              <td>{device.id}</td>
              <td>{device.model || 'Unknown'}</td>
              <td>
                <span className={`status ${device.status}`}>
                  {device.status}
                </span>
              </td>
              <td>
                <button
                  className="flash-btn"
                  onClick={() => onFlash(device.id)}
                  disabled={device.status === 'flashing'}
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
