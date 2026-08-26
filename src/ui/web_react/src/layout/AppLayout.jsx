import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import Header from './Header';

/**
 * 07-UX-ARCHITECTURE.md §9 Layout shell
 * Connects Sidebar, Header, global kill switch banner, and router Outlet.
 */
export default function AppLayout({ currentUser, onSignOut }) {
  const [autonomyMode, setAutonomyMode] = useState('assisted');
  const [killSwitchEngaged, setKillSwitchEngaged] = useState(false);

  const toggleKillSwitch = () => {
    setKillSwitchEngaged(!killSwitchEngaged);
  };

  return (
    <div className="app-container">
      {/* Navigation Sidebar */}
      <Sidebar
        userRole={currentUser?.role || 'manager'}
        signalCount={3}
        approvalCount={1}
      />

      {/* Main Layout Area */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: '100vh', overflowX: 'hidden' }}>
        <Header
          currentUser={currentUser}
          autonomyMode={autonomyMode}
          onAutonomyModeChange={setAutonomyMode}
          killSwitchEngaged={killSwitchEngaged}
          onToggleKillSwitch={toggleKillSwitch}
          onSignOut={onSignOut}
        />

        {/* Global Kill Switch Banner when engaged */}
        {killSwitchEngaged && (
          <div style={{
            background: 'var(--critical)',
            color: '#ffffff',
            padding: '0.65rem 2rem',
            fontWeight: 700,
            fontSize: 'var(--t-body-size)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}>
            <span>⚠ EMERGENCY STOP: Autonomous execution is paused across all categories.</span>
            <button
              onClick={() => setKillSwitchEngaged(false)}
              style={{
                background: 'rgba(255,255,255,0.2)',
                border: '1px solid #ffffff',
                color: '#ffffff',
                padding: '0.2rem 0.6rem',
                borderRadius: 'var(--radius-sm)',
                cursor: 'pointer',
                fontSize: 'var(--t-meta-size)',
                fontWeight: 600,
              }}
            >
              Resume Normal Operation
            </button>
          </div>
        )}

        {/* Router Outlet for screens */}
        <main className="main-content">
          <Outlet context={{ currentUser, autonomyMode, killSwitchEngaged }} />
        </main>
      </div>
    </div>
  );
}
