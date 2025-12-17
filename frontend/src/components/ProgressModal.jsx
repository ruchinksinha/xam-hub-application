import React from 'react'

function ProgressModal({ isOpen, steps, onClose, title, message }) {
  if (!isOpen) return null

  const getStepIcon = (status) => {
    switch (status) {
      case 'completed':
        return '✓'
      case 'failed':
        return '✕'
      case 'pending':
        return '○'
      default:
        return '○'
    }
  }

  const getStepClass = (status) => {
    switch (status) {
      case 'completed':
        return 'step-completed'
      case 'failed':
        return 'step-failed'
      case 'pending':
        return 'step-pending'
      default:
        return 'step-pending'
    }
  }

  const allCompleted = steps && steps.every(step => step.status === 'completed')
  const hasFailed = steps && steps.some(step => step.status === 'failed')

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>{title || 'Operation Progress'}</h3>
          <button className="modal-close-btn" onClick={onClose}>×</button>
        </div>

        <div className="modal-body">
          {message && (
            <div className={`modal-message ${hasFailed ? 'message-error' : allCompleted ? 'message-success' : 'message-info'}`}>
              {message}
            </div>
          )}

          {steps && steps.length > 0 && (
            <div className="progress-steps">
              {steps.map((step) => (
                <div key={step.step} className={`progress-step ${getStepClass(step.status)}`}>
                  <span className="step-icon">{getStepIcon(step.status)}</span>
                  <div className="step-content">
                    <div className="step-description">{step.description}</div>
                    {step.error && (
                      <div className="step-error">{step.error}</div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="modal-footer">
          <button className="modal-ok-btn" onClick={onClose}>
            {allCompleted ? 'Done' : hasFailed ? 'Close' : 'OK'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default ProgressModal
