import React, { useState, useEffect } from 'react'

function OsStatus() {
  const [osImages, setOsImages] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [deleting, setDeleting] = useState(null)

  const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost'

  const fetchOsImages = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await fetch(`${API_BASE_URL}/api/os/list`)
      if (!response.ok) {
        throw new Error('Failed to fetch OS images')
      }
      const data = await response.json()
      setOsImages(data.images || [])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (filename) => {
    if (!confirm(`Are you sure you want to delete ${filename}?`)) {
      return
    }

    try {
      setDeleting(filename)
      const response = await fetch(`${API_BASE_URL}/api/os/delete/${encodeURIComponent(filename)}`, {
        method: 'DELETE'
      })

      if (!response.ok) {
        throw new Error('Failed to delete OS image')
      }

      await fetchOsImages()
    } catch (err) {
      alert(`Failed to delete: ${err.message}`)
    } finally {
      setDeleting(null)
    }
  }

  const formatBytes = (bytes) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
  }

  const formatDate = (timestamp) => {
    return new Date(timestamp * 1000).toLocaleString()
  }

  useEffect(() => {
    fetchOsImages()
  }, [])

  return (
    <div className="os-status-page">
      <div className="page-header">
        <h1>Node OS Status</h1>
        <button onClick={fetchOsImages} className="btn-refresh" disabled={loading}>
          🔄 Refresh
        </button>
      </div>

      {loading && (
        <div className="loading-message">
          <p>Loading OS images...</p>
        </div>
      )}

      {error && (
        <div className="error-message">
          <p>Error: {error}</p>
          <button onClick={fetchOsImages} className="btn-retry">Retry</button>
        </div>
      )}

      {!loading && !error && osImages.length === 0 && (
        <div className="empty-message">
          <p>No OS images downloaded yet</p>
        </div>
      )}

      {!loading && !error && osImages.length > 0 && (
        <div className="os-images-table">
          <table>
            <thead>
              <tr>
                <th>Filename</th>
                <th>Size</th>
                <th>Downloaded</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {osImages.map((image) => (
                <tr key={image.filename}>
                  <td className="filename-cell">
                    <span className="file-icon">📦</span>
                    {image.filename}
                  </td>
                  <td>{formatBytes(image.size)}</td>
                  <td>{formatDate(image.modified)}</td>
                  <td>
                    <button
                      onClick={() => handleDelete(image.filename)}
                      className="btn-delete"
                      disabled={deleting === image.filename}
                    >
                      {deleting === image.filename ? 'Deleting...' : '🗑️ Delete'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

export default OsStatus
