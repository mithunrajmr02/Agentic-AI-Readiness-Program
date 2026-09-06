import React from 'react';

/**
 * SideDockWorkspace Primitive (SIDE DOCK / WORKSPACE LAYOUT)
 * Split-screen master-detail investigation workspace.
 * Left pane: persistent stream/queue; Right pane: rich deep-dive canvas.
 */
export default function SideDockWorkspace({
  dockHeader,
  dockContent,
  workspaceHeader,
  workspaceContent,
  dockWidth = '380px',
  className = '',
}) {
  return (
    <div
      className={`side-dock-workspace ${className}`}
      style={{
        display: 'grid',
        gridTemplateColumns: `${dockWidth} 1fr`,
        gap: '1.5rem',
        alignItems: 'start',
      }}
    >
      {/* Left Dock Pane */}
      <div
        className="dock-pane"
        style={{
          background: 'var(--surface-0)',
          border: '1px solid var(--border)',
          borderRadius: 'var(--radius-md)',
          boxShadow: 'var(--shadow-card)',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
          maxHeight: 'calc(100vh - 7.5rem)',
        }}
      >
        {dockHeader && (
          <div
            style={{
              padding: '1rem 1.25rem',
              borderBottom: '1px solid var(--border)',
              background: 'var(--surface-1)',
            }}
          >
            {dockHeader}
          </div>
        )}
        <div style={{ overflowY: 'auto', flex: 1, padding: '0.75rem' }}>
          {dockContent}
        </div>
      </div>

      {/* Right Workspace Canvas */}
      <div
        className="workspace-pane"
        style={{
          background: 'var(--surface-0)',
          border: '1px solid var(--border)',
          borderRadius: 'var(--radius-md)',
          boxShadow: 'var(--shadow-card)',
          padding: '1.75rem',
          minHeight: '400px',
        }}
      >
        {workspaceHeader && (
          <div
            style={{
              marginBottom: '1.5rem',
              paddingBottom: '1rem',
              borderBottom: '1px solid var(--border)',
            }}
          >
            {workspaceHeader}
          </div>
        )}
        <div>{workspaceContent}</div>
      </div>
    </div>
  );
}
