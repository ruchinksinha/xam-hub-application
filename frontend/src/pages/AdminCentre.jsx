import { useState, useEffect } from 'react';

const API_URL = 'http://localhost';

export default function AdminCentre() {
  const [hotspotStatus, setHotspotStatus] = useState({
    active: false,
    ssid: '',
    interface: '',
    ip_address: '',
    connected_devices: 0
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
  const [showDiagnostics, setShowDiagnostics] = useState(false);
  const [diagnostics, setDiagnostics] = useState(null);

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

  const handleToggleHotspot = async (action) => {
    try {
      const response = await fetch(`${API_URL}/api/admin/hotspot/${action}`, {
        method: 'POST'
      });

      const data = await response.json();

      if (response.ok) {
        fetchHotspotStatus();
        setError(null);
      } else {
        const errorMsg = data.detail || data.error || `Failed to ${action} hotspot`;
        setError(errorMsg);
        alert(errorMsg);
      }
    } catch (error) {
      console.error(`Failed to ${action} hotspot:`, error);
      const errorMsg = `Error: Could not ${action} hotspot. ${error.message}`;
      setError(errorMsg);
      alert(errorMsg);
    }
  };

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

  const fetchDiagnostics = async () => {
    try {
      const response = await fetch(`${API_URL}/api/admin/diagnostics`);
      const data = await response.json();
      setDiagnostics(data);
    } catch (error) {
      console.error('Failed to fetch diagnostics:', error);
      setError('Failed to fetch diagnostics');
    }
  };

  if (loading) {
    return (
      <div className="admin-centre-page">
        <p>Loading...</p>
      </div>
    );
  }

  return (
    <div className="admin-centre-page">
      <div className="devices-header">
        <div>
          <h1>Admin Centre</h1>
          <p className="subtitle">Manage server settings and WiFi hotspot</p>
        </div>
        <div style={{ display: 'flex', gap: '12px' }}>
          <button onClick={() => setShowConfig(!showConfig)} className="refresh-btn">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 15a3 3 0 100-6 3 3 0 000 6z"/>
              <path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-2 2 2 2 0 01-2-2v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83 0 2 2 0 010-2.83l.06-.06a1.65 1.65 0 00.33-1.82 1.65 1.65 0 00-1.51-1H3a2 2 0 01-2-2 2 2 0 012-2h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 010-2.83 2 2 0 012.83 0l.06.06a1.65 1.65 0 001.82.33H9a1.65 1.65 0 001-1.51V3a2 2 0 012-2 2 2 0 012 2v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 0 2 2 0 010 2.83l-.06.06a1.65 1.65 0 00-.33 1.82V9a1.65 1.65 0 001.51 1H21a2 2 0 012 2 2 2 0 01-2 2h-.09a1.65 1.65 0 00-1.51 1z"/>
            </svg>
            Configure
          </button>
          <button onClick={() => {
            setShowDiagnostics(!showDiagnostics);
            if (!showDiagnostics) fetchDiagnostics();
          }} className="refresh-btn" style={{ background: showDiagnostics ? '#3b82f6' : '' }}>
            Diagnostics
          </button>
          <button onClick={fetchHotspotStatus} className="refresh-btn" title="Refresh status">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 12.5a10 10 0 0 1-18.8 4.2"/>
            </svg>
            Refresh
          </button>
        </div>
      </div>

      {error && (
        <div className="error-message">
          <strong>Error:</strong>
          <pre>{error}</pre>
        </div>
      )}

      {showConfig && (
        <div className="admin-card config-card">
          <div className="card-header">
            <h2>Hotspot Configuration</h2>
          </div>
          <div className="card-content">
            {hotspotStatus.active && config.ssid !== hotspotStatus.ssid && (
              <div className="warning-message" style={{
                background: '#fef3c7',
                color: '#92400e',
                padding: '12px',
                borderRadius: '6px',
                marginBottom: '16px',
                border: '1px solid #fbbf24'
              }}>
                <strong>Note:</strong> Configuration changes require restarting the hotspot to take effect.
                Current active SSID: <strong>{hotspotStatus.ssid}</strong>
              </div>
            )}
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
              <div className="form-group">
                <label style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <input
                    type="checkbox"
                    checked={config.auto_start}
                    onChange={(e) => setConfig({ ...config, auto_start: e.target.checked })}
                  />
                  Auto-start hotspot on server startup
                </label>
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
              {hotspotStatus.active ? 'Active' : 'Inactive'}
            </span>
          </div>

          <div className="card-content">
            {hotspotStatus.active ? (
              <>
                <div className="info-grid">
                  <div className="info-item">
                    <span className="label">SSID:</span>
                    <span className="value">{hotspotStatus.ssid || 'N/A'}</span>
                  </div>
                  <div className="info-item">
                    <span className="label">Interface:</span>
                    <span className="value">{hotspotStatus.interface || 'N/A'}</span>
                  </div>
                  <div className="info-item">
                    <span className="label">IP Address:</span>
                    <span className="value">{hotspotStatus.ip_address || 'N/A'}</span>
                  </div>
                  <div className="info-item">
                    <span className="label">Connected Devices:</span>
                    <span className="value">{hotspotStatus.connected_devices || 0}</span>
                  </div>
                </div>

                <button
                  onClick={() => handleToggleHotspot('stop')}
                  className="btn-danger"
                >
                  Stop Hotspot
                </button>
              </>
            ) : (
              <>
                <p className="status-message">WiFi hotspot is currently inactive</p>
                <button
                  onClick={() => handleToggleHotspot('start')}
                  className="btn-primary"
                >
                  Start Hotspot
                </button>
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

      {showDiagnostics && diagnostics && (
        <div className="admin-card diagnostics-card" style={{ marginTop: '24px' }}>
          <div className="card-header">
            <h2>WiFi Diagnostics</h2>
          </div>
          <div className="card-content">
            <div style={{ fontSize: '13px', fontFamily: 'monospace', background: '#1f2937', color: '#f3f4f6', padding: '16px', borderRadius: '6px', overflow: 'auto', maxHeight: '400px' }}>
              <div style={{ marginBottom: '16px' }}>
                <strong style={{ color: '#60a5fa' }}>NetworkManager Status:</strong> {diagnostics.networkmanager_status}
              </div>
              <div style={{ marginBottom: '16px' }}>
                <strong style={{ color: '#60a5fa' }}>AP Mode Supported:</strong> {diagnostics.ap_mode_supported ? 'Yes' : 'No'}
              </div>
              <div style={{ marginBottom: '16px' }}>
                <strong style={{ color: '#60a5fa' }}>All Connections:</strong>
                <pre style={{ whiteSpace: 'pre-wrap', marginTop: '8px' }}>{diagnostics.all_connections}</pre>
              </div>
              <div style={{ marginBottom: '16px' }}>
                <strong style={{ color: '#60a5fa' }}>Interface Info:</strong>
                <pre style={{ whiteSpace: 'pre-wrap', marginTop: '8px' }}>{diagnostics.interface_info}</pre>
              </div>
              <div>
                <strong style={{ color: '#60a5fa' }}>Rfkill Status:</strong>
                <pre style={{ whiteSpace: 'pre-wrap', marginTop: '8px' }}>{diagnostics.rfkill_status}</pre>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
