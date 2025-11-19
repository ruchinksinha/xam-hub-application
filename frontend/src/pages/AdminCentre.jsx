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
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

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

  useEffect(() => {
    fetchHotspotStatus();
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
