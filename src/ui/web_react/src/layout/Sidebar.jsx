import React, { useEffect } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  Radio,
  CheckSquare,
  Package,
  Truck,
  Inbox,
  History,
  TrendingUp,
  Sliders,
  PlayCircle,
  ExternalLink,
} from 'lucide-react';

/**
 * STEWARD Global Navigation Sidebar
 * Groups: OPERATE / MANAGE / PROVE / GOVERNANCE
 * Keyboard shortcuts: ⌘1 .. ⌘8
 */
export default function Sidebar({ userRole = 'manager', signalCount = 3, approvalCount = 1 }) {
  const navigate = useNavigate();

  // Keyboard navigation shortcuts
  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.metaKey || e.ctrlKey) && !e.shiftKey && !e.altKey) {
        if (e.key === '1') { e.preventDefault(); navigate('/tower'); }
        if (e.key === '2') { e.preventDefault(); navigate('/signals'); }
        if (e.key === '3') { e.preventDefault(); navigate('/approvals'); }
        if (e.key === '4') { e.preventDefault(); navigate('/inventory'); }
        if (e.key === '5') { e.preventDefault(); navigate('/suppliers'); }
        if (e.key === '6') { e.preventDefault(); navigate('/receiving'); }
        if (e.key === '7') { e.preventDefault(); navigate('/decisions'); }
        if (e.key === '8') { e.preventDefault(); navigate('/impact'); }
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [navigate]);

  const navLinkClass = ({ isActive }) =>
    `nav-item ${isActive ? 'active' : ''}`;

  return (
    <aside
      className="sidebar"
      style={{
        width: '260px',
        backgroundColor: 'var(--surface-0)',
        borderRight: '1px solid var(--border)',
        display: 'flex',
        flexDirection: 'column',
        height: '100vh',
        position: 'sticky',
        top: 0,
        padding: '1.25rem 0.85rem',
        overflowY: 'auto',
      }}
    >
      {/* Brand Header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.75rem',
          padding: '0.5rem 0.75rem',
          marginBottom: '1.5rem',
        }}
      >
        <div
          style={{
            width: '34px',
            height: '34px',
            borderRadius: 'var(--radius-sm)',
            background: 'var(--accent)',
            color: '#ffffff',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontWeight: 800,
            fontSize: '0.95rem',
            letterSpacing: '-0.03em',
            boxShadow: '0 2px 4px rgba(37, 99, 235, 0.2)',
          }}
        >
          ST
        </div>
        <div>
          <div
            style={{
              fontWeight: 800,
              fontSize: '1.05rem',
              color: 'var(--ink-1)',
              letterSpacing: '-0.02em',
            }}
          >
            STEWARD
          </div>
          <div style={{ fontSize: '11px', color: 'var(--ink-3)', fontWeight: 500 }}>
            Autonomous Control Tower
          </div>
        </div>
      </div>

      {/* Navigation Sections */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem', flex: 1 }}>
        {/* OPERATE */}
        <div>
          <div
            style={{
              fontSize: '10.5px',
              fontWeight: 700,
              color: 'var(--ink-3)',
              padding: '0.25rem 0.75rem',
              textTransform: 'uppercase',
              letterSpacing: '0.06em',
            }}
          >
            OPERATE
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem', marginTop: '0.35rem' }}>
            <NavLink to="/tower" className={navLinkClass}>
              <LayoutDashboard size={17} />
              <span style={{ flex: 1 }}>Control Tower</span>
              <kbd>⌘1</kbd>
            </NavLink>

            <NavLink to="/signals" className={navLinkClass}>
              <Radio size={17} />
              <span style={{ flex: 1 }}>Signals</span>
              {signalCount > 0 && (
                <span className="badge badge-warning" style={{ padding: '0.1rem 0.4rem', fontSize: '10px' }}>
                  {signalCount}
                </span>
              )}
              <kbd>⌘2</kbd>
            </NavLink>

            {/* Approvals (manager visible) */}
            {userRole !== 'staff' && (
              <NavLink to="/approvals" className={navLinkClass}>
                <CheckSquare size={17} />
                <span style={{ flex: 1 }}>Approvals</span>
                {approvalCount > 0 && (
                  <span className="badge badge-danger" style={{ padding: '0.1rem 0.4rem', fontSize: '10px' }}>
                    {approvalCount}
                  </span>
                )}
                <kbd>⌘3</kbd>
              </NavLink>
            )}
          </div>
        </div>

        {/* MANAGE */}
        <div>
          <div
            style={{
              fontSize: '10.5px',
              fontWeight: 700,
              color: 'var(--ink-3)',
              padding: '0.25rem 0.75rem',
              textTransform: 'uppercase',
              letterSpacing: '0.06em',
            }}
          >
            MANAGE
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem', marginTop: '0.35rem' }}>
            <NavLink to="/inventory" className={navLinkClass}>
              <Package size={17} />
              <span style={{ flex: 1 }}>Inventory</span>
              <kbd>⌘4</kbd>
            </NavLink>

            <NavLink to="/suppliers" className={navLinkClass}>
              <Truck size={17} />
              <span style={{ flex: 1 }}>Suppliers</span>
              <kbd>⌘5</kbd>
            </NavLink>

            <NavLink to="/receiving" className={navLinkClass}>
              <Inbox size={17} />
              <span style={{ flex: 1 }}>Receiving</span>
              <kbd>⌘6</kbd>
            </NavLink>
          </div>
        </div>

        {/* PROVE */}
        <div>
          <div
            style={{
              fontSize: '10.5px',
              fontWeight: 700,
              color: 'var(--ink-3)',
              padding: '0.25rem 0.75rem',
              textTransform: 'uppercase',
              letterSpacing: '0.06em',
            }}
          >
            PROVE
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem', marginTop: '0.35rem' }}>
            <NavLink to="/decisions" className={navLinkClass}>
              <History size={17} />
              <span style={{ flex: 1 }}>Decisions</span>
              <kbd>⌘7</kbd>
            </NavLink>

            <NavLink to="/impact" className={navLinkClass}>
              <TrendingUp size={17} />
              <span style={{ flex: 1 }}>Impact Proof</span>
              <kbd>⌘8</kbd>
            </NavLink>
          </div>
        </div>

        {/* GOVERNANCE (Manager only) */}
        {userRole !== 'staff' && (
          <div>
            <div
              style={{
                fontSize: '10.5px',
                fontWeight: 700,
                color: 'var(--ink-3)',
                padding: '0.25rem 0.75rem',
                textTransform: 'uppercase',
                letterSpacing: '0.06em',
              }}
            >
              GOVERNANCE
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem', marginTop: '0.35rem' }}>
              <NavLink to="/settings/autonomy" className={navLinkClass}>
                <Sliders size={17} />
                <span style={{ flex: 1 }}>Autonomy Policies</span>
              </NavLink>

              <NavLink to="/settings/scenarios" className={navLinkClass}>
                <PlayCircle size={17} />
                <span style={{ flex: 1 }}>Simulation & Scenarios</span>
              </NavLink>
            </div>
          </div>
        )}
      </div>

      {/* Footer utility link */}
      <div style={{ borderTop: '1px solid var(--border)', paddingTop: '0.75rem', marginTop: '0.75rem' }}>
        <a
          href="http://localhost:8501"
          target="_blank"
          rel="noreferrer"
          className="nav-item"
          style={{ fontSize: 'var(--t-meta-size)', color: 'var(--ink-3)' }}
          title="Open internal agent inspection console"
        >
          <ExternalLink size={15} />
          <span>Agent Telemetry Console ↗</span>
        </a>
      </div>
    </aside>
  );
}
