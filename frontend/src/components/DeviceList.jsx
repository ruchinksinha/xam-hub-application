import React from 'react'

function DeviceList({ devices, onFlash }) {
  return (
    <div className="device-list">
      <table>
        <thead>
          <tr>
            <th>Connection</th>
            <th>Bus</th>
            <th>Device</th>
            <th>Serial Number</th>
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
              <td>
                {device.connection_type === 'usb' && device.wifi_connected ? (
                  <span style={{ color: '#10b981', fontWeight: '500' }}>USB + WiFi</span>
                ) : device.connection_type === 'usb' ? (
                  <span style={{ color: '#10b981', fontWeight: '500' }}>USB</span>
                ) : device.connection_type === 'wifi' ? (
                  <span style={{ color: '#3b82f6', fontWeight: '500' }}>WiFi</span>
                ) : (
                  <span style={{ color: '#6b7280' }}>Offline</span>
                )}
              </td>
              <td>{device.bus || '-'}</td>
              <td>{device.device || '-'}</td>
              <td>{device.serial || 'N/A'}</td>
              <td>{device.vendor_id || '-'}</td>
              <td>{device.product_id || '-'}</td>
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
                  title='Flash LineageOS'
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
