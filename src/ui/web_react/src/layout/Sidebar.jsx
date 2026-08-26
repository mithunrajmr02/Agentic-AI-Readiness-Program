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
 * 07-UX-ARCHITECTURE.md §3.1 Navigation, grouped by job
 * Groups: OPERATE / MANAGE / PROVE / SETTINGS
 * Keyboard shortcuts: ⌘1 .. ⌘8
 */
export default function Sidebar({ userRole = 'manager', signalCount = 0, approvalCount = 0 }) {
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
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', padding: '0.5rem 0.75rem', marginBottom: '1.5rem' }}>
        <div style={{
          width: '32px',
          height: '32px',
          borderRadius: 'var(--radius-sm)',
          background: 'var(--accent)',
          color: '#ffffff',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontWeight: 800,
          fontSize: '0.9rem',
        }}>
          ST
        </div>
        <div>
          <div style={{ fontWeight: 700, fontSize: '1rem', color: 'var(--ink-1)', letterSpacing: '-0.02em' }}>
            STEWARD
          </div>
          <div style={{ fontSize: '11px', color: 'var(--ink-3)' }}>
            Replenishment Control Tower
          </div>
        </div>
      </div>

      {/* Navigation Sections */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem', flex: 1 }}>
        {/* OPERATE */}
        <div>
          <div style={{ fontSize: '11px', fontWeight: 700, color: 'var(--ink-3)', padding: '0.25rem 0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            OPERATE
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem', marginTop: '0.35rem' }}>
            <NavLink to="/tower" className={navLinkClass}>
              <LayoutDashboard size={18} />
              <span style={{ flex: 1 }}>Control Tower</span>
              <kbd style={{ fontSize: '10px', color: 'var(--ink-3)' }}>⌘1</kbd>
            </NavLink>

            <NavLink to="/signals" className={navLinkClass}>
              <Radio size={18} />
              <span style={{ flex: 1 }}>Signals</span>
              {signalCount > 0 && (
                <span className="badge badge-warning" style={{ padding: '0.1rem 0.4rem', fontSize: '10px' }}>
                  {signalCount}
                </span>
              )}
              <kbd style={{ fontSize: '10px', color: 'var(--ink-3)' }}>⌘2</kbd>
            </NavLink>

            {/* Approvals (manager visible) */}
            {userRole !== 'staff' && (
              <NavLink to="/approvals" className={navLinkClass}>
                <CheckSquare size={18} />
                <span style={{ flex: 1 }}>Approvals</span>
                {approvalCount > 0 && (
                  <span className="badge badge-danger" style={{ padding: '0.1rem 0.4rem', fontSize: '10px' }}>
                    {approvalCount}
                  </span>
                )}
                <kbd style={{ fontSize: '10px', color: 'var(--ink-3)' }}>⌘3</kbd>
              </NavLink>
            )}
          </div>
        </div>

        {/* MANAGE */}
        <div>
          <div style={{ fontSize: '11px', fontWeight: 700, color: 'var(--ink-3)', padding: '0.25rem 0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            MANAGE
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem', marginTop: '0.35rem' }}>
            <NavLink to="/inventory" className={navLinkClass}>
              <Package size={18} />
              <span style={{ flex: 1 }}>Inventory</span>
              <kbd style={{ fontSize: '10px', color: 'var(--ink-3)' }}>⌘4</kbd>
            </NavLink>

            <NavLink to="/suppliers" className={navLinkClass}>
              <Truck size={18} />
              <span style={{ flex: 1 }}>Suppliers</span>
              <kbd style={{ fontSize: '10px', color: 'var(--ink-3)' }}>⌘5</kbd>
            </NavLink>

            <NavLink to="/receiving" className={navLinkClass}>
              <Inbox size={18} />
              <span style={{ flex: 1 }}>Receiving</span>
              <kbd style={{ fontSize: '10px', color: 'var(--ink-3)' }}>⌘6</kbd>
            </NavLink>
          </div>
        </div>

        {/* PROVE */}
        <div>
          <div style={{ fontSize: '11px', fontWeight: 700, color: 'var(--ink-3)', padding: '0.25rem 0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            PROVE
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem', marginTop: '0.35rem' }}>
            <NavLink to="/decisions" className={navLinkClass}>
              <History size={18} />
              <span style={{ flex: 1 }}>Decisions</span>
              <kbd style={{ fontSize: '10px', color: 'var(--ink-3)' }}>⌘7</kbd>
            </NavLink>

            <NavLink to="/impact" className={navLinkClass}>
              <TrendingUp size={18} />
              <span style={{ flex: 1 }}>Impact</span>
              <kbd style={{ fontSize: '10px', color: 'var(--ink-3)' }}>⌘8</kbd>
            </NavLink>
          </div>
        </div>

        {/* SETTINGS (Manager only) */}
        {userRole !== 'staff' && (
          <div>
            <div style={{ fontSize: '11px', fontWeight: 700, color: 'var(--ink-3)', padding: '0.25rem 0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              GOVERNANCE
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem', marginTop: '0.35rem' }}>
              <NavLink to="/settings/autonomy" className={navLinkClass}>
                <Sliders size={18} />
                <span style={{ flex: 1 }}>Autonomy Policy</span>
              </NavLink>

              <NavLink to="/settings/scenarios" className={navLinkClass}>
                <PlayCircle size={18} />
                <span style={{ flex: 1 }}>Demo Scenarios</span>
              </NavLink>
            </div>
          </div>
        )}
      </div>

      {/* Footer link to Streamlit Agent Console */}
      <div style={{ borderTop: '1px solid var(--border)', paddingTop: '0.75rem', marginTop: '0.75rem' }}>
        <a
          href="http://localhost:8501"
          target="_blank"
          rel="noreferrer"
          className="nav-item"
          style={{ fontSize: 'var(--t-meta-size)', color: 'var(--ink-3)' }}
          title="Internal inspection tool"
        >
          <ExternalLink size={16} />
          <span>Agent Console</span>
        </a>
      </div>
    </aside>
  );
}
