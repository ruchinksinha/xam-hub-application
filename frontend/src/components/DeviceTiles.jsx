import React from 'react'

function DeviceTiles({ devices, onFlash }) {
  return (
    <div className="device-tiles">
      {devices.map((device) => (
        <div key={device.id} className="device-tile">
          <div className="device-icon">📱</div>
          <h3>{device.model || 'Unknown Device'}</h3>
          <p className="device-id">ID: {device.id}</p>
          <span className={`status ${device.status}`}>
            {device.status}
          </span>
          <button
            className="flash-btn"
            onClick={() => onFlash(device.id)}
            disabled={device.status === 'flashing'}
          >
            {device.status === 'flashing' ? 'Flashing...' : 'Flash Device'}
          </button>
        </div>
      ))}
    </div>
  )
}

export default DeviceTiles
