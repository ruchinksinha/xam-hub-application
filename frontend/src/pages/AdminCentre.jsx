import { useState } from 'react';
import WifiHotspotTab from '../components/WifiHotspotTab';
import ProfilePublishTab from '../components/ProfilePublishTab';

export default function AdminCentre() {
  const [activeTab, setActiveTab] = useState('wifi-hotspot');

  const tabs = [
    { id: 'wifi-hotspot', label: 'WiFi Hotspot', icon: '📡' },
    { id: 'profile-publish', label: 'Profile Publish', icon: '📋' }
  ];

  return (
    <div className="admin-centre-page">
      <div className="devices-header">
        <div>
          <h1>Admin Centre</h1>
          <p className="subtitle">Manage server settings and configurations</p>
        </div>
      </div>

      <div className="tabs-container">
        <div className="tabs-header">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              className={`tab-button ${activeTab === tab.id ? 'active' : ''}`}
              onClick={() => setActiveTab(tab.id)}
            >
              <span className="tab-icon">{tab.icon}</span>
              <span className="tab-label">{tab.label}</span>
            </button>
          ))}
        </div>

        <div className="tabs-content">
          {activeTab === 'wifi-hotspot' && <WifiHotspotTab />}
          {activeTab === 'profile-publish' && <ProfilePublishTab />}
        </div>
      </div>
    </div>
  );
}
