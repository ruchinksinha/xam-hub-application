import { useState, useEffect } from 'react';

const API_URL = 'http://localhost';

export default function WifiHotspotTab() {
  const [hotspotStatus, setHotspotStatus] = useState({
    active: false,
    aps: []
  });
  const [config, setConfig] = useState({
    ssid: '',
    password: '',
    interface: '',
    auto_start: true
  });
  const [availableInterfaces, setAvailableInterfaces] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showConfig, setShowConfig] = useState(false);
  const [wifiClients, setWifiClients] = useState([]);

  const fetchHotspotStatus = async () => {
    try {
      const [statusRes, clientsRes] = await Promise.all([
        fetch(`${API_URL}/api/admin/hotspot-status`),
        fetch(`${API_URL}/api/admin/wifi-clients`)
      ]);
      const statusData = await statusRes.json();
      const clientsData = await clientsRes.json();

      setHotspotStatus(statusData);
      setWifiClients(clientsData.clients || []);
      setError(null);
    } catch (error) {
      console.error('Failed to fetch hotspot status:', error);
      setError('Failed to fetch hotspot status');
    } finally {
      setLoading(false);
    }
  };

  const fetchConfig = async () => {
    try {
      const [configRes, interfacesRes] = await Promise.all([
        fetch(`${API_URL}/api/admin/hotspot-config`),
        fetch(`${API_URL}/api/admin/available-interfaces`)
      ]);
      const configData = await configRes.json();
      const interfacesData = await interfacesRes.json();
      setConfig(configData);
      setAvailableInterfaces(interfacesData.interfaces || []);
    } catch (error) {
      console.error('Failed to fetch config:', error);
    }
  };

  const handleDisconnectClient = async (ipAddress) => {
    if (!confirm(`Are you sure you want to disconnect the device at ${ipAddress}?`)) {
      return
    }

    try {
      const response = await fetch(`${API_URL}/api/admin/wifi-clients/${ipAddress}`, {
        method: 'DELETE'
      })

      if (response.ok) {
        alert('Device disconnected successfully')
        fetchHotspotStatus()
      } else {
        const data = await response.json()
        alert(`Failed to disconnect device: ${data.detail || 'Unknown error'}`)
      }
    } catch (err) {
      alert(`Error disconnecting device: ${err.message}`)
    }
  };

  useEffect(() => {
    fetchHotspotStatus();
    fetchConfig();
    const interval = setInterval(fetchHotspotStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleUpdateConfig = async () => {
    try {
      const response = await fetch(`${API_URL}/api/admin/hotspot-config`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
      });

      const data = await response.json();

      if (response.ok) {
        alert('Configuration updated successfully');
        setShowConfig(false);
        fetchConfig();
      } else {
        const errorMsg = data.detail || data.error || 'Failed to update configuration';
        alert(errorMsg);
      }
    } catch (error) {
      console.error('Failed to update config:', error);
      alert(`Error: Could not update configuration. ${error.message}`);
    }
  };

  if (loading) {
    return (
      <div style={{ padding: '24px', textAlign: 'center', color: '#6b7280' }}>
        <p>Loading...</p>
      </div>
    );
  }

  return (
    <div className="tab-content">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <h2 style={{ fontSize: '20px', fontWeight: '600', color: '#1f2937', margin: 0 }}>WiFi Hotspot Management</h2>
          <p style={{ color: '#6b7280', fontSize: '14px', marginTop: '4px' }}>Configure and monitor WiFi hotspot settings</p>
        </div>
        <button onClick={fetchHotspotStatus} className="refresh-btn" title="Refresh status">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 12.5a10 10 0 0 1-18.8 4.2"/>
          </svg>
          Refresh
        </button>
      </div>

      {error && (
        <div className="error-message">
          <strong>Error:</strong>
          <pre>{error}</pre>
        </div>
      )}

      {showConfig && (
        <div className="admin-card config-card" style={{ marginBottom: '24px' }}>
          <div className="card-header">
            <h2>Hotspot Configuration</h2>
          </div>
          <div className="card-content">
            <div className="config-form">
              <div className="form-group">
                <label>SSID (Network Name):</label>
                <input
                  type="text"
                  value={config.ssid}
                  onChange={(e) => setConfig({ ...config, ssid: e.target.value })}
                  className="form-input"
                />
              </div>
              <div className="form-group">
                <label>Password:</label>
                <input
                  type="text"
                  value={config.password}
                  onChange={(e) => setConfig({ ...config, password: e.target.value })}
                  className="form-input"
                  placeholder="Minimum 8 characters"
                />
              </div>
              <div className="form-group">
                <label>WiFi Interface:</label>
                <select
                  value={config.interface}
                  onChange={(e) => setConfig({ ...config, interface: e.target.value })}
                  className="form-input"
                >
                  {availableInterfaces.map(iface => (
                    <option key={iface} value={iface}>{iface}</option>
                  ))}
                </select>
              </div>
              <div className="form-group" style={{
                background: '#fef3c7',
                padding: '12px',
                borderRadius: '6px',
                border: '1px solid #fbbf24'
              }}>
                <p style={{ color: '#92400e', fontSize: '14px', margin: 0 }}>
                  <strong>Note:</strong> Hotspot is managed externally via manual scripts.
                  Start/stop operations should be performed using your script.
                </p>
              </div>
              <div style={{ display: 'flex', gap: '12px', marginTop: '16px' }}>
                <button onClick={handleUpdateConfig} className="btn-primary">
                  Save Configuration
                </button>
                <button onClick={() => setShowConfig(false)} className="btn-cancel">
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="admin-cards">
        <div className="admin-card hotspot-card">
          <div className="card-header">
            <h2>WiFi Hotspot</h2>
            <span className={`status-badge ${hotspotStatus.active ? 'active' : 'inactive'}`}>
              {hotspotStatus.active ? `Active (${hotspotStatus.aps?.length || 0})` : 'Inactive'}
            </span>
          </div>

          <div className="card-content">
            {hotspotStatus.active && hotspotStatus.aps && hotspotStatus.aps.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                {hotspotStatus.aps.map((ap, index) => (
                  <div key={index} style={{
                    padding: '16px',
                    backgroundColor: '#f9fafb',
                    borderRadius: '8px',
                    border: '1px solid #e5e7eb'
                  }}>
                    <h3 style={{
                      margin: '0 0 12px 0',
                      fontSize: '16px',
                      fontWeight: '600',
                      color: '#111827'
                    }}>
                      Hotspot {index + 1}
                    </h3>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                      <div className="info-item" style={{ width: '100%' }}>
                        <span className="label">SSID:</span>
                        <span className="value" style={{
                          wordBreak: 'break-all',
                          display: 'block',
                          marginTop: '4px'
                        }}>{ap.ssid || 'N/A'}</span>
                      </div>

                      <div style={{
                        display: 'grid',
                        gridTemplateColumns: 'repeat(3, 1fr)',
                        gap: '12px'
                      }}>
                        <div className="info-item">
                          <span className="label">Interface:</span>
                          <span className="value">{ap.interface || 'N/A'}</span>
                        </div>
                        <div className="info-item">
                          <span className="label">Gateway IP:</span>
                          <span className="value">{ap.ip_address || 'N/A'}</span>
                        </div>
                        <div className="info-item">
                          <span className="label">Connected:</span>
                          <span className="value">{ap.connected_devices || 0}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <>
                <p className="status-message">WiFi hotspot is currently inactive</p>
                <p style={{ color: '#6b7280', fontSize: '14px', marginTop: '8px' }}>
                  Hotspot is managed externally via manual scripts
                </p>
              </>
            )}
          </div>
        </div>

        <div className="admin-card system-info-card">
          <div className="card-header">
            <h2>System Information</h2>
          </div>
          <div className="card-content">
            <div className="info-grid">
              <div className="info-item">
                <span className="label">Server Status:</span>
                <span className="value status-online">Online</span>
              </div>
              <div className="info-item">
                <span className="label">Application:</span>
                <span className="value">Device Flashing Hub</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {hotspotStatus.active && wifiClients.length > 0 && (
        <div className="admin-card wifi-clients-card" style={{ marginTop: '24px' }}>
          <div className="card-header">
            <h2>Connected WiFi Clients</h2>
            <span className="status-badge active">{wifiClients.length} Device{wifiClients.length !== 1 ? 's' : ''}</span>
          </div>
          <div className="card-content">
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: '2px solid #e5e7eb', textAlign: 'left' }}>
                  <th style={{ padding: '12px', fontWeight: '600', color: '#374151' }}>Device Name</th>
                  <th style={{ padding: '12px', fontWeight: '600', color: '#374151' }}>Serial / Hostname</th>
                  <th style={{ padding: '12px', fontWeight: '600', color: '#374151' }}>IP Address</th>
                  <th style={{ padding: '12px', fontWeight: '600', color: '#374151' }}>MAC Address</th>
                  <th style={{ padding: '12px', fontWeight: '600', color: '#374151' }}>ADB Status</th>
                  <th style={{ padding: '12px', fontWeight: '600', color: '#374151' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {wifiClients.map((client, index) => (
                  <tr key={index} style={{ borderBottom: '1px solid #f3f4f6' }}>
                    <td style={{ padding: '12px', color: '#1f2937', fontWeight: '500' }}>
                      {client.registered_device ? (
                        <span>{client.registered_device.name}</span>
                      ) : (
                        <span style={{ color: '#9ca3af', fontStyle: 'italic' }}>Unregistered</span>
                      )}
                    </td>
                    <td style={{ padding: '12px', color: '#1f2937', fontFamily: 'monospace', fontSize: '13px' }}>
                      {client.serial || client.hostname || 'Unknown'}
                    </td>
                    <td style={{ padding: '12px', color: '#1f2937', fontFamily: 'monospace' }}>{client.ip_address}</td>
                    <td style={{ padding: '12px', color: '#6b7280', fontFamily: 'monospace', fontSize: '13px' }}>{client.mac_address}</td>
                    <td style={{ padding: '12px' }}>
                      {client.adb_connected ? (
                        <span style={{ color: '#10b981', fontWeight: '500' }}>Connected</span>
                      ) : (
                        <span style={{ color: '#f59e0b', fontWeight: '500' }}>Not Connected</span>
                      )}
                    </td>
                    <td style={{ padding: '12px' }}>
                      <button
                        onClick={() => handleDisconnectClient(client.ip_address)}
                        style={{
                          padding: '6px 12px',
                          backgroundColor: '#ef4444',
                          color: 'white',
                          border: 'none',
                          borderRadius: '4px',
                          cursor: 'pointer',
                          fontSize: '12px',
                          fontWeight: '500',
                          transition: 'background-color 0.2s'
                        }}
                        onMouseOver={(e) => e.target.style.backgroundColor = '#dc2626'}
                        onMouseOut={(e) => e.target.style.backgroundColor = '#ef4444'}
                      >
                        Disconnect
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
