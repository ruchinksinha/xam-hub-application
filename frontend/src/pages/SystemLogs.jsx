import { useState, useEffect, useRef } from 'react';

const API_URL = 'http://localhost';

export default function SystemLogs() {
  const [logs, setLogs] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [autoScroll, setAutoScroll] = useState(true);
  const [filterType, setFilterType] = useState('all');
  const [isPaused, setIsPaused] = useState(false);
  const logsEndRef = useRef(null);

  const fetchLogs = async () => {
    if (isPaused) return;

    try {
      const typeParam = filterType !== 'all' ? `&log_type=${filterType}` : '';
      const [logsRes, statsRes] = await Promise.all([
        fetch(`${API_URL}/api/logs/list?limit=200${typeParam}`),
        fetch(`${API_URL}/api/logs/stats`)
      ]);

      const logsData = await logsRes.json();
      const statsData = await statsRes.json();

      setLogs(logsData.logs || []);
      setStats(statsData);
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch logs:', error);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
    const interval = setInterval(fetchLogs, 2000);
    return () => clearInterval(interval);
  }, [filterType, isPaused]);

  useEffect(() => {
    if (autoScroll && logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, autoScroll]);

  const handleClearLogs = async () => {
    if (!confirm('Are you sure you want to clear all logs?')) return;

    try {
      const response = await fetch(`${API_URL}/api/logs/clear`, {
        method: 'DELETE'
      });

      if (response.ok) {
        setLogs([]);
        setStats(null);
        alert('Logs cleared successfully');
      }
    } catch (error) {
      alert('Failed to clear logs: ' + error.message);
    }
  };

  const getLogColor = (type) => {
    switch (type) {
      case 'request': return '#3b82f6';
      case 'response': return '#10b981';
      case 'error': return '#ef4444';
      default: return '#6b7280';
    }
  };

  const getLogIcon = (type) => {
    switch (type) {
      case 'request':
        return (
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M17 8l-5-5-5 5M12 3v12"/>
          </svg>
        );
      case 'response':
        return (
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M3 9v6a2 2 0 002 2h14a2 2 0 002-2V9M7 16l5 5 5-5M12 21V9"/>
          </svg>
        );
      case 'error':
        return (
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="8" x2="12" y2="12"/>
            <line x1="12" y1="16" x2="12.01" y2="16"/>
          </svg>
        );
      default:
        return null;
    }
  };

  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      fractionalSecondDigits: 3
    });
  };

  if (loading) {
    return (
      <div className="devices-page">
        <p>Loading logs...</p>
      </div>
    );
  }

  return (
    <div className="devices-page">
      <div className="devices-header">
        <div>
          <h1>Exam Data API Logs</h1>
          <p className="subtitle">Real-time monitoring of exam data sync requests (Port 8000)</p>
        </div>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <button
            onClick={() => setIsPaused(!isPaused)}
            className="refresh-btn"
            style={{ background: isPaused ? '#ef4444' : '#10b981' }}
          >
            {isPaused ? 'Resume' : 'Pause'}
          </button>
          <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '14px' }}>
            <input
              type="checkbox"
              checked={autoScroll}
              onChange={(e) => setAutoScroll(e.target.checked)}
            />
            Auto-scroll
          </label>
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            style={{
              padding: '8px 12px',
              borderRadius: '6px',
              border: '1px solid #d1d5db',
              fontSize: '14px'
            }}
          >
            <option value="all">All Logs</option>
            <option value="request">Requests</option>
            <option value="response">Responses</option>
            <option value="error">Errors</option>
          </select>
          <button onClick={fetchLogs} className="refresh-btn" disabled={isPaused}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 12.5a10 10 0 0 1-18.8 4.2"/>
            </svg>
            Refresh
          </button>
          <button onClick={handleClearLogs} className="btn-danger">
            Clear Logs
          </button>
        </div>
      </div>

      {stats && (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '16px',
          marginBottom: '24px'
        }}>
          <div style={{
            background: 'white',
            padding: '16px',
            borderRadius: '8px',
            border: '1px solid #e5e7eb'
          }}>
            <div style={{ fontSize: '14px', color: '#6b7280', marginBottom: '4px' }}>Total Logs</div>
            <div style={{ fontSize: '28px', fontWeight: '600', color: '#1f2937' }}>{stats.total}</div>
          </div>
          <div style={{
            background: 'white',
            padding: '16px',
            borderRadius: '8px',
            border: '1px solid #e5e7eb'
          }}>
            <div style={{ fontSize: '14px', color: '#6b7280', marginBottom: '4px' }}>Requests</div>
            <div style={{ fontSize: '28px', fontWeight: '600', color: '#3b82f6' }}>
              {stats.by_type?.request || 0}
            </div>
          </div>
          <div style={{
            background: 'white',
            padding: '16px',
            borderRadius: '8px',
            border: '1px solid #e5e7eb'
          }}>
            <div style={{ fontSize: '14px', color: '#6b7280', marginBottom: '4px' }}>Responses</div>
            <div style={{ fontSize: '28px', fontWeight: '600', color: '#10b981' }}>
              {stats.by_type?.response || 0}
            </div>
          </div>
          <div style={{
            background: 'white',
            padding: '16px',
            borderRadius: '8px',
            border: '1px solid #e5e7eb'
          }}>
            <div style={{ fontSize: '14px', color: '#6b7280', marginBottom: '4px' }}>Errors</div>
            <div style={{ fontSize: '28px', fontWeight: '600', color: '#ef4444' }}>
              {stats.by_type?.error || 0}
            </div>
          </div>
        </div>
      )}

      <div style={{
        background: '#1f2937',
        borderRadius: '8px',
        padding: '16px',
        minHeight: '500px',
        maxHeight: '70vh',
        overflowY: 'auto',
        fontFamily: 'monospace',
        fontSize: '13px'
      }}>
        {logs.length === 0 ? (
          <div style={{ color: '#9ca3af', textAlign: 'center', padding: '40px' }}>
            No logs to display
          </div>
        ) : (
          <div>
            {logs.map((log, index) => (
              <div
                key={index}
                style={{
                  padding: '8px',
                  borderBottom: '1px solid #374151',
                  display: 'flex',
                  gap: '12px',
                  alignItems: 'flex-start'
                }}
              >
                <span style={{
                  color: '#6b7280',
                  minWidth: '90px',
                  fontSize: '12px'
                }}>
                  {formatTimestamp(log.timestamp)}
                </span>
                <span style={{
                  color: getLogColor(log.type),
                  minWidth: '20px',
                  display: 'flex',
                  alignItems: 'center'
                }}>
                  {getLogIcon(log.type)}
                </span>
                <span style={{
                  color: getLogColor(log.type),
                  fontWeight: '600',
                  minWidth: '80px',
                  textTransform: 'uppercase',
                  fontSize: '11px'
                }}>
                  {log.type}
                </span>
                <span style={{ color: '#f3f4f6', flex: 1 }}>
                  {log.message}
                </span>
                {log.details?.process_time_ms && (
                  <span style={{
                    color: '#9ca3af',
                    fontSize: '12px',
                    minWidth: '60px',
                    textAlign: 'right'
                  }}>
                    {log.details.process_time_ms}ms
                  </span>
                )}
              </div>
            ))}
            <div ref={logsEndRef} />
          </div>
        )}
      </div>
    </div>
  );
}
