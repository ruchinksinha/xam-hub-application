import { useState, useEffect } from 'react';

const API_URL = 'http://localhost';

export default function RegisteredNodes() {
  const [devices, setDevices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editingDevice, setEditingDevice] = useState(null);
  const [editForm, setEditForm] = useState({ name: '', notes: '' });

  const fetchDevices = async () => {
    try {
      const response = await fetch(`${API_URL}/api/registered-devices`);
      const data = await response.json();
      setDevices(data.devices || []);
    } catch (error) {
      console.error('Failed to fetch registered devices:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDevices();
    const interval = setInterval(fetchDevices, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleEdit = (device) => {
    setEditingDevice(device.serial);
    setEditForm({
      name: device.name || '',
      notes: device.notes || ''
    });
  };

  const handleSave = async (serial) => {
    try {
      const response = await fetch(`${API_URL}/api/registered-devices/${serial}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(editForm)
      });

      if (response.ok) {
        setEditingDevice(null);
        fetchDevices();
      }
    } catch (error) {
      console.error('Failed to update device:', error);
    }
  };

  const handleUnregister = async (serial) => {
    if (!confirm('Are you sure you want to unregister this device?')) return;

    try {
      const response = await fetch(`${API_URL}/api/registered-devices/${serial}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        alert('Device unregistered successfully!');
        fetchDevices();
      } else {
        const data = await response.json();
        alert(`Failed to unregister device: ${data.detail || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Failed to unregister device:', error);
      alert(`Error unregistering device: ${error.message}`);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Never';
    return new Date(dateString).toLocaleString();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="registered-nodes-page">
      <div className="devices-header">
        <div>
          <h1>Registered Node Devices</h1>
          <p className="subtitle">Track and manage all registered devices</p>
        </div>
        <button onClick={fetchDevices} className="refresh-btn" title="Refresh device list">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 12.5a10 10 0 0 1-18.8 4.2"/>
          </svg>
          Refresh
        </button>
      </div>

      {devices.length === 0 ? (
        <p className="no-devices">No registered devices. Connect a device via USB and register it from the Devices page.</p>
      ) : (
        <div className="device-list">
          <table>
            <thead>
              <tr>
                <th>Status</th>
                <th>Name</th>
                <th>Serial</th>
                <th>Model</th>
                <th>Manufacturer</th>
                <th>Connection</th>
                <th>WiFi MAC</th>
                <th>Last Seen</th>
                <th>Registered</th>
                <th>Notes</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {devices.map((device) => (
                <tr key={device.id}>
                  <td>
                    {device.wifi_connected ? (
                      <span className="connection-status connected">
                        WiFi Connected
                      </span>
                    ) : device.is_connected ? (
                      <span className="connection-status connected">
                        Connected
                      </span>
                    ) : (
                      <span className="connection-status disconnected">
                        Disconnected
                      </span>
                    )}
                  </td>
                  <td>
                    {editingDevice === device.serial ? (
                      <input
                        type="text"
                        value={editForm.name}
                        onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                        className="edit-input"
                        placeholder="Device name"
                      />
                    ) : (
                      <strong>{device.name || device.serial}</strong>
                    )}
                  </td>
                  <td className="serial-cell">{device.serial}</td>
                  <td>{device.model || 'N/A'}</td>
                  <td>{device.manufacturer || 'N/A'}</td>
                  <td>
                    {device.is_connected ? (
                      device.connection_type === 'wifi' ? (
                        <span style={{ color: '#3b82f6', fontWeight: '500' }}>WiFi: {device.wifi_ip || 'N/A'}</span>
                      ) : device.usb_bus && device.usb_device ? (
                        <span style={{ color: '#10b981', fontWeight: '500' }}>USB: {device.usb_bus}-{device.usb_device}</span>
                      ) : (
                        <span style={{ color: '#10b981', fontWeight: '500' }}>Connected</span>
                      )
                    ) : (
                      <span style={{ color: '#6b7280' }}>N/A</span>
                    )}
                  </td>
                  <td className="serial-cell" style={{ fontFamily: 'monospace', fontSize: '13px' }}>
                    {device.wifi_mac || '-'}
                  </td>
                  <td>{formatDate(device.last_seen_at)}</td>
                  <td>{formatDate(device.registered_at)}</td>
                  <td>
                    {editingDevice === device.serial ? (
                      <textarea
                        value={editForm.notes}
                        onChange={(e) => setEditForm({ ...editForm, notes: e.target.value })}
                        className="edit-textarea"
                        rows="2"
                        placeholder="Add notes..."
                      />
                    ) : (
                      <span className="notes-cell">{device.notes || '-'}</span>
                    )}
                  </td>
                  <td>
                    <div className="action-buttons">
                      {editingDevice === device.serial ? (
                        <>
                          <button onClick={() => handleSave(device.serial)} className="btn-save">
                            Save
                          </button>
                          <button onClick={() => setEditingDevice(null)} className="btn-cancel">
                            Cancel
                          </button>
                        </>
                      ) : (
                        <>
                          <button onClick={() => handleEdit(device)} className="btn-edit">
                            Edit
                          </button>
                          <button onClick={() => handleUnregister(device.serial)} className="btn-delete">
                            Unregister
                          </button>
                        </>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
