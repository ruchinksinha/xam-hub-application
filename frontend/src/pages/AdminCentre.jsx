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

  const fetchHotspotStatus = async () => {
    try {
      const response = await fetch(`${API_URL}/api/admin/hotspot-status`);
      const data = await response.json();
      setHotspotStatus(data);
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
    </div>
  );
}
