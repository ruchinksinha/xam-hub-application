import { useState, useEffect } from 'react';

const API_URL = 'http://localhost:8000';

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
        fetchDevices();
      }
    } catch (error) {
      console.error('Failed to unregister device:', error);
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
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-slate-800 mb-2">Registered Node Devices</h1>
          <p className="text-slate-600">Track and manage all registered devices</p>
        </div>

        {devices.length === 0 ? (
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-12 text-center">
            <div className="text-slate-400 mb-4">
              <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z" />
              </svg>
            </div>
            <h3 className="text-xl font-semibold text-slate-800 mb-2">No Registered Devices</h3>
            <p className="text-slate-600">Connect a device via USB and register it from the Devices page</p>
          </div>
        ) : (
          <div className="grid gap-4">
            {devices.map((device) => (
              <div
                key={device.id}
                className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 hover:shadow-md transition-shadow"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-3">
                      <div className={`w-3 h-3 rounded-full ${device.is_connected ? 'bg-green-500' : 'bg-red-500'}`}></div>
                      {editingDevice === device.serial ? (
                        <input
                          type="text"
                          value={editForm.name}
                          onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                          className="text-xl font-semibold text-slate-800 border-b-2 border-blue-500 outline-none px-2 py-1"
                          placeholder="Device name"
                        />
                      ) : (
                        <h3 className="text-xl font-semibold text-slate-800">{device.name || device.serial}</h3>
                      )}
                      <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                        device.is_connected
                          ? 'bg-green-100 text-green-700'
                          : 'bg-red-100 text-red-700'
                      }`}>
                        {device.is_connected ? 'Connected' : 'Disconnected'}
                      </span>
                    </div>

                    <div className="grid grid-cols-2 gap-4 text-sm mb-4">
                      <div>
                        <span className="text-slate-500">Serial:</span>
                        <p className="font-mono text-slate-800">{device.serial}</p>
                      </div>
                      <div>
                        <span className="text-slate-500">Model:</span>
                        <p className="text-slate-800">{device.model || 'N/A'}</p>
                      </div>
                      <div>
                        <span className="text-slate-500">Manufacturer:</span>
                        <p className="text-slate-800">{device.manufacturer || 'N/A'}</p>
                      </div>
                      <div>
                        <span className="text-slate-500">Last Seen:</span>
                        <p className="text-slate-800">{formatDate(device.last_seen_at)}</p>
                      </div>
                      <div>
                        <span className="text-slate-500">Registered:</span>
                        <p className="text-slate-800">{formatDate(device.registered_at)}</p>
                      </div>
                      {device.is_connected && device.usb_bus && device.usb_device && (
                        <div>
                          <span className="text-slate-500">USB:</span>
                          <p className="text-slate-800 font-mono">{device.usb_bus}-{device.usb_device}</p>
                        </div>
                      )}
                    </div>

                    <div>
                      <span className="text-slate-500 text-sm">Notes:</span>
                      {editingDevice === device.serial ? (
                        <textarea
                          value={editForm.notes}
                          onChange={(e) => setEditForm({ ...editForm, notes: e.target.value })}
                          className="w-full mt-1 p-2 border border-slate-300 rounded-lg outline-none focus:border-blue-500"
                          rows="2"
                          placeholder="Add notes about this device..."
                        />
                      ) : (
                        <p className="text-slate-700 mt-1">{device.notes || 'No notes'}</p>
                      )}
                    </div>
                  </div>

                  <div className="flex gap-2 ml-4">
                    {editingDevice === device.serial ? (
                      <>
                        <button
                          onClick={() => handleSave(device.serial)}
                          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                        >
                          Save
                        </button>
                        <button
                          onClick={() => setEditingDevice(null)}
                          className="px-4 py-2 bg-slate-300 text-slate-700 rounded-lg hover:bg-slate-400 transition-colors"
                        >
                          Cancel
                        </button>
                      </>
                    ) : (
                      <>
                        <button
                          onClick={() => handleEdit(device)}
                          className="px-4 py-2 bg-slate-100 text-slate-700 rounded-lg hover:bg-slate-200 transition-colors"
                        >
                          Edit
                        </button>
                        <button
                          onClick={() => handleUnregister(device.serial)}
                          className="px-4 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition-colors"
                        >
                          Unregister
                        </button>
                      </>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
