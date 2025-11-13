import React from 'react'

function DeviceList({ devices, onFlash }) {
  return (
    <div className="device-list">
      <table>
        <thead>
          <tr>
            <th>Bus</th>
            <th>Device</th>
            <th>Vendor ID</th>
            <th>Product ID</th>
            <th>Description</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {devices.map((device) => (
            <tr key={device.id}>
              <td>{device.bus}</td>
              <td>{device.device}</td>
              <td>{device.vendor_id}</td>
              <td>{device.product_id}</td>
              <td>{device.description}</td>
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
