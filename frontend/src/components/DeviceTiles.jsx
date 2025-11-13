import React from 'react'

function DeviceTiles({ devices, onFlash }) {
  return (
    <div className="device-tiles">
      {devices.map((device) => (
        <div key={device.id} className="device-tile">
          <div className="device-icon">💻</div>
          <h3>{device.description}</h3>
          <p className="device-id">Bus {device.bus} - Device {device.device}</p>
          <p className="device-serial">Serial: {device.serial || 'N/A'}</p>
          <p className="device-vendor">Vendor: {device.vendor_id} | Product: {device.product_id}</p>
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
