import { useState, useEffect } from 'react';

const API_URL = 'http://localhost';

export default function ProfilePublishTab() {
  const [formData, setFormData] = useState({
    ssid: '',
    nodeapp_apk_path: ''
  });
  const [savedMetadata, setSavedMetadata] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState('');
  const [mtpMap, setMtpMap] = useState({});
  const [scanningMtp, setScanningMtp] = useState(false);
  const [mtpMessage, setMtpMessage] = useState('');

  useEffect(() => {
    fetchMetadata();
    fetchMtpMap();
  }, []);

  const fetchMetadata = async () => {
    try {
      const response = await fetch(`${API_URL}/api/admin/exam-metadata`);
      if (response.ok) {
        const data = await response.json();
        setSavedMetadata(data);
        if (data.metadata) {
          setFormData({
            ssid: data.metadata.ssid || '',
            nodeapp_apk_path: data.metadata.nodeapp_apk_path || ''
          });
        }
        setError(null);
      } else if (response.status === 404) {
        setSavedMetadata(null);
      } else {
        setError('Failed to load metadata');
      }
    } catch (err) {
      console.error('Failed to fetch metadata:', err);
      setError('Failed to connect to server');
    } finally {
      setLoading(false);
    }
  };

  const fetchMtpMap = async () => {
    try {
      const response = await fetch(`${API_URL}/api/devices/mtp-map`);
      if (response.ok) {
        const data = await response.json();
        setMtpMap(data.map || {});
      }
    } catch (err) {
      console.error('Failed to fetch MTP map:', err);
    }
  };

  const handleScanMtp = async () => {
    setScanningMtp(true);
    setMtpMessage('');

    try {
      const response = await fetch(`${API_URL}/api/devices/mtp-map/scan`, {
        method: 'POST'
      });

      if (response.ok) {
        const data = await response.json();
        setMtpMap(data.map || {});
        setMtpMessage(`Successfully scanned ${data.message}`);
        setTimeout(() => setMtpMessage(''), 5000);
      } else {
        const data = await response.json();
        setMtpMessage(`Error: ${data.detail || 'Failed to scan MTP devices'}`);
      }
    } catch (err) {
      console.error('Failed to scan MTP devices:', err);
      setMtpMessage('Error: Failed to connect to server');
    } finally {
      setScanningMtp(false);
    }
  };

  const handleSave = async () => {
    if (!formData.ssid.trim() || !formData.nodeapp_apk_path.trim()) {
      setError('All fields are required');
      return;
    }

    setSaving(true);
    setError(null);
    setSuccessMessage('');

    try {
      const response = await fetch(`${API_URL}/api/admin/exam-metadata`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });

      if (response.ok) {
        const data = await response.json();
        setSavedMetadata(data);
        setSuccessMessage('Profile published successfully!');
        setTimeout(() => setSuccessMessage(''), 3000);
      } else {
        const data = await response.json();
        setError(data.detail || 'Failed to save metadata');
      }
    } catch (err) {
      console.error('Failed to save metadata:', err);
      setError('Failed to connect to server');
    } finally {
      setSaving(false);
    }
  };

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return 'N/A';
    const date = new Date(timestamp);
    return date.toLocaleString();
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
      <div style={{ marginBottom: '24px' }}>
        <h2 style={{ fontSize: '20px', fontWeight: '600', color: '#1f2937', margin: 0 }}>Profile Publish</h2>
        <p style={{ color: '#6b7280', fontSize: '14px', marginTop: '4px' }}>Configure and publish exam metadata</p>
      </div>

      {error && (
        <div className="error-message" style={{ marginBottom: '20px' }}>
          <strong>Error:</strong> {error}
        </div>
      )}

      {successMessage && (
        <div style={{
          background: '#d1fae5',
          border: '1px solid #6ee7b7',
          borderRadius: '8px',
          padding: '16px',
          marginBottom: '20px',
          color: '#065f46'
        }}>
          <strong>Success:</strong> {successMessage}
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '32px', marginBottom: '32px' }}>
        <div className="admin-card" style={{ margin: 0 }}>
          <div className="card-header">
            <h2>Configuration</h2>
          </div>
          <div className="card-content">
            <div className="config-form">
              <div className="form-group">
                <label>SSID:</label>
                <input
                  type="text"
                  value={formData.ssid}
                  onChange={(e) => setFormData({ ...formData, ssid: e.target.value })}
                  className="form-input"
                  placeholder="Enter WiFi SSID"
                />
              </div>

              <div className="form-group">
                <label>Node App APK Path:</label>
                <input
                  type="text"
                  value={formData.nodeapp_apk_path}
                  onChange={(e) => setFormData({ ...formData, nodeapp_apk_path: e.target.value })}
                  className="form-input"
                  placeholder="Enter APK path"
                />
              </div>

              <div style={{ marginTop: '24px' }}>
                <button
                  onClick={handleSave}
                  disabled={saving}
                  className="btn-primary"
                  style={{ width: '100%' }}
                >
                  {saving ? 'Publishing...' : 'Publish Profile'}
                </button>
              </div>
            </div>
          </div>
        </div>

        <div className="admin-card" style={{ margin: 0 }}>
          <div className="card-header">
            <h2>Published Metadata</h2>
          </div>
          <div className="card-content">
            {savedMetadata ? (
              <>
                <div style={{ marginBottom: '16px' }}>
                  <div className="info-item">
                    <span className="label">File:</span>
                    <span className="value" style={{ fontFamily: 'monospace', fontSize: '14px' }}>
                      exam_metadata.json
                    </span>
                  </div>
                </div>

                <div style={{ marginBottom: '16px' }}>
                  <div className="info-item">
                    <span className="label">Last Updated:</span>
                    <span className="value" style={{ fontSize: '14px' }}>
                      {formatTimestamp(savedMetadata.timestamp)}
                    </span>
                  </div>
                </div>

                <div style={{ marginTop: '24px' }}>
                  <h4 style={{ fontSize: '14px', fontWeight: '600', color: '#374151', marginBottom: '12px' }}>
                    JSON Content:
                  </h4>
                  <div style={{
                    background: '#1f2937',
                    color: '#f3f4f6',
                    padding: '16px',
                    borderRadius: '8px',
                    fontFamily: 'monospace',
                    fontSize: '13px',
                    overflow: 'auto',
                    maxHeight: '300px'
                  }}>
                    <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                      {JSON.stringify(savedMetadata.metadata, null, 2)}
                    </pre>
                  </div>
                </div>
              </>
            ) : (
              <div style={{
                textAlign: 'center',
                padding: '32px',
                color: '#9ca3af',
                background: '#f9fafb',
                borderRadius: '8px'
              }}>
                <p style={{ margin: 0, fontSize: '14px' }}>No metadata published yet</p>
                <p style={{ margin: '8px 0 0 0', fontSize: '13px' }}>Fill in the configuration and click "Publish Profile"</p>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="admin-card">
        <div className="card-header">
          <h2>MTP Device Map</h2>
        </div>
        <div className="card-content">
          <p style={{ color: '#6b7280', fontSize: '14px', marginBottom: '16px' }}>
            Create a USB Serial to MTP Index mapping to enable profile push functionality. This map will be automatically cleared when any device is disconnected.
          </p>

          {mtpMessage && (
            <div style={{
              background: mtpMessage.includes('Error') ? '#fee2e2' : '#d1fae5',
              border: `1px solid ${mtpMessage.includes('Error') ? '#fca5a5' : '#6ee7b7'}`,
              borderRadius: '8px',
              padding: '12px',
              marginBottom: '16px',
              color: mtpMessage.includes('Error') ? '#991b1b' : '#065f46',
              fontSize: '14px'
            }}>
              {mtpMessage}
            </div>
          )}

          <button
            onClick={handleScanMtp}
            disabled={scanningMtp}
            className="btn-primary"
            style={{ marginBottom: '20px' }}
          >
            {scanningMtp ? 'Scanning MTP Devices...' : 'Scan MTP Devices'}
          </button>

          {Object.keys(mtpMap).length > 0 ? (
            <div>
              <h4 style={{ fontSize: '14px', fontWeight: '600', color: '#374151', marginBottom: '12px' }}>
                Detected Devices ({Object.keys(mtpMap).length}):
              </h4>
              <div style={{
                background: '#f9fafb',
                borderRadius: '8px',
                overflow: 'hidden',
                border: '1px solid #e5e7eb'
              }}>
                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                  <thead>
                    <tr style={{ background: '#f3f4f6', borderBottom: '1px solid #e5e7eb' }}>
                      <th style={{ padding: '12px', textAlign: 'left', fontSize: '13px', fontWeight: '600', color: '#374151' }}>
                        Serial Number
                      </th>
                      <th style={{ padding: '12px', textAlign: 'left', fontSize: '13px', fontWeight: '600', color: '#374151' }}>
                        MTP Index
                      </th>
                      <th style={{ padding: '12px', textAlign: 'left', fontSize: '13px', fontWeight: '600', color: '#374151' }}>
                        Device Info
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(mtpMap).map(([serial, info]) => (
                      <tr key={serial} style={{ borderBottom: '1px solid #e5e7eb' }}>
                        <td style={{ padding: '12px', fontSize: '13px', fontFamily: 'monospace', color: '#1f2937' }}>
                          {serial}
                        </td>
                        <td style={{ padding: '12px', fontSize: '13px', fontFamily: 'monospace', color: '#059669' }}>
                          {info.mtp_index}
                        </td>
                        <td style={{ padding: '12px', fontSize: '13px', color: '#6b7280' }}>
                          {info.device_info}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : (
            <div style={{
              textAlign: 'center',
              padding: '32px',
              color: '#9ca3af',
              background: '#f9fafb',
              borderRadius: '8px',
              border: '1px solid #e5e7eb'
            }}>
              <p style={{ margin: 0, fontSize: '14px' }}>No MTP devices mapped</p>
              <p style={{ margin: '8px 0 0 0', fontSize: '13px' }}>Click "Scan MTP Devices" to create the mapping</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
