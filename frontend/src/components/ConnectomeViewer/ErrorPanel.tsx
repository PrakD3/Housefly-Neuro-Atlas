import React from 'react';

export interface ErrorPanelProps {
  error: string;
  statusCode?: number;
  onDismiss?: () => void;
  onRetry?: () => void;
}

export const ErrorPanel: React.FC<ErrorPanelProps> = ({
  error,
  statusCode,
  onDismiss,
  onRetry,
}) => {
  const is503 = statusCode === 503 || error.toLowerCase().includes('unavailable') || error.toLowerCase().includes('authentication');
  const is404 = statusCode === 404 || error.toLowerCase().includes('not found');
  const isEmpty = error.toLowerCase().includes('empty');

  let title = 'ERROR';
  let badgeColor = '#ef4444';
  let badgeBorder = '#7f1d1d';

  if (is503) {
    title = 'REAL CONNECTOME UNAVAILABLE';
    badgeColor = '#f59e0b';
    badgeBorder = '#78350f';
  } else if (is404) {
    title = 'NEURON NOT FOUND';
    badgeColor = '#f97316';
    badgeBorder = '#7c2d12';
  } else if (isEmpty) {
    title = 'EMPTY SUBGRAPH';
    badgeColor = '#94a3b8';
    badgeBorder = '#334155';
  }

  return (
    <div
      role="alert"
      style={{
        position: 'absolute',
        top: '1.5rem',
        left: '50%',
        transform: 'translateX(-50%)',
        zIndex: 50,
        backgroundColor: '#0f172a',
        border: `1px solid ${badgeBorder}`,
        borderRadius: '8px',
        padding: '1rem 1.5rem',
        maxWidth: '520px',
        width: '90%',
        boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.7), 0 0 15px rgba(239, 68, 68, 0.2)',
        display: 'flex',
        flexDirection: 'column',
        gap: '0.5rem',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <div
            style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              backgroundColor: badgeColor,
            }}
          />
          <span
            style={{
              color: badgeColor,
              fontWeight: 700,
              fontSize: '0.85rem',
              letterSpacing: '0.05em',
            }}
          >
            {title}
          </span>
        </div>
        {onDismiss && (
          <button
            onClick={onDismiss}
            aria-label="Dismiss error"
            style={{
              background: 'transparent',
              border: 'none',
              color: '#94a3b8',
              cursor: 'pointer',
              fontSize: '1rem',
              lineHeight: 1,
            }}
          >
            ✕
          </button>
        )}
      </div>

      <p style={{ color: '#cbd5e1', fontSize: '0.85rem', margin: '0.25rem 0' }}>
        {error}
      </p>

      {is503 && (
        <p style={{ color: '#94a3b8', fontSize: '0.75rem', margin: 0 }}>
          Ensure <code style={{ color: '#38bdf8' }}>NEUPRINT_TOKEN</code> is set in your environment if querying real data. You can switch to synthetic mode by setting <code style={{ color: '#38bdf8' }}>CONNECTOME_PROVIDER=synthetic</code>.
        </p>
      )}

      {(onRetry || onDismiss) && (
        <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.25rem' }}>
          {onRetry && (
            <button
              onClick={onRetry}
              className="btn btn-primary"
              style={{ fontSize: '0.75rem', padding: '0.25rem 0.75rem' }}
            >
              Retry
            </button>
          )}
          {onDismiss && (
            <button
              onClick={onDismiss}
              className="btn"
              style={{ fontSize: '0.75rem', padding: '0.25rem 0.75rem' }}
            >
              Dismiss
            </button>
          )}
        </div>
      )}
    </div>
  );
};
